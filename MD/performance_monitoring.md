# Performance — Extraction (profiling, optimisation, surveillance)

## Goulots d’étranglement observés
- Cold start embeddings (HuggingFace) : initialisation lente (peut dépasser 10–20s).
- Extraction Agent : temps dominé par les appels LLM (multi-champs) + persistance Supabase.

## Changements appliqués
- Instrumentation runtime (session debug) : timings par étape (upload, indexing, embeddings, FAISS, agent, persist).
- Agent : exécution des champs en parallèle avec sémaphore (`AGENT_CONCURRENCY_LIMIT`).
- UI (mode async) : polling `/status` avec backoff progressif pour réduire la charge.

## Réglages (env)
- `AGENT_CONCURRENCY_LIMIT` : limite max de requêtes LLM concurrentes (défaut 2 pour Groq/OpenAI, cap 4).
- `HF_TOKEN` (si embeddings HuggingFace) : recommandé en production pour de meilleurs rate limits / downloads plus rapides.

## Tests de performance (local)
- Benchmark cache FAISS + embeddings :
  - `python benchmark/perf_index_cache.py`

## Surveillance en production (Railway)
- Suivre la latence moyenne et p95 sur l’endpoint `/extract` (Railway metrics).
- Surveiller les erreurs `429` (rate limit LLM), `403/42501` (Supabase grants/RLS), et les redémarrages (cold start).
- En cas de lenteur “aléatoire”, vérifier si le service a redémarré (cold start embeddings).

