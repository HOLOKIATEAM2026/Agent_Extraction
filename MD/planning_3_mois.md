# 🗓️ Planning — Agent RAG · Analyse de Rapports d'Activité

**Durée :** 3 mois · **Début :** Semaine 1 · **Stack :** Python · LangChain · FAISS/Chroma · OpenAI

***

## Vue d'ensemble

| Mois              | Phases            | Focus                    |
| ----------------- | ----------------- | ------------------------ |
| Mois 1 (S1 → S4)  | Phase 1 + Phase 2 | Cadrage + Architecture   |
| Mois 2 (S5 → S8)  | Phase 3 + Phase 4 | Développement + Données  |
| Mois 3 (S9 → S12) | Phase 5 + Phase 6 | Validation + Intégration |

***

## 🟡 Mois 1 — Cadrage & Architecture

> *Comprendre le problème, poser les fondations techniques.*

### Semaine 1 — Analyse du besoin (T1.1 → T1.3)

- [x] **T1.1** — Inventorier les types de rapports cibles
  - Entreprises privées (PME/ETI), grands groupes cotés
  - Administrations publiques, ONG / associations
- [x] **T1.2** — Définir le catalogue de champs à extraire
  - Financiers : CA, résultat net, EBITDA, trésorerie, bilan
  - RH : effectifs, masse salariale, turnover, absentéisme
  - Opérationnels : projets, KPIs, implantations, RSE
- [x] **T1.3** — Rédiger les spécifications fonctionnelles
  - Cas d'usage, personas (analyste, consultant, auditeur)
  - Scénarios A/B/C détaillés

**Livrable :** `specs_fonctionnelles.md`  *(déja produit)*

***

### Semaine 2 — Collecte des données de test (T1.4 → T1.5)

- [x] **T1.4** — Collecter 15 à 20 rapports d'activité
  - Télécharger des 10-K via SEC EDGAR (script Python fourni)
  - Récupérer des rapports français sur data.gouv.fr
  - Compléter avec des rapports fictifs si nécessaire
- [x] **T1.5** — Valider les spécifications avec l'encadrant
  - Présenter le catalogue de champs
  - Confirmer les priorités d'extraction

**Livrable :** Dossier `data/raw/` avec les rapports bruts

***

### Semaine 3 — Choix de la stack technique (T2.1 → T2.2)

- [x] **T2.1** — Comparer et choisir les outils
  - Framework RAG : LangChain vs LlamaIndex → **décision documentée**
  - Base vectorielle : FAISS vs Chroma vs Azure Cognitive Search
  - Modèle d'embedding : OpenAI vs sentence-transformers multilingue
- [x] **T2.2** — Concevoir le pipeline d'ingestion
  - Parsing PDF : PyMuPDF + pdfplumber (pour les tableaux)
  - Parsing Word : python-docx
  - Nettoyage et normalisation du texte

**Livrable :** `architecture.md` (section stack technique) ✅

***

### Semaine 4 — Architecture & chunking (T2.3 → T2.5)

- [x] **T2.3** — Implémenter la stratégie de chunking hybride
  - Chunking par section/titre pour docs structurés
  - Chunking sémantique (512 tokens, overlap 64) pour docs variables
  - Traitement séparé des tableaux financiers
- [x] **T2.4** — Mettre en place l'indexation vectorielle
  - Choisir et configurer le modèle d'embedding multilingue
  - Créer et peupler la base vectorielle avec les rapports de test
- [x] **T2.5** — Produire le diagramme d'architecture complet

**Livrable :** `architecture.md` finalisé + diagramme technique ✅

***

## 🔵 Mois 2 — Développement du Pipeline

> *Construire le cœur de l'agent : extraction, structuration, citations.*

### Semaine 5 — Module de retrieval (T3.1)

- [ ] **T3.1** — Développer le module de recherche contextuelle
  - Recherche par similarité vectorielle (cosine similarity)
  - Tester différents paramètres (top-k, seuil de similarité)
  - Implémenter le re-ranking si les résultats sont insuffisants
  - Tester sur 5 rapports avec des requêtes financières simples

**Livrable :** `agent/retrieval.py` fonctionnel

***

### Semaine 6 — Prompts d'extraction (T3.2)

- [ ] **T3.2** — Concevoir les prompts d'extraction structurée
  - Prompt système général (anti-hallucination, format JSON strict)
  - Prompt financier : CA, RN, EBITDA, trésorerie
  - Prompt RH : effectifs, masse salariale, turnover
  - Prompt opérationnel : projets, KPIs, implantations
  - Gérer les cas `null` (donnée absente vs. non mentionnée)

**Livrable :** `agent/prompts/` — collection de prompts versionnés

***

### Semaine 7 — Génération JSON & citations (T3.3 → T3.4)

- [ ] **T3.3** — Implémenter la génération de sorties JSON
  - Définir le schéma JSON cible final (modulaire par type d'entité)
  - Validation du format avec Pydantic
  - Gestion des erreurs de parsing LLM
- [ ] **T3.4** — Gérer les citations sources
  - Numéro de page + extrait textuel pour chaque champ extrait
  - Lier chaque valeur JSON à son chunk source

**Livrable :** `agent/extractor.py` + `schema/data_schema.json`

***

### Semaine 8 — Gestion des hallucinations & schéma de données (T3.5 + Phase 4)

- [ ] **T3.5** — Mettre en place la gestion des hallucinations
  - Contraindre le LLM à répondre uniquement depuis le contexte
  - Implémenter le score de confiance par champ (0.0 → 1.0)
  - Post-traitement : vérification de cohérence des valeurs
- [ ] **T4.1 → T4.4** — Finaliser le schéma de données
  - Schéma complet avec profils par type d'entité
  - Mapping automatique LLM → JSON structuré
  - Règles `null` vs champ absent
  - Versionner le schéma (`v1.0`)

**Livrable :** `agent/` complet + `schema/data_schema_v1.json`

***

## 🟢 Mois 3 — Validation & Intégration

> *S'assurer que ça marche vraiment, puis rendre l'agent accessible.*

### Semaine 9 — Constitution du jeu de test (T5.1 → T5.2)

- [ ] **T5.1** — Constituer le ground truth annoté manuellement
  - Annoter 10 rapports à la main (valeurs correctes par champ)
  - Couvrir les 4 types d'organisations
  - Format CSV : `fichier, champ, valeur_attendue, page_source`
- [ ] **T5.2** — Définir les métriques d'évaluation
  - Taux d'extraction correcte par champ (objectif : > 85%)
  - Taux de faux positifs / faux négatifs
  - Taux de détection des données manquantes

**Livrable :** `eval/ground_truth.csv`

***

### Semaine 10 — Évaluation automatique (T5.3 → T5.4)

- [ ] **T5.3** — Implémenter le script d'évaluation automatique
  - Comparer les extractions de l'agent au ground truth
  - Générer un rapport de métriques par champ et par type d'entité
- [ ] **T5.4** — Analyser les erreurs
  - Identifier les patterns d'échec (tableaux mal parsés, ambiguïtés…)
  - Prioriser les corrections selon l'impact

**Livrable :** `eval/evaluate.py` + premier rapport de performance

***

### Semaine 11 — Itérations & optimisation (T5.5 → T5.6)

- [ ] **T5.5** — Itérer sur les prompts et le chunking
  - Corriger les prompts qui produisent le plus d'erreurs
  - Ajuster la taille des chunks si nécessaire
  - Re-tester sur le ground truth après chaque modification
- [ ] **T5.6** — Rédiger le rapport de performance final
  - Métriques avant/après optimisation
  - Analyse des limites connues
  - Recommandations pour la suite

**Livrable :** `rapport_performance.md`

***

### Semaine 12 — Intégration & démonstration (Phase 6)

- [ ] **T6.1** — Exposer le pipeline via une API REST (FastAPI)
  - Endpoint `POST /extract` — upload PDF → JSON en retour
  - Endpoint `GET /health` — statut du service
- [ ] **T6.2** — Créer une interface utilisateur minimale (Streamlit)
  - Upload de document
  - Affichage du JSON extrait avec scores de confiance
  - Visualisation des citations sources
- [ ] **T6.4** — Documenter l'API (Swagger / OpenAPI)
- [ ] Préparer la démonstration finale (live ou vidéo)

**Livrable :** `api/` + `app/` + démo fonctionnelle

***

## 📦 Récapitulatif des Livrables

| #  | Livrable                      | Fichier                       | Semaine cible |
| -- | ----------------------------- | ----------------------------- | ------------- |
| L1 | Spécifications fonctionnelles | `specs_fonctionnelles.md`     | S1 ✅          |
| L2 | Architecture technique        | `architecture.md` + diagramme | S4            |
| L3 | Code source pipeline RAG      | `agent/` (GitHub)             | S8            |
| L4 | Schéma de données             | `schema/data_schema_v1.json`  | S8            |
| L5 | Jeu de tests annoté           | `eval/ground_truth.csv`       | S9            |
| L6 | Rapport de performance        | `rapport_performance.md`      | S11           |
| L7 | Démonstration fonctionnelle   | Vidéo ou démo live            | S12           |

***

## ⚠️ Points de vigilance

- **Semaine 2** — La collecte de données conditionne tout le reste. Ne pas la sous-estimer.
- **Semaine 6** — La qualité des prompts détermine 70% de la qualité finale. Prévoir du temps d'itération.
- **Semaine 9** — L'annotation manuelle du ground truth est longue. Commencer tôt, même partiellement.
- **Phase 6** — Optionnelle si le temps manque. L'API FastAPI est prioritaire sur l'interface Streamlit.

***

## Suivi de Progression

| Phase | Statut | Début | Fin prévue | Commentaires |
|-------|--------|-------|------------|--------------|
| Phase 1 — Analyse du besoin | ✅ Terminée | — | — | |
| Phase 2 — Architecture RAG | ✅ Terminée | — | — | |

***

*Planning v1.0 — Projet Agent RAG — 3 mois*
