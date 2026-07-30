# Debug Session: chat-lang-dark
- **Status**: [OPEN]
- **Issue**: Le sélecteur de langue de `html/chat.html` reste blanc en mode sombre alors que les autres pages affichent correctement un fond sombre.
- **Debug Server**: Pending startup
- **Log File**: `.dbg/trae-debug-log-chat-lang-dark.ndjson`

## Reproduction Steps
1. Ouvrir `html/chat.html`.
2. Activer le mode sombre.
3. Ouvrir le menu déroulant de langue.
4. Observer que le bouton et/ou le menu restent blancs.

## Hypotheses & Verification
| ID | Hypothesis | Likelihood | Effort | Evidence |
|----|------------|------------|--------|----------|
| A | Une règle injectée après le CSS local remet un fond clair sur `.lang-trigger` ou `.lang-menu`. | High | Low | Pending |
| B | Le mode sombre est actif, mais les variables CSS lues par le composant de langue restent sur des fallbacks clairs. | High | Low | Pending |
| C | L'état `open` du menu utilise une autre règle que le bouton fermé, qui garde un fond blanc. | Medium | Low | Pending |
| D | Une règle plus spécifique dans `chat.html` ou un style inline gagne sur les overrides dark. | Medium | Medium | Pending |

## Log Evidence
Pending instrumentation.

## Verification Conclusion
Pending.
