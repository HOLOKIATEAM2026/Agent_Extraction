import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from agent.docx_parser import parse_docx
from agent.llm_provider import LLMProvider
from agent.pdf_parser import parse_pdf
from agent.vectorstore import get_chroma_vectorstore, load_config


@dataclass(frozen=True)
class ApproachCResult:
    final_json: Optional[Dict[str, Any]]
    raw_final: str
    trace: List[Dict[str, Any]]


def _extract_json_block(text: str) -> Optional[str]:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
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


def tool_search_document(
    *,
    config_path: str,
    query: str,
    file_path: Optional[str] = None,
    k: int = 4,
    max_chars_per_doc: int = 600,
) -> Dict[str, Any]:
    cfg = load_config(config_path)
    vs = get_chroma_vectorstore(cfg)

    docs: List[Any]
    if not file_path:
        docs = vs.similarity_search(query, k=k)
    else:
        candidates = []
        raw = str(file_path)
        candidates.append(raw)
        candidates.append(raw.replace("/", "\\"))
        candidates.append(raw.replace("\\", "/"))
        try:
            candidates.append(os.path.normpath(raw))
        except Exception:
            pass

        got: List[Any] = []
        for fp in candidates:
            try:
                got = vs.similarity_search(query, k=k, filter={"file_path": fp})
                if got:
                    break
            except TypeError:
                got = []
                break
            except Exception:
                continue

        if got:
            docs = got
        else:
            docs = vs.similarity_search(query, k=max(k * 5, k))
            want = _norm_path(file_path)
            if want:
                docs = [d for d in docs if _norm_path((d.metadata or {}).get("file_path")) == want]
            docs = docs[:k]

    out_docs: List[Dict[str, Any]] = []
    for d in docs:
        meta = d.metadata or {}
        if file_path and _norm_path(meta.get("file_path")) != _norm_path(file_path):
            continue
        out_docs.append(
            {
                "chunk_id": meta.get("chunk_id"),
                "file_name": meta.get("file_name"),
                "file_path": meta.get("file_path"),
                "type": meta.get("type"),
                "section": meta.get("section"),
                "pages": meta.get("pages"),
                "title": meta.get("title"),
                "text": _truncate(d.page_content or "", max_chars_per_doc),
            }
        )
    return {"query": query, "k": k, "results": out_docs}


def tool_extract_section(
    *,
    file_path: str,
    section: Optional[str],
    chunk_id: Optional[str] = None,
    contexts: Optional[List[Dict[str, Any]]] = None,
    max_chars: int = 6000,
) -> Dict[str, Any]:
    if chunk_id and contexts:
        for c in contexts:
            if str(c.get("chunk_id")) == str(chunk_id):
                return {
                    "file_path": file_path,
                    "type": c.get("type"),
                    "chunk_id": c.get("chunk_id"),
                    "section": c.get("section"),
                    "pages": c.get("pages"),
                    "title": c.get("title"),
                    "text": _truncate(c.get("text") or "", max_chars),
                }

    lower = file_path.lower()
    if lower.endswith(".pdf"):
        doc = parse_pdf(file_path)
        pages = doc["pages"]
        picked = [p for p in pages if (section is None or p.get("section") == section)]
        joined = "\n\n".join([f"Page {p['page']}\n{p.get('text') or ''}" for p in picked])
        return {
            "file_path": file_path,
            "type": "pdf",
            "section": section,
            "page_count": doc.get("page_count"),
            "text": _truncate(joined, max_chars),
        }

    if lower.endswith(".docx"):
        doc = parse_docx(file_path)
        blocks = doc["blocks"]
        picked = [b for b in blocks if (section is None or b.get("section") == section)]
        lines: List[str] = []
        for b in picked:
            if b.get("type") == "paragraph":
                lines.append(b.get("text") or "")
            elif b.get("type") == "table":
                rows = b.get("rows") or []
                for row in rows:
                    lines.append(" | ".join([c for c in row if c]))
        joined = "\n".join([l for l in lines if l])
        return {
            "file_path": file_path,
            "type": "docx",
            "section": section,
            "block_count": doc.get("block_count"),
            "text": _truncate(joined, max_chars),
        }

    if lower.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        return {
            "file_path": file_path,
            "type": "txt",
            "section": None,
            "text": _truncate(raw, max_chars),
        }

    raise ValueError("Unsupported document type (expected .pdf/.docx/.txt)")


def tool_validate_data(
    *,
    extracted: Dict[str, Any],
    contexts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    haystacks = [(c.get("chunk_id"), (c.get("text") or "")) for c in contexts]

    def check_excerpt(excerpt: Optional[str]) -> bool:
        if not excerpt:
            return True
        ex = str(excerpt).strip()
        if not ex:
            return True
        return any(ex in t for _, t in haystacks)

    issues: List[Dict[str, Any]] = []
    checked = 0

    def walk(obj: Any, path: str) -> None:
        nonlocal checked
        if isinstance(obj, dict):
            if set(obj.keys()) >= {"valeur", "source", "confiance"}:
                checked += 1
                src = obj.get("source") or {}
                excerpt = None
                if isinstance(src, dict):
                    excerpt = src.get("extrait")
                if not check_excerpt(excerpt):
                    issues.append({"path": path, "problem": "extrait_absent_du_contexte"})
            for k, v in obj.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")

    walk(extracted, "")

    return {
        "checked_fields": checked,
        "issues_count": len(issues),
        "issues": issues[:50],
    }


def _system_prompt() -> str:
    return (
        "Agent d'extraction autonome.\n"
        "Réponds UNIQUEMENT par un JSON: {\"tool\":...,\"args\":...} ou {\"final\":...}.\n"
        "Outils disponibles:\n"
        "- search_document: args={\"query\": string, \"k\": int}\n"
        "- extract_section: args={\"section\": string|null} OU args={\"chunk_id\": string}\n"
        "- validate_data: args={\"extracted\": object}\n"
        "Ne jamais inventer: absent => valeur=null, source=null, confiance=0; listes => [].\n"
        "Schéma FINAL attendu:\n"
        "{"
        "\"meta\": {\"source_file\": string, \"approach\": \"C_agent\", \"provider\": string, \"model\": string},"
        "\"diagnostic_strategique\": {\"taille_marche\": F, \"taux_croissance\": F, \"intensite_concurrentielle\": F, \"concurrents\": L, \"tendances_marche\": L},"
        "\"diagnostic_financier\": {\"chiffre_affaires\": F, \"resultat_net\": F, \"ebitda\": F, \"evolution_n_vs_n1\": F},"
        "\"diagnostic_rh_ops\": {\"effectif_total\": F, \"masse_salariale\": F, \"kpis\": L}"
        "}\n"
        "Où F={\"valeur\": string|null, \"source\": {\"page\": int|null, \"extrait\": string|null}, \"confiance\": float} "
        "et L={\"valeur\": [string], \"source\": {\"page\": int|null, \"extrait\": string|null}, \"confiance\": float}.\n"
    )


def _goal_prompt(file_path: str) -> str:
    return (
        f"Document cible: {file_path}\n"
        "Objectif: extraire les champs stratégiques + financiers + RH/ops, avec source(page, extrait) si possible.\n"
        "Commence par appeler search_document sur: chiffre d'affaires; résultat net; EBITDA; effectif.\n"
    )


def _empty_field() -> Dict[str, Any]:
    return {"valeur": None, "source": {"page": None, "extrait": None}, "confiance": 0.0}


def _empty_list_field() -> Dict[str, Any]:
    return {"valeur": [], "source": {"page": None, "extrait": None}, "confiance": 0.0}


def _empty_schema(*, file_path: str, provider: str, model: str) -> Dict[str, Any]:
    return {
        "meta": {
            "source_file": file_path,
            "approach": "C_agent",
            "provider": provider,
            "model": model,
        },
        "diagnostic_strategique": {
            "taille_marche": _empty_field(),
            "taux_croissance": _empty_field(),
            "intensite_concurrentielle": _empty_field(),
            "concurrents": _empty_list_field(),
            "tendances_marche": _empty_list_field(),
        },
        "diagnostic_financier": {
            "chiffre_affaires": _empty_field(),
            "resultat_net": _empty_field(),
            "ebitda": _empty_field(),
            "evolution_n_vs_n1": _empty_field(),
        },
        "diagnostic_rh_ops": {
            "effectif_total": _empty_field(),
            "masse_salariale": _empty_field(),
            "kpis": _empty_list_field(),
        },
    }


def run_approach_c(
    file_path: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    config_path: str = "config.yaml",
    max_steps: int = 8,
    top_k: int = 4,
    max_tool_chars: int = 1500,
) -> ApproachCResult:
    llm = LLMProvider(provider=provider, model=model, config_path=config_path)

    trace: List[Dict[str, Any]] = []
    contexts: List[Dict[str, Any]] = []
    extracted_candidate: Optional[Dict[str, Any]] = None
    searched_terms: List[str] = []
    required_terms = ["chiffre d'affaires", "résultat net", "EBITDA", "effectif"]

    messages: List[Tuple[str, str]] = [
        ("system", _system_prompt()),
        ("user", _goal_prompt(file_path)),
    ]

    for step in range(1, max_steps + 1):
        keep = [messages[0]]
        keep.extend(messages[-6:])
        prompt = "\n\n".join([f"{role.upper()}:\n{content}" for role, content in keep])
        raw = llm.complete(prompt)
        obj = _parse_llm_json(raw)

        trace.append({"step": step, "llm_raw": _truncate(raw, 2000), "parsed": obj})

        if not obj:
            messages.append(("assistant", raw))
            messages.append(("user", "Répond uniquement par un JSON valide (tool ou final)."))
            continue

        if "final" in obj:
            final = obj.get("final")
            if isinstance(final, dict):
                final.setdefault("meta", {})
                if isinstance(final["meta"], dict):
                    final["meta"].update(
                        {
                            "source_file": file_path,
                            "approach": "C_agent",
                            "provider": llm.provider,
                            "model": llm.model_name,
                        }
                    )
                extracted_candidate = final
            if step < max_steps:
                missing = [t for t in required_terms if t.lower() not in " ".join(searched_terms).lower()]
                is_all_null = False
                if isinstance(extracted_candidate, dict):
                    fin = extracted_candidate.get("diagnostic_financier") or {}
                    if isinstance(fin, dict):
                        values = [
                            (fin.get("chiffre_affaires") or {}).get("valeur"),
                            (fin.get("resultat_net") or {}).get("valeur"),
                            (fin.get("ebitda") or {}).get("valeur"),
                        ]
                        is_all_null = all(v is None for v in values)
                if missing or is_all_null:
                    messages.append(("assistant", _truncate(raw, 1200)))
                    messages.append(
                        (
                            "user",
                            "Continue. Avant de répondre final, fais search_document sur: "
                            + ", ".join(missing or required_terms)
                            + ".",
                        )
                    )
                    continue
            return ApproachCResult(final_json=extracted_candidate, raw_final=raw, trace=trace)

        tool = obj.get("tool")
        args = obj.get("args") or {}
        if not isinstance(args, dict):
            args = {}

        tool_result: Dict[str, Any]
        if tool == "search_document":
            q_raw = args.get("query")
            queries: List[str]
            if isinstance(q_raw, list):
                queries = [str(x) for x in q_raw if str(x).strip()]
            else:
                queries = [str(q_raw or "").strip()]

            k = int(args.get("k") or top_k)
            merged: List[Dict[str, Any]] = []
            for q in queries:
                if not q:
                    continue
                searched_terms.append(q)
                r = tool_search_document(
                    config_path=config_path,
                    query=q,
                    file_path=file_path,
                    k=k,
                )
                merged.extend(r.get("results") or [])
            seen = set()
            deduped: List[Dict[str, Any]] = []
            for c in merged:
                key = str(c.get("chunk_id") or "") + "|" + str(c.get("pages") or "")
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(c)
            contexts = deduped
            tool_result = {"queries": queries, "k": k, "results": contexts}
        elif tool == "extract_section":
            section = args.get("section")
            chunk_id = args.get("chunk_id")
            tool_result = tool_extract_section(
                file_path=file_path,
                section=section,
                chunk_id=chunk_id,
                contexts=contexts,
                max_chars=max_tool_chars,
            )
        elif tool == "validate_data":
            extracted = args.get("extracted")
            if not isinstance(extracted, dict):
                extracted = extracted_candidate or {}
            tool_result = tool_validate_data(extracted=extracted, contexts=contexts)
        else:
            tool_result = {"error": f"unknown_tool: {tool}"}

        trace.append({"step": step, "tool": tool, "args": args, "result": tool_result})
        messages.append(("assistant", _truncate(raw, 1200)))
        messages.append(
            (
                "user",
                "TOOL_RESULT:\n"
                + _truncate(json.dumps(tool_result, ensure_ascii=False), max_tool_chars),
            )
        )

    if extracted_candidate is None:
        extracted_candidate = _empty_schema(
            file_path=file_path, provider=llm.provider, model=llm.model_name
        )
    return ApproachCResult(final_json=extracted_candidate, raw_final="", trace=trace)


def save_result(result: ApproachCResult, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    payload: Dict[str, Any] = {
        "final": result.final_json,
        "trace": result.trace,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    try:
        from agent.supabase_store import persist_extraction_payload

        persist_extraction_payload(payload)
    except Exception:
        pass
