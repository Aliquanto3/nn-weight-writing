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
- Correctif `c33d367` : `api_driver.py` (réponse tronquée = `error`), `config/models.toml` (`max_tokens` de MiMo à 64000), test.

## Décisions

- D1 Graine 0 pour les jeux (`--n 256 --n-heldout 400`) et les séances, comme les mesures de 1-7.
- D2 Exactitude mesurée hors séance par un script jetable (non commité) sur `heldout/` : `nnww evaluate` ne rend pas l'exactitude (1-14).
- D3 `protocol.toml` et le prompt système inchangés ; `max_tokens` est une configuration de modèle.

## Résultats

9 séances gelées sur 9, 400/400 sur le réservé, 0 à 2 passes sur 20, 0,264 $ facturés (0,281 $ avec la séance perdue), aucun drapeau d'audit. Total du registre : 0,289952 $.

## Reports

- Séances Sonnet (connexion d'Anaël) et recalibrage unique du budget de passes, à consigner avant 1-9.
- Commande qui rend l'exactitude sur le réservé : 1-14.
