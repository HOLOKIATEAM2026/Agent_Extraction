# 🔎 Veille sécurité — Dépendances Python

## Constat (local)

- Plusieurs dépendances sont en retard (ex: `langchain`, `groq`, `requests`, `protobuf`, `openai`).
- Le projet utilise des librairies “rapidement évolutives” (LangChain + providers), ce qui augmente le risque de changements cassants et de correctifs sécurité fréquents.

## Actions recommandées

- Mettre à jour en priorité : `requests`, `certifi`, `protobuf`, `langchain`, `langsmith`, `groq`.
- Éviter les mises à jour “au hasard” sur un projet stable : valider via `test/` + un run d’index + un run benchmark.
- Épingler les versions (pin) dans `requirements.txt` une fois une version stable validée.
- Activer Dependabot (ou équivalent) sur GitHub pour PRs automatiques de mises à jour.
- Ne jamais committer de secrets : `.env` doit rester ignoré (déjà le cas via `.gitignore`).
