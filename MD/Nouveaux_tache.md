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
| Phase 4 | Développement de l'Agent Final | ✅ Terminée |
| Phase 5 | Structuration des Données | ✅ Terminée |
| Phase 6 | Validation & Évaluation | ✅ Terminée |
| Phase 7 | Intégration dans le Copilot Holokia | ✅ Terminée |
| Phase 8 | Interface Avancée : Multi-Documents & Historique | ✅ Terminée |
| Phase 9 | Authentification & Multi-tenant | ✅ Terminée |
| Phase 10 | Mémoire Court / Moyen / Long terme | ✅ Terminée |
| Phase 11 | Perspectives futures | 🔭 Vision |

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
- [x] **T2.10** — Mettre à jour `architecture.md` avec Supabase + stack frontend (HTML / Netlify / Railway)
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

## Phase 4 — Développement de l'Agent Final ✅ TERMINÉE

**Livrable :** `agent/` — code source de l'agent final

> Démarre après validation de l'approche en T3.6

- [x] **T4.0** — 🆕 Analyse préliminaire du document avant extraction
  - Détecter les catégories présentes (Stratégique, Finance, RH, Data, Cyber)
  - Générer uniquement les questions pertinentes
  - Éviter les prompts hors contexte (anti-hallucination / économie de tokens)
- [x] **T4.0bis** — 🆕 Sous-système de conversion PDF → Markdown
  - Détecter titres/sections via taille de police
  - Convertir tableaux en Markdown structuré
  - Sauvegarder dans `data/processed/`
  - Charger depuis le cache si déjà converti
- [x] **T4.1** — Développer le module de retrieval contextuel (approche sélectionnée)
- [x] **T4.2** — Créer les prompts d'extraction par catégorie :
  - Prompt stratégique (marché, concurrents, tendances)
  - Prompt financier (CA, RN, EBITDA)
  - Prompt RH (effectifs, masse salariale)
  - 🆕 Prompt maturité data (qualité, accessibilité, conformité)
  - 🆕 Prompt cybersécurité / gouvernance (risques, conformité NIST)
- [x] **T4.3** — Références sources obligatoires sur chaque champ :
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
- [x] **T4.4** — Indicateur de confiance sur chaque extraction (0.0 → 1.0)
- [x] **T4.5** — Gestion des champs non trouvés (`null` + message explicatif)
- [x] **T4.6** — Anti-hallucination : contraindre le LLM au contexte fourni uniquement

---

## Phase 5 — Structuration des Données ✅ TERMINÉE

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
- [x] **T5.4** — Valider le schéma avec Samad (alignement diagnostics Copilot)
- [x] **T5.5** — 🆕 Configurer le stockage des JSONs dans **Supabase**

---

## Phase 6 — Validation & Évaluation ✅ TERMINÉE

**Livrable :** `eval/` + `rapport_performance.md`

- [x] **T6.1** — Utiliser les rapports annotés (Phase 0) comme ground truth
- [x] **T6.2** — Définir les métriques d'évaluation :
  - Taux d'extraction correcte par champ (objectif : > 85%)
  - Cohérence des références sources citées
  - Taux de hallucinations détectées
  - Taux de champs `null` non justifiés
- [x] **T6.3** — Comparer les métriques entre Groq et Ollama
- [x] **T6.4** — Itérer sur les prompts selon les résultats
- [x] **T6.5** — Rédiger le rapport de performance final (avant / après optimisation)

---

## Phase 7 — Intégration dans le Copilot Holokia ✅ TERMINÉE

> **Changement de statut réunion 18/05** : cette phase n'est **plus optionnelle**.  
> L'agent doit exposer une API pour s'intégrer dans le Copilot Holokia comme brique agentique autonome.

**Livrable :** `api/` + `interface/` + déploiement Railway

- [x] **T7.1** — API REST (FastAPI) : endpoint `POST /extract`
  - Accepte un PDF → retourne le JSON structuré complet
- [x] **T7.2** — 🆕 Endpoint `GET /status/{job_id}`
  - Suivre l'état d'une extraction en cours (utile pour les gros documents)
- [x] **T7.3** — 🆕 Endpoint `GET /results/{entreprise}`
  - Récupérer les extractions stockées dans Supabase
- [x] **T7.4** — Interface démo simple (HTML / CSS)
  - Upload fichier → affichage résultats + JSON + citations
- [x] **T7.5** — 🆕 Déploiement backend sur **Railway**
- [x] **T7.6** — Documentation API (Swagger / OpenAPI auto-générée par FastAPI)
- [x] **T7.7** — (Optionnel) Connecteur direct vers le Copilot Holokia

---

## Phase 8 — Interface Avancée : Multi-Documents & Historique ✅ TERMINÉE

> **Objectif :** Faire évoluer l'interface de démo vers un produit professionnel utilisable par un consultant ou analyste, avec analyse multi-rapports et traçabilité complète des extractions.

**Livrable :** Interface 3 onglets — *Extraction simple · Multi-docs · Historique* — déployée et intégrable dans le Copilot Holokia

### 8A — Mode Multi-Documents + Questions ciblées

- [x] **T8.1** — Modifier l'interface pour accepter plusieurs fichiers simultanément (drag & drop multiple)
- [x] **T8.2** — Ajouter une zone de question libre
  - Exemple : *"Quel est le taux de croissance de chaque entreprise ?"*
- [x] **T8.3** — Ajouter des questions prédéfinies (liste déroulante basée sur le diagnostic Copilot)
  - Taille du marché, concurrents, CA, effectifs, conformité NIST…
- [x] **T8.4** — Modifier `server.py` pour accepter un tableau de fichiers + une question
- [x] **T8.5** — Modifier le pipeline RAG : indexer N documents avec métadonnée `source_fichier` par chunk
- [x] **T8.6** — Afficher les résultats par document avec synthèse comparative finale
- [x] **T8.7** — Chaque réponse conserve sa citation source (page + extrait + nom du fichier)

**Livrable partiel :** Onglet "Analyse multi-docs" + endpoint `POST /extract-multi`

### 8B — Historique des Extractions

- [x] **T8.8** — Créer l'endpoint `GET /extractions` dans FastAPI (lecture depuis Supabase)
- [x] **T8.9** — Créer l'endpoint `GET /extractions/{id}` pour récupérer un résultat complet
- [x] **T8.10** — Ajouter un onglet **Historique** dans l'interface :
  - Liste des rapports analysés (entreprise, date, modèle, score confiance moyen)
  - Cliquer sur une ligne → afficher le JSON complet
- [x] **T8.10bis** — Ajouter les métriques **Complétude** + **Score qualité** :
  - Complétude = champs remplis / total champs attendus (seuil confiance min = 0.6)
  - Score qualité = Confiance moy. × Complétude
- [x] **T8.11** — Filtres : par date, par entreprise, par modèle LLM utilisé
- [x] **T8.12** — Comparaison côte à côte de deux extractions (champ par champ)
- [x] **T8.13** — Export JSON ou CSV depuis l'historique

**Livrable partiel :** Onglet "Historique" + endpoints GET Supabase

---

### 8C — Page d'accueil : Sélection du Mode d'Analyse

> **Objectif :** Ajouter une page d'entrée avec deux modes distincts,
> orientant l'utilisateur vers le bon outil selon son besoin.

- [x] **T8.14** — Créer une page d'accueil (`index.html`) avec deux cartes cliquables :
  - **Mode Chat** → *"Posez vos propres questions sur vos documents"*
  - **Mode Diagnostic** → *"Analyse structurée automatique"*
- [x] **T8.15** — Appliquer un design cohérent avec l'interface existante
  (couleurs, typographie, logo Holokia)
- [x] **T8.16** — Gérer la navigation entre les deux modes sans rechargement
  complet de page (routing côté client)

**Livrable partiel :** Page d'accueil deployée + navigation fonctionnelle

---

### 8D — Mode Chat Libre sur Documents (Option 1)

> **Objectif :** Permettre à un utilisateur d'uploader ses fichiers et
> de poser librement n'importe quelle question en langage naturel.
> Le LLM répond uniquement depuis le contenu des fichiers chargés.

- [x] **T8.17** — Créer l'interface du Mode Chat :
  - Zone d'upload (drag & drop, multi-fichiers PDF/Word/TXT)
  - Zone de conversation (bulles messages user / assistant)
  - Indicateur de chargement pendant l'indexation
- [x] **T8.18** — Modifier `server.py` : ajouter l'endpoint `POST /chat`
  - Accepte : fichiers + historique de conversation + question courante
  - Retourne : réponse texte + liste des citations (page + extrait + nom fichier)
- [x] **T8.19** — Implémenter le pipeline RAG conversationnel multi-tours :
  - Indexer les documents uploadés dans une session isolée (FAISS temporaire)
  - Injecter l'historique des échanges dans le contexte du prompt
  - Contraindre le LLM au contexte fourni (anti-hallucination)
- [x] **T8.20** — Afficher chaque réponse avec ses citations sources :
  - Numéro de page, extrait textuel, nom du fichier source
  - Indicateur de confiance global de la réponse
- [x] **T8.21** — Gérer la session de chat :
  - Bouton *"Nouvelle conversation"* (reset index + historique)
  - Export de la conversation (JSON ou TXT)

**Livrable partiel :** Onglet "Chat libre" fonctionnel + endpoint `POST /chat`

---

### 8E — Mode Diagnostic Éditable (Option 2 améliorée)

> **Objectif :** Conserver le pipeline de diagnostic structuré existant
> et y ajouter un éditeur de questions permettant à l'utilisateur
> d'adapter les questions selon son secteur ou son client,
> sans modifier le code.

- [x] **T8.22** — Ajouter un panneau latéral "Mes questions" dans
  l'interface du Mode Diagnostic :
  - Liste des questions actives (modifiables inline)
  - Bouton *"Ajouter une question"*
  - Bouton *"Supprimer"* par question
  - Bouton *"Réinitialiser aux questions par défaut"*
- [x] **T8.23** — Créer la table `custom_questions` dans **Supabase** :
  - Champs : `id`, `categorie`, `question_text`, `is_default`,
    `created_at`
  - Pré-remplir avec les questions actuelles du code comme valeurs
    par défaut
- [x] **T8.24** — Ajouter les endpoints dans FastAPI :
  - `GET /questions` → retourner la liste des questions actives
  - `POST /questions` → sauvegarder une nouvelle question
  - `DELETE /questions/{id}` → supprimer une question
  - `POST /questions/reset` → restaurer les questions par défaut
- [x] **T8.25** — Modifier le pipeline d'extraction : charger les
  questions depuis Supabase au lieu du code statique
- [x] **T8.26** — Afficher dans les résultats la liste des questions
  utilisées pour cette extraction (traçabilité)

**Livrable partiel :** Éditeur de questions fonctionnel +
endpoints CRUD Supabase + diagnostic piloté par les questions de la base

---

### Dépendances Phase 8 (mise à jour)

```
T8.14 → T8.16   aucune dépendance (page d'accueil autonome)
T8.17 → T8.21   nécessite Phase 4 terminée (agent final) ✅
T8.22 → T8.26   nécessite T2.9 (Supabase) ✅
                nécessite T7.1 (FastAPI)  ✅
```

### Ordre recommandé (mise à jour)

```
T8.14 → Page d'accueil (2 modes)         ← en premier, bloque tout
T8.22 → Éditeur questions Supabase       ← Option 2, dépendances ✅
T8.17 → Chat libre RAG                   ← Option 1, plus complexe
T8.8  → Historique                       ← en dernier
```

---

### 8F — Thème UI (Dark / Light) + Accessibilité

> **Objectif :** Permettre un basculement immédiat entre thème sombre et thème clair, cohérent sur toutes les pages, avec préférence persistée et respect des standards d'accessibilité.

- [x] **T8.27** — Centraliser les tokens CSS (palette Holokia) et ajouter un override `data-theme="light"`
- [x] **T8.28** — Ajouter un bouton de bascule de thème dans les navbars (icône visible + `aria-label`/`aria-pressed`)
- [x] **T8.29** — Persister la préférence utilisateur (localStorage `holokia_theme`) + appliquer le thème avant rendu (script "early theme")
- [x] **T8.30** — Harmoniser les styles pour le thème light (suppression des couleurs hardcodées `#fff/white`, hover, bordures)

**Livrable :** `html/js/theme.js` + mise à jour `html/css/style.css` et intégration sur l'ensemble des pages (y compris `chat.html`, `demo.html`, `test.html`, `holokia-comparaison.html`)

---

## Phase 9 — Authentification & Multi-tenant ✅ TERMINÉE

> **Objectif :** Chaque entreprise cliente a son propre espace 
> isolé avec son historique — personne ne voit les données des autres.

**Livrable :** Pages login/register + protection des routes + RLS Supabase

- [x] **T9.1** — Activer Supabase Auth (Email / Mot de passe)
- [x] **T9.2** — Créer `html/login.html` et `html/register.html`
- [x] **T9.3** — Protéger les 4 pages (diagnostic, chat, multi, historique)
        → rediriger vers login si non connecté
- [x] **T9.4** — Ajouter `user_id` dans toutes les tables Supabase
        (extractions, chat_history, multi_history)
- [x] **T9.5** — Envoyer le token Auth dans chaque appel API FastAPI
- [x] **T9.6** — Vérifier le token côté FastAPI (middleware Auth)
- [x] **T9.7** — Activer Row Level Security (RLS) sur Supabase
        → chaque client voit uniquement ses données
- [x] **T9.8** — Ajouter `html/js/auth.js` — fonctions login/logout/session
- [x] **T9.9** — Ajouter une confirmation de déconnexion (popup accessible) avant `logout()`

**Livrable :** `login.html` + `register.html` + `auth.js` + RLS Supabase

---

## Phase 10 — Mémoire de l'Agent ✅ Terminée

> **Objectif :** L'agent se souvient du client, de ses analyses
> passées et construit un profil qui s'enrichit dans le temps.

**Livrable :** Mémoire 3 niveaux opérationnelle

### 10A — Mémoire Court Terme (dans la session)

- [x] **T10.1** — Mémoire court terme : réinjecter l'historique récent (N derniers tours) dans le prompt du mode Chat
- [x] **T10.2** — Tester que le contexte est bien maintenu sur 5+ tours

### 10B — Mémoire Moyen Terme (entre les sessions)

- [x] **T10.3** — Au démarrage de session : charger les 5 dernières
        extractions de l'utilisateur depuis Supabase
- [x] **T10.4** — Injecter cet historique dans le contexte du prompt
        système au début de chaque conversation
- [x] **T10.5** — Afficher "Bon retour [prénom] — voici vos
        dernières analyses" sur la page d'accueil

### 10C — Mémoire Long Terme (profil permanent entreprise)

- [x] **T10.6** — Créer table `entreprise_profil` dans Supabase :
```sql
  CREATE TABLE entreprise_profil (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    nom TEXT,
    secteur TEXT,
    score_nist_moyen FLOAT DEFAULT 0,
    score_data_moyen FLOAT DEFAULT 0,
    nb_rapports_analyses INT DEFAULT 0,
    premier_diagnostic DATE,
    dernier_diagnostic DATE,
    points_forts TEXT[],
    axes_amelioration TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
  );
```
- [x] **T10.7** — Mettre à jour le profil automatiquement
        après chaque extraction
- [x] **T10.8** — Afficher l'évolution des scores dans le temps
        (graphique simple HTML/JS)
- [x] **T10.9** — Générer un résumé de profil :
        "Depuis votre premier diagnostic en mai 2024,
         votre score NIST est passé de 2,8 à 3,6"

**Livrable :** Table `entreprise_profil` + mise à jour auto + affichage évolution

---

## Phase 11 — Perspectives Futures 🔭

> Ces fonctionnalités dépassent le cadre du stage
> mais représentent la vision produit long terme Holokia.

- [ ] **T11.1** — Export PDF du diagnostic
        (rapport professionnel avec logo Holokia)
- [ ] **T11.2** — Génération automatique de recommandations IA
        ("Voici les 3 actions prioritaires pour améliorer
         votre score NIST de 2,8 à 4,0")
- [x] **T11.3** — Dashboard Analytics
        (KPIs Confiance / Complétude / Score qualité + graphiques d'évolution, benchmark sectoriel)
- [ ] **T11.4** — Support multilingue
        (questions en français sur docs en anglais/arabe)
- [ ] **T11.5** — Traitement automatique par email
        (client envoie PDF → reçoit diagnostic automatiquement)
- [ ] **T11.6** — Intégration LangGraph pour retry et routing
        conditionnel (si RAG échoue → relancer avec autre stratégie)

---

## 📦 Livrables Finaux

| # | Livrable | Format | Phase | Statut |
|---|----------|--------|-------|--------|
| L0 | Corpus élargi (rapports + audits data + cyber) | PDF + CSV | Phase 0 | ✅ |
| L1 | Spécifications fonctionnelles étendues | Markdown | Phase 1 | ✅ |
| L2 | Architecture multi-modèles + Supabase | Markdown + Diagramme | Phase 2 | ✅ |
| L3 | Benchmark 4 approches × 3 types de docs | Code + Rapport | Phase 3 | ✅ |
| L4 | Code source de l'agent final | Python (GitHub) | Phase 4 | ✅ |
| L5 | Schéma JSON étendu (data + cyber) | JSON Schema + Pydantic | Phase 5 | ✅ |
| L6 | Rapport de performance | Markdown / PDF | Phase 6 | ✅ |
| L7 | API déployée sur Railway + démo | URL + Vidéo | Phase 7 | ✅ |
| L8 | Page 2 modes : Chat libre + Diagnostic éditable | Web app | Phase 8 | ✅ |

---

## 🗓️ Suivi de Progression

| Phase | Statut | Point lundi |
|-------|--------|-------------|
| Phase 0 — Collecte documents | ✅ Terminée | |
| Phase 1 — Analyse du besoin | ✅ Terminée | |
| Phase 2 — Architecture multi-modèles | ✅ Terminée | |
| Phase 3 | Benchmark approches | ✅ Terminée | ⚠️ Présenter choix approche D |
| Phase 4 — Développement agent | ✅ Terminée | |
| Phase 5 — Structuration données | ✅ Terminée | |
| Phase 6 — Validation | ✅ Terminée | |
| Phase 7 — Intégration API | ✅ Terminée | |
| Phase 8A — Multi-Documents         | ✅ Terminée | |
| Phase 8B — Historique            | ✅ Terminée | |
| Phase 8C — Page sélection mode   | ✅ Terminée | | 
| Phase 8D — Mode Chat libre       | ✅ Terminée | | 
| Phase 8E — Mode Diagnostic édit. | ✅ Terminée | | 
| Phase 9 — Authentification       | ✅ Terminée | |
| Phase 10 — Mémoire agent         | ✅ Terminée | |

---

## 🛠️ Stack Technique Officielle Holokia

| Couche | Technologie | Statut |
|--------|-------------|--------|
| Frontend | HTML + Netlify | 🆕 Réunion 18/05 |
| Backend / API | FastAPI + **Railway** | ✅ Déployé |
| LLM | **Groq** (cloud gratuit) + **Ollama** (local) | ✅ Validé |
| Base de données | **Supabase** (remplace SQLite) | 🆕 Réunion 18/05 |
| Vectoriel | FAISS / ChromaDB | ✅ Déjà prévu |
| Parsing | PyMuPDF + python-docx | ✅ Déjà prévu |

---

## 🔒 Sécurité — Points d'Alerte (réunion 18/05)

- [ ] Vérifier les vulnérabilités des dépendances Python (`pip audit`)
- [ ] Verrouiller GitHub : branches protégées, aucun secret dans le code
- [x] Variables sensibles uniquement dans `.env` (jamais committées)
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
