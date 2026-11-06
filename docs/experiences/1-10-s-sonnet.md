# Story 1-10 (partie Sonnet et Fable) : séances sur S et S-réservé

Date : 2026-11-06 (séances 06:03 à 06:07 UTC). Lot 1, pilote Claude Code (`claude -p`, abonnement d'Anaël), `sonnet-5.5` (`claude-sonnet-5-5`) et `fable-5.1` (`claude-fable-5-1`), effort `medium`. Protocole inchangé : `pass_budget = 20`, `turn_limit = 200`, `max_session_usd = 5`, `session_timeout_s = 7200`. Environnement posé dans chaque commande : `NNWW_CLAUDE_CWD_ROOT='C:\nnww-cwd'`, configuration dédiée `~/.nnww/claude-config`, aucune `ANTHROPIC_API_KEY`.

**Cette étape : cases B seulement (7 séances).** Les sections A (A-programme, A-littéral) viendront après la fusion de la taille cible des cases A.

## Graines et versions

- Jeux : `nnww datagen --seed 0 legal` dans le worktree (non commités) : `data/<tâche>/session/` (40 exemples non annotés montrés à l'agent) et `heldout/<tâche>/eval/` (4 000 exemples).
- Séances : jeu `session`, tentative `n`, graine de séance `n - 1` (Sonnet : tentatives 1, 2, 3 de graines 0, 1, 2 ; Fable : tentative 1, graine 0), `--lot 1`.
- Code : branche `exp/1-10-s-sonnet` sur `main` 64ad628 ; un seul commit de code, `c262ccc` (option `--par-type` de `scripts/exactitude_reserve.py`). Aucun défaut du harnais trouvé, aucune séance perdue ni rejouée.

## Résultats (7 séances B)

Exactitude sur le réservé (4 000 exemples) par `uv run python scripts/exactitude_reserve.py runs/1/<id> --dataset eval --par-type` (vérification d'empreinte avant lecture). Tours = messages distincts du modèle. Facturé 0 $ partout (abonnement). Équivalent = `cost_equiv_usd` de clôture (journal). Drapeaux d'audit : aucun (`flags` vide dans tous les `script_run`). Toutes les fins sont `frozen` ; aucun refus du harnais en séance.

| Modèle | Tâche | Tent. | Passes /20 | Tours | Exactitude | Équivalent API ($) | Durée (s) | Tokens (entrée / sortie / lecture cache / écriture cache) | `tree_sha256` (16) |
|---|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | legal_s | 1 | 1 | 3 | 3935/4000 (98,4 %) | 0,095701 | 34,6 | 6 / 5 042 / 14 772 / 10 948 | `42ed8281c2b5f0dd` |
| Sonnet 5.5 | legal_s | 2 | 0 | 2 | 3980/4000 (99,5 %) | 0,046533 | 24,9 | 4 / 3 374 / 11 055 / 2 920 | `bbec2fa7d1a76dd1` |
| Sonnet 5.5 | legal_s | 3 | 0 | 2 | 3980/4000 (99,5 %) | 0,043197 | 22,6 | 4 / 3 092 / 11 055 / 2 791 | `60ec8ab4bdb511d3` |
| Sonnet 5.5 | legal_s_reserved | 1 | 0 | 2 | 3496/4000 (87,4 %) | 0,037909 | 14,2 | 4 / 1 683 / 6 707 / 5 100 | `86323191bb9c2f7e` |
| Sonnet 5.5 | legal_s_reserved | 2 | 0 | 2 | 3572/4000 (89,3 %) | 0,025479 | 16,4 | 4 / 1 866 / 10 465 / 1 441 | `757bb2870cccad2` |
| Sonnet 5.5 | legal_s_reserved | 3 | 0 | 2 | 3574/4000 (89,4 %) | 0,031399 | 18,9 | 4 / 2 284 / 10 462 / 1 876 | `d970f38f8852f8ee` |
| Fable 5.1 | legal_s | 1 | 1 | 4 | 3935/4000 (98,4 %) | 0,330858 | 34,4 | 98 / 2 777 / 22 749 / 9 267 | `4610a350f3c449c2` |

Total des 7 séances : 0 $ facturé, 0,611476 $ équivalent API. Registre `budget/ledger.csv` : 14 lignes ajoutées (réservation puis clôture), `billed_usd` = 0.

Détail par type (S, 4 000 exemples : 2 000 vraies, 133 ou 134 fausses par type) : sur `legal_s`, Sonnet t1 et Fable séparent les 15 types sans erreur ; leurs 65 erreurs sont des vraies jugées fausses. Sonnet t2 et t3 classent toutes les vraies correctement et se trompent sur 20 fausses de t05 (114/134). Détail complet : sortie de `--par-type`.

### S-réservé : types connus et types tenus à l'écart

Fausses seulement (vraies à part). Connus : t01, t02, t03, t05, t06, t08, t10, t13, t14, t15 (1 334 exemples). Tenus à l'écart : t04, t07, t09, t11, t12 (666 exemples).

| Tentative | Vraies | Fausses, 10 connus | Fausses, 5 tenus | Détail des tenus à l'écart |
|---|---|---|---|---|
| 1 | 1915/2000 | 1314/1334 (98,5 %) | 267/666 (40,1 %) | t04 0/134, t07 0/133, t09 133/133, t11 133/133, t12 1/133 |
| 2 | 1991/2000 | 1314/1334 (98,5 %) | 267/666 (40,1 %) | idem |
| 3 | 1965/2000 | 1334/1334 (100 %) | 275/666 (41,3 %) | t04 5/134, t07 0/133, t09 133/133, t11 133/133, t12 4/133 |

Lecture : sur les types tenus à l'écart, t09 et t11 (numéro d'appel postérieur à l'arrêt ; format de numéro d'une autre juridiction) sont retrouvés par déduction à partir de la description et des types connus (t01, t13 et t10) ; t04 (siège inconnu), t07 (formation du CE à la mauvaise date) et t12 (dimanche, jour férié) ne le sont presque jamais. Les deux premières tentatives perdent en plus 20 fausses connues de t05 (formations du CE, 114/134) ; la tentative 3 les attrape toutes.

## Porte de coût (methodes-et-lots.md)

Premières séances Sonnet de S (les 3 B sur `legal_s`) :

- Coût **facturé** : 0, 0, 0 $, médiane **0 $** ≤ 2 $, et par abonnement la porte ne joue pas : **3 tentatives par case** pour Sonnet.
- Équivalent API (journal) : 0,095701 ; 0,046533 ; 0,043197 $, médiane **0,046533 $** (également très loin de 2 $, donc même un repli API aurait gardé 3 tentatives sur la foi de ces seules séances B ; les séances A, plus longues, ne sont pas encore mesurées).

Décision à consigner par l'orchestrateur au journal du run : 3 tentatives par case.

## Contrôle du report de 1-8 : `cost_equiv_usd` contre `result.total_cost_usd`

Le pilote verse désormais `result.total_cost_usd` dans un `model_call` de réconciliation. Sur les 7 séances, `end.totals.cost_equiv_usd` égale `result.total_cost_usd` à l'arrondi à 6 décimales près (écart maximal 0,0000007 $, soit 2e-7 relatif) : 0,0957012, 0,0465335, 0,0431975, 0,0379087, 0,0254785, 0,0313982, 0,33085725. Le report est levé : l'équivalent du journal est l'équivalent réel (cache d'une heure comprise) pour les séances qui vont jusqu'au `result`.

## Tarif d'écriture de cache 1 h de Fable 5.1

Séance Fable : 98 jetons d'entrée, 2 777 de sortie, 22 749 de lecture de cache, 9 267 d'écriture en tranche d'une heure (`ephemeral_1h`, 0 en 5 minutes), `total_cost_usd` = 0,33085725 $. Avec 10 $ (entrée), 50 $ (sortie) et 0,25 $ (lecture) par million, le reste vaut 0,18534 $ pour 9 267 jetons, soit **20,00 $/Mtok exactement** : la valeur `cache_write_1h = 20.0` de `pricing.toml` est confirmée par Claude Code. (Le tarif de la page de prix publique n'a pas été relu ; seule la valeur appliquée par Claude Code est confirmée.)

## Séances signalées par les drapeaux d'audit (AD-19) pour jugement en 1-14

Aucune : aucun drapeau dans les 7 séances B (le mode B n'exécute que `submit_rules` et `run_on_examples`).

## Étanchéité

Répertoire courant de `claude` sous `C:\nnww-cwd` ; contrôle `init_problems` du pilote passé pour chaque séance (aucune fin `error`). Les paquets de séance ne contiennent que les 40 exemples non annotés du jeu `session`.

## Ce qui reste

- Cases A (A-programme vers 10⁴ et 10⁵ sur S, 10⁵ sur S-réservé ; A-littéral), Sonnet et MiMo, Fable sur S : à lancer après fusion de la taille cible au harnais.
- B sur MiMo (autre moitié).
- Les rapports de règles écrites à la main (B) sur S sont très proches du plafond ; la discrimination vient de S-réservé (types tenus à l'écart), à reprendre en 1-14 avec C et F.

# Cases A (étape 2)

Date : 2026-11-06 (06:16 à 08:37 UTC). Mêmes paramètres et mêmes relevés que B ; `--size-target 10000` ou `100000` (obligatoire en A), graines de séance 0, 1, 2 pour les tentatives 1, 2, 3 (Fable : tentative 1, graine 0). Le code part de `main` 2d3eeef (taille cible, PR #22).

## Défauts du harnais et séances perdues (AD-14)

- Défaut 1 : `config_dir_problems` refusait `plugins/plugin-directory-cache-v2.json`, catalogue des places de marché que `claude -p` a recréé dans la configuration dédiée entre deux séances (après la 5e séance A, aucun plugin installé). Correctif minimal `f017b3a` (`Fix:`), propre au pilote Claude Code (`session/claude_code.py`, liste `MARKETPLACE_ENTRIES`) ; test ajouté dans `tests/test_claude_code.py`. Aucun des fichiers communs aux deux pilotes (`service.py`, `prompt.py`, `tools.py`, `refusals.py`) n'est touché.
- 13 séances refusées avant lancement par ce défaut (fin `error`, 0 tour, 0 $, registre `reserved` puis `closed` à 0) ; les 13 cases ont été rejouées après le correctif avec les mêmes tentatives et graines (nouveaux identifiants de séance). Leurs dossiers `runs/1/*T0622[4-5]*Z` (fin `error`) ne sont pas des résultats et ne comptent pas.
- Évolution du script de mesure : `scripts/exactitude_reserve.py --par-type` accepte aussi les réseaux gelés (A), commit `3b2f607` (les décomptes de A par `--par-type` et par la voie `score_frozen` coïncident, vérifié sur une séance).

## Résultats (18 séances A, toutes en `frozen`)

Exactitude sur le réservé (4 000 exemples). Équivalent API = `cost_equiv_usd` de clôture, égal à `result.total_cost_usd` de Claude Code à l'arrondi près pour les 18 (écart max 1 µ$) ; facturé 0 $ partout. « Paramètres » = `size_nominal` du gel (nombre de paramètres du réseau gelé, entrées de couches). Aucune séance en `pass_budget`, `turn_limit`, `money_budget` ni limite d'usage. Refus du harnais : colonne « Refus en séance » (aucun `size_out_of_range` : toutes les tailles gelées sont dans les fenêtres, 12 254 à 30 632 pour 10^4 et 98 018 à 306 302 pour 10^5).

| Modèle | Tâche | Case | Tent. | Statut | Passes /20 | Tours | Paramètres | Exactitude | Équiv. API ($) | Durée (s) | Drapeaux | Refus en séance | Dossier gelé |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | legal_s | A-program 10^4 | 1 | frozen | 1 | 6 | 30632 | 2744/4000 (68.6 %) | 0.1440 | 78 | aucun | invalid_manifest 1 | `runs/1/legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z` |
| Sonnet 5.5 | legal_s | A-program 10^4 | 2 | frozen | 0 | 6 | 30632 | 2429/4000 (60.7 %) | 0.0703 | 54 | aucun | invalid_manifest 2, no_network_declared 1 | `runs/1/legal_s-A-program-1e4-sonnet-5.5-t2-20261106T061724Z` |
| Sonnet 5.5 | legal_s | A-program 10^4 | 3 | frozen | 1 | 7 | 30632 | 2449/4000 (61.2 %) | 0.1345 | 82 | aucun | invalid_manifest 2, no_network_declared 1 | `runs/1/legal_s-A-program-1e4-sonnet-5.5-t3-20261106T061819Z` |
| Sonnet 5.5 | legal_s | A-program 10^5 | 1 | frozen | 1 | 6 | 171530 | 3797/4000 (94.9 %) | 0.3059 | 163 | aucun | invalid_manifest 2 | `runs/1/legal_s-A-program-1e5-sonnet-5.5-t1-20261106T062003Z` |
| Sonnet 5.5 | legal_s | A-program 10^5 | 2 | frozen | 1 | 6 | 306302 | 3430/4000 (85.8 %) | 0.2386 | 144 | aucun | invalid_manifest 2 | `runs/1/legal_s-A-program-1e5-sonnet-5.5-t2-20261106T062355Z` |
| Sonnet 5.5 | legal_s | A-program 10^5 | 3 | frozen | 2 | 7 | 245042 | 3722/4000 (93.0 %) | 0.3541 | 188 | aucun | invalid_manifest 1, invalid_blocks 1 | `runs/1/legal_s-A-program-1e5-sonnet-5.5-t3-20261106T062619Z` |
| Sonnet 5.5 | legal_s | A-literal 10^4 | 1 | frozen | 2 | 39 | 30632 | 2318/4000 (58.0 %) | 2.0296 | 722 | aucun | invalid_manifest 1, invalid_weights 1 | `runs/1/legal_s-A-literal-1e4-sonnet-5.5-t1-20261106T062928Z` |
| Sonnet 5.5 | legal_s | A-literal 10^4 | 2 | frozen | 6 | 32 | 30632 | 2651/4000 (66.3 %) | 2.3659 | 873 | aucun | invalid_manifest 2, invalid_weights 3 | `runs/1/legal_s-A-literal-1e4-sonnet-5.5-t2-20261106T064131Z` |
| Sonnet 5.5 | legal_s | A-literal 10^4 | 3 | frozen | 2 | 19 | 12254 | 2254/4000 (56.4 %) | 0.7423 | 283 | aucun | invalid_manifest 1, invalid_weights 1 | `runs/1/legal_s-A-literal-1e4-sonnet-5.5-t3-20261106T065605Z` |
| Fable 5.1 | legal_s | A-program 10^4 | 1 | frozen | 1 | 8 | 30632 | 3689/4000 (92.2 %) | 2.8725 | 499 | aucun | invalid_manifest 3 | `runs/1/legal_s-A-program-1e4-fable-5.1-t1-20261106T073730Z` |
| Fable 5.1 | legal_s | A-program 10^5 | 1 | frozen | 2 | 10 | 276349 | 3935/4000 (98.4 %) | 3.0765 | 483 | fragment_overlap (4); fragment_overlap (4) | invalid_manifest 3 | `runs/1/legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z` |
| Fable 5.1 | legal_s | A-literal 10^4 | 1 | frozen | 4 | 19 | 30632 | 3517/4000 (87.9 %) | 14.4980 | 2609 | aucun | invalid_manifest 2 | `runs/1/legal_s-A-literal-1e4-fable-5.1-t1-20261106T075353Z` |
| Sonnet 5.5 | legal_s_reserved | A-program 10^5 | 1 | frozen | 2 | 7 | 98018 | 3559/4000 (89.0 %) | 0.3106 | 173 | aucun | invalid_manifest 1, invalid_blocks 1 | `runs/1/legal_s_reserved-A-program-1e5-sonnet-5.5-t1-20261106T070108Z` |
| Sonnet 5.5 | legal_s_reserved | A-program 10^5 | 2 | frozen | 1 | 6 | 131711 | 3585/4000 (89.6 %) | 0.2799 | 162 | fragment_overlap (4); fragment_overlap (4) | invalid_manifest 1 | `runs/1/legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z` |
| Sonnet 5.5 | legal_s_reserved | A-program 10^5 | 3 | frozen | 3 | 9 | 196034 | 3511/4000 (87.8 %) | 0.3086 | 159 | aucun | invalid_manifest 1, invalid_blocks 1 | `runs/1/legal_s_reserved-A-program-1e5-sonnet-5.5-t3-20261106T070645Z` |
| Sonnet 5.5 | legal_s_reserved | A-literal 10^4 | 1 | frozen | 2 | 25 | 30632 | 3211/4000 (80.3 %) | 2.2997 | 842 | aucun | invalid_manifest 1, invalid_weights 2 | `runs/1/legal_s_reserved-A-literal-1e4-sonnet-5.5-t1-20261106T070925Z` |
| Sonnet 5.5 | legal_s_reserved | A-literal 10^4 | 2 | frozen | 2 | 18 | 12254 | 2255/4000 (56.4 %) | 0.8408 | 324 | aucun | invalid_manifest 1, invalid_weights 1 | `runs/1/legal_s_reserved-A-literal-1e4-sonnet-5.5-t2-20261106T072328Z` |
| Sonnet 5.5 | legal_s_reserved | A-literal 10^4 | 3 | frozen | 4 | 22 | 21443 | 2615/4000 (65.4 %) | 1.3843 | 516 | aucun | invalid_manifest 2, invalid_weights 2 | `runs/1/legal_s_reserved-A-literal-1e4-sonnet-5.5-t3-20261106T072852Z` |

Paramètres gelés : A-programme 10^4 = 30 632 aux trois tentatives de Sonnet et de Fable (même architecture) ; A-littéral 10^4 = 12 254 à 30 632 ; 10^5 = 98 018 à 306 302.

## Synthèse par case (moyenne, écart entre tentatives = max - min)

| Modèle | Tâche | Case | n | Exactitude moyenne | Écart (points) | Équiv. API moyen ($) | Durée moyenne (s) |
|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | S | A-programme 10^4 | 3 | 63,5 % (2 744 / 2 429 / 2 449) | 7,9 | 0,116 | 71 |
| Sonnet 5.5 | S | A-programme 10^5 | 3 | 91,2 % (3 797 / 3 430 / 3 722) | 9,2 | 0,300 | 165 |
| Sonnet 5.5 | S | A-littéral 10^4 | 3 | 60,2 % (2 318 / 2 651 / 2 254) | 9,9 | 1,713 | 626 |
| Sonnet 5.5 | S-réservé | A-programme 10^5 | 3 | 88,8 % (3 559 / 3 585 / 3 511) | 1,9 | 0,300 | 165 |
| Sonnet 5.5 | S-réservé | A-littéral 10^4 | 3 | 67,3 % (3 211 / 2 255 / 2 615) | 23,9 | 1,508 | 561 |
| Fable 5.1 | S | A-programme 10^4 | 1 | 92,2 % (3 689) | - | 2,873 | 499 |
| Fable 5.1 | S | A-programme 10^5 | 1 | 98,4 % (3 935) | - | 3,076 | 483 |
| Fable 5.1 | S | A-littéral 10^4 | 1 | 87,9 % (3 517) | - | 14,498 | 2 609 |

Repères B (même jeu) : Sonnet 98,4 à 99,5 % sur S, 87,4 à 89,4 % sur S-réservé ; Fable 98,4 % sur S. Hasard : 50 %.

### S-réservé : fausses de 10 types connus et de 5 types tenus à l'écart

| Séance | Vraies | Fausses, 10 connus | Fausses, 5 tenus | Tenus, détail |
|---|---|---|---|---|
| A-programme 10^5 t1 | 1997/2000 | 1296/1334 (97,2 %) | 266/666 (39,9 %) | t09, t11 133/133 ; t04, t07, t12 : 0 |
| A-programme 10^5 t2 | 1996/2000 | 1321/1334 (99,0 %) | 268/666 (40,2 %) | t09, t11 133/133 ; t12 2/133 ; t04, t07 : 0 |
| A-programme 10^5 t3 | 1968/2000 | 1268/1334 (95,1 %) | 275/666 (41,3 %) | t09, t11 133/133 ; t04 5, t12 4 ; t07 0 |
| A-littéral 10^4 t1 | 1959/2000 | 977/1334 (73,2 %) | 275/666 (41,3 %) | t09, t11 133/133 ; t04 5, t12 4 ; t07 0 |
| A-littéral 10^4 t2 | 1991/2000 | 264/1334 (19,8 %) | 0/666 | aucun type tenu détecté |
| A-littéral 10^4 t3 | 2000/2000 | 513/1334 (38,5 %) | 102/666 (15,3 %) | t11 102/133 ; autres 0 |

Les types tenus à l'écart se comportent comme en B : t09 et t11 sont retrouvés par déduction des règles voisines quand le réseau apprend les types connus, t04, t07 et t12 presque jamais. A-programme 10^5 atteint le niveau de B sur les types connus (95 à 99 %). A-littéral à 10^4 est instable : de 19,8 % à 73,2 % sur les mêmes types connus selon la tentative ; les deux tentatives les plus faibles ressemblent à des réseaux qui disent presque toujours « vraie » (vraies 99,6 % et 100 %).

## Drapeaux d'audit (AD-19) : séances signalées pour jugement en 1-14

`fragment_overlap` (4 exemples chaque fois, dans les deux exécutions de script de la séance) :

- `runs/1/legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z` (exemples `legal-s00009`, `-s00012`, `-s00013`...) ;
- `runs/1/legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z` (exemples `legal-r00004`, `-r00012`, `-r00020`...).

Les 16 autres séances A et les 7 B : aucun drapeau.

## Porte de coût : mise à jour

Facturé 0 $, médiane 0 $ : 3 tentatives par case, décision inchangée. Pour information, l'équivalent API des séances Sonnet sur S : médiane des 12 séances (B, A-programme, A-littéral) = 0,19 $ ; A-littéral à 10^4 vaut en revanche 2,03 / 2,37 / 0,74 $ (médiane 2,03 $, au-dessus de 2 $) et sur S-réservé 2,30 / 0,84 / 1,38 $ : en repli API, la porte des 2 $ se jouerait sur A-littéral. Fable : 2,87 $ (A-programme 10^4), 3,08 $ (10^5) et 14,50 $ (A-littéral 10^4, 19 tours, 213 394 jetons de sortie, 43 minutes) en équivalent, soit au-dessus du plafond de 5 $ par séance s'il avait été facturé.

## Observations sur A-littéral à 10^4

Aucune troncature de sortie ni limite d'usage ; durées de 283 s à 873 s pour Sonnet et 2 609 s pour Fable (sous le délai de 7 200 s). Le modèle écrit les poids ligne par ligne (`write_weights`), jusqu'à 39 tours. Fable dépense 14,50 $ équivalent pour 87,9 %, alors que A-programme à 10^5 atteint 98,4 % pour 3,08 $.

## Tarif de cache 1 h de Fable (rappel)

Confirmé à 20,00 $/Mtok sur la séance B (voir plus haut) ; les 3 séances A de Fable retombent sur `total_cost_usd` du `result` au micro-dollar.
