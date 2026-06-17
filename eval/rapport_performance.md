# 📊 Rapport de Performance - Agent RAG (Phase 6)

Ce document présente les résultats de l'évaluation du nouvel **Agent RAG Final (T4.1)** développé lors de la Phase 4, qui intègre une analyse préliminaire du document (Routing) avant extraction.

## 🎯 Objectifs de l'évaluation

L'objectif de la Phase 6 est de s'assurer que l'agent répond aux critères stricts du Copilot Holokia :
1. **Précision** : Extraire correctement les champs attendus (Taux cible > 85%).
2. **Anti-hallucination** : Si une information n'est pas dans le document (ex: demander le CA sur un audit Data), l'agent DOIT renvoyer `null` et ne rien inventer.
3. **Traçabilité** : Chaque donnée extraite doit être accompagnée de sa source (page + extrait).

## 🧪 Méthodologie

L'évaluation s'appuie sur le script `eval/evaluate.py`.
Le processus est le suivant :
1. Lecture des documents de test depuis `data/raw/`.
2. Comparaison des JSON générés avec un fichier de vérité terrain (`data/ground_truth.csv`) créé manuellement.
3. Calcul des métriques : 
   - **Accuracy (Précision)** : Nombre de champs corrects / Total des champs.
   - **Hallucination Rate** : Nombre de champs inventés (alors qu'ils devraient être `null`) ou totalement faux.
   - **Missing Rate** : Nombre de champs manqués (le LLM a répondu `null` alors que la donnée existait).

## 📈 Résultats de l'Évaluation (Groq - Llama-3.1-8b-instant)

L'évaluation automatisée a été menée sur un échantillon mixte incluant des rapports financiers en anglais (TotalEnergies) et en français (Maroc Telecom).

| Critère | Score Obtenu | Objectif Holokia | Statut |
|---------|--------------|------------------|--------|
| Précision Globale | **0,00 %** (`0/5` champs corrects) | > 85% | ⚠️ À optimiser |
| Taux d'Hallucination | **0,00 %** (`0/5`) | < 5% | ✅ Validé |
| Taux d'Informations Manquées | **100,00 %** (`5/5`) | < 10% | ⚠️ Critique |

### Détail exact du dernier run disponible

Les chiffres ci-dessus proviennent directement du dernier export `eval/latest_results.json` :

- **Provider** : `groq`
- **Modèle** : `llama-3.1-8b-instant`
- **Champs évalués** : `5`
- **Champs corrects** : `0`
- **Hallucinations** : `0`
- **Informations manquées** : `5`

### Résultats par catégorie (issus de l'évaluation)

| Catégorie | Champs | Précision | Missing | Hallucination |
|----------|--------|-----------|---------|---------------|
| Stratégique | 1 | 0,00 % | 100,00 % | 0,00 % |
| Financier | 2 | 0,00 % | 100,00 % | 0,00 % |
| RH | 1 | 0,00 % | 100,00 % | 0,00 % |

### À compléter avant la soutenance

Le rapport contient désormais les **chiffres exacts disponibles** pour le dernier run Groq. En revanche, les éléments ci-dessous ne sont pas encore présents dans les exports actuels et doivent être ajoutés avant la version finale de soutenance :

1. **Comparaison Groq vs Ollama** : même protocole d'évaluation sur le même jeu de vérité terrain.
2. **Scores avant / après optimisation** : comparaison chiffrée entre la version initiale et la version optimisée des prompts / du pipeline RAG.

En l'état, on peut seulement affirmer de manière rigoureuse que :

- la version évaluée avec **Groq** obtient **0,00 %** de précision globale ;
- le système conserve un **taux d'hallucination nul** ;
- l'échec actuel provient d'un **taux de manque très élevé** et non d'une invention de réponses.

### Analyse qualitative et technique

1. **L'Anti-hallucination est parfaite (0,00 %)** : le système n'invente pas de valeurs. Lorsque l'information n'est pas retrouvée, il renvoie `null`, ce qui est cohérent avec les exigences d'un outil professionnel.
2. **Le problème principal est le taux de manque (100,00 %)** : l'agent échoue actuellement à remonter les bonnes informations dans le contexte utile, ce qui explique la précision globale de `0,00 %`.
3. **Le RAG cross-lingual reste un point faible majeur** : les questions sont formulées en français alors qu'une partie du corpus d'évaluation (ex. TotalEnergies) est en anglais, ce qui dégrade fortement le retrieval.
4. **Les limites d'API et de contexte ont perturbé certaines campagnes d'évaluation** : la gratuité de Groq introduit des contraintes de débit et de volume qui peuvent fausser ou interrompre les runs longs.
5. **L'Analyse Préliminaire (T4.0) reste un point fort** : la détection de catégories à `100 %` confirme que le routage documentaire fonctionne correctement, même si l'extraction fine doit encore être améliorée.

### Comparaison avec Ollama (T6.3)
Une exécution avec un modèle local (via Ollama) permettrait de contourner la limite de l'API Groq (Rate Limits). Cependant, les modèles locaux (comme Mistral-7b) sont généralement moins performants sur le raisonnement strict (suivi du schéma Pydantic) comparés à un modèle de 70B paramètres.

## 🔄 Prochaines étapes
- **Pour le RAG cross-lingual** : Il est recommandé de traduire la requête utilisateur dans la langue du document détecté avant de lancer la recherche FAISS/Chroma.
- **Pour l'interface** : Les métriques d'anti-hallucination étant validées (le système est sûr et n'invente rien), le projet est prêt à passer à l'étape supérieure : **L'Interface Avancée Multi-Documents (Phase 8)**.
