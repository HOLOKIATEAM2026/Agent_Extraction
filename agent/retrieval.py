from typing import Any, Dict, List, Optional

from agent.vectorstore import get_chroma_vectorstore, load_config


def retrieve(
    query: str,
    *,
    k: int = 3,
    config_path: str = "config.yaml",
    file_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    config = load_config(config_path)
    vs = get_chroma_vectorstore(config)

    if file_path:
        try:
            docs = vs.similarity_search(query, k=k, filter={"file_path": file_path})
        except TypeError:
            docs = vs.similarity_search(query, k=k)
    else:
        docs = vs.similarity_search(query, k=k)

    out: List[Dict[str, Any]] = []
    for d in docs:
        meta = d.metadata or {}
        if file_path and meta.get("file_path") != file_path:
            continue
        out.append(
            {
                "text": d.page_content or "",
                "metadata": dict(meta),
            }
        )
    return out

