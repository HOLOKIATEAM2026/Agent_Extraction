import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from agent.llm_provider import LLMProvider
from agent.vectorstore import get_chroma_vectorstore, load_config


@dataclass(frozen=True)
class ApproachBResult:
    raw_response: str
    parsed_json: Optional[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    meta: Dict[str, Any]


def _extract_json_block(text: str) -> Optional[str]:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    block = _extract_json_block(text)
    if not block:
        return None
    try:
        return json.loads(block)
    except Exception:
        return None


def _queries_for_extraction() -> List[str]:
    return [
        "chiffre d'affaires 2023 2024 revenus",
        "résultat net bénéfice net net income",
        "EBITDA EBE résultat opérationnel",
        "effectif employés headcount",
        "masse salariale rémunération",
        "performance KPI indicateur opérationnel",
        "taille du marché TAM SAM",
        "taux de croissance du marché",
        "intensité concurrentielle concurrence rivalité",
        "principaux concurrents",
        "tendances du marché",
    ]


def _dedupe_by_chunk_id(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for it in items:
        cid = str(it.get("chunk_id") or "")
        key = cid if cid else json.dumps(it, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _norm_path(p: Optional[str]) -> Optional[str]:
    if not p:
        return p
    try:
        return os.path.normpath(p).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


def _similarity_search_safe(
    vs,
    *,
    query: str,
    k: int,
    file_path: Optional[str],
):
    if not file_path:
        return vs.similarity_search(query, k=k)

    candidates = []
    raw = str(file_path)
    candidates.append(raw)
    candidates.append(raw.replace("/", "\\"))
    candidates.append(raw.replace("\\", "/"))
    try:
        candidates.append(os.path.normpath(raw))
    except Exception:
        pass

    for fp in candidates:
        try:
            docs = vs.similarity_search(query, k=k, filter={"file_path": fp})
            if docs:
                return docs
        except TypeError:
            break
        except Exception:
            continue

    docs = vs.similarity_search(query, k=max(k * 5, k))
    want = _norm_path(file_path)
    if want:
        docs = [d for d in docs if _norm_path((d.metadata or {}).get("file_path")) == want]
    return docs[:k]


def _format_chunk(d) -> Tuple[Dict[str, Any], str]:
    meta = dict(d.metadata or {})
    text = d.page_content or ""
    header_parts: List[str] = []
    header_parts.append(f"file={meta.get('file_name')}")
    if meta.get("type") == "pdf":
        header_parts.append(f"pages={meta.get('pages')}")
        if meta.get("title"):
            header_parts.append(f"title={meta.get('title')}")
    if meta.get("section"):
        header_parts.append(f"section={meta.get('section')}")
    header = " | ".join(header_parts)
    blob = f"[{header}]\n{text}"
    meta_out = {
        "chunk_id": meta.get("chunk_id"),
        "type": meta.get("type"),
        "file_name": meta.get("file_name"),
        "file_path": meta.get("file_path"),
        "section": meta.get("section"),
        "pages": meta.get("pages"),
        "title": meta.get("title"),
    }
    return meta_out, blob


def _build_prompt(context: str) -> str:
    return (
        "Réponds uniquement en JSON valide (aucun texte autour).\n"
        "Ne jamais inventer: si absent => valeur=null, source=null, confiance=0. Pour les listes => valeur=[].\n"
        "Si la page est identifiable => page=int sinon page=null.\n"
        "Tu DOIS retourner toutes les clés du schéma, même si tout est null.\n"
        "Format à respecter:\n"
        "{"
        "\"meta\": {\"source_file\": string, \"approach\": \"B_rag\", \"provider\": string, \"model\": string},"
        "\"diagnostic_strategique\": {\"taille_marche\": F, \"taux_croissance\": F, \"intensite_concurrentielle\": F, \"concurrents\": L, \"tendances_marche\": L},"
        "\"diagnostic_financier\": {\"chiffre_affaires\": F, \"resultat_net\": F, \"ebitda\": F, \"evolution_n_vs_n1\": F},"
        "\"diagnostic_rh_ops\": {\"effectif_total\": F, \"masse_salariale\": F, \"kpis\": L}"
        "}\n"
        "Où F={\"valeur\": string|null, \"source\": {\"page\": int|null, \"extrait\": string|null}, \"confiance\": float} "
        "et L={\"valeur\": [string], \"source\": {\"page\": int|null, \"extrait\": string|null}, \"confiance\": float}.\n"
        "\n"
        "Contexte (chunks retrieval):\n"
        "```text\n"
        f"{context}\n"
        "```\n"
    )


def run_approach_b(
    file_path: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
    top_k_per_query: int = 3,
    max_chunks_total: int = 10,
) -> ApproachBResult:
    cfg = load_config(config_path)
    vs = get_chroma_vectorstore(cfg)

    retrieved: List[Dict[str, Any]] = []
    blobs: List[str] = []

    for q in _queries_for_extraction():
        docs = _similarity_search_safe(vs, query=q, k=top_k_per_query, file_path=file_path)
        if file_path:
            docs = [d for d in docs if (d.metadata or {}).get("file_path") == file_path]
        for d in docs:
            meta_out, blob = _format_chunk(d)
            retrieved.append(meta_out)
            blobs.append(blob)
        if max_chunks_total > 0 and len(blobs) >= max_chunks_total:
            break

    retrieved = _dedupe_by_chunk_id(retrieved)
    if max_chunks_total > 0:
        blobs = blobs[:max_chunks_total]

    context = "\n\n".join(blobs)
    llm = LLMProvider(provider=provider, model=model, config_path=config_path)
    prompt = _build_prompt(context)
    raw = llm.complete(prompt)
    parsed = _try_parse_json(raw)

    meta = {
        "source_file": file_path,
        "approach": "B_rag",
        "provider": llm.provider,
        "model": llm.model_name,
        "top_k_per_query": top_k_per_query,
        "max_chunks_total": max_chunks_total,
    }

    if parsed is not None:
        if isinstance(parsed, dict):
            parsed.setdefault("meta", {})
            if isinstance(parsed["meta"], dict):
                parsed["meta"].update(meta)
        else:
            parsed = None

    return ApproachBResult(
        raw_response=raw,
        parsed_json=parsed,
        retrieved_chunks=retrieved,
        meta=meta,
    )


def save_result(result: ApproachBResult, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    payload: Dict[str, Any]
    if result.parsed_json is not None:
        payload = result.parsed_json
        payload["retrieved_chunks"] = result.retrieved_chunks
    else:
        payload = {
            "meta": result.meta,
            "retrieved_chunks": result.retrieved_chunks,
            "raw_response": result.raw_response,
        }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    try:
        from agent.supabase_store import persist_extraction_payload

        persist_extraction_payload(payload)
    except Exception:
        pass
