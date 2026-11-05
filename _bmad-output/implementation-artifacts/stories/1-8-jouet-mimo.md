---
story: "1-8"
title: Séances sur le jouet et calibrage du budget de passes (partie MiMo)
status: review
branch: exp/1-8-jouet-mimo
---

# Story 1-8 (partie MiMo) : séances sur le jouet

## Objet

Séances A-programme, A-littéral et B de MiMo-V2.6-Pro (pilote API, OpenRouter) sur les trois tâches jouet, 1 tentative par case, lot 1. Les séances Sonnet et le recalibrage du budget de passes restent à faire. Relevés complets : `docs/experiences/1-8-jouet-mimo.md`.

## Livrables

- `docs/experiences/1-8-jouet-mimo.md` (tableau des 9 cases, graines, défaut, observations).
- `budget/ledger.csv` écrit par le harnais.
- Correctif `b85cd7e` (`c33d367` avant rebase) : `api_driver.py` (réponse tronquée = `error`), `config/models.toml` (`max_tokens` de MiMo à 64000), test.

## Décisions

- D1 Graine 0 pour les jeux (`--n 256 --n-heldout 400`) et les séances, comme les mesures de 1-7.
- D2 Exactitude mesurée hors séance, après gel, par `scripts/exactitude_reserve.py` (ajouté en revue) : `verify_frozen` d'abord, `heldout/` ensuite ; `nnww evaluate` ne rend pas l'exactitude (1-14).
- D3 `protocol.toml` et le prompt système inchangés ; `max_tokens` est une configuration de modèle.
- D4 (à confirmer par Anaël) Plafond `max_tokens` du pilote API : l'orchestrateur voulait 64000 pour tous (comparabilité AD-15) si chacun l'admet. MiMo à 64000 (motif : réponse tronquée en raisonnement à 16000 ; plus long appel 55 349 jetons). `sonnet-5.5-api` et `fable-5.1-api` restent à 16000, plus haute valeur sûre connue : leur limite de sortie n'est pas documentée dans le dépôt, et le fournisseur Anthropic appelle sans flux avec un délai de 600 s, que MiMo a dépassé à 64000 (634 et 1185 s). Alignement à 64000 après confirmation des limites et passage au flux. Détail : compte rendu, section « Décision à confirmer ».

## Résultats

9 séances gelées sur 9, 400/400 sur le réservé, 0 à 2 passes sur 20, 0,264 $ facturés (0,281 $ avec la séance perdue), aucun drapeau d'audit. Total du registre : 0,289952 $.

## Reports

- Séances Sonnet (connexion d'Anaël) et recalibrage unique du budget de passes, à consigner avant 1-9.
- Commande qui rend l'exactitude sur le réservé : 1-14.

## Revue

### Passe 1 (2026-11-06, SHA revu 6caa74a)

Rebase sur `origin/main` 1110500 (état du run seulement), sans conflit.

- Important · medium · second avis 1 · corrigé : exactitude « après gel » sans empreinte ni méthode reproductible. Ajout de `scripts/exactitude_reserve.py` (vérifie `frozen/` contre le journal avant de lire `heldout/`), rejoué : 400/400 sur les 9 gels, séance perdue refusée avant lecture ; tableau complété par séance et `tree_sha256`.
- Important · medium · second avis 2 · corrigé (décision D4, à confirmer) : `max_tokens` différent selon le modèle. 64000 non vérifiable pour Sonnet et Fable API dans le dépôt, et risqué sans flux (délai 600 s) ; MiMo 64000, Anthropic 16000, consigné dans la spec, le compte rendu et `config/models.toml`.
- Nit · low · second avis 3 · corrigé : la ligne `closed` est bien écrite sur le chemin `error` (bloc `finally` de `session/run.py`, et le registre réel la porte pour la séance perdue) ; assertion ajoutée à `test_truncated_answer_is_error_not_pass_budget`.
- Nit · low · second avis 4 · corrigé : paquets vérifiés (`task.json` et `examples.jsonl` = `data/`, aucune ligne du réservé) ; phrase ajoutée au compte rendu.
- Nit · low · revue · corrigé : le SHA du correctif cité (`c33d367`) n'existait plus après rebase ; remplacé par `b85cd7e`.
- Pre-existing · low · revue · reporté : l'événement `open` ne journalise pas `max_tokens` (AD-10 « paramètres d'échantillonnage ») ; la séance perdue (16000) et sa reprise (64000) ont le même `open`. À ajouter au schéma `open` dans une story du harnais.
- Nit · low · revue · reporté : une réponse coupée par `max_tokens` qui porte des appels d'outil (arguments JSON tronqués) n'est pas traitée en `error` ; elle passe par le refus de décodage des arguments. Aucun cas observé.
- Complexité : 0 constat.
