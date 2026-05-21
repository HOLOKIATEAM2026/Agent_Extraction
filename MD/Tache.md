# 📋 Tâches du Projet — Agent RAG d'Analyse de Rapports d'Activité

### *Mis à jour suite à la réunion Copilot Strategy IA*

> **Projet :** Développement d'un agent IA pour l'extraction structurée de données depuis des rapports d'activité\
> **Stagiaire :** Boubker (travail individuel)\
> **Encadrant :** Samad Filali\
> **Réunion hebdo :** Chaque lundi à 18h30\
> **Durée :** 3 mois\
> **Stack :** Python · LLM multi-modèles · LangChain · FAISS/Chroma · PyMuPDF

***

## Instructions pour Claude (Agent RAG)

Tu es un assistant spécialisé dans l'analyse automatique de rapports d'activité d'entreprises et d'administrations. Tu opères dans un pipeline d'extraction documentaire et tu dois :

- **Comprendre** le contenu des documents chargés (PDF, Word, TXT)
- **Extraire** les informations clés : taille du marché, taux de croissance, intensité concurrentielle, concurrents, tendances du marché, données financières, RH, opérationnelles
- **Structurer** les résultats en JSON exploitable pour préremplir le diagnostic stratégique de la plateforme Copilot Strategy IA
- **Citer obligatoirement** le passage exact source pour chaque donnée extraite (page + extrait textuel)
- **Signaler** les données manquantes ou ambiguës avec un indicateur de confiance — ne jamais inventer
- **Être flexible** : tu peux être appelé avec différents modèles LLM (OpenAI, Gemini, Groq, Qwen, DeepSeek, Ollama)

***

## Phase 0 — Collecte des Documents de Test ⭐ NOUVEAU

### Objectif

Constituer le jeu de données officiel du projet avant tout développement.

### Tâches

- [x] **T0.1** — Identifier 5 à 10 entreprises cotées en bourse avec rapports annuels publics disponibles
  - Exemples : Total Energies, Maroc Telecom, Attijariwafa Bank, L'Oréal, LVMH…
- [x] **T0.2** — Télécharger leurs rapports annuels au format PDF et Texte (source : sites officiels, AMF, AMMC, SEC EDGAR)
- [x] **T0.3** — Créer un dossier `data/raw/` avec les PDFs organisés par entreprise et année
- [x] **T0.4** — Rédiger un fichier `data/README.md` listant chaque document (entreprise, année, source, nb pages)
- [x] **T0.5** — Annoter manuellement 2 rapports (ground truth) pour servir de référence d'évaluation (`data/ground_truth.csv`)

**Livrable :** `data/` — corpus de rapports annoté + README ✅ (Validé)

***

## Phase 1 — Analyse du Besoin

### Objectif

Cadrer précisément les données à extraire et valider avec l'encadrant.

### Tâches

- [x] **T1.1** — Définir les catégories de données à extraire (champs précisés en réunion) :

  **Stratégiques — priorité 1 — préremplissage diagnostic Copilot**
  - Taille du marché
  - Taux de croissance du marché
  - Intensité concurrentielle
  - Liste des concurrents identifiés
  - Tendances du marché
    **Financières — priorité 2**
  - Chiffre d'affaires, résultat net, EBITDA
  - Évolution N vs N-1
    **RH & Opérationnelles — priorité 3**
  - Effectifs, masse salariale
  - Indicateurs de performance clés
- [x] **T1.2** — Mapper chaque champ sur les questions du diagnostic stratégique Copilot
- [x] **T1.3** — Rédiger le document de spécifications fonctionnelles (`validation_encadrant.md` créé)
- [x] **T1.4** — Valider les spécifications avec Samad (point lundi)

**Livrable :** `validation_encadrant.md` préparé ✅ + `mapping_copilot.md` ✅

***

## Phase 2 — Architecture Multi-Modèles & Pipeline RAG ⭐ NOUVEAU

### Objectif

Concevoir une architecture **flexible** permettant de changer de modèle LLM sans modifier le code métier.

### Tâches

#### Architecture multi-modèles (exigence Samad)

- [x] **T2.1** — Concevoir une couche d'abstraction LLM :
  ```python
  # Exemple d'interface cible
  class LLMProvider:
      def __init__(self, provider: str, model: str, **kwargs): ...
      def complete(self, prompt: str) -> str: ...

  # Usage — 1 seule ligne change pour switcher de modèle
  llm = LLMProvider("openai",   "gpt-4o")
  llm = LLMProvider("groq",     "llama3-70b")
  llm = LLMProvider("ollama",   "qwen2.5")
  llm = LLMProvider("deepseek", "deepseek-chat")
  llm = LLMProvider("gemini",   "gemini-1.5-pro")
  ```
- [x] **T2.2** — Configurer les modèles via `config.yaml` / `.env` (aucun hardcode)
- [x] **T2.3** — Tester la connexion avec des providers différents (Groq + Ollama validés via `test_llm.py`)

#### Pipeline documentaire

- [x] **T2.4** — Module de parsing PDF (PyMuPDF) avec extraction des métadonnées (page, section, titre)
- [x] **T2.5** — Module parsing Word (python-docx)
- [x] **T2.6** — Stratégie de chunking intelligent (par section/titre + overlap)
- [x] **T2.7** — Indexation vectorielle (FAISS ou ChromaDB)
- [x] **T2.8** — Diagramme d'architecture (`architecture.md`)

**Livrable :** `architecture.md` + couche LLM abstraite + diagramme

***

## Phase 3 — Benchmark des Approches ⭐ NOUVEAU

### Objectif

Tester et comparer plusieurs méthodes d'extraction — exigence explicite de la réunion.

### Tâches

- [x] **T3.1** — Implémenter **Approche A : Extraction directe LLM** (sans RAG) (`benchmark/approach_a.py`, `run_approach_a.py`)
  - Envoyer le document complet ou tronqué directement au LLM
  - Prompt d'extraction structurée → JSON
  - Avantages : simple / Limites : coût, fenêtre de contexte
- [x] **T3.2** — Implémenter **Approche B : RAG classique** (`benchmark/approach_b.py`, `run_approach_b.py`)
  - Chunking → Vectorisation → Retrieval → Génération
  - Avantages : scalable / Limites : dépend de la qualité du retrieval
- [x] **T3.3** — Implémenter **Approche C : Agent IA autonome** (`benchmark/approach_c_agent.py`, `run_approach_c.py`)
  - Agent avec outils : `search_document`, `extract_section`, `validate_data`
  - Raisonnement multi-étapes (ReAct ou tool-calling)
  - Avantages : flexible / Limites : plus complexe, plus lent
- [x] **T3.4** — Implémenter **Approche D : Combinaison** (`benchmark/approach_d_combo.py`, `run_approach_d.py`)
  - RAG pour le retrieval + Agent pour la validation
- [x] **T3.5** — Tableau comparatif des approches : (`benchmark/comparison.md`)
  | Critère                                                                                                                                            | Approche A                               | Approche B                  | Approche C                          | Approche D                                              |
  | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | --------------------------- | ----------------------------------- | ------------------------------------------------------- |
  | Précision extraction                                                                                                                               | Faible (souvent `null` si texte tronqué) | Bonne (dépend du retrieval) | Variable (dépend du pilotage agent) | Bonne + contrôle citations (issues détectées/corrigées) |
  | Vitesse                                                                                                                                            | Rapide                                   | Moyenne                     | Lente                               | Moyenne → lente                                         |
  | Coût estimé                                                                                                                                        | Élevé (beaucoup de contexte au LLM)      | Moyen                       | Élevé (multi-steps)                 | Moyen (retrieval) → élevé si fix passes                 |
  | Gestion docs longs                                                                                                                                 | Faible                                   | Bonne                       | Bonne                               | Bonne                                                   |
  | Complexité impl.                                                                                                                                   | Faible                                   | Moyenne                     | Élevée                              | Élevée                                                  |
  | **Mesure auto (sur** **`Maroc_Telecom_RFA_2024.pdf`) :** cf. `benchmark/comparison.md` (A: 0/12, B: 7/12, C: 0/12, D: 6/12 + 2 issues validation). | <br />                                   | <br />                      | <br />                              | <br />                                                  |
- [x] **T3.6** — Sélectionner l'approche finale et justifier le choix à Samad (`benchmark/rapport_comparatif.md`)

**Livrable :** `benchmark/` — code des 4 approches + rapport comparatif

***

## Phase 4 — Développement de l'Agent Final

### Objectif

Implémenter l'approche retenue avec toutes les exigences qualité.

### Tâches

- [ ] **T4.1** — Développer le module de retrieval contextuel (approche sélectionnée)
- [ ] **T4.2** — Créer les prompts d'extraction structurée par catégorie
- [ ] **T4.3** — Implémenter les **références sources obligatoires** sur chaque champ :
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
- [ ] **T4.6** — Contraindre le LLM à ne répondre qu'à partir du contexte fourni (anti-hallucination)

**Livrable :** `agent/` — code source de l'agent final

***

## Phase 5 — Structuration des Données

### Objectif

Définir le schéma JSON final aligné sur le diagnostic Copilot Strategy IA.

### Tâches

- [ ] **T5.1** — Schéma JSON cible complet :
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
      "taille_marche": {
        "valeur": "2,3 milliards EUR",
        "source": { "page": 14, "extrait": "..." },
        "confiance": 0.92
      },
      "taux_croissance": {
        "valeur": "8% annuel",
        "source": { "page": 14, "extrait": "..." },
        "confiance": 0.87
      },
      "intensite_concurrentielle": {
        "valeur": "Élevée",
        "source": { "page": 22, "extrait": "..." },
        "confiance": 0.75
      },
      "concurrents": {
        "valeur": ["Concurrent A", "Concurrent B"],
        "source": { "page": 18, "extrait": "..." },
        "confiance": 0.95
      },
      "tendances_marche": {
        "valeur": ["Digitalisation", "IA générative"],
        "source": { "page": 25, "extrait": "..." },
        "confiance": 0.80
      }
    },
    "diagnostic_financier": {
      "chiffre_affaires": { "valeur": null, "source": null, "confiance": 0 },
      "resultat_net":     { "valeur": null, "source": null, "confiance": 0 },
      "ebitda":           { "valeur": null, "source": null, "confiance": 0 }
    },
    "diagnostic_rh": {
      "effectif_total":  { "valeur": null, "source": null, "confiance": 0 },
      "masse_salariale": { "valeur": null, "source": null, "confiance": 0 }
    }
  }
  ```
- [ ] **T5.2** — Validation du schéma avec Pydantic
- [ ] **T5.3** — Versionner le schéma (`schema/v1/data_schema.json`)
- [ ] **T5.4** — Valider le schéma avec Samad (alignement diagnostic Copilot)

**Livrable :** `schema/` — schéma JSON versionné + modèles Pydantic

***

## Phase 6 — Validation & Évaluation

### Objectif

Mesurer la qualité des extractions sur le corpus de rapports réels.

### Tâches

- [ ] **T6.1** — Utiliser les 2 rapports annotés (Phase 0) comme ground truth
- [ ] **T6.2** — Métriques d'évaluation :
  - Taux d'extraction correcte par champ
  - Cohérence des références sources citées
  - Taux de hallucinations détectées
  - Taux de champs `null` non justifiés
- [ ] **T6.3** — Comparer les métriques entre les différents modèles LLM testés
- [ ] **T6.4** — Itérer sur les prompts selon les résultats
- [ ] **T6.5** — Rédiger le rapport de performance final

**Livrable :** `eval/` + `rapport_performance.md`

***

## Phase 7 — Intégration (optionnelle selon avancement)

### Objectif

Rendre l'agent accessible et intégrable dans la plateforme Copilot Strategy IA.

### Tâches

- [ ] **T7.1** — API REST (FastAPI) : endpoint `POST /extract` acceptant un PDF, retournant le JSON
- [ ] **T7.2** — Interface démo Streamlit pour les présentations lundi
- [ ] **T7.3** — (Optionnel) Connecteur vers la plateforme Copilot Strategy IA
- [ ] **T7.4** — Documentation API (Swagger)

**Livrable :** `api/` + `interface/`

***

## Livrables Finaux

| #  | Livrable                           | Format                 | Phase   |
| -- | ---------------------------------- | ---------------------- | ------- |
| L0 | Corpus de rapports annoté          | PDF + CSV              | Phase 0 |
| L1 | Spécifications fonctionnelles      | Markdown               | Phase 1 |
| L2 | Architecture multi-modèles         | Markdown + Diagramme   | Phase 2 |
| L3 | Benchmark des 4 approches          | Code + Rapport         | Phase 3 |
| L4 | Code source de l'agent final       | Python (GitHub)        | Phase 4 |
| L5 | Schéma JSON structuré avec sources | JSON Schema + Pydantic | Phase 5 |
| L6 | Rapport de performance             | Markdown / PDF         | Phase 6 |
| L7 | Démonstration fonctionnelle        | Streamlit / Vidéo      | Phase 7 |

***

## Suivi de Progression

| Phase                                | Statut      | Début | Fin prévue | Point lundi |
| ------------------------------------ | ----------- | ----- | ---------- | ----------- |
| Phase 0 — Collecte documents         | ✅ Terminée  | —     | —          | <br />      |
| Phase 1 — Analyse du besoin          | ✅ Terminée  | —     | —          | <br />      |
| Phase 2 — Architecture multi-modèles | ✅ Terminée  | —     | —          | <br />      |
| Phase 3 — Benchmark approches        | 🔄 En cours | —     | —          | <br />      |
| Phase 4 — Développement agent        | ⏳ À venir   | —     | —          | <br />      |
| Phase 5 — Structuration données      | ⏳ À venir   | —     | —          | <br />      |
| Phase 6 — Validation                 | ⏳ À venir   | —     | —          | <br />      |
| Phase 7 — Intégration                | ⏳ Optionnel | —     | —          | <br />      |

***

## Modèles LLM Recommandés

| Modèle         | Type         | Usage recommandé                 | Données     |
| -------------- | ------------ | -------------------------------- | ----------- |
| GPT-4o         | Propriétaire | Extraction précise, référence    | Cloud       |
| Gemini 1.5 Pro | Propriétaire | Gros documents (contexte long)   | Cloud       |
| Groq / Llama 3 | Propriétaire | Rapidité, tests itératifs        | Cloud       |
| Qwen 2.5       | Open source  | Alternative locale               | Local/Cloud |
| DeepSeek       | Open source  | Raisonnement structuré           | Local/Cloud |
| Ollama         | Open source  | 100% local, souveraineté données | Local ✅     |

> **Règle architecture :** le modèle se configure en 1 ligne dans `config.yaml` — zéro changement dans le code métier.

***

## Compétences Valorisées par Samad

- Curiosité & apprentissage rapide
- Autonomie & sérieux
- Esprit critique sur la qualité des données
- Force de proposition
- Compréhension des enjeux métier, pas seulement la technique

***

*Dernière mise à jour : suite à la réunion Copilot Strategy IA — Boubker*
