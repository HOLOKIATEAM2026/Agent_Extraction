# 📊 Benchmark — Approches d’extraction

Ce dossier contient le code utilisé pour comparer plusieurs approches d’extraction.

## Résumé & décision

- Tableau auto : [comparison.md](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark/comparison.md)
- Rapport + choix final : [rapport_comparatif.md](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark/rapport_comparatif.md)

## Approche A — Extraction directe LLM (sans RAG)

- Code : [approach_a.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark/approach_a.py)
- CLI : [run_approach_a.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/run_approach_a.py)

### Principe

1. Lecture du document (PDF/DOCX/TXT) via le pipeline ingestion existant (`agent/chunking.py`).
2. Sélection d’un extrait (document entier ou tronqué).
3. Appel LLM via [LLMProvider](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/llm_provider.py).
4. Sortie JSON structurée (ou fallback sur `raw_response` si le modèle ne respecte pas le format).

### Exemple (Groq)

```powershell
.\venv\Scripts\python.exe run_approach_a.py --input data\raw\Maroc_Telecom\2024\Maroc_Telecom_RFA_2024.pdf --provider groq --max-chars 5000 --max-chunks 1
```

Sortie : `benchmark/out/<fichier>.approach_a.json`

## Approche B — RAG classique (Vectorstore + Retrieval + LLM)

- Code : [approach_b.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark/approach_b.py)
- CLI : [run_approach_b.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/run_approach_b.py)

### Principe

1. L’index (Chroma) est construit via `build_index.py` (chunking → embeddings → upsert).
2. Pour un fichier donné, on fait un retrieval sur plusieurs requêtes “cibles” (CA, résultat net, effectif, etc.).
3. On déduplique les chunks, puis on envoie uniquement ces chunks au LLM pour produire le JSON.

### Exemple (Groq)

```powershell
.\venv\Scripts\python.exe run_approach_b.py --input data\raw\Maroc_Telecom\2024\Maroc_Telecom_RFA_2024.pdf --provider groq --top-k 3 --max-chunks 10
```

Sortie : `benchmark/out/<fichier>.approach_b.json`

## Approche C — Agent IA autonome (outils + raisonnement multi-étapes)

- Code : [approach_c_agent.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark/approach_c_agent.py)
- CLI : [run_approach_c.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/run_approach_c.py)

### Principe

1. Le LLM pilote un cycle multi-étapes.
2. À chaque étape, il peut appeler un outil (format JSON strict) :
   - `search_document` : retrieval depuis Chroma (top-k chunks)
   - `extract_section` : extrait une section complète (PDF/DOCX) si besoin
   - `validate_data` : vérifie que les extraits cités existent dans le contexte
3. Le résultat final est `{"final": {...}}` + un `trace` pour auditer les appels.

### Exemple

```powershell
.\venv\Scripts\python.exe run_approach_c.py --input data\raw\Maroc_Telecom\2024\Maroc_Telecom_RFA_2024.pdf --provider groq --steps 6 --top-k 4
```

## Approche D — Combinaison (RAG retrieval + validation/correction)

- Code : [approach_d_combo.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark/approach_d_combo.py)
- CLI : [run_approach_d.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/run_approach_d.py)

### Principe

1. Retrieval multi-requêtes (comme l’approche B) pour récupérer un ensemble de chunks.
2. Extraction JSON à partir de ce contexte.
3. Validation automatique : vérifie que chaque `source.extrait` est bien présent dans le contexte.
4. Si erreurs, une passe de correction supplémentaire peut être faite (fix pass).

### Exemple

```powershell
.\venv\Scripts\python.exe run_approach_d.py --input data\raw\Maroc_Telecom\2024\Maroc_Telecom_RFA_2024.pdf --provider groq --top-k 2 --max-chunks 10 --fix-passes 1
```
