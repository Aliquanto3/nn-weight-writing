# Story 1-8 (partie MiMo) : séances sur le jouet

Date : 2026-11-05 (séances 22:42 à 23:35 UTC). Lot 1, 1 tentative par case, pilote API, OpenRouter, fournisseur Xiaomi (`served_by` vérifié), modèle `xiaomi/mimo-v2.6-pro` (`mimo-v2.6-pro`). Protocole inchangé : `pass_budget = 20`, `turn_limit = 200`, prompt système de 1-6. Seule la configuration `max_tokens` de MiMo a changé (16000 puis 64000, voir défauts).

## Graines et versions

- Jeux : `nnww datagen all --seed 0 --n 256 --n-heldout 400` (générateur v2) ; séances : `--seed 0`, tentative 1 ; jeux `data/<tâche>/toy/` (256 exemples) et `heldout/<tâche>/toy/` (400 exemples), non commités.
- Code : worktree `exp/1-8-jouet-mimo` sur `main` 1e62860 + correctif `c33d367`. Python 3.14, dépendances de `uv.lock`.

## Résultats (9 cases)

Exactitude sur le réservé (400 exemples), mesurée hors séance : `nnww evaluate` (commande séparée) ne produit pas l'exactitude (renvoyée en 1-14) ; elle vient de `score_frozen` (A) et de l'exécution des `rules.py` gelées par `sandbox.run` profil B. Coût facturé = équivalent API (pas d'abonnement). Drapeaux d'audit : aucun (`flags` vide dans les 9 événements `script_run`).

| Tâche | Méthode | Statut | Passes /20 | Tours | Exactitude | Facturé ($) | Équivalent API ($) | Drapeaux |
|---|---|---|---|---|---|---|---|---|
| parity | A-programme | freeze | 1 | 9 | 400/400 | 0,015622 | 0,015622 | aucun |
| parity | A-littéral | freeze | 1 | 9 | 400/400 | 0,024460 | 0,024460 | aucun |
| parity | B | freeze | 1 | 3 | 400/400 | 0,006013 | 0,006013 | aucun |
| compare | A-programme | freeze | 1 | 5 | 400/400 | 0,046891 | 0,046891 | aucun |
| compare | A-littéral | freeze | 2 | 8 | 400/400 | 0,059490 | 0,059490 | aucun |
| compare | B | freeze | 1 | 3 | 400/400 | 0,005740 | 0,005740 | aucun |
| automaton | A-programme | freeze | 1 | 6 | 400/400 | 0,084940 | 0,084940 | aucun |
| automaton | A-littéral | freeze | 1 | 9 | 400/400 | 0,017368 | 0,017368 | aucun |
| automaton | B | freeze | 0 | 2 | 400/400 | 0,003612 | 0,003612 | aucun |

Séance perdue par le harnais, rejouée (AD-14) : `parity-A-programme-...-20261105T224224Z`, fin `pass_budget` à tort, 1 tour, 0,017349 $ (inclus dans le total). Total facturé des séances de 1-8 : **0,281485 $** (9 gelées 0,264136 + 0,017349) ; le registre cumule 0,289952 $ avec les trois lignes de 1-2 et 1-6. Plafond de la nuit (3,00 $) très loin. Réservation de séance de 5 $ à l'ouverture, levée à la clôture (aucun dépassement du plafond de lot).

Autres relevés : l'automate A-programme a pris 21 min (un seul appel long), les autres séances 1 à 11 min. Cache chez Xiaomi vérifié (report de 1-6) : `cache_read_tokens` non nul dès le 2e appel (7 040 puis 16 384 ... sur compare A-littéral). Refus du harnais en séance : 12 `invalid_manifest` (clés de couche, activation `linear` inconnue) et 3 `no_network_declared`, tous corrigés par le modèle avant gel.

## Défaut du harnais trouvé (1)

Première séance (parité, A-programme) : le fournisseur a coupé la réponse à `max_tokens = 16000` (`stop_reason: length`) avec un contenu visible vide (MiMo raisonne, le raisonnement n'est pas rendu). Le pilote API l'a prise pour un agent qui rend la main : fin `pass_budget`, 0 passe. Correctif `c33d367` : une réponse sans appel d'outil coupée par `max_tokens` (`length` ou `max_tokens`) termine en `error` avec le détail `réponse tronquée (...) à N jetons` (test `test_truncated_answer_is_error_not_pass_budget`), et `max_tokens` de MiMo passe de 16000 à 64000 dans `config/models.toml` (hors protocole). Séance rejouée avec succès. Aucune autre séance tronquée.

## Observations pour le recalibrage (sans recalibrer)

- Sur MiMo, le jouet est résolu sans effort : 9 cases sur 9 à 100 % sur le réservé, 0 à 2 passes utilisées sur 20, 2 à 9 tours. Le budget de 20 passes ne contraint aucune case, et aucune séance n'a fini en `pass_budget`, `turn_limit` ou `money_budget` ; le jouet ne départage donc pas des budgets de 5 à 20 passes.
- Le maximum observé est de 2 passes. Si la moitié Sonnet reste dans la même plage, le jouet suggère un budget plus bas (de l'ordre de 5 à 10) sans perte, mais il ne dit rien de la tâche S, bien plus dure : fixer un budget sur la seule marge du jouet risque de le sous-dimensionner pour S. À arbitrer avec les séances Sonnet.
- Le coût est négligeable (0,003 à 0,085 $ par séance) ; la porte des 2 $ de 1-10 ne se jouera pas sur MiMo.
- `nnww evaluate` ne donnant pas l'exactitude, la lecture du budget par l'exactitude demande le script de 1-14 ou une commande de plus.

## Ce qui reste

- Moitié Sonnet (pilote Claude Code, abonnement) : 9 séances, connexion d'Anaël à faire.
- Recalibrage unique du budget de passes, avec les deux modèles, consigné comme décision avant 1-9. `config/protocol.toml` n'a pas été touché.
- Cases perdues par défaut du harnais : aucune en suspens.
