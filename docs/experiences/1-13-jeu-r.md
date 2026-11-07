# 1-13 — Jeu R et séances sur R

Compte rendu de la phase B (story 1-13), 2026-11-07. Porte **comparatif** ; décisions S3 par défaut ; appariement selon l’amendement A1. Les séances signalées sont listées pour 1-14b, jamais jugées ici.

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

## Plancher d'indice (S1)

Non joué : `jeu_r.py plancher` exige un entraînement de R, absent pour 80 ≤ F < 120 (« jeu d'entraînement ou réservé de R absent »). L'indice d'écart reste lisible dans `year_gap` (ci-dessus) et par le témoin S → R.

## Séances (D7, D8 comparatif, S2, S11)

Pilote Claude Code (abonnement, `NNWW_CLAUDE_CWD_ROOT='C:\nnww-cwd'`, `~/.nnww/claude-config`, sans `ANTHROPIC_API_KEY`) pour Sonnet ; OpenRouter pour MiMo (`.env` chargé dans la commande seule). Séances en série, 15:30 à 17:05 UTC. Aucune coupure, aucun refus du harnais, aucune troncature MiMo (règle d'arrêt S11 non déclenchée).

Réservé de R : 174 exemples, dont 48 `c00`. **Plafond** = (87 + 39) / 174 = **0,724**. Part du plafond = (exactitude − 0,5) / (plafond − 0,5). Détectable = vraies et fausses autres que `c00` (126).

| Séance | Graine | Statut | Passes | Exactitude | Part du plafond | Détectable | Rappel `c00` | Facturé | Équivalent | Drapeaux |
|---|---|---|---|---|---|---|---|---|---|---|
| Sonnet B t1 | 0 | frozen | 0 | 0,724 | 1,00 | 1,000 | 0/48 | 0 $ | 0,057 $ | — |
| Sonnet B t2 | 1 | frozen | 0 | 0,724 | 1,00 | 1,000 | 0/48 | 0 $ | 0,033 $ | `fragment_overlap` |
| Sonnet B t3 | 2 | frozen | 0 | 0,724 | 1,00 | 1,000 | 0/48 | 0 $ | 0,036 $ | `fragment_overlap` |
| Sonnet A-programme 10⁵ t1 | 0 | frozen | 2 | 0,684 | 0,82 | 0,944 | 0/48 | 0 $ | 0,168 $ | — |
| Sonnet A-programme 10⁵ t2 | 1 | frozen | 1 | 0,690 | 0,85 | 0,952 | 0/48 | 0 $ | 0,097 $ | — |
| Sonnet A-programme 10⁵ t3 | 2 | frozen | 3 | 0,695 | 0,87 | 0,960 | 0/48 | 0 $ | 0,174 $ | — |
| Sonnet A-littéral 10⁴ t1 | 0 | frozen | 3 | 0,690 | 0,85 | 0,952 | 0/48 | 0 $ | 1,694 $ | — |
| Sonnet A-littéral 10⁴ t2 | 1 | frozen | 3 | 0,667 | 0,74 | 0,921 | 0/48 | 0 $ | 0,408 $ | — |
| Sonnet A-littéral 10⁴ t3 | 2 | frozen | 2 | 0,563 | 0,28 | 0,778 | 0/48 | 0 $ | 0,543 $ | — |
| MiMo B t1 | 0 | frozen | 4 | 0,718 | 0,97 | 0,968 | 3/48 | 0,205 $ | 0,205 $ | — |
| MiMo B t2 | 1 | frozen | 2 | 0,741 | 1,08 | 0,921 | **13/48** | 0,192 $ | 0,192 $ | — |
| MiMo B t3 | 2 | frozen | 1 | 0,724 | 1,00 | 1,000 | 0/48 | 0,059 $ | 0,059 $ | — |

Lecture (comparatif, plafond en repère) : B atteint le plafond de la grille (Sonnet 3 sur 3, MiMo 1 sur 3) ; A-programme 10⁵ en est proche et stable (0,684 à 0,695) ; A-littéral 10⁴ est le plus dispersé (0,563 à 0,690). Aucune méthode ne détecte les `c00`, sauf MiMo B t2 (13/48, au prix de 10 vraies manquées, exactitude au-dessus du plafond) : **alerte** au sens de D8 (mémoire ou indice), à juger en 1-14b. Repère de 1-12, sans décision : ministral-3:3b (0,19) et qwen3.5:4b (0,08) sous 30 %.

**Séances signalées pour 1-14b** : Sonnet B t2 et t3 (`fragment_overlap`, 10 exemples) ; MiMo B t2 (rappel `c00` élevé, hors drapeaux AD-19).

Coût facturé de 1-13 : **0,456 $** (MiMo seul, plafond 2 $) ; équivalent API des séances Sonnet 3,21 $. Registre du lot 1 : 1,730 $ facturés.

## Témoins sur R (D9)

80 ≤ F < 120 : aucun jeu d'entraînement de R, donc **ni C, ni F, ni « même réseau » sur R** (D5, D9) ; `[tasks.legal_r]` de `config/train.toml` reste inutilisé. Seule l'option 2 de R3 (entraîner sur S, évaluer sur R) est jouée, ci-dessous.

## S → R (D10)

`nnww evaluate --on legal_r:eval` sur l'emplacement rassemblé, `--from-task legal_s` puis `legal_s_reserved` ; `eval-cross-legal_r-eval.json` (`cross: true`) écrit à côté de chaque `eval.json`.

| Réseaux de S | Exactitude sur R | Rappel `c00` |
|---|---|---|
| B Sonnet `legal_s` (3) | 0,724 (plafond) | 0/48 |
| B Sonnet `legal_s_reserved` (3) | 0,626 ; 0,695 ; 0,695 | 21/48 (t1, 35 vraies manquées) ; 0 ; 0 |
| B Fable, B MiMo `legal_s` | 0,724 ; 0,724 | 5/48 ; 0/48 |
| B MiMo `legal_s_reserved` (2) | 0,695 ; 0,695 | 0/48 |
| A-programme 10⁵ Sonnet `legal_s` / `legal_s_reserved` (3 + 3) | 0,684 à 0,695 / 0,690 à 0,695 | ≤ 5/48 |
| A-programme 10⁴ Sonnet `legal_s` (3) | 0,529 à 0,563 | ≤ 7/48 |
| A-littéral 10⁴ Sonnet `legal_s` / `legal_s_reserved` (3 + 3) | 0,500 à 0,563 / 0,500 à 0,690 | 0/48 |
| A Fable `legal_s` (littéral 10⁴, programme 10⁴, programme 10⁵) | 0,678 ; 0,690 ; 0,724 | 0/48 |
| C `legal_s`, N = 64 / 256 / 1 024 / 8 192 / 32 768 (moyenne de 3 graines) | 0,492 / 0,433 / 0,534 / 0,592 / 0,661 | 31 → 6 |
| F `legal_s`, mêmes N | 0,504 / 0,464 / 0,538 / 0,603 / 0,665 | 39 → 7 |
| C `legal_s_reserved`, mêmes N | 0,485 / 0,473 / 0,519 / 0,571 / 0,580 | 26 → 5 |
| F `legal_s_reserved`, mêmes N | 0,515 / 0,479 / 0,542 / 0,577 / 0,590 | 28 → 5 |
| Même réseau `legal_s` (36) / `legal_s_reserved` (18), N = 8 192 | 0,599 (0,500 à 0,649) / 0,572 (0,557 à 0,598) | 8,6 / 6,8 |

Les règles écrites sur S (B) transfèrent sur R au plafond de la grille ; les réseaux entraînés (C, F, même réseau) restent sous le plafond, même à 32 768 exemples, et leur rappel sur `c00` baisse quand N croît. Mesure hors distribution (formes nouvelles du CE, `c00`), lue comme telle.

## Rassemblement et publication à blanc (D11)

`rassembler_runs.py --to C:\Users\Utilisateur\nnww-artefacts --from <worktree 1-13>` : 77 fichiers copiés, 31 exclus, 0 conflit. Écart : lancé depuis le worktree, la branche du dépôt principal (`chore/etat-run-1-12b`) ne portant pas le script ; la racine principale n'a pas été touchée.

- `--notice` de test (dossier temporaire, non commité ; attribution de la condition 2 de 1-3 avec « extraction du 2026-11-07 » et l'index du CE du 2026-11-07, sans la mention de JADE, non utilisé) : **aucun refus**, rien d'écrit ; 87 séances, 144 témoins, 1 180 membres, 4 174 `raw` réservés contrôlés (1 200 sautés, moins de 12 caractères) ; **archive de R construite (2 jeux)**, `sources.jsonl` compris.
- `--notice` vide : code 1, **trois refus `r_attribution_missing`** seuls (phrase, URL de la licence, date d'extraction).

## Réserves

- **Réserve forte de 1-12** : contrôle de qualité de l'extracteur en échec après le tour de correction ; F, p_R et la composition de R en dépendent.
- R est un jeu de la Cour de cassation (103 paires sur 107) ; p_R = 0,449, sous p_d1 = 0,675, après les exclusions de l'appariement.
- Plafond de la grille = borne basse ; une exactitude au-dessus (MiMo B t2) ne vient que de `c00` marquées.
- Indice d'écart d'année : 39 fausses `none` contre 5 vraies (A1 libère l'écart sur le champ incohérent) ; non mesuré par le plancher, faute d'entraînement.
- Intervalle à 95 % d'une exactitude sur 174 exemples : ± 7 points environ.
