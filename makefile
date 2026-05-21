# Installer les dépendances (recommandé via venv)
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Générer le README des données
.\venv\Scripts\python.exe generate_readme.py

# Télécharger 20 rapports 10-K en texte brut
.\venv\Scripts\python.exe edgar_downloader.py --count 20 --year 2023 --output data/raw/EDGAR

# Ou récupérer les données structurées JSON pour 4 grandes entreprises
.\venv\Scripts\python.exe edgar_downloader.py --mode facts --tickers AAPL MSFT GOOGL AMZN --output data/raw/EDGAR_facts

# Vérifier les providers LLM (Groq + Ollama)
.\venv\Scripts\python.exe test_llm.py

# Préparer les modèles Ollama nécessaires
ollama pull mistral
ollama pull nomic-embed-text

# Tester le parsing PDF / DOCX
.\venv\Scripts\python.exe test_pdf_parser.py
.\venv\Scripts\python.exe test_docx_parser.py

# Tester le chunking (PDF + DOCX)
.\venv\Scripts\python.exe test_chunking.py

# Indexation vectorielle (Chroma) — paramètres sûrs pour éviter les blocages sur gros fichiers
# Exemple minimal (EDGAR, 1 fichier) :
.\venv\Scripts\python.exe build_index.py --reset --data-dir data/raw/EDGAR --limit-files 1 --max-chars 800 --overlap-chars 80 --batch-size 4 --max-chunks-per-file 40

# Test retrieval (après indexation)
.\venv\Scripts\python.exe test\test_retrieval.py

#T3
.\venv\Scripts\python.exe run_approach_a.py --input data\raw\Maroc_Telecom\2024\Maroc_Telecom_RFA_2024.pdf --provider groq --max-chars 5000 --max-chunks 1

#T3.2
.\venv\Scripts\python.exe build_index.py --reset --data-dir data\raw\Maroc_Telecom --limit-files 2
.\venv\Scripts\python.exe run_approach_b.py --input data\raw\Maroc_Telecom\2024\Maroc_Telecom_RFA_2024.pdf --provider groq --top-k 2 --max-chunks 8

#T3.3
.\venv\Scripts\python.exe run_approach_c.py --input data\raw\Maroc_Telecom\2024\Maroc_Telecom_RFA_2024.pdf --provider groq --steps 8 --top-k 2

#T3.4
.\venv\Scripts\python.exe run_approach_d.py --input data\raw\Maroc_Telecom\2024\Maroc_Telecom_RFA_2024.pdf --provider groq --top-k 2 --max-chunks 10 --fix-passes 1 --max-llm-context-chars 6500

#T3.5
.\venv\Scripts\python.exe benchmark\compare.py --glob "benchmark/out/*.json" --out benchmark\comparison.md