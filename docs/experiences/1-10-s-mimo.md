# Story 1-10 (partie MiMo) : séances sur S et S-réservé

Trois étapes. Réglage retenu (étape 3) et résultat de l'essai en tête ; les réglages précédents (étape 2 : 64000, medium ; étape 1 : 64000, effort par défaut) sont en annexes, non comptés dans les cases.

Date : 2026-11-06 (séances 06:03 à 07:23 UTC, en série). Lot 1, pilote API, OpenRouter, modèle `xiaomi/mimo-v2.6-pro`. Paramètres validés par Anaël, inchangés : `pass_budget = 20`, `max_tokens = 64000`, `max_session_usd = 5`, `session_timeout_s = 7200`. Code : `origin/main` 64ad628, sans modification du harnais.

## Réglage retenu (étape 3) : 131 072 jetons, effort medium, graine envoyée

Décision d'Anaël (2026-11-06) : `max_tokens = 131072` (plafond de sortie de `xiaomi/mimo-v2.6-pro` sur OpenRouter, relevé par l'API `/models`, qui liste `seed` parmi les paramètres admis), effort medium gardé, graine de séance transmise au fournisseur. Commits (branche `exp/1-10-s-mimo`, rebasée sur `main` 8fe5c4d) :

- `config/models.toml` : `max_tokens = 131072` (test `test_models_config`).
- `4fe9975` : (b) `ChatRequest.seed`, envoyé dans le corps OpenRouter (`"seed"`), jamais lu par l'adaptateur Anthropic (test : paramètres identiques avec ou sans graine), l'empreinte du prompt système n'est pas touchée (la graine n'entre pas dans le prompt), la graine reste journalisée dans l'événement `open` ; (c) une réponse sans texte ni appel d'outil (`stop`/`end_turn`) finit en `error` (« réponse vide ... »), même classe que la troncature, parce que le protocole réserve `pass_budget` à un agent qui rend la main avec une réponse, et que `error` est déjà le code des échecs du fournisseur ; (d) délai par appel OpenRouter passé de 600 à 3600 s (`OPENROUTER_TIMEOUT_S`, `session/run.py`), pour tenir un appel de 131072 jetons (~25 à 30 min) ; `session_timeout_s = 7200` n'est appliqué qu'au pilote Claude Code, jamais au pilote API (aucun plafond de durée de séance côté API, seulement `max_session_usd`). Aucun fichier commun aux deux pilotes (`service.py`, `prompt.py`, `tools.py`, `refusals.py`) n'est touché ; `providers/types.py` gagne un champ optionnel.
- `--par-type` : celui de `main` (moitié Sonnet) est gardé, mon commit `365c268` est abandonné.

### Résultat de l'essai : `legal_s` A-programme 10⁴, tentative 1, graine 0

Fin `error`, « réponse tronquée (length) à 131072 jetons » : un seul appel, 131 072 jetons de sortie consommés en raisonnement sans réponse visible, 1 412 s, 0 passe, facturé 0,115659 $ (`legal_s-A-program-1e4-mimo-v2.6-pro-t1-20261106T213133Z`, graine 0 et effort medium bien journalisés). **Résultat : MiMo ne tient pas S dans le budget de sortie du fournisseur** (même au plafond de 131 072 jetons, une première réponse de raisonnement ne se termine pas). Selon la règle posée, rien d'autre n'a été lancé : pas de B, ni d'autres A au nouveau réglage, pas de dossier gelé A.

Total facturé de la moitié MiMo de 1-10 : 0,867970 $ (étapes 1 et 2) + 0,115659 $ = **0,983629 $** (plafond 15 $). Séances signalées par drapeau d'audit : aucune.

## Annexe 2 : 64000 jetons, effort medium (étape 2)

Décision d'Anaël (2026-11-06) : MiMo à `effort = "medium"` (aligné sur Sonnet et Fable), `max_tokens` 64000 gardé. `config/models.toml` modifié (commit `6313c1d`, test `test_models_config`). Vérifié : le pilote OpenRouter envoie `reasoning: {effort: "medium"}` (`providers/openrouter.py:91`) et le journal `open` porte `"effort": "medium"` (et `size_target`). Graines 0, 1, 2 (tentatives 1, 2, 3). Même base de code que l'étape 1 rebasée sur `origin/main` (taille cible, PR #22). Jeux : ceux de l'étape 1 (graine 0).

### Section B

| Case | Tent. (graine) | Statut | Passes | Tours | Sortie (jetons) | Exactitude réservé | Facturé ($) | Durée (s) | Drapeaux |
|---|---|---|---|---|---|---|---|---|---|
| B `legal_s` | 1 (0) | error (tronquée) | 0 | 1 | 64000 | - | 0,057379 | 684 | - |
| B `legal_s` | 2 (1) | error (tronquée) | 0 | 1 | 64000 | - | 0,055723 | 699 | - |
| B `legal_s` | 3 (2) | pass_budget (réponse vide, `stop`) | 0 | 1 | 58909 | - | 0,051293 | 617 | - |
| B `legal_s_reserved` | 1 (0) | error (tronquée) | 0 | 1 | 64000 | - | 0,057283 | 394 | - |
| B `legal_s_reserved` | 2 (1) | freeze | 1 | 3 | 34636 | 3589/4000 (89,7 %) | 0,044951 | 218 | aucun |
| B `legal_s_reserved` | 3 (2) | freeze | 1 | 3 | 54882 | 3600/4000 (90,0 %) | 0,073558 | 391 | aucun |

S-réservé, exactitude séparée (`scripts/exactitude_reserve.py --par-type`) : t2 vraies 2000/2000, 10 types connus (fausses) 1323/1334, 5 types tenus à l'écart 266/666 (39,9 %) ; t3 vraies 2000/2000, connus 1334/1334, tenus à l'écart 266/666. Le réseau B n'attrape donc que ~40 % des fausses des types jamais vus. La séance `legal_s` t3 à l'effort medium finit sans appel d'outil : réponse assistant vide avec `stop_reason: stop` après 58 909 jetons de raisonnement ; le pilote la classe `pass_budget` (agent qui rend la main), en réalité même échec que la troncature (aucun texte, aucun outil).

Moyenne et écart entre tentatives : `legal_s` B : aucune tentative gelée (0/3). `legal_s_reserved` B : exactitude 89,9 % en moyenne (89,7 ; 90,0), écart 0,3 point (2 gelées sur 3).

### Section A

Option `--size-target` 10000 (fenêtre [3162 ; 31623]) ou 100000. Seules les trois séances `legal_s` A-programme 10⁴ ont été lancées ; les trois ont fini `error` par troncature à 64000 jetons de sortie dès le premier appel (747, 756 et 780 s ; 0,057307 + 0,055705 + 0,055705 $), 0 passe, aucun refus du harnais, aucun gel. Règle de la consigne appliquée : trois troncatures de suite (A 10⁴ ×3), arrêt et compte rendu. Les 12 autres cases A (A-programme 10⁵ sur `legal_s` et `legal_s_reserved`, A-littéral 10⁴ sur les deux) n'ont pas été jouées : pas de dossier gelé A, pas de paramètres gelés ni de drapeaux à relever.

| Case | Tent. | Statut | Passes | Facturé ($) | Durée (s) |
|---|---|---|---|---|---|
| A-program 10⁴ `legal_s` | 1, 2, 3 | error (tronquée) x3 | 0 | 0,057307 ; 0,055705 ; 0,055705 | 747 ; 756 ; 780 |

### Synthèse et coûts

- Cases B : 2 gels sur 6, tous deux sur S-réservé ; `legal_s` B 0/3 gelée. Cases A : 0/3 gelée sur les 3 jouées.
- Facturé de l'étape 2 : 0,508904 $ ; étape 1 (annexe) : 0,359066 $ ; total de la moitié MiMo : 0,867970 $ (plafond 15 $).
- L'effort medium n'a pas supprimé les troncatures (5 séances sur 9 à 64000 jetons ; 1 réponse vide à 58909) : les coûts des séances tronquées sont identiques à l'étape 1 (0,057379 $ et 0,055723 $), ce qui suggère des entrées et des sorties de même taille, `reasoning.effort` ne plafonnant pas le raisonnement chez Xiaomi. La graine n'est pas envoyée au fournisseur (`sampling` vide) : les tentatives ne sont pas indépendantes par la graine.
- Séances signalées par drapeau d'audit : aucune.
- Défauts du harnais : aucun correctif de code commun. `--par-type` ajouté à `scripts/exactitude_reserve.py` (commit `365c268`), absent de `main`.

## Graines et jeux

- Jeux : `nnww datagen legal --seed 0` ; jeux de séance `data/<tâche>/session/` (40 exemples), réservés `heldout/<tâche>/eval/` (4 000), non commités.
- Commande : `nnww session --task <tâche> --dataset session --method B --model mimo-v2.6-pro --attempt N --seed N --lot 1`. Graine de séance = numéro de tentative (1, 2, 3).

## Annexe 1 : 64000 jetons, effort par défaut (étape 1)

Première étape, avant la décision d'Anaël (effort medium). Graines 1, 2, 3.

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

Séance gelée (t3, `legal_s`) : 3 tours, 57 954 jetons en entrée, 57 832 en sortie, 68 352 lus au cache, `tree_sha256` `76ffecbfcd8629c5`... (complet : événement `freeze` de son journal, non commité). Détail sur le réservé : vraies 1988/2000 ; fausses 1 980/2 000 ; t05 114/134, tous les 14 autres types 100 %. Sur S-réservé : aucune séance gelée, donc pas d'exactitude (ni séparée sur les 10 types connus et les 5 tenus à l'écart).

## Constat : 5 séances sur 6 finissent par réponse tronquée

Dans les 5 séances en erreur, le premier appel consomme les 64 000 jetons de sortie en raisonnement (MiMo ne rend pas son raisonnement), sans contenu visible ni appel d'outil : fin `error`, détail `réponse tronquée (length) à 64000 jetons`, 0 passe, 1 tour, 760 à 890 s. Le harnais se comporte comme prévu (correctif de 1-8, `b85cd7e`) ; ce n'est pas une séance perdue par le harnais (AD-14), donc non rejouée, mais un échec du modèle sous le plafond de 64 000 jetons. Sur le jouet, le plus long appel faisait 55 349 jetons ; S pousse le raisonnement du premier appel au-delà du plafond. Aucun défaut du harnais trouvé, aucun correctif, code commun inchangé.

Pistes (décision d'Anaël, protocole non touché ici) : plafond `max_tokens` plus haut pour MiMo si OpenRouter/Xiaomi l'admet, ou contrôle de l'effort de raisonnement du pilote API. Les séances en erreur comptent comme tentatives en échec (coût 0,056 $ chacune) ; une tentative supplémentaire coûte environ 0,06 à 0,08 $.

## Séances signalées par drapeau d'audit (jugement en 1-14)

Aucune.

## Ce qui reste

- Toutes les cases A et B de MiMo sur S : bloquées par la troncature à 131 072 jetons. Pistes pour Anaël : effort `low` ou `minimal`, autre fournisseur ou autre mode de raisonnement, ou retenir le résultat (MiMo hors d'état de tenir S) pour la sélection du modèle.
