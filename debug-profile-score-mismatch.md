# Debug Session: profile-score-mismatch
- **Status**: [OPEN]
- **Issue**: Les indicateurs du profil affichent des scores NIST/Data non nuls, mais le graphe d'évolution et le résumé affichent des points à 0.
- **Debug Server**: pending
- **Log File**: .dbg/trae-debug-log-profile-score-mismatch.ndjson

## Reproduction Steps
1. Ouvrir `profil.html`.
2. Sélectionner l'entreprise `ATLASPAY_MAROC_SA`.
3. Comparer les valeurs de la zone `Indicateurs` avec le graphe `Évolution (NIST / Data)` et le résumé.

## Hypotheses & Verification
| ID | Hypothesis | Likelihood | Effort | Evidence |
|----|------------|------------|--------|----------|
| A | `/profile/evolution` calcule `score_nist` et `score_data` à `0` malgré un payload utilisable. | High | Low | Pending |
| B | `entreprise_profil` et `extractions` ne lisent pas la même structure de résultat (`result`, `ui_result`, wrapper). | High | Med | Pending |
| C | Le filtre `company` garde des lignes non pertinentes ou ignore les bonnes lignes. | Med | Low | Pending |
| D | Le front reçoit des points corrects mais les dessine mal ou lit des champs différents. | Med | Low | Pending |

## Log Evidence
- Local repro via `tmp/profile_debug_probe.py` sur `ATLASPAY_MAROC_SA`:
  - `entreprise_profil.score_nist_moyen = 1.51518086300635`
  - `entreprise_profil.score_data_moyen = 2.27678571428572`
  - `/profile/evolution` renvoie 4 points avec `score_nist` non nuls sur 3 points:
    - `2026-07-28T20:43:34.769017+00:00 -> nist 2.020243452025405, data 1.8214285714285714`
    - `2026-07-28T21:15:40.254152+00:00 -> nist 2.02024, data 3.642857142857143`
    - `2026-07-28T22:30:01.065171+00:00 -> nist 0.0, data 3.642857142857143`
    - `2026-07-28T22:46:05.274645+00:00 -> nist 2.02024, data 0.0`
  - `/profile/summary` renvoie:
    - `Depuis votre premier diagnostic (...) votre score NIST est passé de 2.0 à 2.0 (...)`

## Verification Conclusion
- Hypothesis A: **Rejected** localement. Le calcul backend actuel ne renvoie pas `0` partout.
- Hypothesis B: **Rejected** sur le code local courant. `entreprise_profil` et `/profile/evolution` utilisent maintenant une logique cohérente.
- Hypothesis C: **Rejected** pour `ATLASPAY_MAROC_SA` sur la repro locale. Le filtre entreprise retrouve bien 4 lignes.
- Hypothesis D: **Partially confirmed** côté environnement: si l'UI affiche encore `0 -> 0`, elle pointe vraisemblablement vers un backend déployé non mis à jour.
