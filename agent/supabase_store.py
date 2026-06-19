import os
from dotenv import load_dotenv
load_dotenv(override=True)

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
        token: Optional[str] = None,
        user_id: Optional[str] = None,
        timeout_s: int = 20,
    ) -> None:
        self.url = (url or os.getenv("SUPABASE_URL") or "").strip()
        # On utilise toujours ANON_KEY comme apikey
        self.key = (key or os.getenv("SUPABASE_ANON_KEY") or "").strip()
        # Si un token utilisateur est fourni, on l'utilise, sinon on utilise le SERVICE_ROLE_KEY ou ANON_KEY
        self.token = (token or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or self.key).strip()
        self.user_id = user_id
        self.timeout_s = timeout_s
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL / SUPABASE_*_KEY")
        self.rest_url = self.url.rstrip("/") + "/rest/v1"
        self.base_headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, *, params: Optional[Dict[str, str]] = None, json: Any = None, prefer: str = ""):
        headers = dict(self.base_headers)
        if prefer:
            headers["Prefer"] = prefer
        url = self.rest_url.rstrip("/") + "/" + path.lstrip("/")
        r = requests.post(url, headers=headers, params=params, json=json, timeout=self.timeout_s)
        
        # Afficher l'erreur si Supabase rejette la requête
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[Supabase Error] POST {path} failed: {r.status_code}")
            print(f"[Supabase Error Response] {r.text}")
            raise e
            
        if not r.text:
            return None
        try:
            return r.json()
        except Exception:
            return None

    def _get(self, path: str, *, params: Optional[Dict[str, str]] = None):
        url = self.rest_url.rstrip("/") + "/" + path.lstrip("/")
        r = requests.get(url, headers=self.base_headers, params=params, timeout=self.timeout_s)
        r.raise_for_status()
        if not r.text:
            return None
        try:
            return r.json()
        except Exception:
            return None

    def _delete(self, path: str, *, params: Optional[Dict[str, str]] = None):
        url = self.rest_url.rstrip("/") + "/" + path.lstrip("/")
        r = requests.delete(url, headers=self.base_headers, params=params, timeout=self.timeout_s)
        r.raise_for_status()
        if not r.text:
            return None
        try:
            return r.json()
        except Exception:
            return None

    def get_extractions_by_company(self, company: str) -> list:
        # On va chercher les documents de cette entreprise
        docs = self._get("documents", params={"company": f"eq.{company}", "select": "id,file_name,year"})
        if not docs:
            return []
            
        doc_ids = [str(d["id"]) for d in docs]
        if not doc_ids:
            return []
            
        # On va chercher les extractions liées à ces documents
        # On utilise l'opérateur 'in' de PostgREST
        doc_ids_str = ",".join(doc_ids)
        extractions = self._get("extractions", params={
            "document_id": f"in.({doc_ids_str})",
            "select": "id,document_id,approach,provider,model,created_at,result"
        })
        
        if not extractions:
            return []
            
        # On merge les infos du document dans chaque extraction pour que ce soit plus clair
        doc_map = {str(d["id"]): d for d in docs}
        
        results = []
        for ext in extractions:
            doc_info = doc_map.get(str(ext["document_id"]), {})
            ext["document_file"] = doc_info.get("file_name")
            ext["document_year"] = doc_info.get("year")
            results.append(ext)
            
        return results

    def get_all_extractions(self) -> list:
        # Get all extractions with their document info
        extractions = self._get("extractions", params={
            "select": "id,document_id,approach,provider,model,created_at,result,documents(file_name,year,company)"
        })
        
        if not extractions:
            return []
            
        results = []
        for ext in extractions:
            doc = ext.get("documents", {}) or {}
            ext["document_file"] = doc.get("file_name")
            ext["document_year"] = doc.get("year")
            ext["company"] = doc.get("company")
            results.append(ext)
            
        return results

    def get_extraction_by_id(self, extraction_id: str) -> Optional[Dict[str, Any]]:
        extractions = self._get("extractions", params={
            "id": f"eq.{extraction_id}",
            "select": "id,document_id,approach,provider,model,created_at,result,documents(file_name,year,company)"
        })
        
        if not extractions or len(extractions) == 0:
            return None
            
        ext = extractions[0]
        doc = ext.get("documents", {}) or {}
        ext["document_file"] = doc.get("file_name")
        ext["document_year"] = doc.get("year")
        ext["company"] = doc.get("company")
        return ext

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
        if self.user_id:
            payload["user_id"] = self.user_id
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
        if self.user_id:
            row["user_id"] = self.user_id
        data = self._post("extractions", json=row, prefer="return=representation")
        if isinstance(data, list) and data:
            return str(data[0].get("id") or "")
        if isinstance(data, dict):
            return str(data.get("id") or "")
        return None

    def get_custom_questions(self) -> list:
        data = self._get("custom_questions", params={"order": "created_at.asc"})
        return data if isinstance(data, list) else []

    def add_custom_question(self, categorie: str, champ: str, question_text: str, q_type: str = "field") -> Optional[str]:
        row = {
            "categorie": categorie,
            "champ": champ,
            "question_text": question_text,
            "type": q_type,
            "is_default": False
        }
        data = self._post("custom_questions", json=row, prefer="return=representation")
        if isinstance(data, list) and data:
            return str(data[0].get("id") or "")
        if isinstance(data, dict):
            return str(data.get("id") or "")
        return None

    def delete_custom_question(self, q_id: str) -> bool:
        try:
            self._delete("custom_questions", params={"id": f"eq.{q_id}"})
            return True
        except Exception:
            return False

    def reset_custom_questions(self) -> bool:
        try:
            self._delete("custom_questions", params={"is_default": "eq.false"})
            return True
        except Exception:
            return False

    # --- Multi History ---
    def get_multi_history(self) -> list:
        data = self._get("multi_history", params={"order": "created_at.desc"})
        return data if isinstance(data, list) else []

    def get_multi_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        data = self._get("multi_history", params={"id": f"eq.{session_id}"})
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return None

    def upsert_multi_session(self, session_data: Dict[str, Any]) -> bool:
        try:
            if self.user_id:
                session_data["user_id"] = self.user_id
            self._post("multi_history", json=session_data, prefer="resolution=merge-duplicates")
            return True
        except Exception:
            return False

    def delete_multi_session(self, session_id: str) -> bool:
        try:
            self._delete("multi_history", params={"id": f"eq.{session_id}"})
            return True
        except Exception:
            return False

    # --- Chat History ---
    def get_chat_history(self) -> list:
        data = self._get("chat_history", params={"order": "created_at.desc"})
        return data if isinstance(data, list) else []

    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        data = self._get("chat_history", params={"id": f"eq.{session_id}"})
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return None

    def upsert_chat_session(self, session_data: Dict[str, Any]) -> bool:
        try:
            if self.user_id:
                session_data["user_id"] = self.user_id
            self._post("chat_history", json=session_data, prefer="resolution=merge-duplicates")
            return True
        except Exception:
            return False

    def delete_chat_session(self, session_id: str) -> bool:
        try:
            self._delete("chat_history", params={"id": f"eq.{session_id}"})
            return True
        except Exception:
            return False


def _extract_meta(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("meta"), dict):
        return payload["meta"]
    if isinstance(payload.get("result"), dict) and isinstance(payload["result"].get("meta"), dict):
        return payload["result"]["meta"]
    if isinstance(payload.get("final"), dict) and isinstance(payload["final"].get("meta"), dict):
        return payload["final"]["meta"]
    return {}


def persist_extraction_payload(payload: Dict[str, Any], user_id: Optional[str] = None, token: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    if not supabase_enabled():
        return None, None
    meta = _extract_meta(payload)
    source = meta.get("source_file")
    if not isinstance(source, str) or not source:
        return None, None
    store = SupabaseStore(user_id=user_id, token=token)
    doc_id = store.upsert_document(source)
    if not doc_id:
        return None, None
    extr_id = store.insert_extraction(document_id=doc_id, meta=meta, payload=payload)
    return doc_id, extr_id
