# Vérification 1-2 : MiMo-V2.6-Pro via OpenRouter

**Verdict : conforme avec réserves.** MiMo-V2.6-Pro est disponible, appelle des outils et accepte les images sur les deux API. Les réserves : les deux API comptent les jetons d'entrée différemment, et `cache_write_tokens` reste à 0 (voir Reports).

Date de la sonde : 2026-11-05. Script : `uv run python -m nn_weight_writing.providers.probe` (`--models-only` pour la partie gratuite).

## Identifiant et prix

- Identifiant exact : `xiaomi/mimo-v2.6-pro` (slug daté `xiaomi/mimo-v2.6-pro-20260921`, contexte 1 050 000). À ne pas confondre avec `xiaomi/mimo-v2.6-pro-ultraspeed` (prix d'entrée et de sortie ×10), `xiaomi/mimo-v2.6-flash` ni `xiaomi/mimo-v2.5-pro` (texte seul).
- Prix relevés dans `GET /api/v1/models` le 2026-11-05, en USD par million de jetons :

| Entrée | Sortie | Lecture du cache | Écriture du cache |
|---|---|---|---|
| 0,435 | 0,87 | 0,0036 | non annoncée (`input_cache_write` absent) |

## Outils et vision

- Outils : `tools` et `tool_choice` dans `supported_parameters`. Sonde : l'appel d'outil `add(17, 25)` puis son retour donnent la réponse 42, sur les deux API. `parallel_tool_calls` n'est pas annoncé pour ce modèle (il l'est pour Flash).
- Vision : `image` dans les modalités d'entrée (aussi vidéo et audio). Sonde : un PNG 16×16 rouge, passé en `image_url` data-URI par chat completions, est décrit comme rouge (30 jetons d'entrée). Vision non testée par `/messages`.

## Comparaison des deux API

Les deux sont annoncées par le modèle (`endpoints` contient `/api/v1/chat/completions` et `/api/v1/messages`).

| Point | Chat completions | Messages (compatible Anthropic) |
|---|---|---|
| Boucle d'outils | OK (`tool_calls`, rôle `tool`) | OK (`tool_use`, `tool_result`) |
| Jetons d'entrée | `prompt_tokens` **inclut** le cache : 4180 dont 4096 lus | `input_tokens` **exclut** le cache : 85, plus 4096 en `cache_read_input_tokens` |
| Lecture du cache | `prompt_tokens_details.cached_tokens` (4096 au 2e appel, cache automatique) | `cache_read_input_tokens` (4096 au 2e appel, avec `cache_control` sur le système) |
| Écriture du cache | `cache_write_tokens` : 0 | `cache_creation_input_tokens` : 0 |
| `usage.cost` | présent partout (avec `usage: {include: true}` côté chat) | présent partout |
| Coût d'un appel de 4 k jetons, 1er puis 2e | 0,001376 puis 0,000061 USD | 0,001376 puis 0,000058 USD |

Le coût facturé est le même à quelques millionièmes de dollar près.

**Recommandation pour l'adaptateur `openrouter` de 1-6 :** garder chat completions (SDK `openai`, `base_url`), comme prévu par AD-10. Rien dans la sonde ne justifie l'endpoint Messages : mêmes capacités, même coût, et l'adaptateur `anthropic` couvre déjà ce format. L'adaptateur normalise ainsi : `input = prompt_tokens - cached_tokens - cache_write_tokens`, `cache_read = cached_tokens`, `cache_write = cache_write_tokens` (à confirmer par 1-6 sur un cas où l'écriture est non nulle), `provider_cost = usage.cost` (le demander avec `usage: {include: true}`; si absent, `None`).

## Coût de la sonde

Total facturé (somme des `usage.cost` des 7 appels) : **0,00451347 USD**, sous le plafond de 0,50 USD. Aucun appel sans coût. À reporter au registre `budget/ledger.csv` par 1-6 : ligne `closed`, session `probe-1-2`, `billed_usd` = 0.00451347.

## Reports

- `cache_write_tokens` et `cache_creation_input_tokens` n'ont jamais été non nuls : le cache de MiMo est automatique et sans tarif d'écriture annoncé. Si le tarif d'écriture existe pour d'autres fournisseurs de ce modèle, 1-6 le vérifie à la première séance réelle.
- Le routage OpenRouter peut changer de fournisseur sous-jacent : l'identifiant du fournisseur n'est pas relevé ici.
- Vision par `/messages`, `parallel_tool_calls` et le comportement de `reasoning` ne sont pas sondés.
- Piège : envoyer l'en-tête `anthropic-version` sur `GET /models` renvoie la liste au format Anthropic (identifiants préfixés `anthropic/`). La sonde ne l'envoie que sur `/messages`.
