# Story 1-8 (partie MiMo) : séances sur le jouet

Date : 2026-11-05 (séances 22:42 à 23:35 UTC). Lot 1, 1 tentative par case, pilote API, OpenRouter, fournisseur Xiaomi (`served_by` vérifié), modèle `xiaomi/mimo-v2.6-pro` (`mimo-v2.6-pro`). Protocole inchangé : `pass_budget = 20`, `turn_limit = 200`, prompt système de 1-6. Seule la configuration `max_tokens` de MiMo a changé (16000 puis 64000, voir défauts).

## Graines et versions

- Jeux : `nnww datagen all --seed 0 --n 256 --n-heldout 400` (générateur v2) ; séances : `--seed 0`, tentative 1 ; jeux `data/<tâche>/toy/` (256 exemples) et `heldout/<tâche>/toy/` (400 exemples), non commités.
- Code : worktree `exp/1-8-jouet-mimo` sur `main` 1e62860 + correctif `b85cd7e`. Python 3.14, dépendances de `uv.lock`.

## Résultats (9 cases)

Exactitude sur le réservé (400 exemples), mesurée hors séance, après gel, par `uv run python scripts/exactitude_reserve.py runs/1/<session_id> ...` (`nnww evaluate` ne rend pas l'exactitude, renvoyée en 1-14). Le script appelle d'abord `verify_frozen` (sha256 de chaque fichier de `frozen/` et `tree_sha256` recalculés contre l'événement `freeze` du journal) et ne lit `heldout/` qu'ensuite ; A : `score_frozen` ; B : `rules.py` gelé exécuté par `sandbox.run` profil B. La séance perdue est refusée (`no_freeze_record`) avant toute lecture du réservé. Coût facturé = équivalent API (pas d'abonnement). Drapeaux d'audit : aucun (`flags` vide dans les 9 événements `script_run`, tous en A-programme et B ; A-littéral n'exécute pas de script).

| Tâche | Méthode | Statut | Passes /20 | Tours | Exactitude | Facturé ($) | Équivalent API ($) | Drapeaux | Séance | `tree_sha256` (16 premiers) |
|---|---|---|---|---|---|---|---|---|---|---|
| parity | A-programme | freeze | 1 | 9 | 400/400 | 0,015622 | 0,015622 | aucun | `parity-A-program-mimo-v2.6-pro-t1-20261105T224746Z` | `5d38406970ed952e` |
| parity | A-littéral | freeze | 1 | 9 | 400/400 | 0,024460 | 0,024460 | aucun | `parity-A-literal-mimo-v2.6-pro-t1-20261105T224942Z` | `74522504d5b572ae` |
| parity | B | freeze | 1 | 3 | 400/400 | 0,006013 | 0,006013 | aucun | `parity-B-mimo-v2.6-pro-t1-20261105T225302Z` | `5ec521c21527563e` |
| compare | A-programme | freeze | 1 | 5 | 400/400 | 0,046891 | 0,046891 | aucun | `compare-A-program-mimo-v2.6-pro-t1-20261105T225332Z` | `512d7440af08d1eb` |
| compare | A-littéral | freeze | 2 | 8 | 400/400 | 0,059490 | 0,059490 | aucun | `compare-A-literal-mimo-v2.6-pro-t1-20261105T230436Z` | `b8c0b46c55780bcb` |
| compare | B | freeze | 1 | 3 | 400/400 | 0,005740 | 0,005740 | aucun | `compare-B-mimo-v2.6-pro-t1-20261105T231047Z` | `c0ef47f797230495` |
| automaton | A-programme | freeze | 1 | 6 | 400/400 | 0,084940 | 0,084940 | aucun | `automaton-A-program-mimo-v2.6-pro-t1-20261105T231059Z` | `c59dc680ec733f90` |
| automaton | A-littéral | freeze | 1 | 9 | 400/400 | 0,017368 | 0,017368 | aucun | `automaton-A-literal-mimo-v2.6-pro-t1-20261105T233158Z` | `e0287d0328f3ebaf` |
| automaton | B | freeze | 0 | 2 | 400/400 | 0,003612 | 0,003612 | aucun | `automaton-B-mimo-v2.6-pro-t1-20261105T233435Z` | `36722b1043d60c4c` |

Séance perdue par le harnais, rejouée (AD-14) : `parity-A-programme-...-20261105T224224Z`, fin `pass_budget` à tort, 1 tour, 0,017349 $ (inclus dans le total). Total facturé des séances de 1-8 : **0,281485 $** (9 gelées 0,264136 + 0,017349) ; le registre cumule 0,289952 $ avec les trois lignes de 1-2 et 1-6. Plafond de la nuit (3,00 $) très loin. Empreintes complètes : événement `freeze` de chaque `runs/1/<séance>/journal.jsonl` (non commité) ; le script ci-dessus les réimprime. Réservation de séance de 5 $ à l'ouverture, levée à la clôture (aucun dépassement du plafond de lot).

Autres relevés : l'automate A-programme a pris 21 min (un seul appel long), les autres séances 1 à 11 min. Cache chez Xiaomi vérifié (report de 1-6) : `cache_read_tokens` non nul dès le 2e appel (7 040 puis 16 384 ... sur compare A-littéral). Refus du harnais en séance : 12 `invalid_manifest` (clés de couche, activation `linear` inconnue) et 3 `no_network_declared`, tous corrigés par le modèle avant gel.

## Défaut du harnais trouvé (1)

Première séance (parité, A-programme) : le fournisseur a coupé la réponse à `max_tokens = 16000` (`stop_reason: length`) avec un contenu visible vide (MiMo raisonne, le raisonnement n'est pas rendu). Le pilote API l'a prise pour un agent qui rend la main : fin `pass_budget`, 0 passe. Correctif `b85cd7e` : une réponse sans appel d'outil coupée par `max_tokens` (`length` ou `max_tokens`) termine en `error` avec le détail `réponse tronquée (...) à N jetons` (test `test_truncated_answer_is_error_not_pass_budget`), et `max_tokens` de MiMo passe de 16000 à 64000 dans `config/models.toml` (hors protocole). Séance rejouée avec succès. Aucune autre séance tronquée ; le plus long appel (automate, A-programme) a produit 55 349 jetons de sortie, 86 % du plafond de 64000.

## Décision à confirmer par Anaël : plafond `max_tokens` du pilote API

L'orchestrateur voulait un plafond technique identique pour tous les modèles du pilote API (AD-15, comparabilité), à 64000 si chacun l'admet. Le dépôt ne documente que MiMo à 64000 (admis par Xiaomi, 9 séances, appels jusqu'à 1185 s). Pour `sonnet-5.5-api` et `fable-5.1-api` (Anthropic), la limite de sortie n'est écrite nulle part dans le dépôt, et le fournisseur Anthropic appelle `messages.create` sans flux avec un délai de 600 s, que des appels à 64000 jetons dépasseraient (MiMo : 634 et 1185 s). Décision : MiMo à 64000 (motif : réponse tronquée en raisonnement), Sonnet et Fable API restent à 16000, plus haute valeur sûre connue ; l'écart est noté dans `config/models.toml`. À confirmer : limites de sortie de Sonnet 5.5 et Fable 5.1, et passage au flux du fournisseur Anthropic, avant d'aligner les trois à 64000. Ces deux modèles ne servent ici qu'en repli du pilote Claude Code, dont le plafond est celui de `claude -p`. Le journal `open` ne porte pas `max_tokens` (seulement `sampling` et `effort`) : le plafond d'une séance se lit dans `config/models.toml` à son commit.

## Étanchéité des paquets

Les dix `runs/1/*/bundle/` ne contiennent que `task.json` (clés `description`, `encoder`, `task`, `vocabulary`) et `examples.jsonl`, identique octet pour octet à `data/<tâche>/toy/examples.jsonl` ; aucune ligne commune avec `heldout/<tâche>/toy/`, aucun `labels.jsonl` réservé.

## Observations pour le recalibrage (sans recalibrer)

- Sur MiMo, le jouet est résolu sans effort : 9 cases sur 9 à 100 % sur le réservé, 0 à 2 passes utilisées sur 20, 2 à 9 tours. Le budget de 20 passes ne contraint aucune case, et aucune séance n'a fini en `pass_budget`, `turn_limit` ou `money_budget` ; le jouet ne départage donc pas des budgets de 5 à 20 passes.
- Le maximum observé est de 2 passes. Si la moitié Sonnet reste dans la même plage, le jouet suggère un budget plus bas (de l'ordre de 5 à 10) sans perte, mais il ne dit rien de la tâche S, bien plus dure : fixer un budget sur la seule marge du jouet risque de le sous-dimensionner pour S. À arbitrer avec les séances Sonnet.
- Le coût est négligeable (0,003 à 0,085 $ par séance) ; la porte des 2 $ de 1-10 ne se jouera pas sur MiMo.
- `nnww evaluate` ne donnant pas l'exactitude, elle vient de `scripts/exactitude_reserve.py` (vérification d'empreinte d'abord) en attendant la commande de 1-14.

## Ce qui reste

- Moitié Sonnet (pilote Claude Code, abonnement) : 9 séances, connexion d'Anaël à faire.
- Recalibrage unique du budget de passes, avec les deux modèles, consigné comme décision avant 1-9. `config/protocol.toml` n'a pas été touché.
- Cases perdues par défaut du harnais : aucune en suspens.
