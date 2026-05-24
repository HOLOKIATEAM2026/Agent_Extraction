import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from agent.llm_provider import LLMProvider
from agent.vectorstore import get_chroma_vectorstore, load_config
from benchmark.approach_c_agent import tool_validate_data


@dataclass(frozen=True)
class ApproachDResult:
    parsed_json: Optional[Dict[str, Any]]
    raw_response: str
    retrieved_chunks: List[Dict[str, Any]]
    validation: Dict[str, Any]
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
        obj = json.loads(block)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _truncate(text: str, limit: int) -> str:
    if limit <= 0:
        return text
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...(truncated)"


def _norm_path(p: Optional[str]) -> Optional[str]:
    if not p:
        return p
    try:
        return os.path.normpath(p).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


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


def _similarity_search_safe(vs, *, query: str, k: int, file_path: Optional[str]):
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


def _dedupe_contexts(contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for c in contexts:
        key = str(c.get("chunk_id") or "") + "|" + str(c.get("pages") or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _format_context_for_llm(contexts: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for c in contexts:
        header = []
        header.append(f"file={c.get('file_name')}")
        if c.get("pages"):
            header.append(f"pages={c.get('pages')}")
        if c.get("section"):
            header.append(f"section={c.get('section')}")
        if c.get("chunk_id"):
            header.append(f"chunk_id={c.get('chunk_id')}")
        parts.append("[" + " | ".join(header) + "]\n" + (c.get("text") or ""))
    return "\n\n".join(parts)


def _build_extraction_prompt(context_text: str, *, validation_issues: Optional[List[Dict[str, Any]]] = None) -> str:
    issues_text = ""
    if validation_issues:
        issues_text = "\nProblèmes détectés sur les extraits (corrige):\n" + json.dumps(
            validation_issues, ensure_ascii=False
        )

    return (
        "Réponds uniquement en JSON valide (aucun texte autour).\n"
        "Ne jamais inventer: si absent => valeur=null, source=null, confiance=0. Pour les listes => valeur=[].\n"
        "Chaque 'source.extrait' DOIT être une sous-chaîne exacte du contexte.\n"
        "Tu DOIS retourner toutes les clés du schéma, même si tout est null.\n"
        "Format à respecter:\n"
        "{"
        "\"meta\": {\"source_file\": string, \"approach\": \"D_rag_plus_validation\", \"provider\": string, \"model\": string},"
        "\"diagnostic_strategique\": {\"taille_marche\": F, \"taux_croissance\": F, \"intensite_concurrentielle\": F, \"concurrents\": L, \"tendances_marche\": L},"
        "\"diagnostic_financier\": {\"chiffre_affaires\": F, \"resultat_net\": F, \"ebitda\": F, \"evolution_n_vs_n1\": F},"
        "\"diagnostic_rh_ops\": {\"effectif_total\": F, \"masse_salariale\": F, \"kpis\": L}"
        "}\n"
        "Où F={\"valeur\": string|null, \"source\": {\"page\": int|null, \"extrait\": string|null}, \"confiance\": float} "
        "et L={\"valeur\": [string], \"source\": {\"page\": int|null, \"extrait\": string|null}, \"confiance\": float}.\n"
        + issues_text
        + "\n\nContexte:\n```text\n"
        + context_text
        + "\n```\n"
    )


def run_approach_d(
    file_path: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
    top_k_per_query: int = 2,
    max_chunks_total: int = 10,
    max_chars_per_doc: int = 600,
    max_llm_context_chars: int = 8000,
    max_fix_passes: int = 1,
) -> ApproachDResult:
    cfg = load_config(config_path)
    vs = get_chroma_vectorstore(cfg)

    contexts: List[Dict[str, Any]] = []
    for q in _queries_for_extraction():
        docs = _similarity_search_safe(vs, query=q, k=top_k_per_query, file_path=file_path)
        for d in docs:
            meta = d.metadata or {}
            if meta.get("file_path") != file_path:
                continue
            contexts.append(
                {
                    "chunk_id": meta.get("chunk_id"),
                    "type": meta.get("type"),
                    "file_name": meta.get("file_name"),
                    "file_path": meta.get("file_path"),
                    "section": meta.get("section"),
                    "pages": meta.get("pages"),
                    "title": meta.get("title"),
                    "text": _truncate(d.page_content or "", max_chars_per_doc),
                }
            )
        if max_chunks_total > 0 and len(contexts) >= max_chunks_total:
            break

    contexts = _dedupe_contexts(contexts)
    if max_chunks_total > 0:
        contexts = contexts[:max_chunks_total]

    context_text = _format_context_for_llm(contexts)
    context_text = _truncate(context_text, max_llm_context_chars)

    llm = LLMProvider(provider=provider, model=model, config_path=config_path)

    extracted: Optional[Dict[str, Any]] = None
    raw = ""
    validation: Dict[str, Any] = {"checked_fields": 0, "issues_count": 0, "issues": []}

    for pass_i in range(0, 1 + max_fix_passes):
        issues = validation.get("issues") if pass_i > 0 else None
        prompt = _build_extraction_prompt(context_text, validation_issues=issues)
        raw = llm.complete(prompt)
        extracted = _try_parse_json(raw)
        if not extracted:
            continue

        extracted.setdefault("meta", {})
        if isinstance(extracted["meta"], dict):
            extracted["meta"].update(
                {
                    "source_file": file_path,
                    "approach": "D_rag_plus_validation",
                    "provider": llm.provider,
                    "model": llm.model_name,
                    "top_k_per_query": top_k_per_query,
                    "max_chunks_total": max_chunks_total,
                }
            )

        validation = tool_validate_data(extracted=extracted, contexts=contexts)
        if validation.get("issues_count", 0) <= 0:
            break

    meta = {
        "source_file": file_path,
        "approach": "D_rag_plus_validation",
        "provider": llm.provider,
        "model": llm.model_name,
        "top_k_per_query": top_k_per_query,
        "max_chunks_total": max_chunks_total,
        "max_chars_per_doc": max_chars_per_doc,
        "max_llm_context_chars": max_llm_context_chars,
        "max_fix_passes": max_fix_passes,
    }

    return ApproachDResult(
        parsed_json=extracted,
        raw_response=raw,
        retrieved_chunks=[
            {
                "chunk_id": c.get("chunk_id"),
                "type": c.get("type"),
                "file_name": c.get("file_name"),
                "file_path": c.get("file_path"),
                "section": c.get("section"),
                "pages": c.get("pages"),
                "title": c.get("title"),
            }
            for c in contexts
        ],
        validation=validation,
        meta=meta,
    )


def save_result(result: ApproachDResult, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    payload: Dict[str, Any] = {
        "meta": result.meta,
        "retrieved_chunks": result.retrieved_chunks,
        "validation": result.validation,
        "result": result.parsed_json,
        "raw_response": result.raw_response if result.parsed_json is None else None,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    try:
        from agent.supabase_store import persist_extraction_payload

        persist_extraction_payload(payload)
    except Exception:
        pass
