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
- `docs/verifications/1-2-sonde-2026-11-05.json` : sortie du second passage de la sonde, sans clé.
- `docs/verifications/1-2-mimo-openrouter.md` : verdict **conforme avec réserves**, `xiaomi/mimo-v2.6-pro`, recommandation de garder chat completions pour 1-6.

## Critères d'acceptation

- Étant donné `/models`, quand on lit l'entrée `xiaomi/mimo-v2.6-pro`, alors prix, outils, vision et endpoints sont extraits (testé sur JSON figé).
- Étant donné un `usage` sans `cost` ou sans détails, quand on le lit, alors les champs valent 0 et `cost` vaut `None`.
- Étant donné une clé posée dans l'environnement, quand la sonde imprime son résumé, alors la clé n'y figure pas.

## Coût

Sonde réelle, deux passages de 6 appels payants (développement, puis revue) : 0,00451347 + 0,00364862 = **0,00816209 USD** facturés, à reporter au registre par 1-6 (ligne `closed`, session `probe-1-2`).

## Reports

- Écriture de cache non observée (toujours 0) ; à revérifier par 1-6.
- Vision par `/messages`, `parallel_tool_calls` et `reasoning` non sondés ; fournisseur sous-jacent relevé par appel (champ `provider`), son épinglage reste à vérifier par 1-6.
- Le registre `budget/ledger.csv` n'existe pas encore : l'écriture de la ligne `probe-1-2` revient à 1-6.

## Revue

### Passe 1 (2026-11-05, SHA revu 7f61638)

Base : `main` à jour (00f3622). Constats du second avis (Haiku) repris un par un.

- Important · medium · second avis 1 · corrigé : `/models` en échec ou modèle absent lançait quand même les appels payants et sortait en 0. `main` s'arrête avant tout appel payant et sort en 1 (aussi sans clé). Test `test_main_models_failure_makes_no_paid_call`.
- Important · medium · second avis 2 · corrigé : `input` de chat completions incluait le cache, celui de Messages non. `parse_chat_usage` renvoie `input = prompt_tokens - cached_tokens - cache_write_tokens` (borné à 0), sémantique de `Usage` de AD-10. Test d'équivalence des deux API sur la même requête.
- Important · medium · second avis 3 · corrigé : écart prix catalogue / `usage.cost` expliqué par le routage (tarif du fournisseur choisi, vérifié à l'unité sur deux appels) ; sortie de la sonde conservée (`docs/verifications/1-2-sonde-2026-11-05.json`, sans clé) ; champ `provider` relevé par appel. Une sonde réelle relancée (0,00364862 USD).
- Important · medium · second avis 4 · corrigé : le code fait 6 appels payants ; « 7 » du premier passage non vérifiable (sortie non conservée), dit tel quel. Coût total recalculé : 0,00816209 USD. Champ `paid_calls` ajouté.
- Important · medium · second avis 5 · corrigé : boucles d'outils, `answer_has_42`, `calls_without_cost`, `budget_ok` testés hors ligne par une doublure de la frontière HTTP (`request` injectable) qui vérifie les corps renvoyés (`tool_call_id`, `tool_result`, somme 42), plus les chemins sans appel d'outil et en erreur HTTP.
- Nit · low · second avis 6 · corrigé (texte) : recommandation fondée sur deux allers-retours par API, dit dans le constat ; ajout de l'épinglage du fournisseur, découvert à la revue.
- Nit · low · second avis 7 · rejeté : `budget_ok` a posteriori suffit, le pire cas est borné (6 appels, `max_tokens` 1500, 0,02 USD au tarif Xiaomi, 0,18 USD chez PrimaLabs, le plus cher), dit dans la docstring.
- Nit · low · second avis 8 · corrigé : sortie JSON en ASCII (`ensure_ascii` par défaut), plus d'erreur d'encodage possible sous cp1252.
- Nit · low · second avis 9 · corrigé : détection par mot entier (`mentions_word`) : `hundred` ne compte plus pour `red`, ni `1420` pour `42`.
- Complexité : 0 constat (aucune structure qui grossit pendant l'exécution au-delà de 6 appels).

### Passe 2 (2026-11-05, SHA revu 04d35b2)

Base : rebasée sur `origin/main` (3a3b2d3, PR de docs 1-1), sans conflit. Relu : correctifs de la passe 1 (7f61638..825fded).

- Correctifs de la passe 1 confirmés : normalisation `input = prompt_tokens - cached_tokens - cache_write_tokens` conforme à `Usage` de AD-10 (même sens que `input_tokens` de Messages), tests à valeurs exactes ; arrêt sans appel payant vérifié ; somme des 6 `cost` du JSON = 0,00364862, total 0,00816209 et calculs à l'unité (1833,96 et 1619,856 µUSD) exacts ; aucune clé dans le JSON ni l'historique ; `pyproject.toml` et `uv.lock` intacts ; aucun appel réseau dans les tests.
- Nit · low · revue · corrigé : une coupure réseau ou un délai (`URLError`, `TimeoutError`) en cours de sonde levait une exception et perdait le résumé des appels déjà facturés ; `_request` les rend en entrée `_error` (corps expurgé). Test `test_request_network_error_becomes_error_entry`.
- Nit · low · revue · corrigé : Reports et Livrables de la story réalignés (fournisseur désormais relevé, JSON de sortie listé).
- Complexité : 0 constat.
