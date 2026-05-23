import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from agent.chunking import chunk_document
from agent.llm_provider import LLMProvider


@dataclass(frozen=True)
class ApproachAResult:
    raw_response: str
    parsed_json: Optional[Dict[str, Any]]
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


def _build_prompt(document_text: str) -> str:
    return (
        "Réponds uniquement en JSON valide (aucun texte autour).\n"
        "Ne jamais inventer: si absent => valeur=null, source=null, confiance=0. Pour les listes => valeur=[].\n"
        "Si la page est identifiable via 'Page X' => page=X sinon page=null.\n"
        "Format à respecter:\n"
        "{"
        "\"meta\": {\"source_file\": string, \"approach\": \"A_direct_llm\", \"provider\": string, \"model\": string, \"input_truncated\": boolean},"
        "\"diagnostic_strategique\": {\"taille_marche\": F, \"taux_croissance\": F, \"intensite_concurrentielle\": F, \"concurrents\": L, \"tendances_marche\": L},"
        "\"diagnostic_financier\": {\"chiffre_affaires\": F, \"resultat_net\": F, \"ebitda\": F, \"evolution_n_vs_n1\": F},"
        "\"diagnostic_rh_ops\": {\"effectif_total\": F, \"masse_salariale\": F, \"kpis\": L}"
        "}\n"
        "Où F={\"valeur\": string|null, \"source\": {\"page\": int|null, \"extrait\": string|null}, \"confiance\": float} "
        "et L={\"valeur\": [string], \"source\": {\"page\": int|null, \"extrait\": string|null}, \"confiance\": float}.\n"
        "Contenu:\n"
        "```text\n"
        f"{document_text}\n"
        "```\n"
    )


def _prepare_document_text(
    file_path: str,
    *,
    max_chars: int,
    max_chunks: int,
) -> Tuple[str, bool]:
    chunks = chunk_document(file_path, max_chars=max_chars, overlap_chars=0)
    if max_chunks > 0:
        chunks = chunks[:max_chunks]
    text = "\n\n".join([c["text"] for c in chunks if c.get("text")])
    truncated = False
    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars]
        truncated = True
    return text, truncated


def run_approach_a(
    file_path: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
    max_chars: int = 8000,
    max_chunks: int = 2,
) -> ApproachAResult:
    llm = LLMProvider(provider=provider, model=model, config_path=config_path)
    document_text, truncated = _prepare_document_text(
        file_path, max_chars=max_chars, max_chunks=max_chunks
    )
    prompt = _build_prompt(document_text)
    raw = llm.complete(prompt)
    parsed = _try_parse_json(raw)

    meta = {
        "source_file": file_path,
        "approach": "A_direct_llm",
        "provider": llm.provider,
        "model": llm.model_name,
        "input_truncated": bool(truncated),
        "max_chars": max_chars,
        "max_chunks": max_chunks,
    }

    if parsed is not None:
        if isinstance(parsed, dict):
            parsed.setdefault("meta", {})
            if isinstance(parsed["meta"], dict):
                parsed["meta"].update(meta)
        else:
            parsed = None

    return ApproachAResult(raw_response=raw, parsed_json=parsed, meta=meta)


def save_result(result: ApproachAResult, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    payload: Dict[str, Any]
    if result.parsed_json is not None:
        payload = result.parsed_json
    else:
        payload = {"meta": result.meta, "raw_response": result.raw_response}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    try:
        from agent.supabase_store import persist_extraction_payload

        persist_extraction_payload(payload)
    except Exception:
        pass
