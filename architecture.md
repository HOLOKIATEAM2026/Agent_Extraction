# 🏗️ Architecture — Agent RAG (Multi‑Modèles)

Ce document décrit l’architecture technique actuelle du projet : ingestion documentaire (PDF/DOCX/TXT), chunking, embeddings, indexation vectorielle, retrieval, et couche d’abstraction LLM.

## Composants

### 1) Configuration

- `config.yaml`
  - `providers.*` : configuration LLM (Groq / Ollama / OpenAI / Gemini)
  - `embeddings.*` : configuration embeddings (Ollama `nomic-embed-text`)
  - `vectorstore.*` : configuration base vectorielle (Chroma persistée)
- `.env` : clés API (ex: `GROQ_API_KEY`)

### 2) Ingestion & Parsing

- PDF : `agent/pdf_parser.py`
  - extraction texte par page
  - métadonnées : `page`, `title`, `section`
- DOCX : `agent/docx_parser.py`
  - extraction paragraphes + tables
  - métadonnées : `style`, `is_heading`, `section`
- TXT (EDGAR) : lecture brute + découpe en segments

### 3) Chunking (par section + overlap)

- `agent/chunking.py`
  - PDF : chunks regroupés par `section` (titres détectés) + overlap
  - DOCX : chunks regroupés par `section` (headings) + overlap
  - TXT : chunks par fenêtre glissante (max chars + overlap)

### 4) Embeddings

- `agent/vectorstore.py`
  - embeddings via `langchain_ollama.OllamaEmbeddings`
  - modèle recommandé : `nomic-embed-text`
  - timeout configuré via `config.yaml`

### 5) Indexation Vectorielle

- `agent/indexing.py` + `build_index.py`
  - vectorstore : Chroma persistée (`vectorstore/chroma`)
  - insertion par batch (`--batch-size`)
  - garde-fou gros fichiers (`--max-chunks-per-file`)

### 6) Retrieval (recherche)

- `test/test_retrieval.py`
  - `similarity_search(query, k=...)`
  - retourne les chunks les plus proches + métadonnées

### 7) Couche LLM multi‑modèles

- `agent/llm_provider.py`
  - `LLMProvider(provider=..., model=...)`
  - bascule Groq / Ollama via config sans changer le code métier

## Diagramme (Mermaid)

```mermaid
flowchart TD

  subgraph DATA[Corpus]
    PDF[PDF]
    DOCX[DOCX]
    TXT[TXT / EDGAR]
  end

  subgraph CFG[Configuration]
    ENV[".env<br/>GROQ_API_KEY"]
    YAML["config.yaml<br/>providers embeddings vectorstore"]
  end

  subgraph ING[Ingestion and Parsing]
    PPDF["pdf_parser.py"]
    PDOCX["docx_parser.py"]
    PTXT["txt_parser.py"]
  end

  subgraph CHK[Chunking]
    CHPDF["chunk_pdf"]
    CHDOCX["chunk_docx"]
    CHTXT["chunk_txt"]
  end

  subgraph EMB[Embeddings]
    OLL_EMB["OllamaEmbeddings<br/>nomic-embed-text"]
    OLLAMA["Ollama Server<br/>localhost:11434"]
  end

  subgraph VS[Vector Store]
    CHROMA["ChromaDB"]
  end

  subgraph RET[Retrieval]
    SIM["similarity_search"]
  end

  subgraph GEN[LLM Generation]
    LLM["llm_provider.py"]
    GROQ["Groq API"]
    OLL_LLM["Ollama LLM<br/>mistral"]
  end

  PDF --> PPDF --> CHPDF --> OLL_EMB
  DOCX --> PDOCX --> CHDOCX --> OLL_EMB
  TXT --> PTXT --> CHTXT --> OLL_EMB

  YAML --> OLL_EMB
  OLL_EMB --> OLLAMA
  OLL_EMB --> CHROMA
  CHROMA --> SIM
  SIM --> LLM
  YAML --> LLM
  ENV --> LLM
  LLM --> GROQ
  LLM --> OLL_LLM
```

## Commandes de vérification (venv)

```powershell
.\venv\Scripts\python.exe test_pdf_parser.py
.\venv\Scripts\python.exe test_docx_parser.py
.\venv\Scripts\python.exe test_chunking.py
.\venv\Scripts\python.exe build_index.py --reset --data-dir data/raw/EDGAR --limit-files 1 --max-chars 800 --overlap-chars 80 --batch-size 4 --max-chunks-per-file 40
.\venv\Scripts\python.exe test\test_retrieval.py
```

