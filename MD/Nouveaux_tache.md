# 📋 Tâches du Projet — Agent RAG d'Analyse de Rapports d'Activité
### *Mis à jour suite à la réunion Holokia du 18/05/2026*

> **Projet :** Développement d'un agent IA pour l'extraction structurée de données depuis des rapports d'activité  
> **Stagiaire :** Boubker (travail individuel)  
> **Encadrant :** Samad Filali  
> **Réunion hebdo :** Chaque lundi à 18h30  
> **Durée :** 3 mois  
> **Stack :** Python · LLM multi-modèles · LangChain · FAISS/Chroma · PyMuPDF · Supabase · React · FastAPI

---

## Instructions pour Claude (Agent RAG)

Tu es un assistant spécialisé dans l'analyse automatique de rapports d'activité d'entreprises et d'administrations. Tu opères dans un pipeline d'extraction documentaire intégré au **Copilot Holokia** et tu dois :

- **Comprendre** le contenu des documents chargés (PDF, Word, TXT) : rapports annuels, audits data, documents cybersécurité, frameworks NIST
- **Extraire** les informations clés : taille du marché, taux de croissance, intensité concurrentielle, concurrents, tendances du marché, données financières, RH, opérationnelles, **maturité data, cybersécurité et gouvernance**
- **Structurer** les résultats en JSON exploitable pour préremplir le diagnostic stratégique de la plateforme Copilot Holokia
- **Citer obligatoirement** le passage exact source pour chaque donnée extraite (page + extrait textuel)
- **Signaler** les données manquantes ou ambiguës avec un indicateur de confiance — ne jamais inventer
- **Être flexible** : tu peux être appelé avec différents modèles LLM (OpenAI, Gemini, Groq, Qwen, DeepSeek, Ollama)
- **Exposer une API** : tu dois être accessible via endpoint REST pour interagir avec les autres agents du Copilot

---

## Phase 0 — Collecte des Documents de Test ✅ TERMINÉE

**Livrable :** `data/` — corpus de rapports annoté + README ✅

- [x] T0.1 — Identifier 5 à 10 entreprises cotées en bourse
- [x] T0.2 — Télécharger rapports annuels PDF/Texte (AMF, AMMC, SEC EDGAR)
- [x] T0.3 — Dossier `data/raw/` organisé par entreprise et année
- [x] T0.4 — `data/README.md` listant chaque document
- [x] T0.5 — Annotation manuelle 2 rapports (`data/ground_truth.csv`)

> 🆕 **À compléter (réunion 18/05)** : ajouter des audits data et documents cybersécurité au corpus
- [x] **T0.6** — Collecter 3 à 5 audits de qualité data (publics ou fictifs)
- [x] **T0.7** — Collecter 2 à 3 documents cybersécurité / gouvernance (frameworks NIST, ISO 27001…)
- [x] **T0.8** — Mettre à jour `data/README.md` avec ces nouvelles sources

---

## Phase 1 — Analyse du Besoin ✅ TERMINÉE

**Livrable :** `validation_encadrant.md` ✅ + `mapping_copilot.md` ✅

- [x] T1.1 — Catalogue des champs à extraire (stratégiques, financiers, RH)
- [x] T1.2 — Mapping diagnostic Copilot
- [x] T1.3 — Spécifications fonctionnelles
- [x] T1.4 — Validation Samad

> 🆕 **À compléter (réunion 18/05)** : élargir le catalogue avec les nouveaux champs data/cyber
- [x] **T1.5** — Ajouter au catalogue les métriques **maturité data** :
  - Existence des données
  - Qualité & accessibilité
  - Volumétrie & historisation
  - Conformité & documentation
- [x] **T1.6** — Ajouter les métriques **cybersécurité & gouvernance** :
  - Évaluation des risques cyber identifiés
  - Conformité NIST / ISO
  - Gouvernance des données
- [x] **T1.7** — Mettre à jour `mapping_copilot.md` avec les nouveaux champs

---

## Phase 2 — Architecture Multi-Modèles & Pipeline RAG ✅ TERMINÉE

**Livrable :** `architecture.md` + couche LLM abstraite + diagramme ✅

- [x] T2.1 — Couche d'abstraction LLM
- [x] T2.2 — Config via `config.yaml` / `.env`
- [x] T2.3 — Test providers (Groq + Ollama validés)
- [x] T2.4 — Parsing PDF (PyMuPDF)
- [x] T2.5 — Parsing Word (python-docx)
- [x] T2.6 — Chunking intelligent
- [x] T2.7 — Indexation vectorielle (FAISS/ChromaDB)
- [x] T2.8 — Diagramme d'architecture

> 🆕 **À compléter (réunion 18/05)** : migration base de données + sécurité
- [x] **T2.9** — Remplacer SQLite par **Supabase** comme base de données officielle du projet
  - Stocker les résultats d'extraction JSON
  - Stocker les métadonnées des documents ingérés
  - Configurer les accès via variables d'environnement
- [x] **T2.10** — Mettre à jour `architecture.md` avec Supabase + stack frontend (React / Netlify / Render)
- [x] **T2.11** — Veille sécurité : vérifier les dépendances Python (Axios équivalent, versions à jour)
- [x] **T2.12** — Verrouiller le dépôt GitHub (branches protégées, secrets hors du code)

---

## Phase 3 — Benchmark des Approches 🔄 EN COURS

**Livrable :** `benchmark/` — code des 4 approches + rapport comparatif

- [x] T3.1 — Approche A : Extraction directe LLM (`benchmark/approach_a.py`)
- [x] T3.2 — Approche B : RAG classique (`benchmark/approach_b.py`)
- [x] T3.3 — Approche C : Agent IA autonome (`benchmark/approach_c_agent.py`)
- [x] T3.4 — Approche D : Combinaison (`benchmark/approach_d_combo.py`)
- [x] T3.5 — Tableau comparatif (`benchmark/comparison.md`)

  | Critère | A | B | C | D |
  |---------|---|---|---|---|
  | Précision | Faible (0/12) | Bonne (7/12) | Variable (0/12) | Bonne (6/12 + 2 issues) |
  | Vitesse | Rapide | Moyenne | Lente | Moyenne→lente |
  | Coût | Élevé | Moyen | Élevé | Moyen→élevé |
  | Docs longs | Faible | Bonne | Bonne | Bonne |
  | Complexité | Faible | Moyenne | Élevée | Élevée |

- [ ] **T3.6** — ⚠️ Finaliser `benchmark/rapport_comparatif.md` et sélectionner l'approche finale
  - Approche B (RAG) semble favorite — à confirmer avec Samad lundi
  - Documenter le choix avec justification claire

> 🆕 **À ajouter (réunion 18/05)** : tester sur les nouveaux types de documents
- [ ] **T3.7** — Relancer le benchmark sur un **audit data** (T0.6) et mesurer les scores
- [ ] **T3.8** — Relancer sur un **document cybersécurité / NIST** (T0.7) et mesurer les scores
- [ ] **T3.9** — Mettre à jour `benchmark/comparison.md` avec ces résultats

---

## Phase 4 — Développement de l'Agent Final ⏳ À VENIR

### Objectif
Implémenter l'approche retenue (probablement B — RAG) avec toutes les exigences qualité.

### Tâches

- [ ] **T4.1** — Développer le module de retrieval contextuel (approche sélectionnée en T3.6)
- [ ] **T4.2** — Créer les prompts d'extraction par catégorie :
  - Prompt stratégique (marché, concurrents, tendances)
  - Prompt financier (CA, RN, EBITDA)
  - Prompt RH (effectifs, masse salariale)
  - 🆕 Prompt maturité data (qualité, accessibilité, conformité)
  - 🆕 Prompt cybersécurité / gouvernance (risques, conformité NIST)
- [ ] **T4.3** — Références sources obligatoires sur chaque champ :
  ```json
  {
    "champ": "taille_marche",
    "valeur": "2,3 milliards EUR",
    "source": {
      "page": 14,
      "section": "Analyse de marché §2.1",
      "extrait": "Le marché adressable est estimé à 2,3 milliards d'euros..."
    },
    "confiance": 0.92
  }
  ```
- [ ] **T4.4** — Indicateur de confiance sur chaque extraction (0.0 → 1.0)
- [ ] **T4.5** — Gestion des champs non trouvés (`null` + message explicatif)
- [ ] **T4.6** — Anti-hallucination : contraindre le LLM au contexte fourni uniquement

**Livrable :** `agent/` — code source de l'agent final

---

## Phase 5 — Structuration des Données ⏳ À VENIR

### Objectif
Définir le schéma JSON final aligné sur tous les diagnostics du Copilot Holokia.

### Tâches

- [ ] **T5.1** — Schéma JSON cible complet (mis à jour réunion 18/05) :
  ```json
  {
    "meta": {
      "entreprise": "Nom SA",
      "annee_rapport": 2023,
      "date_extraction": "2025-01-01T00:00:00Z",
      "modele_utilise": "gpt-4o",
      "approche": "RAG"
    },
    "diagnostic_strategique": {
      "taille_marche":             { "valeur": null, "source": null, "confiance": 0 },
      "taux_croissance":           { "valeur": null, "source": null, "confiance": 0 },
      "intensite_concurrentielle": { "valeur": null, "source": null, "confiance": 0 },
      "concurrents":               { "valeur": [], "source": null, "confiance": 0 },
      "tendances_marche":          { "valeur": [], "source": null, "confiance": 0 }
    },
    "diagnostic_financier": {
      "chiffre_affaires": { "valeur": null, "source": null, "confiance": 0 },
      "resultat_net":     { "valeur": null, "source": null, "confiance": 0 },
      "ebitda":           { "valeur": null, "source": null, "confiance": 0 }
    },
    "diagnostic_rh": {
      "effectif_total":  { "valeur": null, "source": null, "confiance": 0 },
      "masse_salariale": { "valeur": null, "source": null, "confiance": 0 }
    },
    "diagnostic_data": {
      "existence_donnees":  { "valeur": null, "source": null, "confiance": 0 },
      "qualite":            { "valeur": null, "source": null, "confiance": 0 },
      "accessibilite":      { "valeur": null, "source": null, "confiance": 0 },
      "volumetrie":         { "valeur": null, "source": null, "confiance": 0 },
      "historisation":      { "valeur": null, "source": null, "confiance": 0 },
      "conformite":         { "valeur": null, "source": null, "confiance": 0 },
      "documentation":      { "valeur": null, "source": null, "confiance": 0 }
    },
    "diagnostic_cyber_gouvernance": {
      "risques_identifies": { "valeur": [], "source": null, "confiance": 0 },
      "conformite_nist":    { "valeur": null, "source": null, "confiance": 0 },
      "gouvernance_data":   { "valeur": null, "source": null, "confiance": 0 }
    }
  }
  ```
- [ ] **T5.2** — Validation du schéma avec Pydantic
- [ ] **T5.3** — Versionner le schéma (`schema/v1/data_schema.json`)
- [ ] **T5.4** — Valider le schéma avec Samad (alignement tous diagnostics Copilot)
- [ ] **T5.5** — 🆕 Configurer le stockage des JSONs dans **Supabase**

**Livrable :** `schema/` — schéma JSON versionné + modèles Pydantic

---

## Phase 6 — Validation & Évaluation ⏳ À VENIR

### Tâches

- [ ] **T6.1** — Utiliser les rapports annotés (Phase 0) comme ground truth
- [ ] **T6.2** — Métriques d'évaluation :
  - Taux d'extraction correcte par champ
  - Cohérence des références sources citées
  - Taux de hallucinations détectées
  - Taux de champs `null` non justifiés
- [ ] **T6.3** — Comparer les métriques entre les différents modèles LLM
- [ ] **T6.4** — Itérer sur les prompts selon les résultats
- [ ] **T6.5** — Rédiger le rapport de performance final

**Livrable :** `eval/` + `rapport_performance.md`

---

## Phase 7 — Intégration dans le Copilot Holokia ⚠️ OBLIGATOIRE (réunion 18/05)

> **Changement de statut** : cette phase n'est **plus optionnelle**. L'agent doit exposer une API pour s'intégrer dans le Copilot Holokia comme brique agentique autonome.

### Tâches

- [ ] **T7.1** — API REST (FastAPI) : endpoint `POST /extract` acceptant un PDF → retourne le JSON
- [ ] **T7.2** — 🆕 Endpoint `GET /status/{job_id}` pour suivre l'état d'une extraction en cours
- [ ] **T7.3** — 🆕 Endpoint `GET /results/{entreprise}` pour récupérer les extractions stockées dans Supabase
- [ ] **T7.4** — Interface démo Streamlit pour les présentations lundi
- [ ] **T7.5** — 🆕 Déploiement backend sur **Render**
- [ ] **T7.6** — Documentation API (Swagger / OpenAPI)
- [ ] **T7.7** — (Optionnel) Connecteur direct vers le Copilot Holokia

**Livrable :** `api/` + `interface/` + déploiement Render

---

## Livrables Finaux

| # | Livrable | Format | Phase |
|---|----------|--------|-------|
| L0 | Corpus élargi (rapports + audits data + cyber) | PDF + CSV | Phase 0 |
| L1 | Spécifications fonctionnelles étendues | Markdown | Phase 1 |
| L2 | Architecture multi-modèles + Supabase | Markdown + Diagramme | Phase 2 |
| L3 | Benchmark 4 approches × 3 types de docs | Code + Rapport | Phase 3 |
| L4 | Code source de l'agent final | Python (GitHub) | Phase 4 |
| L5 | Schéma JSON étendu (data + cyber) | JSON Schema + Pydantic | Phase 5 |
| L6 | Rapport de performance | Markdown / PDF | Phase 6 |
| L7 | API déployée sur Render + démo Streamlit | URL + Vidéo | Phase 7 |

---

## Suivi de Progression

| Phase | Statut | Point lundi |
|-------|--------|-------------|
| Phase 0 — Collecte documents | ✅ Terminée (T0.6→T0.8 à faire) | |
| Phase 1 — Analyse du besoin | ✅ Terminée (T1.5→T1.7 à faire) | |
| Phase 2 — Architecture multi-modèles | ✅ Terminée (T2.9→T2.12 à faire) | |
| Phase 3 — Benchmark approches | 🔄 En cours — T3.6 à finaliser | ⚠️ Présenter choix approche |
| Phase 4 — Développement agent | ⏳ À venir | |
| Phase 5 — Structuration données | ⏳ À venir | |
| Phase 6 — Validation | ⏳ À venir | |
| Phase 7 — Intégration API | 🔴 Obligatoire (non optionnel) | |

---

## Stack Technique Officielle Holokia

| Couche | Technologie | Statut |
|--------|-------------|--------|
| Frontend | React + Netlify | 🆕 Réunion 18/05 |
| Backend / API | FastAPI + **Render** | 🆕 Réunion 18/05 |
| LLM | Ollama, Gemini, Groq, Qwen, DeepSeek | ✅ Déjà prévu |
| Base de données | **Supabase** (remplace SQLite) | 🆕 Réunion 18/05 |
| Vectoriel | FAISS / ChromaDB | ✅ Déjà prévu |
| Parsing | PyMuPDF + python-docx | ✅ Déjà prévu |

---

## Sécurité — Points d'Alerte (réunion 18/05)

- [ ] Vérifier les vulnérabilités des dépendances Python (`pip audit`)
- [ ] Verrouiller GitHub : branches protégées, aucun secret dans le code
- [ ] Variables sensibles uniquement dans `.env` (jamais commitées)
- [ ] Maintenir les versions à jour (veille dépendances hebdomadaire)

---

## Compétences Valorisées par Samad

- Curiosité & apprentissage rapide
- Autonomie & sérieux
- Esprit critique sur la qualité des données
- Force de proposition
- Compréhension des enjeux métier, pas seulement la technique
- 🆕 Vision stratégique sur les agents autonomes et l'intégration métier

---

*Dernière mise à jour : réunion Holokia 18/05/2026 — Boubker*
