# Performance — Extraction (profiling, optimisation, surveillance)

## Goulots d’étranglement observés
- Cold start embeddings (HuggingFace) : initialisation lente (peut dépasser 10–20s).
- Extraction Agent : temps dominé par les appels LLM (multi-champs) + persistance Supabase.
- Exécution async : appels synchrones (FAISS / chunking / I/O) dans des routes async peuvent bloquer la boucle event-loop et dégrader la réactivité.

## Changements appliqués
- Instrumentation runtime (session debug) : timings par étape (upload, indexing, embeddings, FAISS, agent, persist).
- Agent : exécution des champs en parallèle avec sémaphore (`AGENT_CONCURRENCY_LIMIT`).
- UI (mode async) : polling `/status` avec backoff progressif pour réduire la charge.
- Vectorstore : verrouillage des initialisations embeddings et des accès au cache FAISS pour éviter les “double init” sous concurrence.
- Async : offload des étapes lourdes (indexing, PDF→MD, FAISS load/retrieval) vers des threads (`asyncio.to_thread`) pour éviter le blocage.

## Réglages (env)
- `AGENT_CONCURRENCY_LIMIT` : limite max de requêtes LLM concurrentes (défaut 3 pour Groq/OpenAI, cap 6).
- `RAG_WARMUP_EMBEDDINGS` : pré-charge les embeddings au démarrage du serveur (`1` par défaut).
- `RAG_CONFIG_PATH` : chemin config utilisé pour le warmup (`config.yaml` par défaut).
- `HF_TOKEN` (si embeddings HuggingFace) : recommandé en production pour de meilleurs rate limits / downloads plus rapides.
- `HF_HOME` ou `embeddings.cache_folder` (config.yaml) : dossier cache local HF (défaut `data/hf_cache`).

## Tests de performance (local)
- Benchmark cache FAISS + embeddings :
  - `python benchmark/perf_index_cache.py`
- Benchmark multi-tailles (small/medium/large) :
  - `python benchmark/perf_vectorstore_matrix.py`

## Surveillance en production (Railway)
- Suivre la latence moyenne et p95 sur l’endpoint `/extract` (Railway metrics).
- Surveiller les erreurs `429` (rate limit LLM), `403/42501` (Supabase grants/RLS), et les redémarrages (cold start).
- En cas de lenteur “aléatoire”, vérifier si le service a redémarré (cold start embeddings).
