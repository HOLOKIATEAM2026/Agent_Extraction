import os
import threading
import time
from typing import Any, Dict, Optional

import yaml
import requests

_EMBEDDINGS_CACHE: Dict[Any, Any] = {}
_EMBEDDINGS_LOCK = threading.Lock()
_FAISS_LOCKS: Dict[str, threading.Lock] = {}
_FAISS_LOCKS_LOCK = threading.Lock()

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


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Fichier de configuration introuvable: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_embeddings(config: Dict[str, Any]):
    emb_cfg = config.get("embeddings", {}) or {}
    provider = emb_cfg.get("provider", "ollama")

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        model = emb_cfg.get("model", "nomic-embed-text")
        base_url = emb_cfg.get("base_url", "http://localhost:11434")
        # On augmente drastiquement le timeout pour éviter les httpx.ReadTimeout
        sync_client_kwargs = emb_cfg.get("sync_client_kwargs") or {"timeout": 900.0}
        cache_key = (
            "ollama",
            model,
            base_url,
            tuple(sorted((sync_client_kwargs or {}).items())),
        )
        cached = _EMBEDDINGS_CACHE.get(cache_key)
        if cached is not None:
            _dbg("embeddings.cache_hit", provider="ollama", model=model)
            return cached
        with _EMBEDDINGS_LOCK:
            cached = _EMBEDDINGS_CACHE.get(cache_key)
            if cached is not None:
                _dbg("embeddings.cache_hit", provider="ollama", model=model)
                return cached
            t0 = time.perf_counter()
            embeddings = OllamaEmbeddings(
                model=model,
                base_url=base_url,
                client_kwargs=sync_client_kwargs,
            )
            _EMBEDDINGS_CACHE[cache_key] = embeddings
            _dbg("embeddings.init", provider="ollama", model=model, ms=(time.perf_counter() - t0) * 1000.0)
            return embeddings

    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        model = emb_cfg.get("model", "all-MiniLM-L6-v2")
        cache_key = ("huggingface", model)
        cached = _EMBEDDINGS_CACHE.get(cache_key)
        if cached is not None:
            _dbg("embeddings.cache_hit", provider="huggingface", model=model)
            return cached
        with _EMBEDDINGS_LOCK:
            cached = _EMBEDDINGS_CACHE.get(cache_key)
            if cached is not None:
                _dbg("embeddings.cache_hit", provider="huggingface", model=model)
                return cached
            cache_folder = emb_cfg.get("cache_folder") or os.getenv("HF_HOME") or os.path.join("data", "hf_cache")
            try:
                os.makedirs(cache_folder, exist_ok=True)
            except Exception:
                cache_folder = None
            t0 = time.perf_counter()
            if cache_folder:
                embeddings = HuggingFaceEmbeddings(model_name=model, cache_folder=cache_folder)
            else:
                embeddings = HuggingFaceEmbeddings(model_name=model)
            _EMBEDDINGS_CACHE[cache_key] = embeddings
            _dbg("embeddings.init", provider="huggingface", model=model, ms=(time.perf_counter() - t0) * 1000.0)
            return embeddings

    raise ValueError(f"Embeddings provider non supporté: {provider}")


def get_chroma_vectorstore(
    config: Optional[Dict[str, Any]] = None,
    *,
    embedding_function=None,
    persist_dir: Optional[str] = None,
    clear: bool = False
):
    if config is None:
        config = load_config()

    try:
        from langchain_chroma import Chroma
    except ImportError:
        from langchain_community.vectorstores import Chroma

    vs_cfg = config.get("vectorstore", {}) or {}
    if vs_cfg.get("type", "chroma") != "chroma":
        raise ValueError("vectorstore.type doit être 'chroma'")

    if persist_dir is None:
        persist_dir = vs_cfg.get("persist_dir", "vectorstore/chroma")
    collection_name = vs_cfg.get("collection_name", "reports")

    if clear and os.path.exists(persist_dir):
        import shutil
        shutil.rmtree(persist_dir, ignore_errors=True)

    if embedding_function is None:
        embedding_function = get_embeddings(config)

    os.makedirs(persist_dir, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        persist_directory=persist_dir,
        embedding_function=embedding_function,
    )

def get_or_create_faiss_vectorstore(
    chunks: list, 
    doc_name: str, 
    embeddings=None, 
    config: Optional[Dict[str, Any]] = None
):
    """
    Crée un vectorstore FAISS ou le charge depuis le cache s'il existe déjà.
    """
    from langchain_community.vectorstores import FAISS
    import os
    
    # Remplacer les caractères spéciaux dans doc_name pour éviter des problèmes de chemin
    safe_doc_name = "".join([c if c.isalnum() else "_" for c in doc_name])
    
    if config is None:
        config = load_config()
        
    if embeddings is None:
        embeddings = get_embeddings(config)
        
    cache_dir = os.path.join("data", "faiss_cache", safe_doc_name)
    os.makedirs(cache_dir, exist_ok=True)

    with _FAISS_LOCKS_LOCK:
        lock = _FAISS_LOCKS.get(safe_doc_name)
        if lock is None:
            lock = threading.Lock()
            _FAISS_LOCKS[safe_doc_name] = lock

    with lock:
        if os.path.exists(os.path.join(cache_dir, "index.faiss")):
            print(f"[CACHE] Vectorstore FAISS trouvé pour {doc_name}")
            t0 = time.perf_counter()
            vs = FAISS.load_local(cache_dir, embeddings, allow_dangerous_deserialization=True)
            _dbg("faiss.load_local", doc_name=doc_name, cache_dir=cache_dir, ms=(time.perf_counter() - t0) * 1000.0)
            return vs

        if not chunks:
            print("[WARNING] Aucun document fourni et aucun cache trouvé.")
            from langchain_core.documents import Document
            dummy_doc = Document(page_content="empty", metadata={"source": "empty"})
            t0 = time.perf_counter()
            vectorstore = FAISS.from_documents([dummy_doc], embeddings)
            _dbg("faiss.empty_created", doc_name=doc_name, ms=(time.perf_counter() - t0) * 1000.0)
            return vectorstore

        print(f"[INFO] Création du vectorstore FAISS pour {doc_name} (en batchs)...")
        _dbg("faiss.build_start", doc_name=doc_name, docs=len(chunks))

        batch_size = 10
        t0 = time.perf_counter()
        vectorstore = FAISS.from_documents(chunks[:batch_size], embeddings)

        for start in range(batch_size, len(chunks), batch_size):
            end = start + batch_size
            print(f"[INFO] FAISS : embedding batch {start}:{min(end, len(chunks))}/{len(chunks)}")
            vectorstore.add_documents(chunks[start:end])

        vectorstore.save_local(cache_dir)
        print(f"[CACHE] Vectorstore FAISS sauvegardé pour {doc_name}")
        _dbg("faiss.build_done", doc_name=doc_name, docs=len(chunks), ms=(time.perf_counter() - t0) * 1000.0, cache_dir=cache_dir)

        return vectorstore
