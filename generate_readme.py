import os
import fitz  # PyMuPDF
import json

DATA_DIR = os.path.join("data", "raw")
README_PATH = os.path.join("data", "README.md")

def generate_readme():
    if not os.path.exists(DATA_DIR):
        print(f"Le dossier {DATA_DIR} n'existe pas.")
        return

    content = [
        "# 📂 Corpus de Rapports d'Activité",
        "",
        "Ce dossier contient les rapports annuels bruts au format PDF utilisés pour l'entraînement et l'évaluation de l'agent RAG.",
        "",
        "## 📄 Liste des documents",
        "",
        "| Entreprise | Année | Langue | Fichier | Nombre de pages |",
        "|------------|-------|--------|---------|-----------------|"
    ]

    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.lower().endswith((".pdf", ".txt", ".json")):
                filepath = os.path.join(root, file)
                
                # Déduire les informations depuis le chemin (ex: data/raw/Attijariwafa Bank/fr/2023/...)
                rel_path = os.path.relpath(filepath, DATA_DIR)
                parts = rel_path.split(os.sep)
                
                entreprise = parts[0] if len(parts) > 0 else "Inconnu"
                
                # Chercher l'année et la langue dans l'arborescence
                annee = "Inconnue"
                langue = "Inconnue"
                
                for part in parts:
                    if part.isdigit() and len(part) == 4:
                        annee = part
                    elif part.lower() in ["fr", "en", "an"]:
                        langue = "FR" if part.lower() == "fr" else "EN"
                
                # Compter les pages
                nb_pages = "N/A"
                if file.lower().endswith(".pdf"):
                    try:
                        doc = fitz.open(filepath)
                        nb_pages = str(doc.page_count)
                        doc.close()
                    except Exception as e:
                        print(f"Erreur de lecture pour {file}: {e}")
                elif file.lower().endswith(".txt"):
                    nb_pages = "Texte brut"
                elif file.lower().endswith(".json"):
                    nb_pages = "Données JSON"

                row = f"| {entreprise.replace('_', ' ')} | {annee} | {langue} | `{file}` | {nb_pages} |"
                content.append(row)

    content.extend([
        "",
        "---",
        "*Généré automatiquement.*"
    ])

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    
    print(f"✅ {README_PATH} généré avec succès !")

if __name__ == "__main__":
    generate_readme()
