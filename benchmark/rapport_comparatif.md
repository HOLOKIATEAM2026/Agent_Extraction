# 🧾 Rapport comparatif & choix final — Benchmark A/B/C/D

## Contexte et objectif

L’objectif du benchmark est de comparer plusieurs stratégies d’extraction afin de sélectionner l’approche la plus adaptée aux contraintes du projet :
- Documents longs (PDF/DOCX/TXT)
- Citations sources obligatoires (page + extrait)
- Réduction des hallucinations (ne pas inventer)
- Architecture multi-modèles (Groq / Ollama / etc.)

## Approches testées

### Approche A — Extraction directe LLM (sans RAG)

- Principe : envoyer le document (ou un extrait tronqué) directement au LLM, obtenir un JSON.
- Points forts : très simple, rapide à prototyper.
- Limites : faible robustesse sur documents longs (troncature), coût élevé si on augmente la fenêtre de contexte, citations souvent fragiles.

### Approche B — RAG classique (Vectorstore + Retrieval + LLM)

- Principe : chunking → embeddings → indexation Chroma → retrieval top-k → génération JSON à partir des chunks.
- Points forts : scalable, compatible docs longs, coût maîtrisé (on n’envoie que des chunks).
- Limites : la qualité dépend fortement du retrieval (si le bon chunk n’est pas récupéré, le champ sera `null`).

### Approche C — Agent IA autonome (outils + raisonnement multi-étapes)

- Principe : l’agent pilote plusieurs étapes et utilise des outils (`search_document`, `extract_section`, `validate_data`).
- Points forts : flexible, capable d’itérer, d’affiner la recherche.
- Limites : plus lent et plus complexe ; si le pilotage n’est pas bien contraint, il peut “tourner” sur de mauvais indices ou se focaliser sur un faux positif.

### Approche D — Combinaison (RAG retrieval + validation/correction)

- Principe : retrieval (comme B) + validation automatique des citations (`validate_data`) + (optionnel) une passe de correction.
- Points forts : garde la scalabilité du RAG et ajoute un contrôle qualité sur les citations (réduction des hallucinations).
- Limites : un peu plus coûteuse/complexe que B, surtout si on active plusieurs passes de correction.

## Résultats mesurés (auto)

Le tableau de mesures est généré dans : [comparison.md](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark/comparison.md)

Lecture :
- Champs remplis = nombre de champs `valeur` non-nuls (ou listes non vides) / total des champs.
- Issues validation (Approche D) = nombre d’extraits cités absents du contexte.

## Tests sur nouveaux types de documents (réunion 18/05)

Deux nouveaux types de documents ont été ajoutés au corpus :
- **Audit data** (TXT) : `data/raw/Audits_Data/...`
- **Cybersécurité / NIST** (PDF) : `data/raw/Cybersecurity/...`

Relance effectuée sur :
- `audit_qualite_data_exemple_1.txt`
- `NIST_SP_1308_CSF2.0_QSG.pdf`

Constat :
- Les champs “stratégique/financier/RH” du schéma actuel sont **normalement absents** de ces documents → les approches retournent majoritairement `null`/listes vides (0/12).
- L’important ici est la **robustesse du format** (JSON complet) et la **qualité des citations** :
  - Approche B : JSON complet, champs à `null` si non présents.
  - Approche C : JSON complet (fallback si l’agent ne converge pas).
  - Approche D : JSON complet + validation citations (`issues_count=0` sur ces tests).

Note : pour benchmarker “maturité data” et “cyber & gouvernance”, il faudra étendre le schéma et les prompts (Phase 4/5).

## Décision recommandée (à présenter à Samad)

### Choix final proposé : **Approche D** (RAG + validation/correction)

Raisons principales :
- **Conformité “métier”** : citations sources obligatoires et mécanisme explicite de contrôle des extraits (réduction des hallucinations).
- **Scalabilité** : on ne dépend pas de la fenêtre de contexte du modèle (docs longs OK).
- **Multi-modèles** : fonctionne avec Groq (rapide) et Ollama (local) via la couche `LLMProvider`.
- **Auditabilité** : la validation et les issues permettent d’identifier précisément les champs douteux → itération ciblée.

### Plan d’utilisation recommandé

- Mode par défaut : Approche D avec `fix_passes=1`, `top_k=2..3`, `max_chunks=10..20`.
- Si `issues_count > 0` :
  - augmenter `max_chunks` ou `top_k`
  - relancer l’extraction
  - sinon, laisser le champ en `null` (et/ou demander une validation manuelle)

### Pourquoi pas B “seul” ?

L’approche B est excellente comme baseline et pour la performance, mais elle n’a pas nativement :
- un mécanisme de **validation automatique des citations**
- une boucle de correction guidée par les erreurs

L’approche D répond mieux à l’exigence “citer obligatoirement + ne jamais inventer”.

## Livrables du benchmark

- Code A/B/C/D : dossier [benchmark](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark)
- Exécutions : `benchmark/out/*.json`
- Tableau auto : [comparison.md](file:///c:/Users/boubk/Downloads/S8/Stage/RAG/benchmark/comparison.md)
- Rapport (ce document) : `benchmark/rapport_comparatif.md`
