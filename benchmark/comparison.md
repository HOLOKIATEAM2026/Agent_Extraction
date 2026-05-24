# 📊 Tableau comparatif — Approches A/B/C/D

Ce tableau est généré automatiquement à partir des sorties dans `benchmark/out/*.json`.

| Fichier | Approche | Provider | Modèle | JSON OK | Champs remplis | Issues validation |
|---|---|---|---|---:|---:|---:|
| Maroc_Telecom_RFA_2024.pdf.approach_a.json | approach_a | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |
| Maroc_Telecom_RFA_2024.pdf.approach_b.json | approach_b | groq | llama-3.1-8b-instant | ✅ | 7/12 |  |
| Maroc_Telecom_RFA_2024.pdf.approach_c.json | approach_c | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |
| Maroc_Telecom_RFA_2024.pdf.approach_d.json | approach_d | groq | llama-3.1-8b-instant | ✅ | 6/12 | 2 |
| NIST_SP_1308_CSF2.0_QSG.pdf.approach_a.json | approach_a | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |
| NIST_SP_1308_CSF2.0_QSG.pdf.approach_b.json | approach_b | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |
| NIST_SP_1308_CSF2.0_QSG.pdf.approach_c.json | approach_c | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |
| NIST_SP_1308_CSF2.0_QSG.pdf.approach_d.json | approach_d | groq | llama-3.1-8b-instant | ✅ | 0/12 | 0 |
| audit_qualite_data_exemple_1.txt.approach_a.json | approach_a | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |
| audit_qualite_data_exemple_1.txt.approach_b.json | approach_b | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |
| audit_qualite_data_exemple_1.txt.approach_c.json | approach_c | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |
| audit_qualite_data_exemple_1.txt.approach_d.json | approach_d | groq | llama-3.1-8b-instant | ✅ | 0/12 | 0 |
| company_0_2023.txt.approach_a.json | approach_a | groq | llama-3.1-8b-instant | ✅ | 0/12 |  |

## Lecture rapide

- Champs remplis = nombre de champs `valeur` non-nuls (ou listes non vides) / total des champs.
- Issues validation = nombre d’extraits cités absents du contexte (disponible surtout en Approche D).
