# 📋 Tâches du Projet — Agent RAG d'Analyse de Rapports d'Activité
### *Mis à jour suite à la réunion Holokia du 18/05/2026*

> **Projet :** Développement d'un agent IA pour l'extraction structurée de données depuis des rapports d'activité  
> **Stagiaire :** Boubker (travail individuel)  
> **Encadrant :** Samad Filali  
> **Réunion hebdo :** Chaque lundi à 18h30  
> **Durée :** 3 mois  
> **Stack :** Python · LLM multi-modèles (Groq + Ollama) · LangChain · FAISS/Chroma · PyMuPDF · Supabase · html · FastAPI

---

## Vue d'ensemble des Phases

| Phase | Titre | Statut |
|-------|-------|--------|
| Phase 0 | Collecte des Documents de Test | ✅ Terminée |
| Phase 1 | Analyse du Besoin | ✅ Terminée |
| Phase 2 | Architecture Multi-Modèles & Pipeline RAG | ✅ Terminée |
| Phase 3 | Benchmark des Approches | ✅ Terminée |
| Phase 4 | Développement de l'Agent Final | ⏳ À venir |
| Phase 5 | Structuration des Données | ⏳ À venir |
| Phase 6 | Validation & Évaluation | ⏳ À venir |
| Phase 7 | Intégration dans le Copilot Holokia | 🔴 Obligatoire |
| Phase 8 | Interface Avancée : Multi-Documents & Historique | ⏳ À venir |

---

## Instructions pour Claude (Agent RAG)

Tu es un assistant spécialisé dans l'analyse automatique de rapports d'activité d'entreprises et d'administrations. Tu opères dans un pipeline d'extraction documentaire intégré au **Copilot Holokia** et tu dois :

- **Comprendre** le contenu des documents chargés (PDF, Word, TXT) : rapports annuels, audits data, documents cybersécurité, frameworks NIST
- **Extraire** les informations clés : taille du marché, taux de croissance, intensité concurrentielle, concurrents, tendances du marché, données financières, RH, opérationnelles, **maturité data, cybersécurité et gouvernance**
- **Structurer** les résultats en JSON exploitable pour préremplir le diagnostic stratégique de la plateforme Copilot Holokia
- **Citer obligatoirement** le passage exact source pour chaque donnée extraite (page + extrait textuel)
- **Signaler** les données manquantes ou ambiguës avec un indicateur de confiance — ne jamais inventer
- **Être flexible** : tu peux être appelé avec différents modèles LLM (Groq, Ollama)
- **Exposer une API** : tu dois être accessible via endpoint REST pour interagir avec les autres agents du Copilot

---

## Phase 0 — Collecte des Documents de Test ✅ TERMINÉE

**Livrable :** `data/` — corpus de rapports annoté + README ✅

- [x] **T0.1** — Identifier 5 à 10 entreprises cotées en bourse
- [x] **T0.2** — Télécharger rapports annuels PDF/Texte (AMF, AMMC, SEC EDGAR)
- [x] **T0.3** — Dossier `data/raw/` organisé par entreprise et année
- [x] **T0.4** — `data/README.md` listant chaque document
- [x] **T0.5** — Annotation manuelle 2 rapports (`data/ground_truth.csv`)

> 🆕 **Ajouté réunion 18/05** : élargir le corpus avec des documents data & cyber

- [x] **T0.6** — Collecter 3 à 5 audits de qualité data (publics ou fictifs)
- [x] **T0.7** — Collecter 2 à 3 documents cybersécurité / gouvernance (frameworks NIST, ISO 27001…)
- [x] **T0.8** — Mettre à jour `data/README.md` avec ces nouvelles sources

---

## Phase 1 — Analyse du Besoin ✅ TERMINÉE

**Livrable :** `validation_encadrant.md` ✅ + `mapping_copilot.md` ✅

- [x] **T1.1** — Catalogue des champs à extraire (stratégiques, financiers, RH)
- [x] **T1.2** — Mapping diagnostic Copilot
- [x] **T1.3** — Spécifications fonctionnelles
- [x] **T1.4** — Validation Samad

> 🆕 **Ajouté réunion 18/05** : élargir le catalogue avec les nouveaux champs data/cyber

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

- [x] **T2.1** — Couche d'abstraction LLM (Groq + Ollama)
- [x] **T2.2** — Config via `config.yaml` / `.env`
- [x] **T2.3** — Test providers (Groq + Ollama validés)
- [x] **T2.4** — Parsing PDF (PyMuPDF)
- [x] **T2.5** — Parsing Word (python-docx)
- [x] **T2.6** — Chunking intelligent (hybride : sectionnel + sémantique)
- [x] **T2.7** — Indexation vectorielle (FAISS/ChromaDB)
- [x] **T2.8** — Diagramme d'architecture

> 🆕 **Ajouté réunion 18/05** : migration base de données + sécurité

- [x] **T2.9** — Remplacer SQLite par **Supabase** comme base de données officielle
  - Stocker les résultats d'extraction JSON
  - Stocker les métadonnées des documents ingérés
  - Configurer les accès via variables d'environnement
- [x] **T2.10** — Mettre à jour `architecture.md` avec Supabase + stack frontend (HTML / Netlify / Render)
- [x] **T2.11** — Veille sécurité : vérifier les dépendances Python (versions à jour)
- [x] **T2.12** — Verrouiller le dépôt GitHub (branches protégées, secrets hors du code)

---

## Phase 3 — Benchmark des Approches ✅ TERMINÉE

**Livrable :** `benchmark/` — code des 4 approches + rapport comparatif

- [x] **T3.1** — Approche A : Extraction directe LLM (`benchmark/approach_a.py`)
- [x] **T3.2** — Approche B : RAG classique (`benchmark/approach_b.py`)
- [x] **T3.3** — Approche C : Agent IA autonome (`benchmark/approach_c_agent.py`)
- [x] **T3.4** — Approche D : Combinaison RAG + validation (`benchmark/approach_d_combo.py`)
- [x] **T3.5** — Tableau comparatif (`benchmark/comparison.md`)

  | Critère | A — Direct | B — RAG | C — Agent | D — Combo |
  |---------|-----------|---------|-----------|-----------|
  | Précision | Faible (0/12) | Bonne (7/12) | Variable (0/12) | Bonne (6/12 + 2 issues) |
  | Vitesse | Rapide | Moyenne | Lente | Moyenne → lente |
  | Coût | Élevé | Moyen | Élevé | Moyen → élevé |
  | Docs longs | Faible | Bonne | Bonne | Bonne |
  | Complexité | Faible | Moyenne | Élevée | Élevée |

- [x] **T3.6** — ⚠️ Finaliser `benchmark/rapport_comparatif.md` et **sélectionner l'approche finale**
  - Choix proposé : **Approche D** (RAG + validation/correction)
  - Documenter la justification clairement pour présentation lundi

> 🆕 **Ajouté réunion 18/05** : tester sur les nouveaux types de documents

- [x] **T3.7** — Relancer le benchmark sur un **audit data** (T0.6) et mesurer les scores
- [x] **T3.8** — Relancer sur un **document cybersécurité / NIST** (T0.7) et mesurer les scores
- [x] **T3.9** — Mettre à jour `benchmark/comparison.md` avec ces résultats

**Démo intermédiaire :** `test.html` + `server.py`
- Upload PDF/Word/TXT → `POST /extract` → affichage champs + sources + JSON complet
- Usage : démo réunion + validation rapide des résultats

---

## Phase 4 — Développement de l'Agent Final ⏳ À VENIR

**Livrable :** `agent/` — code source de l'agent final

> Démarre après validation de l'approche en T3.6

- [ ] **T4.0** — 🆕 Analyse préliminaire du document avant extraction
  - Détecter les catégories présentes (Stratégique, Finance, RH, Data, Cyber)
  - Générer uniquement les questions pertinentes
  - Éviter les prompts hors contexte (anti-hallucination / économie de tokens)
- [ ] **T4.1** — Développer le module de retrieval contextuel (approche sélectionnée)
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

---

## Phase 5 — Structuration des Données ⏳ À VENIR

**Livrable :** `schema/` — schéma JSON versionné + modèles Pydantic

- [x] **T5.1** — Schéma JSON cible complet (mis à jour réunion 18/05) :
  ```json
  {
    "meta": {
      "entreprise": "Nom SA",
      "annee_rapport": 2023,
      "date_extraction": "2025-01-01T00:00:00Z",
      "modele_utilise": "llama-3.1-70b",
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
      "existence_donnees": { "valeur": null, "source": null, "confiance": 0 },
      "qualite":           { "valeur": null, "source": null, "confiance": 0 },
      "accessibilite":     { "valeur": null, "source": null, "confiance": 0 },
      "volumetrie":        { "valeur": null, "source": null, "confiance": 0 },
      "historisation":     { "valeur": null, "source": null, "confiance": 0 },
      "conformite":        { "valeur": null, "source": null, "confiance": 0 },
      "documentation":     { "valeur": null, "source": null, "confiance": 0 }
    },
    "diagnostic_cyber_gouvernance": {
      "risques_identifies": { "valeur": [], "source": null, "confiance": 0 },
      "conformite_nist":    { "valeur": null, "source": null, "confiance": 0 },
      "gouvernance_data":   { "valeur": null, "source": null, "confiance": 0 }
    }
  }
  ```
- [x] **T5.2** — Validation du schéma avec Pydantic
- [x] **T5.3** — Versionner le schéma (`schema/v1/data_schema.json`)
- [ ] **T5.4** — Valider le schéma avec Samad (alignement diagnostics Copilot)
- [x] **T5.5** — 🆕 Configurer le stockage des JSONs dans **Supabase**

---

## Phase 6 — Validation & Évaluation ⏳ À VENIR

**Livrable :** `eval/` + `rapport_performance.md`

- [ ] **T6.1** — Utiliser les rapports annotés (Phase 0) comme ground truth
- [ ] **T6.2** — Définir les métriques d'évaluation :
  - Taux d'extraction correcte par champ (objectif : > 85%)
  - Cohérence des références sources citées
  - Taux de hallucinations détectées
  - Taux de champs `null` non justifiés
- [ ] **T6.3** — Comparer les métriques entre Groq et Ollama
- [ ] **T6.4** — Itérer sur les prompts selon les résultats
- [ ] **T6.5** — Rédiger le rapport de performance final (avant / après optimisation)

---

## Phase 7 — Intégration dans le Copilot Holokia 🔴 OBLIGATOIRE

> **Changement de statut réunion 18/05** : cette phase n'est **plus optionnelle**.  
> L'agent doit exposer une API pour s'intégrer dans le Copilot Holokia comme brique agentique autonome.

**Livrable :** `api/` + `interface/` + déploiement Render

- [x] **T7.1** — API REST (FastAPI) : endpoint `POST /extract`
  - Accepte un PDF → retourne le JSON structuré complet
- [x] **T7.2** — 🆕 Endpoint `GET /status/{job_id}`
  - Suivre l'état d'une extraction en cours (utile pour les gros documents)
- [x] **T7.3** — 🆕 Endpoint `GET /results/{entreprise}`
  - Récupérer les extractions stockées dans Supabase
- [x] **T7.4** — Interface démo simple (HTML / CSS)
  - Upload fichier → affichage résultats + JSON + citations
- [x] **T7.5** — 🆕 Déploiement backend sur **Render**
- [x] **T7.6** — Documentation API (Swagger / OpenAPI auto-générée par FastAPI)
- [ ] **T7.7** — (Optionnel) Connecteur direct vers le Copilot Holokia

---

## Phase 8 — Interface Avancée : Multi-Documents & Historique ⏳ À VENIR

> **Objectif :** Faire évoluer l'interface de démo vers un produit professionnel utilisable par un consultant ou analyste, avec analyse multi-rapports et traçabilité complète des extractions.

**Livrable :** Interface 3 onglets — *Extraction simple · Multi-docs · Historique* — déployée et intégrable dans le Copilot Holokia

### 8A — Mode Multi-Documents + Questions ciblées

- [ ] **T8.1** — Modifier l'interface pour accepter plusieurs fichiers simultanément (drag & drop multiple)
- [ ] **T8.2** — Ajouter une zone de question libre
  - Exemple : *"Quel est le taux de croissance de chaque entreprise ?"*
- [ ] **T8.3** — Ajouter des questions prédéfinies (liste déroulante basée sur le diagnostic Copilot)
  - Taille du marché, concurrents, CA, effectifs, conformité NIST…
- [ ] **T8.4** — Modifier `server.py` pour accepter un tableau de fichiers + une question
- [ ] **T8.5** — Modifier le pipeline RAG : indexer N documents avec métadonnée `source_fichier` par chunk
- [ ] **T8.6** — Afficher les résultats par document avec synthèse comparative finale
- [ ] **T8.7** — Chaque réponse conserve sa citation source (page + extrait + nom du fichier)

**Livrable partiel :** Onglet "Analyse multi-docs" + endpoint `POST /extract-multi`

### 8B — Historique des Extractions

- [ ] **T8.8** — Créer l'endpoint `GET /extractions` dans FastAPI (lecture depuis Supabase)
- [ ] **T8.9** — Créer l'endpoint `GET /extractions/{id}` pour récupérer un résultat complet
- [ ] **T8.10** — Ajouter un onglet **Historique** dans l'interface :
  - Liste des rapports analysés (entreprise, date, modèle, score confiance moyen)
  - Cliquer sur une ligne → afficher le JSON complet
- [ ] **T8.11** — Filtres : par date, par entreprise, par modèle LLM utilisé
- [ ] **T8.12** — Comparaison côte à côte de deux extractions (champ par champ)
- [ ] **T8.13** — Export JSON ou CSV depuis l'historique

**Livrable partiel :** Onglet "Historique" + endpoints GET Supabase

### Dépendances Phase 8

```
T8.1 → T8.7   nécessite Phase 4 terminée (agent final)
T8.8 → T8.13  nécessite T2.9 (Supabase) ✅ déjà fait
               nécessite T7.1 (FastAPI)  ← Phase 7 d'abord
```

### Ordre recommandé

```
Phase 5  → Schéma JSON finalisé
Phase 7  → FastAPI + Render déployé     ← débloque 8B
Phase 4  → Agent final opérationnel     ← débloque 8A
Phase 8  → Interface avancée            ← en dernier
```

---

## 📦 Livrables Finaux

| # | Livrable | Format | Phase | Statut |
|---|----------|--------|-------|--------|
| L0 | Corpus élargi (rapports + audits data + cyber) | PDF + CSV | Phase 0 | ✅ |
| L1 | Spécifications fonctionnelles étendues | Markdown | Phase 1 | ✅ |
| L2 | Architecture multi-modèles + Supabase | Markdown + Diagramme | Phase 2 | ✅ |
| L3 | Benchmark 4 approches × 3 types de docs | Code + Rapport | Phase 3 | ✅ |
| L4 | Code source de l'agent final | Python (GitHub) | Phase 4 | ⏳ |
| L5 | Schéma JSON étendu (data + cyber) | JSON Schema + Pydantic | Phase 5 | ⏳ |
| L6 | Rapport de performance | Markdown / PDF | Phase 6 | ⏳ |
| L7 | API déployée sur Render + démo | URL + Vidéo | Phase 7 | ⏳ |
| L8 | Interface 3 onglets déployée | Web app | Phase 8 | ⏳ |

---

## 🗓️ Suivi de Progression

| Phase | Statut | Point lundi |
|-------|--------|-------------|
| Phase 0 — Collecte documents | ✅ Terminée | |
| Phase 1 — Analyse du besoin | ✅ Terminée | |
| Phase 2 — Architecture multi-modèles | ✅ Terminée | |
| Phase 3 | Benchmark approches | ✅ Terminée | ⚠️ Présenter choix approche D |
| Phase 4 — Développement agent | ⏳ À venir | |
| Phase 5 — Structuration données | ⏳ À venir | |
| Phase 6 — Validation | ⏳ À venir | |
| Phase 7 — Intégration API | 🔴 Obligatoire | |
| Phase 8 — Interface avancée | ⏳ À venir | |

---

## 🛠️ Stack Technique Officielle Holokia

| Couche | Technologie | Statut |
|--------|-------------|--------|
| Frontend | HTML + Netlify | 🆕 Réunion 18/05 |
| Backend / API | FastAPI + **Render** | 🆕 Réunion 18/05 |
| LLM | **Groq** (cloud gratuit) + **Ollama** (local) | ✅ Validé |
| Base de données | **Supabase** (remplace SQLite) | 🆕 Réunion 18/05 |
| Vectoriel | FAISS / ChromaDB | ✅ Déjà prévu |
| Parsing | PyMuPDF + python-docx | ✅ Déjà prévu |

---

## 🔒 Sécurité — Points d'Alerte (réunion 18/05)

- [ ] Vérifier les vulnérabilités des dépendances Python (`pip audit`)
- [ ] Verrouiller GitHub : branches protégées, aucun secret dans le code
- [ ] Variables sensibles uniquement dans `.env` (jamais committées)
- [ ] Maintenir les versions à jour (veille dépendances hebdomadaire)

---

## ⭐ Compétences Valorisées par Samad

- Curiosité & apprentissage rapide
- Autonomie & sérieux
- Esprit critique sur la qualité des données
- Force de proposition
- Compréhension des enjeux métier, pas seulement la technique
- 🆕 Vision stratégique sur les agents autonomes et l'intégration métier

---

*Dernière mise à jour : réunion Holokia 18/05/2026 — Boubker*