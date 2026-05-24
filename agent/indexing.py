import hashlib
import json
import os
import shutil
from typing import Any, Dict, Iterable, List, Optional, Tuple

from langchain_core.documents import Document

from agent.chunking import chunk_document
from agent.vectorstore import get_chroma_vectorstore, load_config


def iter_document_paths(data_dir: str) -> Iterable[str]:
    for root, _, files in os.walk(data_dir):
        for name in files:
            lower = name.lower()
            if lower.endswith((".pdf", ".docx", ".txt")):
                yield os.path.join(root, name)


def _stable_id(parts: List[str]) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8", errors="ignore"))
        h.update(b"\x1f")
    return h.hexdigest()


def _meta_primitive(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    try:
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(v)


def chunks_to_langchain_docs(chunks: List[Dict[str, Any]]) -> Tuple[List[Document], List[str]]:
    docs: List[Document] = []
    ids: List[str] = []

    for idx, c in enumerate(chunks):
        meta: Dict[str, Any] = {
            "type": c.get("type"),
            "file_name": c.get("file_name"),
            "file_path": c.get("file_path"),
            "section": c.get("section"),
        }

        if c.get("type") == "pdf":
            meta["pages"] = _meta_primitive(c.get("pages"))
            meta["title"] = c.get("title")
            id_parts = [
                "pdf",
                str(meta.get("file_path") or ""),
                str(meta.get("pages") or ""),
                str(meta.get("section") or ""),
            ]
        elif c.get("type") == "docx":
            meta["block_indexes"] = _meta_primitive(c.get("block_indexes"))
            id_parts = [
                "docx",
                str(meta.get("file_path") or ""),
                str(meta.get("block_indexes") or ""),
                str(meta.get("section") or ""),
            ]
        else:
            id_parts = [
                "chunk",
                str(meta.get("file_path") or ""),
                str(meta.get("section") or ""),
            ]

        id_parts.append(str(idx))
        chunk_id = _stable_id(id_parts)
        meta["chunk_id"] = chunk_id

        docs.append(Document(page_content=c.get("text") or "", metadata=meta))
        ids.append(chunk_id)

    return docs, ids


def build_chroma_index(
    *,
    data_dir: str = os.path.join("data", "raw"),
    config_path: str = "config.yaml",
    reset: bool = False,
    max_chars: int = 6000,
    overlap_chars: int = 600,
    batch_size: int = 32,
    max_chunks_per_file: Optional[int] = 300,
    limit_files: Optional[int] = None,
    enable_supabase: bool = False,
) -> Dict[str, Any]:
    config = load_config(config_path)
    vs_cfg = config.get("vectorstore", {}) or {}
    persist_dir = vs_cfg.get("persist_dir", "vectorstore/chroma")

    if reset and os.path.exists(persist_dir):
        try:
            shutil.rmtree(persist_dir)
        except PermissionError:
            alt_dir = f"{persist_dir}_reset"
            if os.path.exists(alt_dir):
                shutil.rmtree(alt_dir, ignore_errors=True)
            persist_dir = alt_dir
            config.setdefault("vectorstore", {})
            config["vectorstore"]["persist_dir"] = persist_dir

    vectorstore = get_chroma_vectorstore(config)

    indexed_files = 0
    processed_files = 0
    total_chunks = 0
    skipped_files = 0

    sb = None
    if enable_supabase:
        try:
            from agent.supabase_store import SupabaseStore

            sb = SupabaseStore()
        except Exception as e:
            print(f"[WARN] Supabase disabled: {e}")
            sb = None

    for path in iter_document_paths(data_dir):
        if limit_files is not None and processed_files >= limit_files:
            break
        processed_files += 1
        try:
            print(f"[INFO] Indexing: {path}")
            if sb is not None:
                try:
                    sb.upsert_document(path)
                except Exception as e:
                    print(f"[WARN] Supabase upsert_document failed for {path}: {e}")
            chunks = chunk_document(path, max_chars=max_chars, overlap_chars=overlap_chars)
            if max_chunks_per_file is not None and len(chunks) > max_chunks_per_file:
                chunks = chunks[:max_chunks_per_file]
            docs, ids = chunks_to_langchain_docs(chunks)
            if docs:
                if batch_size <= 0:
                    batch_size = 32
                for start in range(0, len(docs), batch_size):
                    end = start + batch_size
                    print(f"[INFO]   upsert {start}:{min(end, len(docs))}/{len(docs)}")
                    vectorstore.add_documents(docs[start:end], ids=ids[start:end])
            indexed_files += 1
            total_chunks += len(docs)
            print(f"[INFO]   chunks={len(docs)} (total={total_chunks})")
        except Exception as e:
            print(f"[WARN] Skip {path}: {e}")
            skipped_files += 1

    persist_fn = getattr(vectorstore, "persist", None)
    if callable(persist_fn):
        persist_fn()

    return {
        "persist_dir": persist_dir,
        "indexed_files": indexed_files,
        "processed_files": processed_files,
        "skipped_files": skipped_files,
        "total_chunks": total_chunks,
        "collection_name": vs_cfg.get("collection_name", "reports"),
    }
