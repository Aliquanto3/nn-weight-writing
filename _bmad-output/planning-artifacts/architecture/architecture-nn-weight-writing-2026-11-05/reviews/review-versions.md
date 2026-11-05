# Revue factuelle : versions, OpenRouter, SDK Anthropic, Python 3.14, git

Date de la revue : 2026-11-05. Lecture seule du spine (`ARCHITECTURE-SPINE.md`) ; seul ce fichier a été écrit.
Méthode : `curl https://pypi.org/pypi/<paquet>/json` pour les versions et les fichiers ; documentation officielle (docs.python.org, git-scm.com, openrouter.ai) lue en ligne ; code du SDK `anthropic` 2.6.0 extrait du wheel PyPI et lu (rien n'a été exécuté).

Légende : **confirmé** / **infirmé** / **partiel** / **non vérifiable**.

## 1. Stack (versions et roues)

| Affirmation | Verdict | Constat | Source |
| --- | --- | --- | --- |
| numpy 2.5.4 | confirmé | Dernière version publiée sur PyPI. | https://pypi.org/pypi/numpy/json |
| numpy : roue Windows cp314 | confirmé | `numpy-2.5.4-cp314-cp314-win_amd64.whl` (et variante cp314t) présentes. | https://pypi.org/pypi/numpy/2.5.4/json |
| anthropic (SDK) 2.6.0 | confirmé | Dernière version sur PyPI. | https://pypi.org/pypi/anthropic/json |
| openai (SDK) 3.46.0 | confirmé | Dernière version sur PyPI. | https://pypi.org/pypi/openai/json |
| torch 2.15.0 | confirmé | Dernière version sur PyPI. | https://pypi.org/pypi/torch/json |
| torch : roue Windows cp314 (CPU) | confirmé | Sur PyPI : `torch-2.15.0-cp314-cp314-win_amd64.whl` (et cp314t). Sur l'index CPU : `torch-2.15.0+cpu-cp314-cp314-win_amd64.whl`. Remarque : la roue PyPI par défaut peut ne pas être la build CPU ; pour une build CPU stricte, l'index `https://download.pytorch.org/whl/cpu` est la référence. | https://download.pytorch.org/whl/cpu/torch/ |
| uv 0.12.23 « à jour » | **infirmé** | 0.12.23 existe sur PyPI, mais la dernière version est **0.13.7**. Le spine dit « Versions relevées sur PyPI » : la valeur n'est pas la dernière. À corriger ou à reformuler (« version figée au cadrage »). | https://pypi.org/pypi/uv/json ; https://pypi.org/pypi/uv/0.12.23/json |
| pytest 9.2 | confirmé | Dernière version : 9.2.0. | https://pypi.org/pypi/pytest/json |
| ruff 0.17 | confirmé | Dernière version : 0.17.4 (le spine dit « 0.17 », correct en plage ; une précision « 0.17.4 » serait plus nette). | https://pypi.org/pypi/ruff/json |

## 2. OpenRouter

| Affirmation | Verdict | Constat | Source |
| --- | --- | --- | --- |
| Chat completions compatible OpenAI accepte `tools` et renvoie `tool_calls` | confirmé | `POST /api/v1/chat/completions` ; les outils sont imbriqués sous `function` ; le modèle renvoie `tool_calls` sur le message assistant ; les résultats reviennent en `role: "tool"`. Le support dépend du modèle (filtre `supported_parameters=tools`). | https://openrouter.ai/docs/guides/features/tool-calling.md |
| Renvoie `usage.cost` | confirmé | Champ `cost` dans `usage` (exemple chat completions), en crédits, avec `cost_details`. | https://openrouter.ai/docs/guides/guides/usage-accounting.md |
| Renvoie les tokens de cache | confirmé, avec un point de nommage | Les champs sont `prompt_tokens_details.cached_tokens` (lecture) et `prompt_tokens_details.cache_write_tokens` (écriture). Ce ne sont pas les noms Anthropic (`cache_read_input_tokens`, `cache_creation_input_tokens`) : l'adaptateur doit faire la correspondance vers `Usage.cache_read` / `Usage.cache_write`. | https://openrouter.ai/docs/guides/guides/usage-accounting.md ; https://openrouter.ai/docs/guides/features/prompt-caching.md |
| Endpoint officiel compatible Anthropic Messages | confirmé | `POST /api/v1/messages`, « Create a message » au format Anthropic Messages (texte, images, PDF, outils, réflexion étendue). Le spine retient le SDK OpenAI ; cet endpoint est une option à mentionner comme alternative. | https://openrouter.ai/docs/api/api-reference/anthropic-messages/create-a-message.md ; index : https://openrouter.ai/docs/llms.txt |
| `base_url` à confirmer par la sonde | confirmé | URL de base de l'API chat completions : `https://openrouter.ai/api/v1`. | https://openrouter.ai/docs/api/reference/overview.md |

## 3. API Anthropic (SDK Python 2.6.0)

| Affirmation | Verdict | Constat | Source |
| --- | --- | --- | --- |
| `cache_control` existe | confirmé | Paramètre `cache_control` dans `message_create_params.py` ; type `cache_control_ephemeral_param.py` dans le paquet. | Wheel : https://files.pythonhosted.org/packages/38/0b/705a05ab68558914e725cf1143d7e409fa3bb596c35bca1eceab42402abe/anthropic-2.6.0-py3-none-any.whl (fichiers `anthropic/types/`) |
| `cache_read_input_tokens` et `cache_creation_input_tokens` existent | confirmé | Dans `anthropic/types/usage.py` : `cache_creation_input_tokens: Optional[int]` et `cache_read_input_tokens: Optional[int]`. | Même wheel, `anthropic/types/usage.py` |

## 4. Python 3.14

| Affirmation | Verdict | Constat | Source |
| --- | --- | --- | --- |
| `sys.addaudithook` ne peut pas être retiré | confirmé | La documentation décrit seulement l'ajout (la liste des hooks n'a pas d'API de suppression) ; elle précise qu'un code malveillant peut désactiver ou contourner les hooks. Un hook dont l'exception dérive de `RuntimeError` empêche l'ajout d'un autre hook. | https://docs.python.org/3.14/library/sys.html |
| Événement `open` | confirmé | Présent dans la table des événements. | https://docs.python.org/3.14/library/audit_events.html |
| `os.listdir`, `os.scandir` | confirmé | Présents. | Même page |
| `socket.connect` | confirmé | Présent. Le motif `socket.*` du spine n'a pas été vérifié pour les autres événements `socket.`. | Même page |
| `subprocess.Popen` | confirmé | Présent. | Même page |
| `os.system`, `os.exec`, `os.spawn` | confirmé | Présents (familles `os.exec*` et `os.spawn*` selon la table). | Même page |
| `os.startfile` | confirmé | Présent (et `os.startfile/2`). | Même page |
| `ctypes.dlopen` | confirmé | Présent. Le motif `ctypes.*` du spine n'a pas été vérifié pour les autres événements `ctypes.`. | Même page |
| Événement `import` (dans la liste de AD-5) | confirmé | Présent dans la table. | Même page |
| Option `-I` ignore `PYTHON*` et le répertoire du script dans `sys.path` | confirmé | « sys.path contains neither the script's directory nor the user's site-packages directory. All PYTHON* environment variables are ignored, too. » ; `-I` implique `-E`, `-P` et `-s`. | https://docs.python.org/3.14/using/cmdline.html |

Remarque : la mention « un `import os` vers un module déjà chargé ne lève aucun événement d'audit (vérifié sous Python 3.14.6) » n'est pas vérifiable par la documentation ; elle relève d'un test local. Non vérifiée ici.

## 5. `.gitattributes` avec `merge=union`

| Affirmation | Verdict | Constat | Source |
| --- | --- | --- | --- |
| `merge=union` est un pilote de fusion intégré à git | confirmé | `union` est un pilote intégré : fusion à trois voies au niveau fichier pour les fichiers texte, en gardant les lignes des deux versions. Attention pour `budget/ledger.csv` : l'en-tête et l'ordre des lignes peuvent être dupliqués ou mal ordonnés après fusion ; un test du registre serait utile. | https://git-scm.com/docs/gitattributes |

## Bilan

- Confirmés : 26 lignes (stack 8, OpenRouter 5, SDK Anthropic 2, Python 10, git 1). Réserve : pour les motifs `socket.*` et `ctypes.*`, seuls `socket.connect` et `ctypes.dlopen` ont été lus dans la table des événements.
- Infirmés : 1 (uv 0.12.23 n'est pas la dernière version ; la dernière est 0.13.7).
- Non vérifiables : 1 (affirmation de test local « import os sans événement d'audit sous 3.14.6 »).
