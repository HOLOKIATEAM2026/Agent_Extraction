# PROJET DE FIN D'ÉTUDES

## Développement d'un Agent Intelligent d'Analyse Automatique de Rapports d'Activité Basé sur l'Architecture RAG

### Intégration dans le Copilot Holokia

---

**Réalisé par :** CHEYOUKH Boubker  
**Formation :** 4IIA - Intelligence Artificielle  
**Encadrant académique :** HOUEKPO DANNON Gilchris Mahunan - HESTIM  
**Encadrant industriel :** M. Samad Filali - Holokia  
**Période de stage :** 11/05/2026 → 11/08/2026

Année universitaire 2025-2026

---

## Dédicaces

_Du profond de mon cœur, je dédie ce travail à tous ceux qui me sont chers._

**À MES CHERS PARENTS**

Que ce travail soit l'expression de ma reconnaissance pour vos sacrifices consentis, votre soutien moral et matériel que vous n'avez cessé de prodiguer. Vous avez tout fait pour mon bonheur et ma réussite. Que Dieu vous préserve en bonne santé et vous accorde une longue vie.

**À MES FRÈRES ET SŒURS**

Vous étiez toujours présents pour m'aider et m'encourager. Sachiez que vous serez toujours dans mon cœur.

**À TOUS MES AMIS**

À tous mes amis qui n'ont cessé de m'encourager et de me soutenir.

---

## Remerciements

_« الحمد لله الذي هدانا لهذا وما كنا لنهتدي لولا أن هدانا الله »_

Nous exprimons nos profondes gratitudes et respectueuse reconnaissance à notre encadreur.

La réalisation de ce projet de fin d'études n'aurait pas été possible sans le concours de nombreuses personnes à qui j'exprime ici ma plus sincère reconnaissance.

Mes remerciements les plus chaleureux s'adressent en premier lieu à **M. Samad Filali**, encadrant industriel au sein de Holokia, pour m'avoir accueilli dans son équipe, pour la confiance qu'il m'a accordée dès le premier jour et pour la qualité de l'encadrement dont j'ai pu bénéficier tout au long de ces trois mois. Sa disponibilité, ses conseils avisés et sa vision stratégique sur les enjeux de l'intelligence artificielle appliquée aux métiers m'ont profondément enrichi.

Je tiens également à remercier **HOUEKPO DANNON Gilchris Mahunan**, tuteur pédagogique à HESTIM, pour le suivi rigoureux et constructif qu'il m'a apporté, ainsi que pour ses orientations méthodologiques précieuses lors de la rédaction de ce rapport.

Mes remerciements vont aussi à l'ensemble de l'équipe Holokia pour son accueil, sa bienveillance et les échanges professionnels enrichissants qui ont contribué à nourrir ma réflexion tout au long du stage.

Enfin, j'adresse une pensée reconnaissante à ma famille et à mes proches pour leur soutien moral constant, ainsi qu'à l'ensemble du corps pédagogique d'HESTIM pour la qualité de la formation qui m'a préparé à relever ce défi.

---

## Liste des acronymes et abréviations

| Acronyme | Signification |
|----------|---------------|
| **API** | Application Programming Interface |
| **CA** | Chiffre d'Affaires |
| **EBITDA** | Earnings Before Interest, Taxes, Depreciation and Amortization |
| **FAISS** | Facebook AI Similarity Search |
| **IA** | Intelligence Artificielle |
| **ISO** | International Organization for Standardization |
| **JSON** | JavaScript Object Notation |
| **LLM** | Large Language Model (Grand Modèle de Langage) |
| **NIST** | National Institute of Standards and Technology |
| **NLP** | Natural Language Processing (Traitement du Langage Naturel) |
| **PFE** | Projet de Fin d'Études |
| **RAG** | Retrieval-Augmented Generation |
| **REST** | Representational State Transfer |
| **RH** | Ressources Humaines |
| **RN** | Résultat Net |

---

## Résumé exécutif

Ce projet de fin d'études présente le développement d'un agent intelligent basé sur l'architecture RAG (Retrieval-Augmented Generation), conçu pour automatiser l'extraction et l'analyse de données à partir de rapports d'activité d'entreprises. Intégré au sein du Copilot Holokia, cet agent constitue une brique essentielle pour la transformation digitale des processus d'analyse stratégique.

Le système développé est capable de traiter des documents aux formats PDF, Word et texte brut, d'en extraire automatiquement les informations clés selon cinq dimensions diagnostiques (stratégique, financière, RH, maturité data, cybersécurité), et de restituer ces données sous forme d'un objet JSON structuré accompagné de citations sources précises.

Les résultats obtenus démontrent l'efficacité de l'approche : un taux d'extraction correcte supérieur à 85% sur les champs cibles, un mécanisme d'anti-hallucination efficace, et une intégration réussie via une API REST déployée en production sur Render.

**Mots-clés :** RAG, LLM, extraction d'information, rapports d'activité, intelligence artificielle générative, JSON, FastAPI, Supabase, LangChain, Groq, Ollama

---

## Abstract

Organizations produce yearly large volumes of activity reports that contain highly valuable strategic, financial, operational and HR data. Yet, manually processing these documents is time-consuming, costly, and prone to interpretation errors. The challenge is to design a reliable system capable of automating this analytical reading in a structured way.

This paper presents the development of an intelligent agent based on the RAG (Retrieval-Augmented Generation) architecture, integrated into the Holokia Copilot, a decision-support platform for consultants and analysts. The agent processes PDF, Word, or plain-text files, automatically extracts key data - markets, financial indicators, HR metrics, data maturity, cybersecurity and governance - and returns a structured JSON object with mandatory source citations and confidence scores.

**Keywords:** RAG, LLM, information extraction, activity reports, generative artificial intelligence, JSON, FastAPI, Supabase, LangChain, Groq, Ollama

---

## Table des matières

1. Introduction générale
   1.1 Contexte général
   1.2 Problématique, objectifs et périmètre
   1.3 Organisation du rapport

2. Fondements Théoriques : IA Générative, LLM et Architecture RAG
   2.1 L'intelligence artificielle générative et les grands modèles de langage
   2.2 L'architecture RAG (Retrieval-Augmented Generation)
   2.3 Extraction d'information depuis des documents non structurés
   2.4 Conclusion du chapitre et hypothèses de travail

3. Contexte Opérationnel, Analyse du Besoin et Conception de l'Architecture
   3.1 Présentation de l'entreprise d'accueil : Holokia
   3.2 Analyse du besoin et spécifications fonctionnelles
   3.3 Benchmark comparatif des approches d'extraction
   3.4 Architecture technique du système

4. Développement, Validation et Intégration de l'Agent Intelligent
   4.1 Développement de l'agent final
   4.2 Schéma de données structuré
   4.3 Validation et évaluation des performances
   4.4 Intégration dans le Copilot Holokia
   4.5 Perspectives : interface avancée multi-documents

5. Conclusion Générale
   5.1 Synthèse des résultats
   5.2 Bilan du stage
   5.3 Perspectives et ouvertures

Références Bibliographiques
Annexes

---

*[Le contenu détaillé du rapport continue avec tous les chapitres...]*

## Captures d'écran de l'application

### Figure 1 : Page d'accueil du Copilot Holokia

![Page d'accueil](capture%20écran/RAG_acceuil.png)

**Description :** L'écran d'accueil présente les trois modes d'analyse disponibles : Diagnostic automatique, Chat libre et Comparaison multi-documents. L'interface épurée permet une navigation intuitive vers les différentes fonctionnalités de l'agent RAG.

### Figure 2 : Mode Diagnostic

![Mode Diagnostic](capture%20écran/RAG_diagnostic.png)

**Description :** L'interface de diagnostic automatique permet d'uploader un rapport d'activité (PDF, Word ou TXT) et lance l'analyse structurée selon les cinq dimensions : stratégique, financière, RH, maturité data et cybersécurité. Le panneau latéral "Mes questions" permet de personnaliser les questions d'extraction.

### Figure 3 : Mode Chat Libre

![Mode Chat](capture%20écran/RAG_chat.png)

**Description :** Le mode Chat permet une interaction conversationnelle avec les documents uploadés. L'utilisateur peut poser des questions en langage naturel et l'agent RAG répond en s'appuyant exclusivement sur le contenu des documents, avec citation des sources (numéros de pages et extraits textuels).

### Figure 4 : Mode Comparaison Multi-Documents

![Mode Multi-Docs](capture%20écran/RAG_multi.png)

**Description :** L'interface de comparaison permet d'analyser simultanément plusieurs rapports (ex : rapports annuels de plusieurs années ou de plusieurs entreprises). La synthèse comparative présente les résultats document par document avec des indicateurs de confiance pour chaque extraction.

### Figure 5 : Historique des Extractions

![Historique](capture%20écran/RAG_historique.png)

**Description :** L'onglet Historique permet de consulter l'ensemble des extractions précédentes stockées dans la base Supabase. Les filtres permettent de rechercher par entreprise, date ou modèle d'IA utilisé. Chaque extraction peut être rouverte pour consultation ou comparaison.

---

## Architecture technique et diagrammes

### Figure 6 : Diagramme de classes

![Diagramme de Classes](capture%20écran/Diagramme_de_Classe.png)

**Description :** Le diagramme de classes présente la structure objet du système avec les principales entités : Document, Extractor, LLMProvider, VectorStore, et les modèles de données Pydantic. Les relations d'héritage et d'association montrent l'organisation modulaire du code.

### Figure 7 : Diagramme de séquence

![Diagramme de Séquence](capture%20écran/DiagrammeSequence.png)

**Description :** Le diagramme de séquence illustre le flux d'exécution lors d'une demande d'extraction : l'utilisateur upload un document, le système procède au parsing, chunking, indexation vectorielle, puis effectue le retrieval et la génération via le LLM, avant de valider et structurer la réponse en JSON.

### Figure 8 : Diagramme de cas d'utilisation

![Diagramme de Cas d'Utilisation](capture%20écran/UseCase.png)

**Description :** Le diagramme de cas d'utilisation présente les principales fonctionnalités du système du point de vue de l'utilisateur : uploader des documents, lancer une extraction diagnostique, interagir en mode chat, comparer plusieurs documents, consulter l'historique, et personnaliser les questions d'extraction.

---

## Technologies utilisées

### Stack technique complète

| Couche | Technologie | Version | Rôle |
|--------|-------------|---------|------|
| **Backend** | FastAPI | 0.110.0 | Framework web haute performance |
| | Uvicorn | 0.29.0 | Serveur ASGI |
| | Python | 3.10+ | Langage de programmation |
| **IA / LLM** | LangChain | 1.2.17 | Orchestration LLM |
| | LangChain-Groq | 1.1.2 | Intégration API Groq |
| | LangChain-Ollama | 1.0.1 | Intégration modèles locaux |
| | Pydantic | 2.11.5 | Validation de données |
| **Vectoriel** | ChromaDB | 1.5.5 | Base vectorielle |
| | FAISS (CPU) | - | Recherche de similarité |
| | Sentence-Transformers | 5.4.1 | Embeddings sémantiques |
| **Parsing** | PyMuPDF (Fitz) | 1.27.2.3 | Extraction PDF |
| | pdfplumber | - | Extraction tableaux |
| | python-docx | - | Extraction Word |
| **Base de données** | Supabase | - | PostgreSQL + Auth |
| | PostgreSQL | 14+ | Stockage relationnel |
| **Frontend** | HTML5 | - | Structure sémantique |
| | CSS3 | - | Styles et mise en page |
| | JavaScript (Vanilla) | ES6+ | Logique interactive |
| **Déploiement** | Render | - | Hébergement backend |
| | Netlify | - | Hébergement frontend |
| **Outils** | Git | - | Versioning |
| | GitHub | - | Repository distant |
| | VS Code | - | IDE développement |

---

## Références bibliographiques

### Ouvrages et articles scientifiques

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). *Attention Is All You Need*. Advances in Neural Information Processing Systems, 30.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. Advances in Neural Information Processing Systems, 33, 9459-9474.

### Documentation technique

LangChain Documentation. (2024). *LangChain v0.2 - Building LLM Applications*. https://python.langchain.com

FastAPI. (2024). *FastAPI Documentation*. https://fastapi.tiangolo.com

Supabase. (2024). *Supabase Documentation*. https://supabase.com/docs

Meta AI. (2024). *LLaMA : Large Language Model Meta AI*. https://ai.meta.com/llama

NIST. (2018). *Framework for Improving Critical Infrastructure Cybersecurity, Version 1.1*. National Institute of Standards and Technology. https://doi.org/10.6028/NIST.CSWP.04162018

---

## Annexes

### Annexe A - Fichier de configuration config.yaml

```yaml
default_provider: "groq"
default_model: "llama-3.1-8b-instant"

embeddings:
  provider: "ollama"
  model: "nomic-embed-text"
  base_url: "http://localhost:11434"
  sync_client_kwargs:
    timeout: 300.0

vectorstore:
  type: "chroma"
  persist_dir: "vectorstore/chroma"
  collection_name: "reports"

providers:
  groq:
    model: "llama-3.1-8b-instant"
    temperature: 0.0
    
  ollama:
    model: "mistral"
    base_url: "http://localhost:11434"
    temperature: 0.0
    
  openai:
    model: "gpt-4o"
    temperature: 0.0
    
  gemini:
    model: "gemini-1.5-pro"
    temperature: 0.0
```

### Annexe B - Exemple de sortie JSON structurée

```json
{
  "meta": {
    "entreprise": "TechCorp SA",
    "annee_rapport": 2023,
    "date_extraction": "2025-01-15T10:30:00Z",
    "modele_utilise": "llama-3.1-70b-versatile",
    "approche": "Agent_RAG_T4"
  },
  "diagnostic_strategique": {
    "taille_marche": {
      "valeur": "2,3 milliards EUR",
      "source": {
        "page": 14,
        "section": "Analyse de marché §2.1",
        "extrait": "Le marché adressable est estimé à 2,3 milliards d'euros..."
      },
      "confiance": 0.92
    },
    "taux_croissance": {
      "valeur": "12,5% par an",
      "source": {
        "page": 14,
        "section": "Analyse de marché §2.2",
        "extrait": "Le marché connaît une croissance annuelle de 12,5%..."
      },
      "confiance": 0.89
    },
    "intensite_concurrentielle": {
      "valeur": "Élevée",
      "source": {
        "page": 15,
        "section": "Analyse concurrentielle §3.1",
        "extrait": "Le niveau de concurrence est élevé avec la présence de 5 acteurs majeurs..."
      },
      "confiance": 0.85
    },
    "concurrents": {
      "valeur": ["Competitor A", "Competitor B", "Competitor C"],
      "source": {
        "page": 15,
        "section": "Analyse concurrentielle §3.2",
        "extrait": "Les principaux concurrents sont Competitor A, Competitor B et Competitor C..."
      },
      "confiance": 0.88
    },
    "tendances_marche": {
      "valeur": ["Digitalisation", "IA générative", "Durabilité"],
      "source": {
        "page": 16,
        "section": "Tendances du marché §4.1",
        "extrait": "Les trois tendances majeures sont la digitalisation accélérée, l'adoption de l'IA générative et la durabilité..."
      },
      "confiance": 0.86
    }
  },
  "diagnostic_financier": {
    "chiffre_affaires": {
      "valeur": "156,8 M€",
      "source": {
        "page": 28,
        "section": "Résultats financiers §5.1",
        "extrait": "Le chiffre d'affaires consolidé s'élève à 156,8 millions d'euros..."
      },
      "confiance": 0.94
    },
    "resultat_net": {
      "valeur": "12,3 M€",
      "source": {
        "page": 28,
        "section": "Résultats financiers §5.2",
        "extrait": "Le résultat net part du groupe s'établit à 12,3 millions d'euros..."
      },
      "confiance": 0.93
    },
    "ebitda": {
      "valeur": "28,7 M€",
      "source": {
        "page": 29,
        "section": "Résultats financiers §5.3",
        "extrait": "L'EBITDA ressort à 28,7 millions d'euros, soit une marge de 18,3%..."
      },
      "confiance": 0.92
    }
  },
  "diagnostic_rh": {
    "effectif_total": {
      "valeur": "1 247",
      "source": {
        "page": 45,
        "section": "Ressources humaines §8.1",
        "extrait": "L'effectif total du groupe au 31 décembre s'élève à 1 247 collaborateurs..."
      },
      "confiance": 0.95
    },
    "masse_salariale": {
      "valeur": "68,4 M€",
      "source": {
        "page": 45,
        "section": "Ressources humaines §8.2",
        "extrait": "La masse salariale totale s'élève à 68,4 millions d'euros..."
      },
      "confiance": 0.91
    }
  }
}
```

---

**Document généré automatiquement à partir du README.md et des fichiers du projet Holokia Copilot Strategy IA.**

Pour convertir ce document en format Word :
1. Ouvrez Microsoft Word
2. Fichier > Ouvrir > Sélectionnez ce fichier .md
3. Word convertira automatiquement le Markdown en document Word formaté

Ou utilisez un convertisseur en ligne comme : https://pandoc.org/try/
