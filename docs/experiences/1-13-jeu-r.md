# 1-13 — Jeu R et séances sur R

Compte rendu de la phase B (story 1-13). Partiel au commit « jeu R figé » : construction seule ; séances, témoins, évaluations et publication à blanc suivent.

## Jeu R figé (2026-11-07)

- Porte de 1-12 (`config/r_gate.toml`) : **comparatif**, p_d1 = 0,675 [0,630 ; 0,717], n = 437. **Réserve forte de 1-12** : contrôle de qualité de l'extracteur en échec après le tour de correction ; R hérite de cette réserve.
- Classement lu : tour 1, sha256 `527869b523444148eae709919a079a092449d7eeba8746efd2f9c74ee4ca62de` (égal à `r_gate.toml`) ; normaliseur `legal_r.normalize@2`, grille 1.
- Index du CE : manifeste `345a8a2c…806bc` ; cache Judilibre de 1-12 relu, sha256 `bf69c542…386a9` (653 pages, 0 requête réseau à la construction).
- `corpus_date` = **2026-11-07** (date d'extraction, S5), posée dans `R_CORPUS_DATE`.
- Appariement selon l'amendement A1 (spec), graine par `unit_id`.

### Entonnoir

| Étape | Avant A1 (S1, S6) | Après A1 |
|---|---|---|
| Unités du classement | 1 099 | 1 099 |
| `not_in_gate` | 662 | 662 |
| `not_d1` | 277 | 277 |
| `span_context` | 3 | 3 |
| `before_window` (CE) | 4 | 4 |
| `number_repeated` | 13 | 13 |
| `found_at_build` | 0 | 0 |
| `no_real_in_stratum` | 74 | 33 |
| **F** | **66** (60 `c00`) | **107** |
| p_R | ≈ 0,09 | **0,449** (p_d1 = 0,675) |

`found_at_build` est presque nul par construction : la revérification D4 relit le même client, le même index et le même cache que 1-12, qui a interrogé ces jours quelques heures plus tôt (décision de l'orchestrateur, pas de rafraîchissement des `/scan`). Critères libérés par A1 : écart d'année 41 paires, type de jour 14, formation 13.

### Jeux

80 ≤ F < 120 : 20 paires de séance, **aucun jeu d'entraînement** (D5), 87 paires réservées.

| Jeu | Exemples | Types des fausses | sha256 de `dataset.json` |
|---|---|---|---|
| `data/legal_r/session` | 40 | c00 11, t05 3, t10 3, t03, t11, t14 1 | `9ac9ce9eefb47bdbf940495faeea4d2d54a0202fb8ca79baa25dfbdcf47467e6` |
| `data/legal_r/train` | 0 (non construit) | — | — |
| `heldout/legal_r/eval` | 174 | c00 48, t10 24, t05 8, t12 5, t03 1, t08 1 | `e4aaa64bbb98ff925c43b291d98d39ec0472353de05fe7a969b7726b19d02df9` |

Indice visible : classe d'écart `none` chez 39 fausses (t10 surtout) contre 5 vraies ; le plancher de S1 le mesure.
