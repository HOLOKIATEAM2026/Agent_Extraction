# Holokia Copilot Strategy IA — Agent RAG 🚀

![Holokia Logo](html/logo/cropped-logo_holokia_noir.jpg)

**Holokia Copilot Strategy IA** est une application avancée d'extraction d'informations et d'analyse de rapports d'activité basée sur l'intelligence artificielle (RAG - Retrieval-Augmented Generation). Conçu pour automatiser le diagnostic stratégique des entreprises, ce copilote extrait, structure et source les données clés depuis des documents complexes (PDF, Word, TXT).

---

## 📸 Aperçu de l'Application

### 1. Page d'Accueil
Le point d'entrée du copilote, offrant une vue d'ensemble des capacités de l'agent.
![Accueil](capture%20écran/RAG_acceuil.png)

### 2. Mode Diagnostic
L'outil principal d'extraction. Importez un rapport d'activité et l'IA génère automatiquement un diagnostic structuré (Stratégique, Financier, RH, Data, Cyber), avec un système de questions dynamiques personnalisables.
![Diagnostic](capture%20écran/RAG_diagnostic.png)

### 3. Mode Chat Libre
Discutez naturellement avec vos documents. L'agent RAG analyse le contexte de vos fichiers et vous fournit des réponses précises avec les numéros de pages sources.
![Chat](capture%20écran/RAG_chat.png)

### 4. Mode Comparaison (Multi-Documents)
Analysez plusieurs rapports simultanément (ex: Rapports de 2022, 2023 et 2024 ou rapports de concurrents). Posez vos questions et obtenez une synthèse comparative document par document.
![Multi-Docs](capture%20écran/RAG_multi.png)

### 5. Historique des Extractions
Retrouvez toutes vos extractions précédentes, filtrez par entreprise ou modèle d'IA, et rouvrez instantanément vos diagnostics grâce à la base de données Supabase.
![Historique](capture%20écran/RAG_historique.png)

### 6. Profil Client
Consultez et éditez votre profil entreprise (nom, secteur), suivez l’évolution des scores et accédez rapidement à l’historique et aux nouvelles extractions.
![Profil](capture%20écran/Profil.png)

### 7. Dashboard Analytics
Visualisez vos analyses sous forme de graphiques (évolution, répartition par modèle, maturité par domaine, top entreprises) avec filtres (entreprise, modèle, période).
![Dashboard](capture%20écran/Dashboard.png)

---

## ✨ Fonctionnalités Clés

- **Extraction Intelligente (RAG)** : Analyse de documents complexes pour en tirer des données stratégiques, financières, RH, etc.
- **Support Multi-Modèles** : Compatible avec les API Cloud (Groq, OpenAI) et les modèles locaux (Ollama : Mistral, Qwen).
- **Citations et Sourçage** : Chaque information extraite est accompagnée de son extrait source et du numéro de page.
- **Questions Dynamiques** : L'interface permet d'ajouter, modifier et gérer vos propres questions d'extraction.
- **Base de données persistante** : Historique complet des diagnostics, des sessions de chat et des comparaisons via **Supabase** (multi-tenant par utilisateur).
- **Profil & Évolution** : Page profil dédiée (édition + courbe d’évolution NIST/Data).
- **Dashboard Analytics** : Graphiques classiques (lignes, barres, radar, donut) filtrables.
- **Traitement Asynchrone** : Support des documents volumineux grâce à un traitement en arrière-plan.

---

## 🏗️ Architecture Technique

Le projet est divisé en un backend robuste en Python (FastAPI) et un frontend fluide en HTML/JS pur.

### Backend (Python / FastAPI)
- **Framework Web** : `FastAPI` + `Uvicorn`
- **Orchestration IA** : `LangChain` (Core, Community, Groq, Ollama)
- **Base Vectorielle** : `ChromaDB` / `FAISS` pour la recherche de similarité.
- **Traitement Documentaire** : `PyMuPDF` (Fitz), `pdfplumber`, `python-docx`
- **Validation des données** : `Pydantic` (Génération de JSON structurés)
- **Base de Données relationnelle** : `Supabase` (PostgreSQL)

### Frontend (HTML / CSS / JS)
- Architecture sans framework lourd (Vanilla JS).
- Découpage par logique métier (`diagnostic.js`, `chat.js`, `multi.js`, `historique.js`).
- UI moderne, responsive, avec gestion des états asynchrones et des chargements.

---

## 🚀 Installation & Lancement

### Prérequis
- **Python 3.10+**
- (Optionnel) **Ollama** installé localement si vous souhaitez utiliser des modèles open-source sans API.
- Un projet **Supabase** (pour l'historique).

### 1. Cloner et préparer l'environnement

```bash
git clone <votre-repo>
cd RAG
python -m venv venv

# Activation sous Windows :
venv\Scripts\activate
# Activation sous Mac/Linux :
source venv/bin/activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration des variables d'environnement
Créez un fichier `.env` à la racine du projet et ajoutez vos clés :

```env
# API Keys LLM
GROQ_API_KEY=gsk_votre_cle_groq
# OPENAI_API_KEY=sk_votre_cle_openai (Optionnel)

# Configuration Supabase (Base de données)
SUPABASE_ENABLED=1
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_SERVICE_ROLE_KEY=votre_cle_secrete_supabase
```

### 4. Initialiser la base de données
Exécutez le script SQL présent dans `supabase/migrations/setup_history_tables.sql` directement dans l'éditeur SQL de votre projet Supabase pour créer les tables nécessaires.

### 5. Lancer le serveur

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. Accéder à l'application
Ouvrez le fichier `html/index.html` dans votre navigateur web, ou servez le dossier `html` via un serveur statique léger (comme Live Server sur VSCode).

---

## 🛠️ Configuration Avancée (`config.yaml`)

Le fichier `config.yaml` permet de définir le comportement par défaut de l'agent :

```yaml
default_provider: "groq"
default_model: "llama-3.1-8b-instant"

embeddings:
  provider: "ollama"
  model: "nomic-embed-text"
  base_url: "http://localhost:11434"

vectorstore:
  type: "chroma"
  persist_dir: "vectorstore/chroma"
```
*Note pour le déploiement Cloud (ex: Render) : Pensez à modifier le provider d'embeddings si vous n'avez pas accès à une instance Ollama locale en production.*

---

## 📐 Diagrammes

### 1. Diagramme de Cas d'Utilisation
Vue globale des interactions principales entre l'utilisateur et le système : upload de documents, extraction diagnostique, chat libre, comparaison multi-documents et consultation de l'historique.

![Use Case](capture%20écran/UseCase.png)

### 2. Diagramme de Classes
Représentation de la structure logique du projet, des principales entités métier et des relations entre les modules backend, les composants RAG et les objets de données.

![Diagramme de Classes](capture%20écran/Diagramme_de_Classe.png)

### 3. Diagramme de Séquence
Illustration du déroulement d'une extraction, depuis l'envoi d'un document par l'utilisateur jusqu'au traitement RAG, la génération de la réponse et le retour du résultat structuré.

![Diagramme de Séquence](capture%20écran/DiagrammeSequence.png)

---


## 👥 Auteur
Projet développé dans le cadre de l'outil **Holokia Copilot Strategy IA**.
