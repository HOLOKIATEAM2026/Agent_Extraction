import os
import json
import csv
from typing import Dict, Any

from agent.extractor import run_agent_extraction

def load_ground_truth(csv_path: str) -> Dict[str, Dict[str, str]]:
    """Charge le fichier CSV de vérité terrain généré en Phase 0."""
    truth = {}
    if not os.path.exists(csv_path):
        print(f"⚠️ Fichier Ground Truth introuvable: {csv_path}")
        return truth
        
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entreprise = row.get("entreprise", "").strip()
            annee = row.get("annee", "").strip()
            
            if not entreprise:
                continue
                
            # Pour l'instant, on cherche un fichier PDF ou TXT qui correspond à l'entreprise
            # Ceci est une simplification pour s'adapter à la structure des dossiers
            doc_name = None
            
            # 1. On cherche d'abord dans tous les sous-dossiers de data/raw/
            for root, _, files in os.walk("data/raw"):
                for file in files:
                    if file.endswith((".pdf", ".txt", ".docx")):
                        # Vérifier si le nom de l'entreprise est dans le nom du fichier
                        entreprise_normalized = entreprise.lower().replace(" ", "_")
                        file_normalized = file.lower()
                        if entreprise_normalized in file_normalized or entreprise.lower() in file_normalized:
                            doc_name = os.path.join(os.path.relpath(root, "data/raw"), file)
                            break
                if doc_name:
                    break
                    
            if not doc_name:
                print(f"⚠️ Aucun fichier trouvé pour {entreprise} ({annee}) dans data/raw/")
                continue
                
            if doc_name not in truth:
                truth[doc_name] = {}
            truth[doc_name][row["champ"]] = row["valeur_attendue"]
    return truth

def calculate_metrics(extracted: Dict[str, Any], expected: Dict[str, str]) -> Dict[str, float]:
    """Compare l'extraction avec la vérité terrain."""
    total_fields = 0
    correct_fields = 0
    hallucinations = 0
    missing_fields = 0
    
    # Aplatir le JSON extrait pour faciliter la comparaison
    flat_extracted = {}
    for section_name, section_data in extracted.items():
        if not isinstance(section_data, dict) or section_name == "meta":
            continue
        for field_name, field_data in section_data.items():
            if isinstance(field_data, dict) and "valeur" in field_data:
                val = field_data["valeur"]
                # Convertir liste en string pour comparaison
                if isinstance(val, list):
                    val = ", ".join([str(v) for v in val]) if val else None
                flat_extracted[field_name] = str(val).lower() if val is not None else None
                
    # 2. Indicateur: Null non justifié (Manquant vs Attendu)
    unjustified_nulls = missing_fields
    
    # 3. Cohérence des références sources
    source_coherence_issues = 0
    for section_name, section_data in extracted.items():
        if not isinstance(section_data, dict) or section_name == "meta":
            continue
        for field_name, field_data in section_data.items():
            if isinstance(field_data, dict) and field_data.get("valeur") is not None:
                # Si on a une valeur mais pas de source ou pas d'extrait, c'est incohérent
                src = field_data.get("source")
                if src is None or not isinstance(src, dict) or not src.get("extrait"):
                    # On ignore les champs vides []
                    if field_data.get("valeur") != []:
                        source_coherence_issues += 1
                        
    # Comparaison des résultats
    for champ, val_attendue in expected.items():
        total_fields += 1
        val_attendue = str(val_attendue).lower()
        val_extraite = flat_extracted.get(champ)
        
        if val_attendue == "null" or val_attendue == "":
            if val_extraite is None:
                correct_fields += 1
            else:
                hallucinations += 1 # Le LLM a inventé quelque chose
        else:
            if val_extraite is None:
                missing_fields += 1
            elif val_attendue in val_extraite or val_extraite in val_attendue:
                # Tolérance: si l'une est incluse dans l'autre
                correct_fields += 1
            else:
                # Mauvaise valeur extraite
                hallucinations += 1
                
    accuracy = (correct_fields / total_fields) * 100 if total_fields > 0 else 0
    hallucination_rate = (hallucinations / total_fields) * 100 if total_fields > 0 else 0
    
    return {
        "accuracy": round(accuracy, 2),
        "hallucination_rate": round(hallucination_rate, 2),
        "total_fields": total_fields,
        "correct": correct_fields,
        "hallucinations": hallucinations,
        "missing": missing_fields,
        "unjustified_nulls": unjustified_nulls,
        "source_coherence_issues": source_coherence_issues
    }

def run_evaluation(docs_dir: str, truth_csv: str, provider: str = "groq", model: str = "llama3-70b-8192"):
    """Exécute l'agent sur les documents de test et calcule le score."""
    print(f"\n🚀 DÉMARRAGE DE L'ÉVALUATION (Phase 6)")
    print(f"Modèle: {model} ({provider})")
    print("-" * 50)
    
    truth = load_ground_truth(truth_csv)
    if not truth:
        print("Veuillez créer un fichier data/ground_truth.csv avec les colonnes: document, champ, valeur_attendue")
        return
        
    global_metrics = {
        "total": 0, 
        "correct": 0, 
        "hallucinations": 0, 
        "missing": 0,
        "source_issues": 0
    }
    
    for doc_name, expected_fields in truth.items():
        doc_path = os.path.join(docs_dir, doc_name)
        if not os.path.exists(doc_path):
            print(f"⚠️ Document introuvable: {doc_path}")
            continue
            
        print(f"\n📄 Évaluation de : {doc_name}")
        
        try:
            # Lancer l'extraction
            result = run_agent_extraction(
                file_path=doc_path,
                provider=provider,
                model=model,
                config_path="config.yaml"
            )
            
            # Calculer les métriques
            metrics = calculate_metrics(result, expected_fields)
            
            print(f"✅ Précision: {metrics['accuracy']}%")
            print(f"❌ Hallucinations: {metrics['hallucination_rate']}%")
            print(f"   Détails: {metrics['correct']} corrects, {metrics['hallucinations']} faux/inventés, {metrics['missing']} manquants")
            print(f"🔗 Problèmes de cohérence source: {metrics['source_coherence_issues']}")
            
            # Agrégation globale
            global_metrics["total"] += metrics["total_fields"]
            global_metrics["correct"] += metrics["correct"]
            global_metrics["hallucinations"] += metrics["hallucinations"]
            global_metrics["missing"] += metrics["missing"]
            global_metrics["source_issues"] += metrics["source_coherence_issues"]
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {doc_name}: {e}")
            
    # Score final
    if global_metrics["total"] > 0:
        final_accuracy = (global_metrics["correct"] / global_metrics["total"]) * 100
        final_hallucination = (global_metrics["hallucinations"] / global_metrics["total"]) * 100
        
        print("\n" + "=" * 50)
        print("🏆 RÉSULTATS GLOBAUX DE L'AGENT FINAL (Approche D améliorée)")
        print("=" * 50)
        print(f"Total des champs évalués : {global_metrics['total']}")
        print(f"✅ Précision Moyenne      : {round(final_accuracy, 2)}%")
        print(f"❌ Taux d'Hallucination   : {round(final_hallucination, 2)}%")
        print(f"⚠️ Informations manquées  : {round((global_metrics['missing'] / global_metrics['total']) * 100, 2)}%")
        print(f"🔗 Problèmes de sources   : {global_metrics['source_issues']}")
        print("=" * 50)
        
        # Sauvegarder les résultats
        os.makedirs("eval", exist_ok=True)
        with open("eval/latest_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "model": model,
                "provider": provider,
                "accuracy": final_accuracy,
                "hallucination_rate": final_hallucination,
                "raw_metrics": global_metrics
            }, f, indent=2)

if __name__ == "__main__":
    # Pour lancer le script: python -m eval.evaluate
    run_evaluation(
        docs_dir="data/raw", # Ajuste le chemin si besoin
        truth_csv="data/ground_truth.csv",
        provider="groq",
        model="llama-3.3-70b-versatile" # Changement du modèle car llama3-70b-8192 est obsolète
    )