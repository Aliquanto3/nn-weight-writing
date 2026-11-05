---
story: "1-2"
title: Vérifier MiMo-V2.6-Pro via OpenRouter
status: review
branch: feat/1-2-sonde-mimo
---

# Story 1-2 : Vérifier MiMo-V2.6-Pro via OpenRouter

## Objet

Établir l'identifiant, le prix, les outils et la vision de MiMo-V2.6-Pro sur OpenRouter, et comparer chat completions à l'endpoint compatible Anthropic (CAP-1, AD-10, AD-11).

## Livrables

- `src/nn_weight_writing/providers/probe.py` : sonde (`uv run python -m nn_weight_writing.providers.probe`, `--models-only` gratuit). Fonctions pures de lecture de `/models` et de `usage` séparées du réseau (`urllib`, aucune dépendance ajoutée).
- `tests/test_probe.py` : tests hors ligne, dont l'absence de la clé dans la sortie.
- `docs/verifications/1-2-mimo-openrouter.md` : verdict **conforme avec réserves**, `xiaomi/mimo-v2.6-pro`, recommandation de garder chat completions pour 1-6.

## Critères d'acceptation

- Étant donné `/models`, quand on lit l'entrée `xiaomi/mimo-v2.6-pro`, alors prix, outils, vision et endpoints sont extraits (testé sur JSON figé).
- Étant donné un `usage` sans `cost` ou sans détails, quand on le lit, alors les champs valent 0 et `cost` vaut `None`.
- Étant donné une clé posée dans l'environnement, quand la sonde imprime son résumé, alors la clé n'y figure pas.

## Coût

Sonde réelle : 0,00451347 USD facturés (7 appels), à reporter au registre par 1-6 (ligne `closed`, session `probe-1-2`).

## Reports

- Écriture de cache non observée (toujours 0) ; à revérifier par 1-6.
- Vision par `/messages`, `parallel_tool_calls`, `reasoning` et fournisseur sous-jacent non sondés.
- Le registre `budget/ledger.csv` n'existe pas encore : l'écriture de la ligne `probe-1-2` revient à 1-6.
