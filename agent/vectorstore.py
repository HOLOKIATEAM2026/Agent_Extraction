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
        sync_client_kwargs = emb_cfg.get("sync_client_kwargs") or {"timeout": 60.0}
        return OllamaEmbeddings(
            model=model,
            base_url=base_url,
            sync_client_kwargs=sync_client_kwargs,
        )

    raise ValueError(f"Embeddings provider non supporté: {provider}")


def get_chroma_vectorstore(
    config: Dict[str, Any],
    *,
    embedding_function=None,
):
    try:
        from langchain_chroma import Chroma
    except ImportError:
        from langchain_community.vectorstores import Chroma

    vs_cfg = config.get("vectorstore", {}) or {}
    if vs_cfg.get("type", "chroma") != "chroma":
        raise ValueError("vectorstore.type doit être 'chroma'")

    persist_dir = vs_cfg.get("persist_dir", "vectorstore/chroma")
    collection_name = vs_cfg.get("collection_name", "reports")

    if embedding_function is None:
        embedding_function = get_embeddings(config)

    os.makedirs(persist_dir, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        persist_directory=persist_dir,
        embedding_function=embedding_function,
    )
