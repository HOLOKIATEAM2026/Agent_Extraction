# 📊 Benchmark — Approches d’extraction

Ce dossier contient le code utilisé pour comparer plusieurs approches d’extraction.

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
