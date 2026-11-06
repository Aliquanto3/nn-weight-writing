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

Détail par type (S, 4 000 exemples : 2 000 vraies, 133 ou 134 fausses par type) : sur `legal_s`, les trois séances Sonnet et Fable séparent tous les types sans erreur (15 types à 100 %) ; les erreurs sont toutes sur les vraies jugées fausses (65 pour Sonnet t1 et Fable, 20 pour t2 et t3). Détail complet : sortie de `--par-type`.

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
