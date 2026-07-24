[OPEN] Debug Session: extract-slow-performance

## Symptômes
- Lancement extraction très lent même pour fichiers courts (ex: .txt)
- Logs observés:
  - Chargement de poids (HuggingFace) au démarrage
  - Création / chargement FAISS
  - Erreurs Supabase 403 sur `custom_questions`
  - Polling `/status/{job_id}` très fréquent

## Hypothèses (falsifiables)
1) Le temps est dominé par l'initialisation embeddings (HuggingFace / Ollama) à chaque requête ou à chaque cold start.
2) Le pipeline indexe deux fois (ex: `_index_single_file()` + `run_agent_extraction()`), créant des embeddings FAISS redondants même quand non utilisés.
3) La persistance/chargement du cache FAISS est inefficace en environnement cloud (disque éphémère), ce qui force des reconstructions fréquentes.
4) Les appels Supabase (notamment `custom_questions`) échouent (403) et déclenchent des retries/chemins de fallback coûteux.
5) Le mode asynchrone + polling `/status` trop agressif dégrade la perf perçue (beaucoup de requêtes concurrentes) et masque le vrai temps pipeline.

## Plan (evidence-first)
1) Démarrer le Debug Server (session `extract-slow-performance`) et collecter des timings runtime.
2) Instrumenter (sans changer la logique) les étapes clés:
   - upload/save fichier
   - conversion PDF→MD
   - `_index_single_file()`
   - `run_agent_extraction()` (routing, génération questions, RAG)
   - `get_embeddings()` et création/chargement FAISS
   - appels Supabase (custom_questions, persist)
3) Reproduire sur 2 cas: petit TXT + petit PDF (si possible) avec `async_mode=false` et `async_mode=true`.
4) Analyser les logs (pré-fix) et décider du correctif minimal.
5) Implémenter fix + tests de perf + comparaison pré/post.

## Données à fournir (si possible)
- Environnement d'exécution (local / Railway), nombre de workers uvicorn, taille du fichier.

## Statut
- Debug server: pending
- Instrumentation: pending
- Repro: pending
- Fix: pending

## Evidence (pré-fix)
- Run #1 (small.txt) total: ~36.2s
  - embeddings.init (HuggingFace): ~20.4s
  - index.done: ~21.5s (dominé par embeddings.init)
  - agent.done: ~10.3s
  - persist (Supabase): ~4.0s
- Run #2 (small.txt) total: ~12.0s (même process, cache chaud)
  - index.done: ~0.13s (FAISS + embeddings en cache)
  - agent.done: ~8.1s
  - persist (Supabase): ~3.6s

## Statut hypothèses
1) Initialisation embeddings domine le cold start → CONFIRMÉ
2) Indexing redondant → PARTIEL (indexing requis pour FAISS, mais des optimisations sont possibles)
3) Cache FAISS inefficace en cloud éphémère → PROBABLE (à valider en prod)
4) Supabase 403 custom_questions → CONFIRMÉ (vu côté prod, corrigeable via GRANT)
5) Polling /status trop agressif → PROBABLE (impact UX et charge, mais pas le goulot principal de calcul)

## Evidence (post-fix)
- Changement: exécution parallèle des champs (agent) + backoff polling.
- Run (small.txt, cache chaud) total: ~7.9s
  - index.done: ~0.14–0.17s
  - agent.done: ~5.35s
  - persist (Supabase): ~2.24s
