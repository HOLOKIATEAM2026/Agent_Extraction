# 🔐 Verrouillage GitHub — Checklist

## Paramètres dépôt

- Visibilité : privé
- Secrets : ajouter les clés dans “Secrets and variables” (Actions / Dependabot), jamais dans le code
- Secret scanning : activé

## Branch protection (recommandé)

- Protéger `main`
- Exiger PR avant merge
- Exiger au moins 1 review
- Bloquer le push direct sur `main`

## Dépendances

- Activer Dependabot (pip) pour remonter les mises à jour sécurité
- Valider les PR Dependabot avec les tests du dossier `test/`
