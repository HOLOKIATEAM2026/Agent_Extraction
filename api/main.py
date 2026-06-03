import os
import uuid
import traceback
import asyncio
from typing import Any, Dict, Optional, List
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.chunking import chunk_document
from agent.indexing import chunks_to_langchain_docs
from agent.vectorstore import get_chroma_vectorstore, load_config
from agent.extractor import run_agent_extraction
from agent.multi_extractor import run_multi_extraction
from benchmark.approach_a import run_approach_a
from benchmark.approach_b import run_approach_b
from benchmark.approach_c_agent import run_approach_c
from benchmark.approach_d_combo import run_approach_d

app = FastAPI(
    title="Copilot Holokia - RAG API",
    description="API d'extraction intelligente de rapports d'activité via RAG",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory job store for background processing
JOBS_STORE: Dict[str, Dict[str, Any]] = {}

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _safe_filename(name: str) -> str:
    keep = []
    for c in (name or ""):
        if c.isalnum() or c in "._-":
            keep.append(c)
    out = "".join(keep).strip(".")
    return out if out else "upload"


def _derive_ui_meta(*, file_path: str, provider: str, model: str, approach: str) -> Dict[str, Any]:
    base = os.path.basename(file_path)
    entreprise = os.path.splitext(base)[0]
    return {
        "entreprise": entreprise,
        "annee_rapport": None,
        "modele_utilise": model if provider != "ollama" else model,
        "provider": provider,
        "approche": approach,
        "source_file": file_path,
    }


def _ui_empty_field() -> Dict[str, Any]:
    return {"valeur": None, "source": None, "confiance": 0.0}


def _ui_empty_list_field() -> Dict[str, Any]:
    return {"valeur": [], "source": None, "confiance": 0.0}


def _normalize_field(value: Any, *, is_list: bool) -> Dict[str, Any]:
    if isinstance(value, dict) and "valeur" in value:
        out = {
            "valeur": value.get("valeur"),
            "source": value.get("source"),
            "confiance": value.get("confiance", 0.0),
        }
        if out["source"] is not None and not isinstance(out["source"], dict):
            out["source"] = None
        if out["source"] is None:
            out["source"] = None
        try:
            out["confiance"] = float(out["confiance"] or 0.0)
        except Exception:
            out["confiance"] = 0.0
        if is_list and out["valeur"] is None:
            out["valeur"] = []
        return out

    if value is None:
        return _ui_empty_list_field() if is_list else _ui_empty_field()

    if is_list:
        if isinstance(value, list):
            return {"valeur": value, "source": None, "confiance": 0.0}
        return {"valeur": [str(value)], "source": None, "confiance": 0.0}

    if isinstance(value, (str, int, float, bool)):
        return {"valeur": value, "source": None, "confiance": 0.0}

    return {"valeur": str(value), "source": None, "confiance": 0.0}


def _normalize_group(group: Any, *, field_kinds: Dict[str, bool]) -> Dict[str, Any]:
    if not isinstance(group, dict):
        group = {}
    out: Dict[str, Any] = {}
    
    # Process explicit fields
    for k, is_list in field_kinds.items():
        out[k] = _normalize_field(group.get(k), is_list=is_list)
        
    # Process any dynamic extra fields from custom questions
    for k, v in group.items():
        if k not in out:
            # Try to guess if it's a list field based on its current value
            is_list = False
            if isinstance(v, dict) and isinstance(v.get("valeur"), list):
                is_list = True
            elif isinstance(v, list):
                is_list = True
            out[k] = _normalize_field(v, is_list=is_list)
            
    return out


def _to_ui_schema(payload: Dict[str, Any]) -> Dict[str, Any]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    result_obj: Optional[Dict[str, Any]] = None
    if isinstance(payload.get("result"), dict):
        result_obj = payload["result"]
    elif isinstance(payload.get("final"), dict):
        result_obj = payload["final"]
    elif isinstance(payload.get("meta"), dict) and any(k.startswith("diagnostic_") for k in payload.keys()):
        result_obj = payload

    if not isinstance(result_obj, dict):
        result_obj = {}

    ui: Dict[str, Any] = {"meta": {}}

    ui["meta"] = _derive_ui_meta(
        file_path=str(meta.get("source_file") or ""),
        provider=str(meta.get("provider") or ""),
        model=str(meta.get("modele_utilise") or ""),
        approach=str(meta.get("approche") or ""),
    )

    ui["diagnostic_strategique"] = _normalize_group(
        result_obj.get("diagnostic_strategique"),
        field_kinds={
            "taille_marche": False,
            "taux_croissance": False,
            "intensite_concurrentielle": False,
            "concurrents": True,
            "tendances_marche": True,
        },
    )
    ui["diagnostic_financier"] = _normalize_group(
        result_obj.get("diagnostic_financier"),
        field_kinds={
            "chiffre_affaires": False,
            "resultat_net": False,
            "ebitda": False,
            "evolution_n_vs_n1": False,
        },
    )
    ui["diagnostic_rh"] = _normalize_group(
        result_obj.get("diagnostic_rh") or result_obj.get("diagnostic_rh_ops"),
        field_kinds={
            "effectif_total": False,
            "masse_salariale": False,
            "kpis": True,
        },
    )
    ui["diagnostic_data"] = _normalize_group(
        result_obj.get("diagnostic_data"),
        field_kinds={
            "existence_donnees": False,
            "qualite": False,
            "accessibilite": False,
            "volumetrie": False,
            "historisation": False,
            "conformite": False,
            "documentation": False,
        },
    )
    
    ui["diagnostic_cyber_gouvernance"] = _normalize_group(
        result_obj.get("diagnostic_cyber_gouvernance"),
        field_kinds={
            "risques_identifies": True,
            "conformite_nist": False,
            "gouvernance_data": False,
        },
    )

    return ui


def _index_single_file(*, file_path: str, config_path: str) -> Dict[str, Any]:
    from agent.chunking import chunk_document
    from agent.indexing import chunks_to_langchain_docs
    from agent.vectorstore import get_or_create_faiss_vectorstore
    import os

    chunks = chunk_document(file_path)
    if not chunks:
        return {"chunks": 0}

    lc_docs, _ = chunks_to_langchain_docs(chunks)
    doc_name = os.path.basename(file_path).split('.')[0]
    vectorstore = get_or_create_faiss_vectorstore(lc_docs, doc_name)

    return {"chunks": len(lc_docs)}


def _run_approach(
    *,
    approach: str,
    file_path: str,
    provider: Optional[str],
    model: Optional[str],
    config_path: str,
) -> Dict[str, Any]:
    a = (approach or "agent").strip().lower()
    
    # 🆕 NOUVELLE APPROCHE PAR DÉFAUT : L'AGENT FINAL (T4.1)
    if a in {"agent", "final", "t4"}:
        result_dict = run_agent_extraction(
            file_path=file_path, 
            provider=provider, 
            model=model, 
            config_path=config_path
        )
        return {"meta": result_dict.get("meta", {}), "result": result_dict}

    # Anciennes approches du benchmark conservées pour rétrocompatibilité
    if a in {"a", "approach_a"}:
        r = run_approach_a(file_path, provider=provider, model=model, config_path=config_path)
        return {"meta": r.meta, "result": r.parsed_json, "raw_response": r.raw_response}
    if a in {"b", "approach_b"}:
        r = run_approach_b(file_path, provider=provider, model=model, config_path=config_path)
        return {"meta": r.meta, "result": r.parsed_json, "retrieved_chunks": r.retrieved_chunks, "raw_response": r.raw_response}
    if a in {"c", "approach_c"}:
        r = run_approach_c(file_path, provider=provider, model=model, config_path=config_path, max_steps=6)
        return {"final": r.final_json, "trace": r.trace}
    
    # Fallback sur l'approche D
    r = run_approach_d(file_path, provider=provider, model=model, config_path=config_path, top_k_per_query=2, max_chunks_total=10, max_fix_passes=1)
    return {
        "meta": r.meta,
        "result": r.parsed_json,
        "retrieved_chunks": r.retrieved_chunks,
        "validation": r.validation,
        "raw_response": r.raw_response if r.parsed_json is None else None,
    }


def _process_extraction_job(
    job_id: str,
    stored_path: str,
    provider: Optional[str],
    model: Optional[str],
    approach: str,
    config: str
) -> None:
    try:
        JOBS_STORE[job_id]["status"] = "processing"
        
        orig_name = JOBS_STORE[job_id].get("filename", "")
        # Convertir en MD pour l'asynchrone aussi
        stored_path = _process_document_to_md(stored_path, orig_name)
        
        pipeline: Dict[str, Any] = {"saved_file": stored_path}
        need_index = str(approach).lower().strip() not in {"a", "approach_a"}
        
        if need_index:
            try:
                pipeline["indexing"] = _index_single_file(file_path=stored_path, config_path=config)
            except Exception as e:
                pipeline["indexing_error"] = str(e)
                approach = "a"

        raw_payload = _run_approach(
            approach=approach,
            file_path=stored_path,
            provider=provider,
            model=model,
            config_path=config,
        )

        storage: Dict[str, Any] = {"supabase_enabled": False, "document_id": None, "extraction_id": None}
        try:
            from agent.supabase_store import persist_extraction_payload, supabase_enabled

            storage["supabase_enabled"] = bool(supabase_enabled())
            if storage["supabase_enabled"]:
                doc_id, extr_id = persist_extraction_payload(raw_payload)
                storage["document_id"] = doc_id
                storage["extraction_id"] = extr_id
        except Exception as e:
            storage["error"] = f"{type(e).__name__}: {e}"

        ui = _to_ui_schema(raw_payload)
        ui["pipeline"] = pipeline
        ui["storage"] = storage
        
        JOBS_STORE[job_id]["status"] = "completed"
        JOBS_STORE[job_id]["result"] = ui
        JOBS_STORE[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        traceback.print_exc()
        JOBS_STORE[job_id]["status"] = "failed"
        JOBS_STORE[job_id]["error"] = f"{type(e).__name__}: {str(e)}"
        JOBS_STORE[job_id]["completed_at"] = datetime.now().isoformat()

def _process_document_to_md(file_path: str, orig_name: str) -> str:
    """Convertit le document en Markdown et retourne le nouveau chemin."""
    try:
        from converter.pdf_to_md import pdf_to_markdown_with_tables
        
        _ensure_dir("data/processed")
        md_filename = orig_name.replace('.pdf', '.md')
        # On ne met plus d'UUID pour profiter du cache !
        md_path = os.path.join("data/processed", md_filename)
        
        if orig_name.lower().endswith('.pdf'):
            if not os.path.exists(md_path):
                print(f"[INFO] Conversion de {orig_name} en Markdown...")
                md_content = pdf_to_markdown_with_tables(file_path)
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
            else:
                print(f"[INFO] Fichier Markdown trouvé en cache pour {orig_name}")
            return md_path
    except Exception as e:
        print(f"Warning: Async Markdown conversion failed: {e}")
    return file_path

@app.get("/health")
def health_check():
    return {"ok": True}


@app.post("/extract")
async def extract_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    provider: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    approach: str = Form("agent"),
    config: str = Form("config.yaml"),
    async_mode: bool = Form(False),
):
    try:
        uploads_dir = "uploads"
        _ensure_dir(uploads_dir)
        fn = file.filename or ""
        orig_name = _safe_filename(fn if fn else "upload")
        # Retirer le préfixe uuid pour permettre la réutilisation du fichier .md en cache
        stored = os.path.join(uploads_dir, orig_name)
        
        with open(stored, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Étape 2 - Conversion en Markdown pour optimiser le token usage
        try:
            from converter.pdf_to_md import pdf_to_markdown_with_tables
            
            _ensure_dir("data/processed")
            md_filename = orig_name.replace('.pdf', '.md')
            md_path = os.path.join("data/processed", f"{uuid.uuid4().hex}_{md_filename}")
            
            # Convertir en Markdown si c'est un PDF
            if orig_name.lower().endswith('.pdf'):
                md_content = pdf_to_markdown_with_tables(stored)
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                # On utilise le Markdown pour la suite du pipeline
                stored = md_path
        except Exception as e:
            # Si la conversion échoue, on continue avec le fichier original
            print(f"Warning: Markdown conversion failed: {e}")

        # Si async_mode=true, on crée un job et on répond tout de suite
        if async_mode:
            job_id = uuid.uuid4().hex
            JOBS_STORE[job_id] = {
                "id": job_id,
                "status": "queued",
                "filename": orig_name,
                "created_at": datetime.now().isoformat(),
                "result": None,
                "error": None
            }
            background_tasks.add_task(
                _process_extraction_job, 
                job_id, stored, provider, model, approach, config
            )
            return JSONResponse(content={"ok": True, "job_id": job_id, "status": "queued"})

        # Sinon (mode synchrone classique, pour la compatibilité avec l'UI actuelle)
        pipeline: Dict[str, Any] = {"saved_file": stored}

        need_index = str(approach).lower().strip() not in {"a", "approach_a"}
        if need_index:
            try:
                pipeline["indexing"] = _index_single_file(file_path=stored, config_path=config)
            except Exception as e:
                pipeline["indexing_error"] = str(e)
                approach = "a"

        raw_payload = _run_approach(
            approach=approach,
            file_path=stored,
            provider=provider,
            model=model,
            config_path=config,
        )

        storage: Dict[str, Any] = {"supabase_enabled": False, "document_id": None, "extraction_id": None}
        try:
            from agent.supabase_store import persist_extraction_payload, supabase_enabled

            storage["supabase_enabled"] = bool(supabase_enabled())
            if storage["supabase_enabled"]:
                doc_id, extr_id = persist_extraction_payload(raw_payload)
                storage["document_id"] = doc_id
                storage["extraction_id"] = extr_id
        except Exception as e:
            storage["error"] = f"{type(e).__name__}: {e}"

        ui = _to_ui_schema(raw_payload)
        ui["pipeline"] = pipeline
        ui["storage"] = storage
        
        return JSONResponse(content=ui)
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {e}"})


@app.get("/status/{job_id}")
def get_job_status(job_id: str):
    if job_id not in JOBS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = JOBS_STORE[job_id]
    
    # Ne pas renvoyer tout le résultat si le job est juste en cours
    if job["status"] != "completed":
        return {
            "id": job["id"],
            "status": job["status"],
            "filename": job["filename"],
            "created_at": job["created_at"],
            "error": job.get("error")
        }
        
    # Si complété, renvoyer le job avec son résultat complet
    return job


@app.post("/extract-multi")
async def extract_multi(
    files: List[UploadFile] = File(None),
    questions: str = Form(...),
    provider: str = Form("groq"),
    model: str = Form("llama-3.3-70b-versatile"),
    cached_files: str = Form(None)
):
    """
    Endpoint pour le mode Multi-Documents (Phase 8A).
    Reçoit plusieurs fichiers et une ou plusieurs questions.
    """
    try:
        import json
        try:
            questions_list = json.loads(questions)
        except:
            questions_list = [q.strip() for q in questions.split(",") if q.strip()]
            
        if not questions_list:
            raise ValueError("Aucune question valide fournie.")
            
        # 1. Sauvegarder et traiter tous les fichiers
        temp_dir = "uploads"
        _ensure_dir(temp_dir)
        
        all_chunks = []
        file_names = []
        
        if files:
            for file in files:
                if not file.filename:
                    continue
                safe_name = _safe_filename(file.filename)
                # Retirer le préfixe uuid pour garder le même nom
                # et permettre la réutilisation du fichier .md
                unique_name = safe_name
                file_path = os.path.join(temp_dir, unique_name)
                
                # Ne sauvegarder que si le fichier n'existe pas déjà
                if not os.path.exists(file_path):
                    content = await file.read()
                    with open(file_path, "wb") as f:
                        f.write(content)
                    
                # Vérifier si on peut convertir le PDF en MD pour optimiser (T4.0bis)
                if file_path.lower().endswith(".pdf"):
                    try:
                        from converter.pdf_to_md import pdf_to_markdown_with_tables
                        md_dir = os.path.join("data", "processed")
                        _ensure_dir(md_dir)
                        md_path = os.path.join(md_dir, unique_name.replace(".pdf", ".md"))
                        
                        if not os.path.exists(md_path):
                            print(f"[INFO] Conversion de {unique_name} en Markdown...")
                            md_content = pdf_to_markdown_with_tables(file_path)
                            with open(md_path, 'w', encoding='utf-8') as f:
                                f.write(md_content)
                        else:
                            print(f"[INFO] Fichier Markdown trouvé en cache pour {unique_name}")
                        
                        file_path_to_chunk = md_path
                    except Exception as e:
                        print(f"Avertissement: Impossible de convertir le PDF en MD: {e}")
                        file_path_to_chunk = file_path
                else:
                    file_path_to_chunk = file_path
                    
                file_names.append(file.filename)
                # Réduire la taille des chunks de 6000 à 2500 pour éviter l'erreur de dépassement
                # de la fenêtre de contexte d'Ollama (the input length exceeds the context length)
                chunks = chunk_document(file_path_to_chunk, max_chars=2500, overlap_chars=250)
                
                # On remplace le file_name par le nom original pour l'affichage UI
                for c in chunks:
                    c["file_name"] = file.filename
                    
                all_chunks.extend(chunks)
                
        if cached_files:
            try:
                cached_list = json.loads(cached_files)
                file_names.extend(cached_list)
                # Ajout d'un chunk bidon pour passer la vérification
                all_chunks.append({"text": "dummy", "file_name": "dummy"})
            except Exception as e:
                print(f"Erreur parsing cached_files: {e}")
                
        if not all_chunks and not file_names:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Veuillez uploader au moins un fichier."})
            
        # 2. Indexer tout dans un vectorstore temporaire avec des batchs plus petits
        lc_docs = []
        if files:
            lc_docs, _ = chunks_to_langchain_docs(all_chunks)
            
        from langchain_community.vectorstores import FAISS
        from agent.vectorstore import get_embeddings, get_or_create_faiss_vectorstore
        
        doc_name = "multi_" + "_".join(sorted([os.path.splitext(n)[0] for n in file_names]))
        
        if files and lc_docs:
            embeddings = get_embeddings({})
            vectorstore = FAISS.from_documents([lc_docs[0]], embeddings)
            batch_size = 10
            for start in range(1, len(lc_docs), batch_size):
                end = start + batch_size
                print(f"[INFO] Multi-Docs (FAISS) : upsert batch {start}:{min(end, len(lc_docs))}/{len(lc_docs)}")
                vectorstore.add_documents(lc_docs[start:end])
            # Sauvegarder le vectorstore avec le doc_name pour pouvoir le récupérer plus tard
            vectorstore = get_or_create_faiss_vectorstore(lc_docs, doc_name)
        else:
            # Charger depuis le cache
            vectorstore = get_or_create_faiss_vectorstore([], doc_name)
        
        # 3. Extraction
        result = run_multi_extraction(
            vectorstore=vectorstore,
            questions=questions_list,
            provider=provider,
            model=model
        )
        
        return {
            "ok": True,
            "files_analyzed": file_names,
            "questions": questions_list,
            "results": result
        }
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"}
        )

@app.post("/chat")
async def chat_endpoint(
    message: str = Form(...),
    history: str = Form("[]"),
    provider: str = Form("groq"),
    model: str = Form("llama-3.3-70b-versatile"),
    files: List[UploadFile] = File(None),
    cached_files: str = Form(None)
):
    """
    Endpoint pour le Mode Chat Libre (Phase 8D).
    """
    try:
        import json
        history_list = json.loads(history)
        
        # 1. Traiter les fichiers uploadés (si nouveaux)
        temp_dir = "uploads"
        _ensure_dir(temp_dir)
        
        all_chunks = []
        file_names = []
        
        if files:
            for file in files:
                if not file.filename:
                    continue
                    
                safe_name = _safe_filename(file.filename)
                file_path = os.path.join(temp_dir, safe_name)
                
                if not os.path.exists(file_path):
                    content = await file.read()
                    with open(file_path, "wb") as f:
                        f.write(content)
                        
                # Conversion MD
                if file_path.lower().endswith(".pdf"):
                    try:
                        from converter.pdf_to_md import pdf_to_markdown_with_tables
                        md_dir = os.path.join("data", "processed")
                        _ensure_dir(md_dir)
                        md_path = os.path.join(md_dir, safe_name.replace(".pdf", ".md"))
                        
                        if not os.path.exists(md_path):
                            md_content = pdf_to_markdown_with_tables(file_path)
                            with open(md_path, 'w', encoding='utf-8') as f:
                                f.write(md_content)
                        file_path_to_chunk = md_path
                    except Exception:
                        file_path_to_chunk = file_path
                else:
                    file_path_to_chunk = file_path
                    
                file_names.append(file.filename)
                
                # Chunking
                chunks = chunk_document(file_path_to_chunk, max_chars=2500, overlap_chars=250)
                for c in chunks:
                    c["file_name"] = file.filename
                all_chunks.extend(chunks)
                
        # Handle cached files (when restoring chat session without re-uploading)
        elif cached_files:
            try:
                cached_list = json.loads(cached_files)
                file_names.extend(cached_list)
                # We don't need chunks if we're just reading from the FAISS cache
                # But we add a dummy chunk to bypass the "no file" check below
                # The FAISS cache will be loaded directly using doc_name
                all_chunks.append({"text": "dummy", "file_name": "dummy"})
            except Exception as e:
                print(f"Erreur parsing cached_files: {e}")
                
        # 2. Vectorisation (FAISS temporaire ou en cache)
        if not all_chunks and not file_names:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Veuillez uploader au moins un fichier."})
            
        lc_docs = []
        if files:
            lc_docs, _ = chunks_to_langchain_docs(all_chunks)
            
        from agent.vectorstore import get_or_create_faiss_vectorstore
        
        # Pour le chat multi-fichiers, on utilise une clé de cache combinée
        doc_name = "chat_" + "_".join(sorted([os.path.splitext(n)[0] for n in file_names]))
        
        vectorstore = get_or_create_faiss_vectorstore(lc_docs, doc_name)
        
        # 3. Réponse du LLM (Chat)
        from agent.chat_extractor import run_chat_rag
        
        result = run_chat_rag(
            vectorstore=vectorstore,
            message=message,
            history=history_list,
            provider=provider,
            model=model
        )
        
        return {
            "ok": True,
            "answer": result["answer"],
            "citations": result["citations"]
        }
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"}
        )

@app.get("/results/{entreprise}")
def get_results_by_entreprise(entreprise: str):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        
        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")
            
        store = SupabaseStore()
        results = store.get_extractions_by_company(entreprise)
        
        return {
            "ok": True,
            "entreprise": entreprise,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

# ---------------------------------------------------------------------------
# ROUTES: GESTION DES QUESTIONS DYNAMIQUES (T8.24)
# ---------------------------------------------------------------------------
from pydantic import BaseModel

class CustomQuestionCreate(BaseModel):
    categorie: str
    champ: str
    question_text: str
    type: str = "field"

@app.get("/questions")
def get_questions():
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
            
        store = SupabaseStore()
        questions = store.get_custom_questions()
        return {"ok": True, "data": questions}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.post("/questions")
def add_question(q: CustomQuestionCreate):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
            
        store = SupabaseStore()
        q_id = store.add_custom_question(
            categorie=q.categorie,
            champ=q.champ,
            question_text=q.question_text,
            q_type=q.type
        )
        if not q_id:
            return JSONResponse(status_code=500, content={"ok": False, "error": "Échec de l'ajout"})
            
        return {"ok": True, "id": q_id}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.delete("/questions/{q_id}")
def delete_question(q_id: str):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
            
        store = SupabaseStore()
        success = store.delete_custom_question(q_id)
        return {"ok": success}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.post("/questions/reset")
def reset_questions():
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
            
        store = SupabaseStore()
        success = store.reset_custom_questions()
        return {"ok": success}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.get("/extractions")
def get_all_extractions():
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        
        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")
            
        store = SupabaseStore()
        results = store.get_all_extractions()
        
        return {
            "ok": True,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

@app.get("/extractions/{extraction_id}")
def get_extraction_by_id(extraction_id: str):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        
        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")
            
        store = SupabaseStore()
        result = store.get_extraction_by_id(extraction_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Extraction non trouvée")
            
        return {
            "ok": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})


