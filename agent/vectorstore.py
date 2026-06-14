import os
from typing import Any, Dict, Optional

import yaml


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
        return OllamaEmbeddings(
            model=model,
            base_url=base_url,
            client_kwargs=sync_client_kwargs, # Nouvelle API Langchain-Ollama
        )
    elif provider == "huggingface" or provider == "sentence-transformers":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        
        model = emb_cfg.get("model", "all-MiniLM-L6-v2")
        model_kwargs = emb_cfg.get("model_kwargs", {})
        encode_kwargs = emb_cfg.get("encode_kwargs", {"normalize_embeddings": True})
        
        return HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

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
    
    if config is None:
        config = load_config()
        
    if embeddings is None:
        embeddings = get_embeddings(config)
        
    cache_dir = os.path.join("data", "vectors")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{doc_name}.faiss")
    
    # Si déjà indexé -> charger depuis le disque (instantané)
    if os.path.exists(cache_path):
        print(f"[CACHE] Vectorstore FAISS trouvé pour {doc_name}")
        return FAISS.load_local(cache_path, embeddings, allow_dangerous_deserialization=True)
    
    # Si pas de chunks, return None or empty? Wait no—if chunks is empty but cache doesn't exist?
    if len(chunks) == 0:
        # Create an empty vectorstore? Wait no—maybe create a dummy one? Or raise error?
        print(f"[WARNING] Pas de chunks pour {doc_name}, création d'un vectorstore vide!")
        from langchain_core.documents import Document
        dummy_doc = Document(page_content="dummy", metadata={})
        vectorstore = FAISS.from_documents([dummy_doc], embeddings)
        vectorstore.save_local(cache_path)
        return vectorstore
    
    # Sinon -> créer et sauvegarder en batchs pour éviter le timeout Ollama
    print(f"[INFO] Création du vectorstore FAISS pour {doc_name} (en batchs)...")
    
    # On initialise le vectorstore avec le premier batch
    batch_size = 10
    if len(chunks) <= batch_size:
        vectorstore = FAISS.from_documents(chunks, embeddings)
    else:
        vectorstore = FAISS.from_documents(chunks[:batch_size], embeddings)
        # On ajoute le reste par batchs
        for start in range(batch_size, len(chunks), batch_size):
            end = start + batch_size
            print(f"[INFO] FAISS : embedding batch {start}:{min(end, len(chunks))}/{len(chunks)}")
            vectorstore.add_documents(chunks[start:end])
        
    vectorstore.save_local(cache_path)
    print(f"[CACHE] Vectorstore FAISS sauvegardé pour {doc_name}")
    
    return vectorstore
