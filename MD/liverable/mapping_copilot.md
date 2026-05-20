# 🗺️ Mapping : Champs RAG vs Questions Diagnostic Copilot

Ce document fait le pont entre les données extraites par l'Agent RAG (depuis les rapports d'activité) et les questions du formulaire de diagnostic stratégique de la plateforme **Copilot Strategy IA**.

## 1. Axe Stratégique & Marché (Priorité 1)

| Champ extrait par l'Agent RAG | Question correspondante dans Copilot Strategy IA | Objectif d'analyse (Framework) |
| :--- | :--- | :--- |
| **Taille du marché** | *« Quelle est la taille actuelle du marché adressable (TAM/SAM) ? »* | Évaluation du potentiel commercial |
| **Taux de croissance du marché** | *« Quelle est la dynamique de croissance du secteur sur les dernières années ? »* | Attractivité du secteur |
| **Intensité concurrentielle** | *« Comment évaluez-vous l'intensité de la rivalité entre les acteurs existants ? »* | 5 Forces de Porter (Rivalité) |
| **Liste des concurrents identifiés** | *« Quels sont les principaux concurrents directs et indirects ? »* | Cartographie concurrentielle |
| **Tendances du marché** | *« Quelles sont les grandes évolutions (technologiques, réglementaires, sociétales) qui impactent le secteur ? »* | Analyse PESTEL |

---

## 2. Axe Santé Financière (Priorité 2)

| Champ extrait par l'Agent RAG | Question correspondante dans Copilot Strategy IA | Objectif d'analyse (Framework) |
| :--- | :--- | :--- |
| **Chiffre d'affaires (CA)** | *« Quel est le volume d'affaires généré par l'entreprise sur le dernier exercice ? »* | Performance commerciale |
| **Résultat Net (RN)** | *« Quel est le niveau de rentabilité nette de l'entreprise ? »* | Rentabilité globale |
| **EBITDA / EBE** | *« Quelle est la rentabilité opérationnelle (avant impôts et amortissements) ? »* | Performance d'exploitation |
| **Évolution N vs N-1** | *« L'entreprise est-elle sur une dynamique de croissance ou de décroissance de ses revenus ? »* | Tendance financière |

---

## 3. Axe Ressources & Opérations (Priorité 3)

| Champ extrait par l'Agent RAG | Question correspondante dans Copilot Strategy IA | Objectif d'analyse (Framework) |
| :--- | :--- | :--- |
| **Effectif total** | *« Quel est le volume de la force de travail mobilisée par l'entreprise ? »* | Capacité de production (Ressources) |
| **Masse salariale** | *« Quel est le coût de la structure humaine ? »* | Structure de coûts |
| **Indicateurs de performance (KPIs)** | *« Quels sont les accomplissements opérationnels ou jalons clés atteints cette année ? »* | Chaîne de valeur & Avantage concurrentiel |

---

> **Note technique pour l'intégration :** 
> Le JSON final généré par l'agent RAG utilisera les clés (ex: `taille_marche`, `intensite_concurrentielle`) pour auto-remplir les champs de l'interface frontend de Copilot via l'API. Si un champ RAG retourne `null` ou une confiance < `0.60`, la question Copilot restera vide pour saisie manuelle par l'utilisateur.
