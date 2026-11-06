# Story 1-10 (partie MiMo) : séances sur S et S-réservé

Section B (cette étape). Les sections A-programme et A-littéral viennent après l'ajout de la taille cible des cases A au harnais.

Date : 2026-11-06 (séances 06:03 à 07:23 UTC, en série). Lot 1, pilote API, OpenRouter, modèle `xiaomi/mimo-v2.6-pro`. Paramètres validés par Anaël, inchangés : `pass_budget = 20`, `max_tokens = 64000`, `max_session_usd = 5`, `session_timeout_s = 7200`. Code : `origin/main` 64ad628, sans modification du harnais.

## Graines et jeux

- Jeux : `nnww datagen legal --seed 0` ; jeux de séance `data/<tâche>/session/` (40 exemples), réservés `heldout/<tâche>/eval/` (4 000), non commités.
- Commande : `nnww session --task <tâche> --dataset session --method B --model mimo-v2.6-pro --attempt N --seed N --lot 1`. Graine de séance = numéro de tentative (1, 2, 3).

## Résultats (6 séances, 3 tentatives par case)

Exactitude sur le réservé (4 000 exemples) après gel, par `scripts/exactitude_reserve.py runs/1/<séance> --dataset eval` (aucune adaptation nécessaire : `--dataset` existait). Drapeaux d'audit : aucun (`flags` vide dans le seul événement `script_run`). Coût facturé = équivalent API.

| Case | Tent. | Statut | Passes /20 | Exactitude | Facturé ($) | Durée (s) | Séance |
|---|---|---|---|---|---|---|---|
| B `legal_s` | 1 | error (tronquée) | 0 | - | 0,057379 | 827 | `legal_s-B-mimo-v2.6-pro-t1-20261106T060302Z` |
| B `legal_s` | 2 | error (tronquée) | 0 | - | 0,055723 | 786 | `legal_s-B-mimo-v2.6-pro-t2-20261106T061711Z` |
| B `legal_s` | 3 | freeze | 1 | 3968/4000 (99,2 %) | 0,075771 | 683 | `legal_s-B-mimo-v2.6-pro-t3-20261106T063042Z` |
| B `legal_s_reserved` | 1 | error (tronquée) | 0 | - | 0,057173 | 758 | `legal_s_reserved-B-mimo-v2.6-pro-t1-20261106T064206Z` |
| B `legal_s_reserved` | 2 | error (tronquée) | 0 | - | 0,057283 | 886 | `legal_s_reserved-B-mimo-v2.6-pro-t2-20261106T065445Z` |
| B `legal_s_reserved` | 3 | error (tronquée) | 0 | - | 0,055737 | 842 | `legal_s_reserved-B-mimo-v2.6-pro-t3-20261106T070932Z` |

Total facturé de l'étape : **0,359066 $** (plafond de l'étape 4 $, de la moitié MiMo 15 $).

Séance gelée (t3, `legal_s`) : 3 tours, 57 954 jetons en entrée, 57 832 en sortie, 68 352 lus au cache, `tree_sha256` `76ffecbfcd8629c5`... (complet : événement `freeze` de son journal, non commité). Détail sur le réservé : vraies 1988/2000 ; fausses 1 970/2 000 ; t05 114/134, tous les 14 autres types 100 %. Sur S-réservé : aucune séance gelée, donc pas d'exactitude (ni séparée sur les 10 types connus et les 5 tenus à l'écart).

## Constat : 5 séances sur 6 finissent par réponse tronquée

Dans les 5 séances en erreur, le premier appel consomme les 64 000 jetons de sortie en raisonnement (MiMo ne rend pas son raisonnement), sans contenu visible ni appel d'outil : fin `error`, détail `réponse tronquée (length) à 64000 jetons`, 0 passe, 1 tour, 760 à 890 s. Le harnais se comporte comme prévu (correctif de 1-8, `b85cd7e`) ; ce n'est pas une séance perdue par le harnais (AD-14), donc non rejouée, mais un échec du modèle sous le plafond de 64 000 jetons. Sur le jouet, le plus long appel faisait 55 349 jetons ; S pousse le raisonnement du premier appel au-delà du plafond. Aucun défaut du harnais trouvé, aucun correctif, code commun inchangé.

Pistes (décision d'Anaël, protocole non touché ici) : plafond `max_tokens` plus haut pour MiMo si OpenRouter/Xiaomi l'admet, ou contrôle de l'effort de raisonnement du pilote API. Les séances en erreur comptent comme tentatives en échec (coût 0,056 $ chacune) ; une tentative supplémentaire coûte environ 0,06 à 0,08 $.

## Séances signalées par drapeau d'audit (jugement en 1-14)

Aucune.

## Ce qui reste

- Cases A (A-programme, A-littéral) sur `legal_s` et `legal_s_reserved`, quand la taille cible sera au harnais.
- Décision sur le plafond de sortie de MiMo avant de rejouer les 5 cases en erreur.
