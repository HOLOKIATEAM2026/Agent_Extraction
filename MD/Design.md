# ✦ DESIGN SYSTEM — Agent RAG ✦
### *L'Élégance de l'Intelligence*

---

## ◈ Vision & Âme du Projet

> **Un mot. Un seul.**
>
> # `LUMIÈRE`
>
> *L'agent qui illumine ce qui était caché dans l'ombre des documents.*

Le design de cet agent n'est pas une interface — c'est une **expérience**. Chaque interaction doit évoquer la précision d'un instrument de haute horlogerie suisse : tout est mesuré, tout est intentionnel, tout est beau. L'or ne brille pas pour séduire — il signifie la **valeur extraite** depuis le chaos documentaire.

---

## ◈ Identité Visuelle

### Concept Central
```
OMBRE  →  LUMIÈRE  →  STRUCTURE
(PDF brut)  (extraction RAG)  (JSON raffiné)
```

Le noir profond représente le document non-traité, l'inconnu.  
L'or représente l'information extraite, révélée, précieuse.  
Le blanc cassé représente la clarté, la lisibilité, la vérité.

---

## ◈ Palette de Couleurs

### Couleurs Primaires

| Nom | Hex | Usage |
|-----|-----|-------|
| **Noir Abyssal** | `#0A0A0F` | Fond principal, arrière-plan |
| **Noir Profond** | `#111118` | Cartes, panels |
| **Noir Velours** | `#1A1A24` | Surfaces secondaires |
| **Noir Graphite** | `#252535` | Bordures, séparateurs |

### Couleurs Or (La Signature)

| Nom | Hex | Usage |
|-----|-----|-------|
| **Or Impérial** | `#D4AF37` | Accent primaire, titres clés |
| **Or Solaire** | `#F5CC50` | Hover, états actifs |
| **Or Champagne** | `#E8D5A0` | Texte secondaire sur fond sombre |
| **Or Pâle** | `#F0E6C0` | Texte de lecture, corps |
| **Or Brûlé** | `#8B6914` | Ombres colorées, profondeur |
| **Or Fantôme** | `rgba(212, 175, 55, 0.08)` | Backgrounds subtils, glow diffus |

### Couleurs Fonctionnelles

| Nom | Hex | Usage |
|-----|-----|-------|
| **Succès Émeraude** | `#2ECC71` | Extraction réussie, validation |
| **Alerte Ambre** | `#E67E22` | Données incertaines, avertissement |
| **Erreur Rubis** | `#E74C3C` | Hallucination détectée, erreur |
| **Info Saphir** | `#3498DB` | Information neutre, lien |
| **Blanc Ivoire** | `#F8F6F0` | Texte principal sur fond sombre |

---

## ◈ Typographie

### Hiérarchie Typographique

```
DISPLAY  →  Cormorant Garamond  (titres héroïques, grands formats)
HEADING  →  Cinzel              (titres de sections, élégance classique)
BODY     →  Crimson Pro         (lecture confortable, sérif moderne)
CODE     →  JetBrains Mono      (JSON, code, données structurées)
LABEL    →  Raleway             (étiquettes, navigation, UI)
```

### Échelle Typographique

| Niveau | Font | Taille | Poids | Espacement lettres |
|--------|------|--------|-------|---------------------|
| Hero | Cormorant Garamond | 72px | 300 | +0.05em |
| H1 | Cinzel | 48px | 400 | +0.08em |
| H2 | Cinzel | 32px | 400 | +0.06em |
| H3 | Raleway | 22px | 600 | +0.04em |
| Body | Crimson Pro | 18px | 400 | normal |
| Label | Raleway | 13px | 500 | +0.12em |
| Code | JetBrains Mono | 14px | 400 | normal |

### Règles Typographiques

- Les titres en `Cinzel` : **toujours en MAJUSCULES** — ils commandent l'attention
- Les corps de texte : couleur `Or Champagne (#E8D5A0)` sur fond sombre
- Line-height corps : `1.85` — la lecture doit respirer
- Jamais plus de 70 caractères par ligne (mesure optimale)
- Césures : autorisées uniquement dans le corps de texte

---

## ◈ Espacement & Grille

### Système de Grille
```
Conteneur max : 1280px
Gouttières     : 32px
Colonnes       : 12 (desktop) / 4 (mobile)
Padding page   : 64px (desktop) / 24px (mobile)
```

### Échelle d'Espacement (base 8px)

```
xs  →   4px   (micro-détails)
sm  →   8px   (éléments inline)
md  →  16px   (composants)
lg  →  32px   (sections internes)
xl  →  64px   (sections majeures)
2xl → 128px   (héros, espaces respiratoires)
```

---

## ◈ Animations & Motion

### Philosophie du Mouvement

> *"Tout ce qui se révèle doit le faire avec grâce."*

L'animation n'est pas de la décoration — elle **raconte** le processus RAG. L'information émerge. Elle ne pop pas, elle ne saute pas. Elle **apparaît**, comme si on éclairait progressivement une pièce sombre.

### Catalogue d'Animations

#### ① Reveal Doré — Entrée des éléments
```css
@keyframes goldReveal {
  0%   { opacity: 0; transform: translateY(20px); filter: blur(4px); }
  60%  { filter: blur(0px); }
  100% { opacity: 1; transform: translateY(0); }
}

.reveal {
  animation: goldReveal 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
```

#### ② Shimmer Or — Lignes de chargement
```css
@keyframes shimmer {
  0%   { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    #1A1A24 25%,
    #D4AF37 50%,
    #1A1A24 75%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite;
}
```

#### ③ Pulse Extraction — Indicateur en cours
```css
@keyframes extractionPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4); }
  50%       { box-shadow: 0 0 0 12px rgba(212, 175, 55, 0); }
}

.processing {
  animation: extractionPulse 2s ease infinite;
}
```

#### ④ Écriture JSON — Apparition des données
```css
@keyframes typewriter {
  from { clip-path: inset(0 100% 0 0); }
  to   { clip-path: inset(0 0% 0 0); }
}

.json-reveal {
  animation: typewriter 1.2s steps(40) forwards;
}
```

#### ⑤ Scan Document — Lecture en cours
```css
@keyframes documentScan {
  0%   { top: 0%; opacity: 0.6; }
  50%  { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

.scan-line {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #D4AF37, transparent);
  animation: documentScan 3s ease-in-out infinite;
}
```

#### ⑥ Glow Hover — Interaction utilisateur
```css
.card-gold {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-gold:hover {
  transform: translateY(-4px);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.4),
    0 0 30px rgba(212, 175, 55, 0.15);
  border-color: #D4AF37;
}
```

### Courbes d'Accélération

| Usage | Valeur | Sensation |
|-------|--------|-----------|
| Entrées | `cubic-bezier(0.16, 1, 0.3, 1)` | Fluide, naturelle |
| Sorties | `cubic-bezier(0.4, 0, 1, 1)` | Nette, résolue |
| Interactions | `cubic-bezier(0.4, 0, 0.2, 1)` | Réactive |
| Rebond doux | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Vivante, légère |

### Durées

```
Micro         :  80ms  (retour de clic)
Rapide        : 200ms  (hover, toggle)
Standard      : 350ms  (transitions de page)
Lent          : 600ms  (apparition de modales)
Cinematique   : 1200ms (animations de chargement, héros)
```

---

## ◈ Composants UI

### La Carte d'Extraction (Card Extrait)

```
┌──────────────────────────────────────────────┐
│ ◆ DONNÉES FINANCIÈRES            ✓ EXTRAIT   │  ← Header doré
├──────────────────────────────────────────────┤
│                                              │
│  Chiffre d'affaires     12 500 000 €         │
│  Résultat net            870 000 €           │
│  EBITDA                      —               │  ← null élégant
│                                              │
├──────────────────────────────────────────────┤
│ Source : p.12 · "Le CA s'élève à 12,5 M€…"  │  ← Citation source
└──────────────────────────────────────────────┘

Fond       : #111118
Bordure    : 1px solid #252535
Bordure top: 2px solid #D4AF37 (signature)
Border-rad : 8px
```

### La Barre de Progression RAG

```
DOCUMENT INGÉRÉ ──────────────── EXTRACTION ──── JSON GÉNÉRÉ
      ●━━━━━━━━━━━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━○
      ✓ Parsing          ✓ Vectorisation     → En cours...

Ligne remplie : #D4AF37
Ligne vide    : #252535
Points actifs : glow 0 0 8px #D4AF37
```

### Le Badge de Confiance

```css
/* Haute confiance */
.badge-high {
  background: rgba(46, 204, 113, 0.1);
  border: 1px solid rgba(46, 204, 113, 0.3);
  color: #2ECC71;
  /* "● 94%" */
}

/* Confiance moyenne */
.badge-medium {
  background: rgba(230, 126, 34, 0.1);
  border: 1px solid rgba(230, 126, 34, 0.3);
  color: #E67E22;
  /* "● 61%" */
}

/* Faible confiance */
.badge-low {
  background: rgba(231, 76, 60, 0.1);
  border: 1px solid rgba(231, 76, 60, 0.3);
  color: #E74C3C;
  /* "● 23%" */
}
```

### Le Bloc Citation Source

```
│ ❝                                            │
│   "Le chiffre d'affaires consolidé atteint   │
│    12,5 millions d'euros au 31 décembre,     │
│    en hausse de 8% par rapport à l'exercice  │
│    précédent."                               │
│                                              │
│                    — Rapport annuel 2023     │
│                       Page 12, §3.2          │
└──────────────────────────────────────────────┘

Bordure gauche : 3px solid #D4AF37
Fond           : rgba(212, 175, 55, 0.04)
Texte          : Crimson Pro Italic, #E8D5A0
```

---

## ◈ Effets Spéciaux

### Grain de Luxe (Texture)
```css
.luxury-grain::after {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,..."); /* SVG noise */
  opacity: 0.03;
  pointer-events: none;
  z-index: 9999;
}
```

### Séparateur Or
```css
.divider-gold {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    #D4AF37 20%,
    #F5CC50 50%,
    #D4AF37 80%,
    transparent 100%
  );
  margin: 48px 0;
}
```

### Curseur Personnalisé
```css
* { cursor: none; }

.cursor {
  width: 12px; height: 12px;
  border: 1.5px solid #D4AF37;
  border-radius: 50%;
  position: fixed;
  pointer-events: none;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.cursor-follower {
  width: 32px; height: 32px;
  background: rgba(212, 175, 55, 0.08);
  border-radius: 50%;
  position: fixed;
  pointer-events: none;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
```

### Shadow System

```css
/* Élévation 1 — Cartes standard */
--shadow-sm: 0 2px 8px rgba(0,0,0,0.3);

/* Élévation 2 — Cartes au hover */
--shadow-md: 0 8px 24px rgba(0,0,0,0.4),
             0 0 20px rgba(212,175,55,0.08);

/* Élévation 3 — Modales, overlays */
--shadow-lg: 0 20px 60px rgba(0,0,0,0.6),
             0 0 40px rgba(212,175,55,0.12);

/* Or incandescent — éléments CTAs */
--shadow-gold: 0 4px 20px rgba(212,175,55,0.25),
               0 0 60px rgba(212,175,55,0.1);
```

---

## ◈ Iconographie

### Style d'Icônes
- **Librairie** : Phosphor Icons (variante `thin` pour l'élégance)
- **Stroke** : 1px — jamais bold, jamais filled
- **Couleur** : Or `#D4AF37` pour actif, `#888` pour inactif
- **Taille** : 20px (inline), 32px (cards), 48px (héros)

### Icônes Clés du Projet

```
◈  document-text    →  Rapport d'activité
◈  cpu              →  Agent IA / Traitement
◈  database         →  Base vectorielle
◈  intersect        →  RAG / Retrieval
◈  brackets-curly   →  Sortie JSON
◈  chart-line       →  Données financières
◈  users            →  Données RH
◈  gear             →  Pipeline
◈  magnifying-glass →  Recherche contextuelle
◈  shield-check     →  Validation / Fiabilité
```

---

## ◈ Layout de la Page Principale

```
┌────────────────────────────────────────────────────┐
│           ✦  AGENT RAG  ✦                          │
│     Analyse Intelligente de Rapports               │
│                                    [UPLOAD]        │
├────────────────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│ │ PARSING  │→ │VECTORIEL │→ │EXTRACTION│          │
│ │  ✓ Done  │  │ ◌ 78%    │  │  ○ Wait  │          │
│ └──────────┘  └──────────┘  └──────────┘          │
├────────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌─────────────────────┐  │
│ │  FINANCIER          │  │  RH                 │  │
│ │  CA : 12.5M€  ✓ 94%│  │  Effectif : 142 ✓  │  │
│ │  RN : 870K€   ✓ 91%│  │  Masse sal : —  ? 43%│ │
│ └─────────────────────┘  └─────────────────────┘  │
├────────────────────────────────────────────────────┤
│ {  JSON OUTPUT  }                    [EXPORT ↓]    │
└────────────────────────────────────────────────────┘
```

---

## ◈ Tokens CSS — Variables Globales

```css
:root {
  /* Couleurs fondamentales */
  --c-void:          #0A0A0F;
  --c-deep:          #111118;
  --c-surface:       #1A1A24;
  --c-border:        #252535;
  --c-border-hover:  #3A3A55;

  /* Or */
  --c-gold:          #D4AF37;
  --c-gold-bright:   #F5CC50;
  --c-gold-pale:     #E8D5A0;
  --c-gold-ghost:    rgba(212, 175, 55, 0.08);
  --c-gold-glow:     rgba(212, 175, 55, 0.25);

  /* Texte */
  --c-text-primary:  #F8F6F0;
  --c-text-body:     #E8D5A0;
  --c-text-muted:    #888899;
  --c-text-ghost:    #444455;

  /* Sémantique */
  --c-success:       #2ECC71;
  --c-warning:       #E67E22;
  --c-danger:        #E74C3C;
  --c-info:          #3498DB;

  /* Typographie */
  --font-display:    'Cormorant Garamond', Georgia, serif;
  --font-heading:    'Cinzel', 'Trajan Pro', serif;
  --font-body:       'Crimson Pro', Georgia, serif;
  --font-ui:         'Raleway', sans-serif;
  --font-code:       'JetBrains Mono', 'Fira Code', monospace;

  /* Rayons */
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:  12px;
  --radius-xl:  20px;

  /* Transitions */
  --ease-smooth:  cubic-bezier(0.16, 1, 0.3, 1);
  --ease-snap:    cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce:  cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Durées */
  --dur-fast:   200ms;
  --dur-std:    350ms;
  --dur-slow:   600ms;
  --dur-hero:  1200ms;
}
```

---

## ◈ Règles d'Or du Design

```
I.   L'or s'utilise avec parcimonie — il perd sa valeur si sur-utilisé.
II.  Tout élément doit avoir une raison d'exister.
III. L'espace vide est aussi précieux que le contenu.
IV.  Les animations révèlent — elles ne décorent pas.
V.   La donnée extraite est la vedette. L'interface est son écrin.
VI.  Le noir n'est pas un fond — c'est une profondeur.
VII. La confiance se construit par la rigueur visuelle.
```

---

## ◈ Inspirations & Références

| Direction | Référence | Ce qu'on en emprunte |
|-----------|-----------|----------------------|
| Horlogerie | A. Lange & Söhne | Précision, lisibilité, or sur noir |
| Finance | Bloomberg Terminal | Densité de l'info, couleurs fonctionnelles |
| Architecture | Mies van der Rohe | "Less is more", proportions |
| Typographie | The Gentlewoman | Sérif élégant, espacement généreux |
| Motion | Apple keynotes | Reveals progressives, cinématique |

---

*"La complexité technique mérite une beauté à la hauteur."*

✦

---
*Design System v1.0 — Projet Agent RAG — Confidentiel*
