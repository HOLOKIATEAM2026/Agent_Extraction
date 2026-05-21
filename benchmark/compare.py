import argparse
import glob
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RunSummary:
    file: str
    approach: str
    provider: Optional[str]
    model: Optional[str]
    json_ok: bool
    filled_fields: int
    total_fields: int
    validation_issues: Optional[int]


def _iter_field_objects(obj: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            if set(x.keys()) >= {"valeur", "source", "confiance"}:
                out.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return out


def _count_filled(fields: List[Dict[str, Any]]) -> int:
    filled = 0
    for f in fields:
        v = f.get("valeur")
        if isinstance(v, list):
            if len(v) > 0:
                filled += 1
        elif v is not None:
            if str(v).strip():
                filled += 1
    return filled


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_result_payload(payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if "result" in payload and isinstance(payload.get("result"), dict):
        return payload.get("result"), payload.get("meta") if isinstance(payload.get("meta"), dict) else None
    if "final" in payload and isinstance(payload.get("final"), dict):
        return payload.get("final"), None
    if "meta" in payload and isinstance(payload.get("meta"), dict) and any(
        k.startswith("diagnostic_") for k in payload.keys()
    ):
        return payload, payload.get("meta")
    return None, payload.get("meta") if isinstance(payload.get("meta"), dict) else None


def summarize_file(path: str) -> RunSummary:
    base = os.path.basename(path)
    parts = base.split(".")
    approach = next((p for p in parts if p.startswith("approach_")), "unknown")

    payload = _load_json(path)
    result_obj, meta_obj = _extract_result_payload(payload)

    provider = None
    model = None
    if meta_obj:
        provider = meta_obj.get("provider")
        model = meta_obj.get("model")
    elif result_obj and isinstance(result_obj.get("meta"), dict):
        provider = result_obj["meta"].get("provider")
        model = result_obj["meta"].get("model")
    elif isinstance(payload.get("meta"), dict):
        provider = payload["meta"].get("provider")
        model = payload["meta"].get("model")

    json_ok = result_obj is not None
    fields = _iter_field_objects(result_obj) if result_obj else []
    total_fields = len(fields)
    filled_fields = _count_filled(fields)

    validation_issues = None
    if isinstance(payload.get("validation"), dict):
        validation_issues = int(payload["validation"].get("issues_count") or 0)

    return RunSummary(
        file=path,
        approach=approach,
        provider=provider,
        model=model,
        json_ok=json_ok,
        filled_fields=filled_fields,
        total_fields=total_fields,
        validation_issues=validation_issues,
    )


def to_markdown_table(rows: List[RunSummary]) -> str:
    header = (
        "| Fichier | Approche | Provider | Modèle | JSON OK | Champs remplis | Issues validation |\n"
        "|---|---|---|---|---:|---:|---:|\n"
    )
    lines: List[str] = [header]
    for r in rows:
        issues = "" if r.validation_issues is None else str(r.validation_issues)
        lines.append(
            f"| {os.path.basename(r.file)} | {r.approach} | {r.provider or ''} | {r.model or ''} | "
            f"{'✅' if r.json_ok else '❌'} | {r.filled_fields}/{r.total_fields} | {issues} |\n"
        )
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--glob", default="benchmark/out/*.json")
    parser.add_argument("--out", default="benchmark/comparison.md")
    args = parser.parse_args()

    paths = sorted(glob.glob(args.glob))
    rows = [summarize_file(p) for p in paths]

    md = "# 📊 Tableau comparatif — Approches A/B/C/D\n\n"
    md += "Ce tableau est généré automatiquement à partir des sorties dans `benchmark/out/*.json`.\n\n"
    md += to_markdown_table(rows)
    md += "\n"
    md += "## Lecture rapide\n\n"
    md += "- Champs remplis = nombre de champs `valeur` non-nuls (ou listes non vides) / total des champs.\n"
    md += "- Issues validation = nombre d’extraits cités absents du contexte (disponible surtout en Approche D).\n"

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)

    print(args.out)


if __name__ == "__main__":
    main()
