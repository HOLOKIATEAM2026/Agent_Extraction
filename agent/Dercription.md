# 📘 Description des fichiers — dossier `agent/`

Ce document décrit le rôle de chaque fichier Python dans le dossier [agent](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent).

## Vue d’ensemble

Le dossier `agent/` contient les briques “cœur” du pipeline RAG :
- Parsing des documents (PDF / DOCX)
- Chunking (découpage) avec métadonnées
- Indexation (ChromaDB) + embeddings (Ollama)
- Abstraction LLM (switch Groq/Ollama/etc. via `config.yaml`)

## Détails par fichier

- [__init__.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/__init__.py)
  - Rôle : transforme `agent/` en package Python importable (`import agent...`).

- [llm_provider.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/llm_provider.py)
  - Rôle : couche d’abstraction LLM (T2.1).
  - Ce que ça fait :
    - Lit `config.yaml` + `.env`
    - Instancie un provider LangChain selon `provider` (ex: `groq`, `ollama`, `openai`, `gemini`)
    - Expose une méthode simple `complete(prompt)` pour générer du texte.

- [pdf_parser.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/pdf_parser.py)
  - Rôle : parser PDF (T2.4) basé sur PyMuPDF.
  - Ce que ça extrait :
    - Texte par page
    - Métadonnées : `page`, `title` (titre détecté), `section` (titre courant propagé).

- [docx_parser.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/docx_parser.py)
  - Rôle : parser DOCX (T2.5) basé sur `python-docx`.
  - Ce que ça extrait :
    - Paragraphes + tables
    - Métadonnées : `style`, `is_heading`, `section` (heading courant).

- [word_parser.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/word_parser.py)
  - Rôle : variante alternative de parser DOCX (même objectif que `docx_parser.py`).
  - Remarque : si vous gardez un seul parseur Word, `docx_parser.py` est celui utilisé par le chunking/indexation.

- [chunking.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/chunking.py)
  - Rôle : stratégie de chunking (T2.6).
  - Ce que ça fait :
    - `chunk_pdf()` : découpe par sections issues du PDF (`section/title`) + overlap
    - `chunk_docx()` : découpe par sections issues des headings DOCX + overlap
    - `chunk_txt()` : découpe de texte brut (EDGAR) en fenêtres glissantes
    - `chunk_document()` : routeur `.pdf` / `.docx` / `.txt`.

- [vectorstore.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/vectorstore.py)
  - Rôle : création/chargement des embeddings + vectorstore (ChromaDB).
  - Ce que ça fait :
    - Charge `config.yaml`
    - Instancie les embeddings (Ollama `nomic-embed-text`)
    - Instancie Chroma (persist_dir, collection_name).

- [indexing.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/agent/indexing.py)
  - Rôle : indexation vectorielle (T2.7).
  - Ce que ça fait :
    - Parcourt `data/raw/` (PDF/DOCX/TXT)
    - Chunking → conversion en `Document` LangChain (+ ids stables)
    - Insertion par batch dans Chroma (avec limites anti “gros fichiers”).

## Liens utiles (scripts hors `agent/`)

- [build_index.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/build_index.py) : lance l’indexation Chroma.
- [test_llm.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/test_llm.py) : teste Groq + Ollama.
- [test_pdf_parser.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/test_pdf_parser.py) : test parsing PDF.
- [test_docx_parser.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/test_docx_parser.py) : test parsing DOCX.
- [test_chunking.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/test/test_chunking.py) : test chunking.
- [test_retrieval.py](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/test/test_retrieval.py) : test retrieval depuis Chroma.

## Dossiers importants (hors `agent/`)

- [data/](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/data)
  - Rôle : contient le corpus de documents et les fichiers de suivi du dataset.
  - Contenu :
    - [README.md](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/data/README.md) : inventaire des documents (généré par `generate_readme.py`).
    - [ground_truth.csv](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/data/ground_truth.csv) : annotations manuelles (référence pour évaluation).
    - `raw/` : documents bruts organisés par source/entreprise/année.
      - `Attijariwafa Bank/`, `TotalEnergies/`, `Maroc_Telecom/` : PDF.
      - `EDGAR/` : fichiers `.txt` téléchargés via `edgar_downloader.py`.

- [vectorstore/](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/vectorstore)
  - Rôle : stockage persistant de la base vectorielle Chroma.
  - Détails :
    - `vectorstore/chroma/` : index normal (persist_dir configuré dans `config.yaml`).
    - `vectorstore/chroma_reset/` : index alternatif créé si Windows bloque la suppression de `chroma.sqlite3` pendant un `--reset`.
  - Remarque : ce dossier est ignoré par git (cf. `.gitignore`) car il peut être régénéré.

- [MD/liverable/](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/MD/liverable)
  - Rôle : regroupe les livrables “rédactionnels” (à envoyer/présenter).
  - Contenu :
    - [mapping_copilot.md](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/MD/liverable/mapping_copilot.md) : mapping champs ↔ questions Copilot.
    - [validation_encadrant.md](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/MD/liverable/validation_encadrant.md) : document de validation des specs.
    - [specs_fonctionnelles.docx](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/MD/liverable/specs_fonctionnelles.docx) : spécifications fonctionnelles.
