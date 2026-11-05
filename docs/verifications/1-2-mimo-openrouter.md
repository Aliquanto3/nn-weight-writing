# Vérification 1-2 : MiMo-V2.6-Pro via OpenRouter

**Verdict : conforme avec réserves.** MiMo-V2.6-Pro est disponible, appelle des outils et accepte les images sur les deux API. Les réserves : les deux API comptent les jetons d'entrée différemment, le routage OpenRouter change de fournisseur d'un appel à l'autre (prix et cache différents), et `cache_write_tokens` reste à 0 (voir Reports).

Date de la sonde : 2026-11-05. Script : `uv run python -m nn_weight_writing.providers.probe` (`--models-only` pour la partie gratuite). Sortie du second passage (revue), sans clé : `docs/verifications/1-2-sonde-2026-11-05.json`.

## Identifiant et prix

- Identifiant exact : `xiaomi/mimo-v2.6-pro` (slug daté `xiaomi/mimo-v2.6-pro-20260921`, contexte 1 050 000). À ne pas confondre avec `xiaomi/mimo-v2.6-pro-ultraspeed` (prix d'entrée et de sortie ×10), `xiaomi/mimo-v2.6-flash` ni `xiaomi/mimo-v2.5-pro` (texte seul).
- Prix catalogue relevés dans `GET /api/v1/models` le 2026-11-05 (ce sont ceux du fournisseur Xiaomi), en USD par million de jetons :

| Entrée | Sortie | Lecture du cache | Écriture du cache |
|---|---|---|---|
| 0,435 | 0,87 | 0,0036 | non annoncée (`input_cache_write` absent) |

- Prix par fournisseur (`GET /api/v1/models/xiaomi/mimo-v2.6-pro/endpoints`, même jour), entrée / sortie / lecture du cache : GMICloud bf16 0,32625 / 0,6525 / 0,003 (remise 25 %), DeepInfra fp8 0,387 / 0,783 / 0,00324 (remise 10 %), Xiaomi fp8 0,435 / 0,87 / 0,0036, StreamLake 0,522 / 1,044 / 0,00432, PrimaLabs fp8 4 / 8 / 0,036.

## Outils et vision

- Outils : `tools` et `tool_choice` dans `supported_parameters`. Sonde : l'appel d'outil `add(17, 25)` puis son retour donnent la réponse 42, sur les deux API. `parallel_tool_calls` n'est pas annoncé pour ce modèle (il l'est pour Flash).
- Vision : `image` dans les modalités d'entrée (aussi vidéo et audio). Sonde : un PNG 16×16 rouge, passé en `image_url` data-URI par chat completions, est décrit comme rouge (30 jetons d'entrée). Vision non testée par `/messages`.

## Comparaison des deux API

Les deux sont annoncées par le modèle (`endpoints` contient `/api/v1/chat/completions` et `/api/v1/messages`).

| Point | Chat completions | Messages (compatible Anthropic) |
|---|---|---|
| Boucle d'outils | OK (`tool_calls`, rôle `tool`) | OK (`tool_use`, `tool_result`) |
| Jetons d'entrée | `prompt_tokens` **inclut** le cache (premier passage : 4180 dont 4096 lus) ; la sonde le normalise en `input` hors cache | `input_tokens` **exclut** le cache : 85, plus 4096 en `cache_read_input_tokens` |
| Lecture du cache | `prompt_tokens_details.cached_tokens` (4096 au 2e appel, cache automatique) | `cache_read_input_tokens` (4096 au 2e appel, avec `cache_control` sur le système) |
| Écriture du cache | `cache_write_tokens` : 0 | `cache_creation_input_tokens` : 0 |
| `usage.cost` | présent partout (avec `usage: {include: true}` côté chat) | présent partout |
| Coût de l'aller-retour d'outil (second passage), 1er puis 2e appel | 0,00183396 (Xiaomi, sans cache) puis 0,00005013 USD (GMICloud, 4096 lus) | 0,00161986 (DeepInfra, sans cache) puis 0,00004622 USD (GMICloud, 4096 lus) |

À fournisseur égal, le coût facturé ne dépend pas de l'API. **Écart avec le prix catalogue, expliqué :** `usage.cost` est le nombre de jetons au tarif du fournisseur que le routage a choisi, pas au tarif de `/models`. Vérifié à l'unité près : 4126 × 0,435 + 45 × 0,87 = 1833,96 µUSD (Xiaomi) et 4127 × 0,387 + 29 × 0,783 = 1619,856 µUSD (DeepInfra). Le 0,001376 USD du premier passage correspond au tarif GMICloud (4180 × 0,32625 ≈ 1363,7 µUSD, plus la sortie).

**Recommandation pour l'adaptateur `openrouter` de 1-6 :** garder chat completions (SDK `openai`, `base_url`), comme prévu par AD-10. Rien dans la sonde ne justifie l'endpoint Messages : mêmes capacités, même coût à fournisseur égal, et l'adaptateur `anthropic` couvre déjà ce format (constat fondé sur deux allers-retours d'outil par API, pas sur une séance longue). Fixer le fournisseur (`provider: {order: [...], allow_fallbacks: false}` dans le corps de la requête) : sans cela, le cache se perd quand le routage change de fournisseur (second passage : 4096 jetons lus chez GMICloud, 0 chez Xiaomi et DeepInfra au premier appel) et le prix varie de 0,326 à 4 USD/Mtok en entrée. À vérifier par 1-6. L'adaptateur normalise ainsi : `input = prompt_tokens - cached_tokens - cache_write_tokens`, `cache_read = cached_tokens`, `cache_write = cache_write_tokens` (à confirmer par 1-6 sur un cas où l'écriture est non nulle), `provider_cost = usage.cost` (le demander avec `usage: {include: true}`; si absent, `None`).

## Coût de la sonde

La sonde fait 6 appels payants (texte, outil aller et retour, vision, outil aller et retour par Messages), plus `GET /models` gratuit.

| Passage | Appels payants | `usage.cost` cumulé |
|---|---|---|
| Premier (développement) | 6 selon le code ; le constat initial disait 7, sortie non conservée, non vérifiable | 0,00451347 USD |
| Second (revue, sortie conservée) | 6, tous avec `usage.cost` | 0,00364862 USD |
| **Total** | 12 | **0,00816209 USD** |

Sous le plafond de 0,50 USD. À reporter au registre `budget/ledger.csv` par 1-6 : ligne `closed`, session `probe-1-2`, `billed_usd` = 0.00816209.

## Reports

- `cache_write_tokens` et `cache_creation_input_tokens` n'ont jamais été non nuls : le cache de MiMo est automatique et sans tarif d'écriture annoncé. Si le tarif d'écriture existe pour d'autres fournisseurs de ce modèle, 1-6 le vérifie à la première séance réelle.
- Le routage OpenRouter change de fournisseur sous-jacent d'un appel à l'autre (relevé dans le champ `provider` de chaque réponse) : épinglage à vérifier par 1-6.
- Vision par `/messages`, `parallel_tool_calls` et le comportement de `reasoning` ne sont pas sondés.
- Le compteur `usage` de `GET /api/v1/key` n'a augmenté que de 0,00192 USD juste après le second passage (0,00365 USD de `usage.cost`) : décalage de mise à jour probable, non vérifié.
- Piège : envoyer l'en-tête `anthropic-version` sur `GET /models` renvoie la liste au format Anthropic (identifiants préfixés `anthropic/`). La sonde ne l'envoie que sur `/messages`.
