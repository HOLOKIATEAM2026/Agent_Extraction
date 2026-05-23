import os
from typing import Any, Dict, Optional, Tuple

import requests


def supabase_enabled() -> bool:
    v = (os.getenv("SUPABASE_ENABLED") or "").strip().lower()
    return v in {"1", "true", "yes", "on"}


def _normalize_storage_path(path: str) -> str:
    if not path:
        return path
    p = os.path.normpath(path)
    try:
        cwd = os.path.normpath(os.getcwd())
        common = os.path.commonpath([cwd, p])
        if common == cwd:
            rel = os.path.relpath(p, cwd)
            return rel.replace("\\", "/")
    except Exception:
        pass
    return p.replace("\\", "/")


def _parse_corpus_path(file_path: str) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    norm = os.path.normpath(file_path)
    parts = [p for p in norm.split(os.sep) if p]

    def find_idx(name: str) -> int:
        name_l = name.lower()
        for i, p in enumerate(parts):
            if p.lower() == name_l:
                return i
        return -1

    raw_idx = find_idx("raw")
    if raw_idx != -1 and raw_idx + 1 < len(parts):
        company = parts[raw_idx + 1]
        meta["company"] = company
        if raw_idx + 2 < len(parts):
            maybe_lang = parts[raw_idx + 2]
            if len(maybe_lang) in {2, 3}:
                meta["language"] = maybe_lang
                if raw_idx + 3 < len(parts):
                    maybe_year = parts[raw_idx + 3]
                    if maybe_year.isdigit():
                        meta["year"] = int(maybe_year)
            else:
                if maybe_lang.isdigit():
                    meta["year"] = int(maybe_lang)
    return meta


class SupabaseStore:
    def __init__(
        self,
        *,
        url: Optional[str] = None,
        key: Optional[str] = None,
        timeout_s: int = 20,
    ) -> None:
        self.url = (url or os.getenv("SUPABASE_URL") or "").strip()
        self.key = (
            (key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
        )
        self.timeout_s = timeout_s
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL / SUPABASE_*_KEY")
        self.rest_url = self.url.rstrip("/") + "/rest/v1"
        self.base_headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, *, params: Optional[Dict[str, str]] = None, json: Any = None, prefer: str = ""):
        headers = dict(self.base_headers)
        if prefer:
            headers["Prefer"] = prefer
        url = self.rest_url.rstrip("/") + "/" + path.lstrip("/")
        r = requests.post(url, headers=headers, params=params, json=json, timeout=self.timeout_s)
        r.raise_for_status()
        if not r.text:
            return None
        try:
            return r.json()
        except Exception:
            return None

    def upsert_document(self, file_path: str) -> Optional[str]:
        if not file_path:
            return None

        st_path = _normalize_storage_path(file_path)
        base = os.path.basename(file_path)
        lower = base.lower()
        doc_type = "pdf" if lower.endswith(".pdf") else "docx" if lower.endswith(".docx") else "txt"
        extra = _parse_corpus_path(file_path)
        payload: Dict[str, Any] = {
            "file_path": st_path,
            "file_name": base,
            "doc_type": doc_type,
            "company": extra.get("company"),
            "year": extra.get("year"),
            "language": extra.get("language"),
        }
        data = self._post(
            "documents",
            params={"on_conflict": "file_path"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
        if isinstance(data, list) and data:
            return str(data[0].get("id") or "")
        if isinstance(data, dict):
            return str(data.get("id") or "")
        return None

    def insert_extraction(self, *, document_id: str, meta: Dict[str, Any], payload: Dict[str, Any]) -> Optional[str]:
        if not document_id:
            return None
        row = {
            "document_id": document_id,
            "approach": meta.get("approach"),
            "provider": meta.get("provider"),
            "model": meta.get("model"),
            "result": payload,
        }
        data = self._post("extractions", json=row, prefer="return=representation")
        if isinstance(data, list) and data:
            return str(data[0].get("id") or "")
        if isinstance(data, dict):
            return str(data.get("id") or "")
        return None


def _extract_meta(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("meta"), dict):
        return payload["meta"]
    if isinstance(payload.get("result"), dict) and isinstance(payload["result"].get("meta"), dict):
        return payload["result"]["meta"]
    if isinstance(payload.get("final"), dict) and isinstance(payload["final"].get("meta"), dict):
        return payload["final"]["meta"]
    return {}


def persist_extraction_payload(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    if not supabase_enabled():
        return None, None
    meta = _extract_meta(payload)
    source = meta.get("source_file")
    if not isinstance(source, str) or not source:
        return None, None
    store = SupabaseStore()
    doc_id = store.upsert_document(source)
    if not doc_id:
        return None, None
    extr_id = store.insert_extraction(document_id=doc_id, meta=meta, payload=payload)
    return doc_id, extr_id
