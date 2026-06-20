import os
from dotenv import load_dotenv
load_dotenv(override=True)

from typing import Any, Dict, Optional, Tuple

import requests
from datetime import date, datetime


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
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[Supabase Error] GET {path} failed: {r.status_code}")
            print(f"[Supabase Error Response] {r.text}")
            raise e
        if not r.text:
            return None

    def _patch(self, path: str, *, params: Optional[Dict[str, str]] = None, json: Any = None, prefer: str = ""):
        headers = dict(self.base_headers)
        if prefer:
            headers["Prefer"] = prefer
        url = self.rest_url.rstrip("/") + "/" + path.lstrip("/")
        r = requests.patch(url, headers=headers, params=params, json=json, timeout=self.timeout_s)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[Supabase Error] PATCH {path} failed: {r.status_code}")
            print(f"[Supabase Error Response] {r.text}")
            raise e
        if not r.text:
            return None
        try:
            return r.json()
        except Exception:
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
        # Get all extractions
        # We don't join with documents here to avoid RLS/Foreign key issues if permissions are tight
        # We need to make sure we only fetch rows for this user (or null)
        params = {
            "select": "id,document_id,approach,provider,model,created_at,result",
            "order": "created_at.desc"
        }

        if self.user_id:
            params["user_id"] = f"eq.{self.user_id}"
            
        extractions = self._get("extractions", params=params)
        
        if not extractions:
            return []
            
        return extractions

    def get_recent_extractions(self, limit: int = 5) -> list:
        params = {
            "select": "id,document_id,approach,provider,model,created_at,result",
            "order": "created_at.desc",
            "limit": str(limit),
        }
        if self.user_id:
            params["user_id"] = f"eq.{self.user_id}"
        data = self._get("extractions", params=params)
        return data if isinstance(data, list) else []

    def get_extraction_by_id(self, extraction_id: str) -> Optional[Dict[str, Any]]:
        params = {
            "id": f"eq.{extraction_id}",
            "select": "id,document_id,approach,provider,model,created_at,result"
        }

        if self.user_id:
            params["user_id"] = f"eq.{self.user_id}"
            
        extractions = self._get("extractions", params=params)
        
        if not extractions or len(extractions) == 0:
            return None
            
        ext = extractions[0]
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
            params={"on_conflict": "user_id,file_path"},
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
        params = {"order": "created_at.desc"}
        if self.user_id:
            params["user_id"] = f"eq.{self.user_id}"
        data = self._get("multi_history", params=params)
        return data if isinstance(data, list) else []

    def get_multi_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        params = {"id": f"eq.{session_id}"}
        if self.user_id:
            params["user_id"] = f"eq.{self.user_id}"
        data = self._get("multi_history", params=params)
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
        params = {"order": "created_at.desc"}
        if self.user_id:
            params["user_id"] = f"eq.{self.user_id}"
        data = self._get("chat_history", params=params)
        return data if isinstance(data, list) else []

    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        params = {"id": f"eq.{session_id}"}
        if self.user_id:
            params["user_id"] = f"eq.{self.user_id}"
        data = self._get("chat_history", params=params)
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


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", ".")
        num = ""
        dot_used = False
        for ch in s:
            if ch.isdigit():
                num += ch
            elif ch == "." and not dot_used:
                num += ch
                dot_used = True
        try:
            return float(num) if num else None
        except Exception:
            return None
    return None


def _iter_conf_fields(payload: Dict[str, Any]):
    for sec, sec_val in payload.items():
        if not isinstance(sec, str) or not sec.startswith("diagnostic_"):
            continue
        if not isinstance(sec_val, dict):
            continue
        for k, field in sec_val.items():
            if isinstance(field, dict) and isinstance(field.get("confiance"), (int, float)):
                yield sec, k, field


def _compute_scores(payload: Dict[str, Any]) -> Tuple[float, float]:
    nist_score = 0.0
    data_score = 0.0

    cyber = payload.get("diagnostic_cyber_gouvernance")
    if isinstance(cyber, dict):
        n = cyber.get("conformite_nist")
        if isinstance(n, dict):
            v = _safe_float(n.get("valeur"))
            if v is not None:
                nist_score = float(v)
            else:
                conf = n.get("confiance")
                if isinstance(conf, (int, float)):
                    nist_score = float(conf) * 5.0

    data = payload.get("diagnostic_data")
    if isinstance(data, dict):
        confs = []
        for _, f in data.items():
            if isinstance(f, dict) and isinstance(f.get("confiance"), (int, float)):
                confs.append(float(f["confiance"]))
        if confs:
            data_score = (sum(confs) / len(confs)) * 5.0

    return nist_score, data_score


def _compute_strengths_axes(payload: Dict[str, Any], top_n: int = 3) -> Tuple[list, list]:
    items = []
    for sec, k, field in _iter_conf_fields(payload):
        conf = float(field.get("confiance") or 0.0)
        items.append((conf, f"{sec}.{k}"))
    items.sort(key=lambda x: x[0])
    axes = [x[1] for x in items[:top_n]]
    forts = [x[1] for x in items[-top_n:]][::-1]
    return forts, axes


def _payload_core(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("ui_result"), dict):
        return payload["ui_result"]
    if isinstance(payload.get("result"), dict) and isinstance(payload["result"].get("result"), dict):
        return payload["result"]["result"]
    if isinstance(payload.get("result"), dict):
        return payload["result"]
    return payload


def _update_company_profile(store: SupabaseStore, payload: Dict[str, Any], company_name: Optional[str]) -> None:
    if not store.user_id or not company_name:
        return
    core = _payload_core(payload)
    nist_score, data_score = _compute_scores(core)
    forts, axes = _compute_strengths_axes(core)
    today = date.today().isoformat()

    existing = store._get(
        "entreprise_profil",
        params={
            "user_id": f"eq.{store.user_id}",
            "nom": f"eq.{company_name}",
            "limit": "1",
        },
    )
    row = existing[0] if isinstance(existing, list) and existing else None
    old_count = int(row.get("nb_rapports_analyses") or 0) if isinstance(row, dict) else 0
    new_count = old_count + 1
    old_nist = float(row.get("score_nist_moyen") or 0.0) if isinstance(row, dict) else 0.0
    old_data = float(row.get("score_data_moyen") or 0.0) if isinstance(row, dict) else 0.0

    score_nist_moyen = (old_nist * old_count + nist_score) / new_count if new_count else nist_score
    score_data_moyen = (old_data * old_count + data_score) / new_count if new_count else data_score

    premier = row.get("premier_diagnostic") if isinstance(row, dict) else None
    payload_row: Dict[str, Any] = {
        "user_id": store.user_id,
        "nom": company_name,
        "score_nist_moyen": score_nist_moyen,
        "score_data_moyen": score_data_moyen,
        "nb_rapports_analyses": new_count,
        "premier_diagnostic": premier or today,
        "dernier_diagnostic": today,
        "points_forts": forts,
        "axes_amelioration": axes,
        "updated_at": datetime.utcnow().isoformat(),
    }
    store._post(
        "entreprise_profil",
        params={"on_conflict": "user_id,nom"},
        json=payload_row,
        prefer="resolution=merge-duplicates",
    )


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
    try:
        extra = _parse_corpus_path(source)
        company = extra.get("company") if isinstance(extra, dict) else None
        if not company:
            company = meta.get("entreprise") if isinstance(meta, dict) else None
        if not company and isinstance(payload.get("meta"), dict):
            company = payload["meta"].get("entreprise")
        _update_company_profile(store, payload, company)
    except Exception:
        pass
    return doc_id, extr_id
