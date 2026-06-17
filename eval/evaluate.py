import argparse
import asyncio
import csv
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from agent.chunking import chunk_document
from agent.indexing import chunks_to_langchain_docs
from agent.multi_extractor import run_multi_extraction
from agent.vectorstore import get_embeddings, get_or_create_faiss_vectorstore, load_config


FIELD_TO_CATEGORY: Dict[str, str] = {
    "taille_marche": "strategique",
    "taux_croissance": "strategique",
    "intensite_concurrentielle": "strategique",
    "concurrents": "strategique",
    "tendances_marche": "strategique",
    "chiffre_affaires": "financier",
    "resultat_net": "financier",
    "ebitda": "financier",
    "evolution_n_vs_n1": "financier",
    "effectif_total": "rh",
    "masse_salariale": "rh",
    "kpis": "rh",
    "existence_donnees": "data",
    "qualite": "data",
    "accessibilite": "data",
    "volumetrie": "data",
    "historisation": "data",
    "conformite": "data",
    "documentation": "data",
    "risques_identifies": "cyber",
    "conformite_nist": "cyber",
    "gouvernance_data": "cyber",
}


FIELD_TO_QUESTION: Dict[str, str] = {
    "chiffre_affaires": "Quel est le chiffre d'affaires total ?",
    "resultat_net": "Quel est le résultat net ?",
    "effectif_total": "Quel est l'effectif total de l'entreprise ?",
    "concurrents": "Quels sont les principaux concurrents cités ?",
    "taux_croissance": "Quel est le taux de croissance ?",
}


def _read_truth_rows(csv_path: str) -> List[Dict[str, str]]:
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, "r", encoding="utf-8") as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = ";" if ";" in first_line else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        rows: List[Dict[str, str]] = []
        for row in reader:
            rows.append({k: (v or "").strip() for k, v in row.items() if k})
        return rows


def _find_doc_for_entreprise(entreprise: str) -> Optional[str]:
    entreprise_normalized = entreprise.lower().replace(" ", "_")
    candidates_dirs = ["data/raw", "data/processed"]
    for base in candidates_dirs:
        if not os.path.exists(base):
            continue
        for root, _, files in os.walk(base):
            for file in files:
                if not file.lower().endswith((".pdf", ".txt", ".docx", ".md")):
                    continue
                file_normalized = file.lower()
                if entreprise_normalized in file_normalized or entreprise.lower() in file_normalized:
                    return os.path.join(root, file)
    return None


def load_ground_truth(csv_path: str) -> Dict[str, Dict[str, str]]:
    truth: Dict[str, Dict[str, str]] = {}
    rows = _read_truth_rows(csv_path)
    if not rows:
        print(f"⚠️ Fichier Ground Truth introuvable ou vide: {csv_path}")
        return truth

    for row in rows:
        entreprise = row.get("entreprise", "")
        annee = row.get("annee", "")
        champ = row.get("champ", "")
        valeur = row.get("valeur_attendue", "")

        if not entreprise or entreprise.lower() == "entreprise":
            continue
        if not champ or champ.lower() == "champ":
            continue

        doc_path = _find_doc_for_entreprise(entreprise)
        if not doc_path:
            print(f"⚠️ Aucun fichier trouvé pour {entreprise} ({annee}) dans data/raw ou data/processed")
            continue

        if doc_path not in truth:
            truth[doc_path] = {}
        truth[doc_path][champ] = valeur

    return truth


def _normalize_value(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, list):
        if not val:
            return None
        return ", ".join(str(v) for v in val).strip().lower()
    if isinstance(val, (int, float, bool)):
        return str(val).strip().lower()
    s = str(val).strip()
    if not s:
        return None
    return s.lower()


def calculate_metrics(
    extracted_flat: Dict[str, Optional[str]],
    expected: Dict[str, str],
) -> Dict[str, Any]:
    total_fields = 0
    correct_fields = 0
    hallucinations = 0
    missing_fields = 0

    per_field: Dict[str, str] = {}

    for champ, val_attendue in expected.items():
        total_fields += 1
        exp = str(val_attendue).strip().lower()
        got = extracted_flat.get(champ)

        if exp in {"", "null", "none"}:
            if got is None:
                correct_fields += 1
                per_field[champ] = "correct"
            else:
                hallucinations += 1
                per_field[champ] = "hallucination"
            continue

        if got is None:
            missing_fields += 1
            per_field[champ] = "missing"
            continue

        if exp in got or got in exp:
            correct_fields += 1
            per_field[champ] = "correct"
        else:
            hallucinations += 1
            per_field[champ] = "incorrect"

    accuracy = (correct_fields / total_fields) * 100 if total_fields > 0 else 0.0
    hallucination_rate = (hallucinations / total_fields) * 100 if total_fields > 0 else 0.0
    missing_rate = (missing_fields / total_fields) * 100 if total_fields > 0 else 0.0

    return {
        "accuracy": round(accuracy, 2),
        "hallucination_rate": round(hallucination_rate, 2),
        "missing_rate": round(missing_rate, 2),
        "total_fields": total_fields,
        "correct": correct_fields,
        "hallucinations": hallucinations,
        "missing": missing_fields,
        "per_field": per_field,
    }


def _aggregate_by_category(per_field_status: Dict[str, str]) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for field, status in per_field_status.items():
        cat = FIELD_TO_CATEGORY.get(field, "autre")
        if cat not in out:
            out[cat] = {"total": 0, "correct": 0, "missing": 0, "hallucinations": 0}
        out[cat]["total"] += 1
        if status == "correct":
            out[cat]["correct"] += 1
        elif status == "missing":
            out[cat]["missing"] += 1
        elif status in {"hallucination", "incorrect"}:
            out[cat]["hallucinations"] += 1
    return out


async def _extract_for_eval(
    file_path: str,
    fields: List[str],
    *,
    provider: str,
    model: str,
) -> Dict[str, Optional[str]]:
    questions: List[str] = []
    question_to_field: Dict[str, str] = {}
    for field in fields:
        q = FIELD_TO_QUESTION.get(field)
        if not q:
            continue
        questions.append(q)
        question_to_field[q] = field

    config = load_config("config.yaml")
    embeddings = get_embeddings(config)

    doc_name = os.path.splitext(os.path.basename(file_path))[0]
    chunks = chunk_document(file_path, max_chars=2500, overlap_chars=250)
    for c in chunks:
        c["file_name"] = os.path.basename(file_path)
    lc_docs, _ = chunks_to_langchain_docs(chunks)
    vectorstore = get_or_create_faiss_vectorstore(lc_docs, f"eval_{doc_name}", embeddings=embeddings, config=config)

    result = await run_multi_extraction(
        vectorstore=vectorstore,
        questions=questions,
        provider=provider,
        model=model,
        config_path="config.yaml",
    )

    fname = os.path.basename(file_path)
    extracted_flat: Dict[str, Optional[str]] = {}
    by_doc = (result or {}).get("results_by_document") or {}
    doc_answers = by_doc.get(fname) or {}
    for q, ans in doc_answers.items():
        field = question_to_field.get(q)
        if not field:
            continue
        extracted_flat[field] = _normalize_value(ans.get("valeur") if isinstance(ans, dict) else None)

    for f in fields:
        if f not in extracted_flat:
            extracted_flat[f] = None

    return extracted_flat


async def run_evaluation(
    truth_csv: str,
    *,
    provider: str,
    model: str,
) -> Dict[str, Any]:
    truth = load_ground_truth(truth_csv)
    if not truth:
        raise RuntimeError("Ground truth vide: impossible de lancer l'évaluation.")

    global_metrics = {"total": 0, "correct": 0, "hallucinations": 0, "missing": 0}
    per_doc: Dict[str, Any] = {}
    merged_per_field: Dict[str, str] = {}

    for doc_path, expected_fields in truth.items():
        if not os.path.exists(doc_path):
            continue

        fields = list(expected_fields.keys())
        extracted_flat = await _extract_for_eval(doc_path, fields, provider=provider, model=model)
        metrics = calculate_metrics(extracted_flat, expected_fields)

        per_doc[os.path.basename(doc_path)] = {
            "metrics": {k: metrics[k] for k in ["accuracy", "hallucination_rate", "missing_rate", "total_fields", "correct", "hallucinations", "missing"]},
            "per_field": metrics["per_field"],
            "expected": {k: str(v) for k, v in expected_fields.items()},
            "extracted": extracted_flat,
        }

        global_metrics["total"] += metrics["total_fields"]
        global_metrics["correct"] += metrics["correct"]
        global_metrics["hallucinations"] += metrics["hallucinations"]
        global_metrics["missing"] += metrics["missing"]

        for f, status in metrics["per_field"].items():
            merged_per_field[f] = status

    total = global_metrics["total"]
    accuracy = (global_metrics["correct"] / total) * 100 if total else 0.0
    hallucination_rate = (global_metrics["hallucinations"] / total) * 100 if total else 0.0
    missing_rate = (global_metrics["missing"] / total) * 100 if total else 0.0

    per_category_counts = _aggregate_by_category(merged_per_field)
    per_category: Dict[str, Any] = {}
    for cat, counts in per_category_counts.items():
        t = counts["total"] or 0
        per_category[cat] = {
            **counts,
            "accuracy": round((counts["correct"] / t) * 100, 2) if t else 0.0,
            "missing_rate": round((counts["missing"] / t) * 100, 2) if t else 0.0,
            "hallucination_rate": round((counts["hallucinations"] / t) * 100, 2) if t else 0.0,
        }

    return {
        "provider": provider,
        "model": model,
        "accuracy": round(accuracy, 2),
        "hallucination_rate": round(hallucination_rate, 2),
        "missing_rate": round(missing_rate, 2),
        "raw_metrics": global_metrics,
        "per_category": per_category,
        "per_document": per_doc,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth_csv", default="data/ground_truth.csv")
    parser.add_argument("--provider", default="groq")
    parser.add_argument("--model", default="llama-3.1-8b-instant")
    args = parser.parse_args()

    print(f"\n🚀 DÉMARRAGE DE L'ÉVALUATION (Phase 6)")
    print(f"Provider: {args.provider}")
    print(f"Modèle: {args.model}")
    print("-" * 50)

    results = asyncio.run(run_evaluation(args.truth_csv, provider=args.provider, model=args.model))

    os.makedirs("eval", exist_ok=True)
    with open("eval/latest_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print("🏆 RÉSULTATS GLOBAUX")
    print("=" * 50)
    print(f"Total des champs évalués : {results['raw_metrics']['total']}")
    print(f"✅ Précision Moyenne      : {results['accuracy']}%")
    print(f"❌ Taux d'Hallucination   : {results['hallucination_rate']}%")
    print(f"⚠️ Informations manquées  : {results['missing_rate']}%")
    print("=" * 50)


if __name__ == "__main__":
    main()
