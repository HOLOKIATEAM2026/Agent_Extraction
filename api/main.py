import os
import uuid
import traceback
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.chunking import chunk_document
from agent.indexing import chunks_to_langchain_docs
from agent.vectorstore import get_chroma_vectorstore, load_config
from agent.extractor import run_agent_extraction
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
    for k, is_list in field_kinds.items():
        out[k] = _normalize_field(group.get(k), is_list=is_list)
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
    cfg = load_config(config_path)
    emb_cfg = cfg.get("embeddings", {}) or {}
    sync_client_kwargs = emb_cfg.get("sync_client_kwargs") or {}
    if "timeout" not in sync_client_kwargs:
        sync_client_kwargs = {**sync_client_kwargs, "timeout": 300.0}
    cfg = {**cfg, "embeddings": {**emb_cfg, "sync_client_kwargs": sync_client_kwargs}}

    vs = get_chroma_vectorstore(cfg)
    chunks = chunk_document(file_path, max_chars=1600, overlap_chars=120)
    max_chunks = 60
    if len(chunks) > max_chunks:
        n = len(chunks)
        step = n / max_chunks
        picked = []
        for i in range(max_chunks):
            idx = int(i * step)
            if idx >= n:
                idx = n - 1
            picked.append(chunks[idx])
        chunks = picked
    docs, ids = chunks_to_langchain_docs(chunks)
    if docs:
        batch = 12
        for i in range(0, len(docs), batch):
            vs.add_documents(docs[i : i + batch], ids=ids[i : i + batch])
    persist_fn = getattr(vs, "persist", None)
    if callable(persist_fn):
        persist_fn()
    return {"chunks": len(docs)}


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
        stored = os.path.join(uploads_dir, f"{uuid.uuid4().hex}_{orig_name}")
        
        with open(stored, "wb") as f:
            content = await file.read()
            f.write(content)

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

