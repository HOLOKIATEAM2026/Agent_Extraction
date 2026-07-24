import os
import uuid
import traceback
import asyncio
import time
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests

from agent.chunking import chunk_document
from agent.indexing import chunks_to_langchain_docs
from agent.vectorstore import get_chroma_vectorstore, load_config
from agent.extractor import run_agent_extraction
from agent.multi_extractor import run_multi_extraction
from benchmark.approach_a import run_approach_a
from benchmark.approach_b import run_approach_b
from benchmark.approach_c_agent import run_approach_c
from benchmark.approach_d_combo import run_approach_d

#region debug-point extract-slow-performance
def _dbg(event: str, **data: Any) -> None:
    url = os.getenv("DEBUG_SERVER_URL")
    if not url:
        return
    payload = {
        "sessionId": os.getenv("DEBUG_SESSION_ID"),
        "event": event,
        "ts": time.time(),
        **data,
    }
    try:
        requests.post(url, json=payload, timeout=0.8)
    except Exception:
        return
#endregion debug-point extract-slow-performance

app = FastAPI(
    title="Copilot Holokia - RAG API",
    description="API d'extraction intelligente de rapports d'activité via RAG",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://holokia-rag-api.netlify.app",
        "https://agentextraction.netlify.app",
        "https://holokia-rag.vercel.app",
        "https://holokia-jfl1za1y8-boubkers-projects.vercel.app",
        "https://rag-nine-self.vercel.app",
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def _warmup_embeddings() -> None:
    enabled = str(os.getenv("RAG_WARMUP_EMBEDDINGS", "1")).strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return
    try:
        from agent.vectorstore import load_config, get_embeddings

        config_path = os.getenv("RAG_CONFIG_PATH") or "config.yaml"
        cfg = load_config(config_path)
        await asyncio.to_thread(get_embeddings, cfg)
    except Exception:
        return

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant ou invalide")
    
    token = authorization.replace("Bearer ", "")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_anon_key:
        # En mode developpement local sans supabase, on bypass
        if os.getenv("SUPABASE_ENABLED") not in {"1", "true", "yes", "on"}:
            return {"id": "local-user", "email": "local@holokia.com"}
        raise HTTPException(status_code=500, detail="Supabase non configuré")
        
    url = f"{supabase_url}/auth/v1/user"
    headers = {"apikey": supabase_anon_key, "Authorization": f"Bearer {token}"}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            raise HTTPException(status_code=401, detail="Session expirée ou token invalide")
        user_data = res.json()
        return {"user": user_data, "token": token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erreur d'authentification: {str(e)}")

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
    
    # Préserver les questions utilisées si présentes (T8.26)
    if "questions_utilisees" in meta:
        ui["meta"]["questions_utilisees"] = meta["questions_utilisees"]
    elif result_obj and "meta" in result_obj and "questions_utilisees" in result_obj["meta"]:
        ui["meta"]["questions_utilisees"] = result_obj["meta"]["questions_utilisees"]

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
    from agent.vectorstore import get_or_create_faiss_vectorstore, load_config, get_embeddings
    import os
    t0 = time.perf_counter()
    _dbg("index.start", file_path=file_path)

    t_chunks0 = time.perf_counter()
    chunks = chunk_document(file_path)
    _dbg("index.chunk.done", file_path=file_path, ms=(time.perf_counter() - t_chunks0) * 1000.0, chunks=len(chunks or []))
    if not chunks:
        _dbg("index.done", file_path=file_path, ms=(time.perf_counter() - t0) * 1000.0, chunks=0)
        return {"chunks": 0}

    t_docs0 = time.perf_counter()
    lc_docs, _ = chunks_to_langchain_docs(chunks)
    _dbg("index.docs.done", file_path=file_path, ms=(time.perf_counter() - t_docs0) * 1000.0, docs=len(lc_docs or []))
    doc_name = os.path.basename(file_path).split('.')[0]
    t_cfg0 = time.perf_counter()
    config = load_config(config_path)
    _dbg("index.config.done", ms=(time.perf_counter() - t_cfg0) * 1000.0)

    t_emb0 = time.perf_counter()
    embeddings = get_embeddings(config)
    _dbg("index.embeddings.done", ms=(time.perf_counter() - t_emb0) * 1000.0)

    t_vs0 = time.perf_counter()
    vectorstore = get_or_create_faiss_vectorstore(lc_docs, doc_name, embeddings=embeddings, config=config)
    _dbg("index.faiss.done", doc_name=doc_name, ms=(time.perf_counter() - t_vs0) * 1000.0)

    _dbg("index.done", file_path=file_path, doc_name=doc_name, ms=(time.perf_counter() - t0) * 1000.0, docs=len(lc_docs or []))
    return {"chunks": len(lc_docs)}


async def _run_approach(
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
        result_dict = await run_agent_extraction(
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


async def _process_extraction_job_async(
    job_id: str,
    stored_path: str,
    provider: Optional[str],
    model: Optional[str],
    approach: str,
    config: str,
    user_id: Optional[str] = None,
    token: Optional[str] = None
) -> None:
    try:
        JOBS_STORE[job_id]["status"] = "processing"
        
        orig_name = JOBS_STORE[job_id].get("filename", "")
        # Convertir en MD pour l'asynchrone aussi
        stored_path = await asyncio.to_thread(_process_document_to_md, stored_path, orig_name)
        
        pipeline: Dict[str, Any] = {"saved_file": stored_path}
        need_index = str(approach).lower().strip() not in {"a", "approach_a"}
        
        if need_index:
            try:
                pipeline["indexing"] = await asyncio.to_thread(_index_single_file, file_path=stored_path, config_path=config)
            except Exception as e:
                pipeline["indexing_error"] = str(e)
                approach = "a"

        raw_payload = await _run_approach(
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
                doc_id, extr_id = persist_extraction_payload(raw_payload, user_id=user_id, token=token)
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

def _process_extraction_job(
    job_id: str,
    stored_path: str,
    provider: Optional[str],
    model: Optional[str],
    approach: str,
    config: str,
    user_id: Optional[str] = None,
    token: Optional[str] = None,
) -> None:
    try:
        asyncio.run(
            _process_extraction_job_async(
                job_id,
                stored_path,
                provider,
                model,
                approach,
                config,
                user_id,
                token,
            )
        )
    except Exception as e:
        try:
            traceback.print_exc()
            JOBS_STORE[job_id]["status"] = "failed"
            JOBS_STORE[job_id]["error"] = f"{type(e).__name__}: {str(e)}"
            JOBS_STORE[job_id]["completed_at"] = datetime.now().isoformat()
        except Exception:
            return

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
    user_auth: dict = Depends(get_current_user),
):
    try:
        run_id = uuid.uuid4().hex
        t0 = time.perf_counter()
        _dbg(
            "extract.start",
            runId=run_id,
            filename=(file.filename or ""),
            provider=provider,
            model=model,
            approach=approach,
            async_mode=bool(async_mode),
        )
        uploads_dir = "uploads"
        _ensure_dir(uploads_dir)
        fn = file.filename or ""
        orig_name = _safe_filename(fn if fn else "upload")
        # Retirer le préfixe uuid pour permettre la réutilisation du fichier .md en cache
        stored = os.path.join(uploads_dir, orig_name)
        
        with open(stored, "wb") as f:
            t_read0 = time.perf_counter()
            content = await file.read()
            f.write(content)
        _dbg("extract.file_saved", runId=run_id, stored=stored, bytes=len(content or b""), ms=(time.perf_counter() - t_read0) * 1000.0)
            
        # Étape 2 - Conversion en Markdown pour optimiser le token usage
        try:
            from converter.pdf_to_md import pdf_to_markdown_with_tables
            
            _ensure_dir("data/processed")
            md_filename = orig_name.replace('.pdf', '.md')
            # Retirer le UUID pour profiter du cache
            md_path = os.path.join("data/processed", md_filename)
            
            # Convertir en Markdown si c'est un PDF
            if orig_name.lower().endswith('.pdf'):
                t_md0 = time.perf_counter()
                cached_md = os.path.exists(md_path)
                if not cached_md:
                    print(f"[INFO] Conversion de {orig_name} en Markdown...")
                    md_content = await asyncio.to_thread(pdf_to_markdown_with_tables, stored)
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(md_content)
                else:
                    print(f"[INFO] Fichier Markdown trouvé en cache pour {orig_name}")
                # On utilise le Markdown pour la suite du pipeline
                stored = md_path
                _dbg("extract.pdf_to_md", runId=run_id, md_path=md_path, ms=(time.perf_counter() - t_md0) * 1000.0, cached=bool(cached_md))
        except Exception as e:
            # Si la conversion échoue, on continue avec le fichier original
            print(f"Warning: Markdown conversion failed: {e}")
            _dbg("extract.pdf_to_md_error", runId=run_id, error=f"{type(e).__name__}: {e}")

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
                job_id, stored, provider, model, approach, config, user_auth["user"].get("id"), user_auth["token"]
            )
            _dbg("extract.queued", runId=run_id, job_id=job_id, stored=stored, ms=(time.perf_counter() - t0) * 1000.0)
            return JSONResponse(content={"ok": True, "job_id": job_id, "status": "queued"})

        # Sinon (mode synchrone classique, pour la compatibilité avec l'UI actuelle)
        pipeline: Dict[str, Any] = {"saved_file": stored}

        need_index = str(approach).lower().strip() not in {"a", "approach_a"}
        if need_index:
            try:
                t_idx0 = time.perf_counter()
                pipeline["indexing"] = await asyncio.to_thread(_index_single_file, file_path=stored, config_path=config)
                _dbg("extract.indexing_done", runId=run_id, ms=(time.perf_counter() - t_idx0) * 1000.0)
            except Exception as e:
                pipeline["indexing_error"] = str(e)
                approach = "a"
                _dbg("extract.indexing_error", runId=run_id, error=f"{type(e).__name__}: {e}")

        t_run0 = time.perf_counter()
        raw_payload = await _run_approach(
            approach=approach,
            file_path=stored,
            provider=provider,
            model=model,
            config_path=config,
        )
        _dbg("extract.approach_done", runId=run_id, ms=(time.perf_counter() - t_run0) * 1000.0, approach=approach)

        storage: Dict[str, Any] = {"supabase_enabled": False, "document_id": None, "extraction_id": None}
        try:
            from agent.supabase_store import persist_extraction_payload, supabase_enabled

            storage["supabase_enabled"] = bool(supabase_enabled())
            if storage["supabase_enabled"]:
                t_store0 = time.perf_counter()
                doc_id, extr_id = persist_extraction_payload(raw_payload, user_id=user_auth["user"].get("id"), token=user_auth["token"])
                storage["document_id"] = doc_id
                storage["extraction_id"] = extr_id
                _dbg("extract.persist_done", runId=run_id, ms=(time.perf_counter() - t_store0) * 1000.0)
        except Exception as e:
            storage["error"] = f"{type(e).__name__}: {e}"
            _dbg("extract.persist_error", runId=run_id, error=f"{type(e).__name__}: {e}")

        ui = _to_ui_schema(raw_payload)
        ui["pipeline"] = pipeline
        ui["storage"] = storage
        
        _dbg("extract.done", runId=run_id, ms=(time.perf_counter() - t0) * 1000.0)
        return JSONResponse(content=ui)
        
    except Exception as e:
        traceback.print_exc()
        _dbg("extract.fatal_error", error=f"{type(e).__name__}: {e}")
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
    model: str = Form("llama-3.1-8b-instant"),
    cached_files: str = Form(None),
    user_auth: dict = Depends(get_current_user)
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
        from agent.vectorstore import get_embeddings, get_or_create_faiss_vectorstore, load_config
        
        doc_name = "multi_" + "_".join(sorted([os.path.splitext(n)[0] for n in file_names]))
        
        config = load_config()
        if files and lc_docs:
            embeddings = get_embeddings(config)
            if len(lc_docs) > 0:
                vectorstore = get_or_create_faiss_vectorstore(lc_docs, doc_name, embeddings=embeddings, config=config)
            else:
                vectorstore = get_or_create_faiss_vectorstore([], doc_name, embeddings=embeddings, config=config)
        else:
            # Charger depuis le cache
            embeddings = get_embeddings(config)
            
            # Vérifier si le cache existe vraiment sur le serveur (important pour le déploiement Cloud éphémère)
            safe_doc_name = "".join([c if c.isalnum() else "_" for c in doc_name])
            cache_dir = os.path.join("data", "faiss_cache", safe_doc_name)
            if not os.path.exists(os.path.join(cache_dir, "index.faiss")):
                return JSONResponse(status_code=400, content={
                    "ok": False, 
                    "error": "Les fichiers de cette session ne sont plus sur le serveur (cache expiré). Veuillez créer une nouvelle comparaison et ré-uploader les documents."
                })
                
            vectorstore = get_or_create_faiss_vectorstore([], doc_name, embeddings=embeddings, config=config)
        
        # 3. Extraction
        result = await run_multi_extraction(
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
    model: str = Form("llama-3.1-8b-instant"),
    files: List[UploadFile] = File(None),
    cached_files: str = Form(None),
    user_auth: dict = Depends(get_current_user)
):
    """
    Endpoint pour le Mode Chat Libre (Phase 8D).
    """
    try:
        import json
        history_list = json.loads(history)

        try:
            from agent.supabase_store import SupabaseStore, supabase_enabled
            if supabase_enabled():
                store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
                recent = store.get_recent_extractions(limit=5)
                lines = []
                for r in recent:
                    payload = r.get("result") if isinstance(r, dict) else None
                    meta = payload.get("meta") if isinstance(payload, dict) else None
                    if not isinstance(meta, dict):
                        continue
                    ent = meta.get("entreprise")
                    yr = meta.get("annee_rapport")
                    dt = meta.get("date_extraction") or r.get("created_at")
                    mdl = meta.get("modele_utilise") or r.get("model") or r.get("provider")
                    parts = []
                    if ent:
                        parts.append(str(ent))
                    if yr:
                        parts.append(str(yr))
                    head = " · ".join(parts) if parts else "Analyse"
                    lines.append(f"- {head} | {mdl} | {dt}")
                if lines:
                    memory_text = "Mémoire (5 dernières extractions):\n" + "\n".join(lines[:5])
                    if isinstance(history_list, list):
                        history_list = [{"role": "system", "content": memory_text}] + history_list
        except Exception:
            pass
        
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
                            md_content = await asyncio.to_thread(pdf_to_markdown_with_tables, file_path)
                            with open(md_path, 'w', encoding='utf-8') as f:
                                f.write(md_content)
                        file_path_to_chunk = md_path
                    except Exception:
                        file_path_to_chunk = file_path
                else:
                    file_path_to_chunk = file_path
                    
                file_names.append(file.filename)
                
                # Chunking
                chunks = await asyncio.to_thread(chunk_document, file_path_to_chunk, max_chars=2500, overlap_chars=250)
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
            lc_docs, _ = await asyncio.to_thread(chunks_to_langchain_docs, all_chunks)
            
        from agent.vectorstore import get_or_create_faiss_vectorstore, load_config, get_embeddings
        
        # Pour le chat multi-fichiers, on utilise une clé de cache combinée
        doc_name = "chat_" + "_".join(sorted([os.path.splitext(n)[0] for n in file_names]))
        
        # Vérifier si on charge depuis le cache et si le cache existe
        if not files:
            safe_doc_name = "".join([c if c.isalnum() else "_" for c in doc_name])
            cache_dir = os.path.join("data", "faiss_cache", safe_doc_name)
            if not os.path.exists(os.path.join(cache_dir, "index.faiss")):
                return JSONResponse(status_code=400, content={
                    "ok": False, 
                    "error": "Les fichiers de cette session ne sont plus sur le serveur (cache expiré). Veuillez créer un nouveau chat et ré-uploader les documents."
                })

        config_obj = load_config()
        embeddings = get_embeddings(config_obj)
        vectorstore = await asyncio.to_thread(
            get_or_create_faiss_vectorstore,
            lc_docs,
            doc_name,
            embeddings,
            config_obj,
        )
        
        # 3. Réponse du LLM (Chat)
        from agent.chat_extractor import run_chat_rag
        
        result = await asyncio.to_thread(
            run_chat_rag,
            vectorstore,
            message,
            history_list,
            provider,
            model,
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
def get_results_by_entreprise(entreprise: str, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        
        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")
            
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
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
def get_questions(user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
            
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        questions = store.get_custom_questions()
        return {"ok": True, "data": questions}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.post("/questions")
def add_question(q: CustomQuestionCreate, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
            
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
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
def delete_question(q_id: str, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
            
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        success = store.delete_custom_question(q_id)
        return {"ok": success}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.post("/questions/reset")
def reset_questions(user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
            
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        success = store.reset_custom_questions()
        return {"ok": success}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.get("/extractions")
def get_all_extractions(limit: int = 0, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        
        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")
            
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        if limit and limit > 0:
            results = store.get_recent_extractions(limit=limit)
        else:
            results = store.get_all_extractions()

        doc_ids = [
            str(r.get("document_id"))
            for r in results
            if isinstance(r, dict) and r.get("document_id")
        ]
        doc_map: Dict[str, Dict[str, Any]] = {}
        if doc_ids:
            ids = ",".join(sorted(set(doc_ids)))
            params: Dict[str, str] = {"id": f"in.({ids})", "select": "id,file_name,company,year"}
            if store.user_id:
                params["user_id"] = f"eq.{store.user_id}"
            docs = store._get("documents", params=params)
            if isinstance(docs, list):
                for d in docs:
                    if isinstance(d, dict) and d.get("id"):
                        doc_map[str(d["id"])] = d
        
        # Normaliser chaque résultat pour le format UI (T8.27)
        for ext in results:
            if isinstance(ext, dict):
                doc = doc_map.get(str(ext.get("document_id") or ""), {})
                if doc:
                    ext["document_file"] = doc.get("file_name") or ext.get("document_file")
                    ext["document_year"] = doc.get("year") or ext.get("document_year")
                    ext["company"] = doc.get("company") or ext.get("company")
                payload = ext.get("result") if isinstance(ext.get("result"), dict) else None
                if payload:
                    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else None
                    if meta:
                        if not ext.get("company"):
                            ext["company"] = meta.get("entreprise") or meta.get("company") or ext.get("company")
                        if not ext.get("document_file"):
                            src = meta.get("source_file")
                            if isinstance(src, str) and src:
                                ext["document_file"] = os.path.basename(src)
            if "result" in ext and ext["result"]:
                try:
                    # On passe le payload raw stocké dans result
                    ext["ui_result"] = _to_ui_schema(ext["result"])
                except Exception as e:
                    print(f"Erreur de normalisation pour l'extraction {ext.get('id')}: {e}")
                    ext["ui_result"] = None
        
        return {
            "ok": True,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

@app.get("/profile")
def get_profile(user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled

        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")

        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        data = store._get("entreprise_profil", params={"order": "updated_at.desc"})
        return {"ok": True, "data": data if isinstance(data, list) else []}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

@app.post("/profile")
def create_profile(request: dict, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled

        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")

        user_id = user_auth["user"].get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Utilisateur non authentifié")

        nom = request.get("nom")
        if not isinstance(nom, str) or not nom.strip():
            raise HTTPException(status_code=400, detail="Le champ 'nom' est requis")

        payload: Dict[str, Any] = {
            "user_id": user_id,
            "nom": nom.strip(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        if "secteur" in request:
            payload["secteur"] = request.get("secteur")

        store = SupabaseStore(user_id=user_id, token=user_auth["token"])
        data = store._post(
            "entreprise_profil",
            params={"on_conflict": "user_id,nom"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
        if isinstance(data, list) and data:
            return {"ok": True, "data": data[0]}
        return {"ok": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

def _score_pair_from_payload(payload: dict) -> Tuple[float, float]:
    try:
        cyber = payload.get("diagnostic_cyber_gouvernance")
        nist_score = 0.0
        if isinstance(cyber, dict):
            n = cyber.get("conformite_nist")
            if isinstance(n, dict):
                conf = n.get("confiance")
                if isinstance(conf, (int, float)):
                    nist_score = float(conf) * 5.0
        data = payload.get("diagnostic_data")
        data_score = 0.0
        if isinstance(data, dict):
            confs = []
            for _, f in data.items():
                if isinstance(f, dict) and isinstance(f.get("confiance"), (int, float)):
                    confs.append(float(f["confiance"]))
            if confs:
                data_score = (sum(confs) / len(confs)) * 5.0
        return nist_score, data_score
    except Exception:
        return 0.0, 0.0

@app.get("/profile/evolution")
def get_profile_evolution(company: str = "", limit: int = 30, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled

        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")

        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        rows = store.get_recent_extractions(limit=max(1, min(int(limit or 30), 100)))
        points = []
        for r in reversed(rows):
            payload = r.get("result") if isinstance(r, dict) else None
            if not isinstance(payload, dict):
                continue
            if company:
                meta = payload.get("meta")
                if not isinstance(meta, dict) or (meta.get("entreprise") or "") != company:
                    continue
            nist, data = _score_pair_from_payload(payload)
            points.append({
                "created_at": r.get("created_at"),
                "score_nist": nist,
                "score_data": data,
            })
        return {"ok": True, "data": points}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

@app.get("/profile/summary")
def get_profile_summary(company: str = "", user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled

        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")

        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        rows = store.get_recent_extractions(limit=100)
        if company:
            rows = [
                r for r in rows
                if isinstance(r, dict)
                and isinstance(r.get("result"), dict)
                and isinstance(r["result"].get("meta"), dict)
                and (r["result"]["meta"].get("entreprise") or "") == company
            ]
        if not rows:
            return {"ok": True, "summary": ""}
        oldest = rows[-1]
        newest = rows[0]
        p_old = oldest.get("result") if isinstance(oldest, dict) else None
        p_new = newest.get("result") if isinstance(newest, dict) else None
        if not isinstance(p_old, dict) or not isinstance(p_new, dict):
            return {"ok": True, "summary": ""}
        old_nist, _ = _score_pair_from_payload(p_old)
        new_nist, _ = _score_pair_from_payload(p_new)
        d0 = oldest.get("created_at") or ""
        d1 = newest.get("created_at") or ""
        summary = f"Depuis votre premier diagnostic ({d0}), votre score NIST est passé de {old_nist:.1f} à {new_nist:.1f} ({d1})."
        return {"ok": True, "summary": summary}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

@app.patch("/profile/{profile_id}")
def update_profile(profile_id: str, request: dict, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled

        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")

        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        payload: Dict[str, Any] = {}
        if isinstance(request.get("nom"), str) and request.get("nom").strip():
            payload["nom"] = request["nom"].strip()
        if "secteur" in request:
            payload["secteur"] = request.get("secteur")
        if not payload:
            return {"ok": True, "data": None}
        payload["updated_at"] = datetime.utcnow().isoformat()
        data = store._patch(
            "entreprise_profil",
            params={"id": f"eq.{profile_id}"},
            json=payload,
            prefer="return=representation",
        )
        if isinstance(data, list) and data:
            return {"ok": True, "data": data[0]}
        return {"ok": True, "data": data}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

@app.get("/extractions/{extraction_id}")
def get_extraction_by_id(extraction_id: str, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        
        if not supabase_enabled():
            raise HTTPException(status_code=503, detail="Supabase n'est pas activé ou configuré dans .env")
            
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        result = store.get_extraction_by_id(extraction_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Extraction non trouvée")
            
        # Normaliser pour le format UI
        if "result" in result and result["result"]:
            try:
                result["ui_result"] = _to_ui_schema(result["result"])
            except Exception as e:
                print(f"Erreur de normalisation pour l'extraction {extraction_id}: {e}")
                result["ui_result"] = None
            
        return {
            "ok": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": f"{type(e).__name__}: {str(e)}"})

# ---------------------------------------------------------------------------
# ROUTES: HISTORIQUE MULTI-DOCUMENTS & CHAT (Supabase)
# ---------------------------------------------------------------------------

@app.get("/history/multi")
def get_multi_history(user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        return {"ok": True, "data": store.get_multi_history()}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.post("/history/multi")
async def save_multi_history(request: dict, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        # On renomme date -> created_at pour matcher la BDD
        session_data = request.copy()
        if "date" in session_data:
            session_data["created_at"] = session_data.pop("date")
        success = store.upsert_multi_session(session_data)
        return {"ok": success}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.delete("/history/multi/{session_id}")
def delete_multi_history(session_id: str, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        success = store.delete_multi_session(session_id)
        return {"ok": success}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.get("/history/chat")
def get_chat_history(user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        return {"ok": True, "data": store.get_chat_history()}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.post("/history/chat")
async def save_chat_history(request: dict, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        # On renomme date -> created_at pour matcher la BDD
        session_data = request.copy()
        if "date" in session_data:
            session_data["created_at"] = session_data.pop("date")
        success = store.upsert_chat_session(session_data)
        return {"ok": success}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.delete("/history/chat/{session_id}")
def delete_chat_history(session_id: str, user_auth: dict = Depends(get_current_user)):
    try:
        from agent.supabase_store import SupabaseStore, supabase_enabled
        if not supabase_enabled():
            return JSONResponse(status_code=503, content={"ok": False, "error": "Supabase n'est pas activé"})
        store = SupabaseStore(user_id=user_auth["user"].get("id"), token=user_auth["token"])
        success = store.delete_chat_session(session_id)
        return {"ok": success}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


