# 📋 Validation des Spécifications - Projet Agent RAG

**À l'attention de :** Samad Filali  
**Date :** 2026-05-21  
**Objet :** Validation du catalogue de champs et des priorités d'extraction

---

## 1. Catalogue des Champs à Extraire (Proposition)

Afin de cadrer l'extraction de l'Agent RAG, voici les champs que nous proposons de cibler sur les rapports d'activité.

### 📈 Données Marché & Stratégie (Priorité : Haute)
- **Taille du marché** (TAM / SAM)
- **Taux de croissance du marché**
- **Intensité concurrentielle**
- **Liste des concurrents identifiés**
- **Tendances du marché** (tech / régulation / macro / sociétal)

### 💰 Données Financières (Priorité : Haute)
*Ces données sont souvent standardisées mais peuvent varier selon les normes comptables (IFRS, US GAAP).*
- **Chiffre d'Affaires (ou Produit Net Bancaire)**
- **Résultat Net (et Résultat Net Part du Groupe)**
- **EBITDA / EBE (Excédent Brut d'Exploitation)**
- **Dette Nette / Trésorerie**

### 👥 Données RH (Priorité : Moyenne)
- **Effectif total** (répartition géographique si pertinente)
- **Masse salariale**
- **Turnover / Taux de rotation**

### ⚙️ Données Opérationnelles & RSE (Priorité : Moyenne/Basse)
- **Émissions de GES (Scopes 1, 2, 3)**
- **Investissements R&D / CAPEX**
- **Objectifs stratégiques à moyen terme**

### 🧩 Maturité Data (Priorité : Moyenne)
- **Existence des données** (sources, couverture, données manquantes)
- **Qualité** (complétude, exactitude, cohérence)
- **Accessibilité** (disponibilité, self-service, outillage)
- **Volumétrie** (volumes, croissance, types de données)
- **Historisation** (rétention, traçabilité, lineage)
- **Conformité** (RGPD, politiques internes, classification)
- **Documentation** (catalogue, dictionnaire, règles de gestion)

### 🔐 Cybersécurité & Gouvernance (Priorité : Moyenne)
- **Risques cyber identifiés** (menaces, incidents, impacts)
- **Conformité / référentiels** (NIST CSF, ISO 27001, politiques internes)
- **Mesures de sécurité clés** (IAM, chiffrement, SOC, audits, sensibilisation)
- **Gouvernance des données** (rôles, comités, responsabilités, processus)

---

## 2. Questions pour validation

1. **Périmètre des champs :** Ce catalogue correspond-il à vos attentes ? Y a-t-il des KPIs spécifiques à notre métier (ou à certains secteurs particuliers comme la banque) qu'il faut absolument ajouter ?
2. **Gestion des données manquantes :** Confirmez-vous que l'agent doit retourner `null` plutôt que de tenter une déduction si une information (ex: Turnover) n'est pas explicitement mentionnée dans le rapport ?
3. **Format de sortie :** Le format JSON strict (avec numéros de pages sources) tel que défini dans le design system vous convient-il ?
4. **Nouveaux axes data/cyber :** Confirmez-vous la granularité des champs “maturité data” et “cybersécurité & gouvernance” pour intégration au diagnostic Copilot ?

---

## 3. État d'avancement des données (T1.4)

Pour information, la constitution du jeu de test (ground truth) a été réalisée. 
Le dossier `data/raw/` contient actuellement :
- **TotalEnergies** (2023, 2024, 2025)
- **Attijariwafa Bank** (2023, 2024, 2025)
- **Maroc Telecom** (2024)
- **Scripts de collecte automatisée** (`edgar_downloader.py`) pour enrichir la base avec des rapports internationaux.
- **Audits data** (exemples FR) pour tester l'extraction “maturité data”
- **Documents cybersécurité** (exemples FR + PDFs NIST) pour tester l'extraction “cyber & gouvernance”

Un échantillon de ground truth manuel a été initialisé dans `data/ground_truth.csv` pour servir de référence aux futures évaluations.
