import json
import os
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from agent.chunking import chunk_document
from agent.indexing import chunks_to_langchain_docs
from agent.vectorstore import get_chroma_vectorstore, load_config
from benchmark.approach_a import run_approach_a
from benchmark.approach_b import run_approach_b
from benchmark.approach_c_agent import run_approach_c
from benchmark.approach_d_combo import run_approach_d


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def _bad_request(handler: BaseHTTPRequestHandler, msg: str) -> None:
    _json_response(handler, 400, {"ok": False, "error": msg})


def _server_error(handler: BaseHTTPRequestHandler, msg: str) -> None:
    _json_response(handler, 500, {"ok": False, "error": msg})


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
        model=str(meta.get("model") or ""),
        approach=str(meta.get("approach") or ""),
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
            "qualite": False,
            "accessibilite": False,
            "conformite": False,
            "historisation": False,
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
    a = (approach or "d").strip().lower()
    if a in {"a", "approach_a"}:
        r = run_approach_a(file_path, provider=provider, model=model, config_path=config_path)
        return {"meta": r.meta, "result": r.parsed_json, "raw_response": r.raw_response}
    if a in {"b", "approach_b"}:
        r = run_approach_b(file_path, provider=provider, model=model, config_path=config_path)
        return {"meta": r.meta, "result": r.parsed_json, "retrieved_chunks": r.retrieved_chunks, "raw_response": r.raw_response}
    if a in {"c", "approach_c"}:
        r = run_approach_c(file_path, provider=provider, model=model, config_path=config_path, max_steps=6)
        return {"final": r.final_json, "trace": r.trace}
    r = run_approach_d(file_path, provider=provider, model=model, config_path=config_path, top_k_per_query=2, max_chunks_total=10, max_fix_passes=1)
    return {
        "meta": r.meta,
        "result": r.parsed_json,
        "retrieved_chunks": r.retrieved_chunks,
        "validation": r.validation,
        "raw_response": r.raw_response if r.parsed_json is None else None,
    }


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            _json_response(self, 200, {"ok": True})
            return
        _bad_request(self, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/extract":
            _bad_request(self, "Not found")
            return

        ctype = self.headers.get("Content-Type") or ""
        if "multipart/form-data" not in ctype:
            _bad_request(self, "Expected multipart/form-data")
            return

        try:
            import cgi

            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
            try:
                file_item = form["file"]
            except Exception:
                file_item = None
            if file_item is None:
                _bad_request(self, "Missing file")
                return
            if getattr(file_item, "file", None) is None:
                _bad_request(self, "Missing file")
                return

            provider = form.getfirst("provider", None)
            if provider is not None:
                provider = str(provider).strip() or None

            model = form.getfirst("model", None)
            if model is not None:
                model = str(model).strip() or None

            approach = form.getfirst("approach", "d")
            approach = str(approach).strip() if approach is not None else "d"
            if not approach:
                approach = "d"

            config_path = form.getfirst("config", "config.yaml")
            config_path = str(config_path).strip() if config_path is not None else "config.yaml"
            if not config_path:
                config_path = "config.yaml"

            uploads_dir = "uploads"
            _ensure_dir(uploads_dir)
            fn = getattr(file_item, "filename", None)
            fn = str(fn) if fn is not None else ""
            orig_name = _safe_filename(fn if fn else "upload")
            stored = os.path.join(uploads_dir, f"{uuid.uuid4().hex}_{orig_name}")
            with open(stored, "wb") as f:
                f.write(file_item.file.read())

            pipeline: Dict[str, Any] = {"saved_file": stored}

            need_index = str(approach).lower().strip() not in {"a", "approach_a"}
            if need_index:
                try:
                    pipeline["indexing"] = _index_single_file(file_path=stored, config_path=config_path)
                except Exception as e:
                    pipeline["indexing_error"] = str(e)
                    approach = "a"

            raw_payload = _run_approach(
                approach=approach,
                file_path=stored,
                provider=provider,
                model=model,
                config_path=config_path,
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
            _json_response(self, 200, ui)
        except Exception as e:
            try:
                print(traceback.format_exc())
            except Exception:
                pass
            _server_error(self, f"{type(e).__name__}: {e}")


def main() -> None:
    host = "127.0.0.1"
    port = 8000
    server = HTTPServer((host, port), Handler)
    print(f"[INFO] Server listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
