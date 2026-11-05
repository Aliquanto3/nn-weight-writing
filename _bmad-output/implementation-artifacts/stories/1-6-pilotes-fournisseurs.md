---
story: "1-6"
title: Pilotes Claude Code et API, fournisseurs, coût et plafond
status: review
branch: feat/1-6-pilotes-fournisseurs
---

# Story 1-6 : Pilotes Claude Code et API, fournisseurs, coût et plafond

## Objet

Port fournisseur avec adaptateurs OpenRouter, Anthropic (repli) et simulé ; pilote API ; pilote Claude Code par `claude -p` et serveur MCP local sur le catalogue de 1-5 ; coût facturé et coût équivalent API par appel ; registre budgétaire, plafonds de lot et de projet sur le facturé, arrêt au plafond de séance (CAP-3 ; AD-10, AD-11, AD-14, AD-15 ; `harnais.md`). Story pivot, transverse.

## Livrables

- Dépendances par `uv add` : `anthropic` 2.6.0, `openai` 3.46.0, `mcp` 2.3.0 (avec `httpx2`, `uvicorn`, `starlette`).
- `config/models.toml` (nom → pilote, fournisseur, identifiant, effort, `max_tokens`, `provider_order`), `config/pricing.toml` (tarifs datés et sourcés), section `[budget]` de `config/protocol.toml` ; lecteurs dans `config.py` (`load_models`, `load_pricing`, `ProtocolConfig.max_session_usd`, `project_cap_usd`, `lot_caps_usd`).
- `providers/types.py` (port `ModelProvider.complete(ChatRequest) -> ChatResponse`, `Usage`), `providers/usage.py` (normalisation de 1-2, déplacée de `probe.py`, qui la réimporte), `providers/openrouter.py`, `providers/anthropic.py`, `providers/fake.py`.
- `budget/cost.py` (seule formule : `cost_equiv_usd`, `billed_usd`), `budget/ledger.py` (seul écrivain `append`, `reserve`, `close`, `read`, `spend`, `reconcile`), `budget/ledger.csv` commité, `merge=union` dans `.gitattributes`, verrou `budget/*.lock` ignoré.
- `session/prompt.py` (prompt système par méthode, description de tâche, empreinte), `session/api_driver.py` (`ApiLoopDriver`), `session/mcp_server.py` (serveur MCP HTTP sur 127.0.0.1), `session/claude_code.py` (`ClaudeCodeDriver`), `session/run.py` (`run_session`), `tasks/registry.py` (registre des tâches, vide jusqu'à 1-7).
- Service de 1-5 étendu : verrou (le serveur MCP appelle depuis un autre fil), `totals`, `end(reason, detail)` ; événement `end` avec `detail` (cause d'une fin). `tools.catalogue(method)`.
- CLI : `nnww session --task --dataset --method --model --attempt --seed --lot` et `nnww ledger reconcile`.
- Tests : `test_api_driver`, `test_claude_code` (faux `claude` : `tests/fake_claude.py`), `test_providers` (vrais SDK, transport `httpx2.MockTransport`), `test_ledger`, `test_cli_session`, `test_config` étendu, `test_live` (3 tests `live`). 437 tests hors `live`, verts.

## Décisions

- D1 Fin `pass_budget` dès que l'agent répond sans appeler d'outil, quelles que soient les passes restantes (AD-6 : « si l'agent rend la main sans geler »). Les deux pilotes se comportent ainsi : `claude -p` s'arrête de lui-même dans ce cas, et le pilote API ne relance pas l'agent (pas de message de relance), ce qui garde le protocole identique. Le prompt système l'annonce.
- D2 Tour = un appel au modèle ; `turn_limit` (200) borne la boucle API et devient `--max-turns` pour Claude Code (résultat `error_max_turns` → `turn_limit`).
- D3 `money_budget` : vérifié après chaque appel, sur le total `billed_usd` de la séance ; le dépassement est donc d'au plus un appel (revue adversaire L-3). Les outils de l'appel qui franchit le plafond ne sont pas exécutés.
- D4 Plafonds : `max_session_usd = 5.0` (proposé, à confirmer par Anaël), `project_cap_usd = 200.0`, lots 1 / 2 / 3 à 100 / 75 / 25 $ (SPEC.md). Validation : somme des lots ≤ projet, plafond de séance ≤ plus petit plafond de lot. Le changement de `protocol.toml` change `protocol_sha256` ; aucune séance mesurée n'existe encore.
- D5 Séance par abonnement : réservation de 0 $ (lignes `reserved` et `closed` écrites quand même, pour la trace) ; la vérification des plafonds ne la bloque pas (AD-11 : la porte ne joue pas sur l'abonnement).
- D6 Registre : colonnes `ts, session_id, lot, status, reserved_usd, billed_usd, cost_equiv_usd`, montants à 6 décimales. Vérification et réservation sous un verrou de fichier (création exclusive, expiration à 120 s) : des séances parallèles se voient (test à 4 fils). Une séance déjà inscrite est refusée. `reconcile` clôt une réservation orpheline depuis les `model_call` de son journal, à 0 $ sans journal (l'événement `open` précède tout appel).
- D7 OpenRouter : fournisseur fixé à `xiaomi` (`provider.order`, `allow_fallbacks: false`), éditeur du modèle, au prix catalogue relevé par 1-2 (0,435 / 0,87 / 0,0036 $ par Mtok). Effort transmis en `reasoning.effort` s'il est configuré (aucun pour MiMo). Cache : `prompt_tokens_details.cached_tokens`, automatique.
- D8 Anthropic : points de cache sur le système, le dernier outil et le dernier bloc de la conversation ; effort en `output_config.effort` (même effort que par Claude Code). Prix des écritures du cache : tarif à 5 minutes.
- D9 Tarifs Anthropic : page officielle non lue dans cette story (pas d'outil web) ; repris du relevé du 2026-10-13 sur `platform.claude.com/docs/en/about-claude/pricing` (mémoire de l'utilisateur `prix-cache-sonnet-haiku`), cohérent avec le `CLAUDE.md` global : Sonnet 5.5 2 / 10 / lecture 0,10 / écriture 2,50 ; Fable 5.1 10 / 50 / 0,25 / 12,50. Source citée dans `pricing.toml`.
- D10 Identifiants Anthropic `claude-sonnet-5-5` et `claude-fable-5-1` : déduits de `claude-opus-5-5`, à confirmer par le test live de Claude Code. Effort `medium` pour les modèles Claude (proposé, à confirmer).
- D11 Pilote Claude Code, en plus de AD-14 : `--allowedTools` limité aux outils MCP du catalogue (sans autorisation, `-p` refuse les appels MCP) et `--disable-slash-commands` (aucune skill ni commande). Environnement : toutes les variables `ANTHROPIC_*`, `CLAUDE*`, `OPENROUTER_*`, `OPENAI_*`, `AWS_BEARER*` retirées (une clé d'API ferait facturer la séance), puis `CLAUDE_CONFIG_DIR`. Le dossier dédié est refusé avant lancement s'il contient `CLAUDE.md`, `plugins`, `skills`, `agents`, `commands`, `output-styles`, `hooks`, `settings.local.json` ou un `settings.json` non vide. L'événement `system/init` du flux est contrôlé : outils hors catalogue (sauf `ListMcpResourcesTool`, `ReadMcpResourceTool`, inoffensifs), autre serveur MCP, skills, commandes ou plugins non intégrés → arrêt `error` (« contamination »).
- D12 Flux `stream-json` : un `model_call` par événement `assistant` ; l'usage d'un même identifiant de message n'est compté qu'une fois (delta par champ), les messages `<synthetic>` (« Not logged in », limite d'usage) ne sont pas des appels. Description de tâche écrite en octets UTF-8 sur l'entrée standard (sans traduction des fins de ligne sous Windows ; défaut trouvé par le test de contamination).
- D13 Limite d'usage : motif `usage limit|limit reached|hit your limit|rate limit|out of extra usage` dans l'erreur de l'API, le résultat ou `terminal_reason`, ou `api_error_status` 429 → `error`, détail `usage_limit : …`. Toute autre erreur (`is_error`, sous-type autre que `success`, processus sans résultat) → `error` avec la cause.
- D14 Serveur MCP : SDK `mcp` 2.3 (`Server` bas niveau, `streamable_http_app`), uvicorn dans un fil, port libre sur 127.0.0.1, chemin aléatoire (`/mcp/<jeton>`), protection DNS rebinding par défaut du SDK. Les appels passent par `anyio.to_thread` vers `ToolService.call`.
- D15 Arguments d'outil non JSON venant d'un pilote (report de 1-5) : le texte brut est transmis au service, qui refuse `invalid_arguments` (« les arguments doivent être un objet ») et journalise `{"invalid": …}` ; la séance continue. Les pilotes ne transmettent que du JSON décodé (report 1-5 sur les valeurs non sérialisables).
- D16 Ligne de la sonde 1-2 au registre : `probe-1-2`, lot 1, `closed`, 0,008162 $ facturés et équivalents (0,00816209 arrondi à 6 décimales).

## Écarts

1. **Structure** : la graine prévoit des dossiers `session/api/` et `session/claude_code/` ; les pilotes sont des modules plats (`api_driver.py`, `claude_code.py`, `mcp_server.py`).
2. **`end.detail`** : champ ajouté à l'événement `end` (cause d'une erreur, précision du motif), facultatif dans le dataclass mais toujours écrit ; un journal antérieur sans ce champ ne se relirait plus (aucun n'existe).
3. **`open.model`** : identifiant du fournisseur (`claude-sonnet-5-5`, `xiaomi/mimo-v2.6-pro`) ; le nom de `models.toml` sert à l'identifiant de séance.
4. **Contrôle de `usage.cost`** : journalisé dans `provider_cost` ; la comparaison avec le calcul tarifaire n'est faite qu'au test live (écart toléré 10 %), pas à chaque appel.
5. **Tâches** : `nnww session` lit `data/<task>/<dataset>/examples.jsonl` et un registre de tâches vide ; les tâches réelles s'inscrivent à partir de 1-7.

## Tests (critères d'acceptation)

- Contamination (faux `claude`) : prompt système = fichier `system_prompt.md` = `system_prompt(method, 20)` ; entrée standard = description de tâche seule, octet pour octet ; répertoire courant vide ; `CLAUDE_CONFIG_DIR` dédié ; aucune variable de clé ni réglage Claude hérité ; `--tools ""`, `--strict-mcp-config`, un seul serveur MCP local ; aucune option qui ajoute du contexte. Init contaminé et dossier non dédié → `error`.
- Identité du catalogue (A-littéral, A-programme, B) : même prompt système, description, outils (nom, description, schéma) et budget de passes pour MiMo (API), Sonnet par l'API et Sonnet par Claude Code (outils lus par le client MCP).
- `billed_usd` à 0 par l'abonnement, `cost_equiv_usd` journalisé aux valeurs exactes ; usage d'un message répété compté une fois.
- Ouverture refusée au-delà du plafond facturé, réservations comprises (message exact) ; plafond de projet ; réservations parallèles.
- Arrêt `money_budget` au 3e appel (0,0036 ≥ 0,003) ; `turn_limit` ; `pass_budget` ; arguments non JSON refusés sans plantage.
- Ligne `closed` même en erreur du fournisseur et même si la séance plante avant l'ouverture du journal.
- Limite d'usage → `error`, cause `usage_limit : …` ; `error_max_turns` → `turn_limit` ; processus sans résultat → `error`.
- Adaptateurs par les vrais SDK : corps OpenRouter (`provider.order`, `allow_fallbacks: false`, `usage.include`), normalisation (4180 dont 4096 lus → 84 en entrée), nouvelle tentative sur 503 dans l'adaptateur, points de cache Anthropic.
- Aucune clé dans le journal ; registre sans en-tête, dédoublonné, `merge=union`.

## Tests live

| Test | Joué | Résultat |
|---|---|---|
| `test_openrouter_one_real_call` | oui, 2026-11-05 | servi par Xiaomi, 350 jetons d'entrée, 64 de sortie, `usage.cost` 0,00020793 $ = calcul tarifaire au millionième ; 0,000208 $ inscrit au registre (`live-1-6-mimo-v2.6-pro-20261105T221315Z`) |
| `test_anthropic_one_real_call` | non | `ANTHROPIC_API_KEY` absente |
| `test_claude_code_one_real_session` | non | connexion unique d'Anaël pas encore faite |

### Procédure de connexion unique (Anaël)

Dans PowerShell, une seule fois :

```powershell
New-Item -ItemType Directory -Force "$HOME\.nnww\claude-config"
$env:CLAUDE_CONFIG_DIR = "$HOME\.nnww\claude-config"
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
claude   # puis /login avec le compte de l'abonnement, puis /exit
```

N'y copier aucun réglage, plugin, skill ni `CLAUDE.md`. Vérifier ensuite, dans le dépôt : `uv run pytest -m live tests/test_live.py -k claude_code -s` (une séance de 2 tours, 0 $ facturé ; confirme aussi l'identifiant `claude-sonnet-5-5` et les options cachées `--max-turns` et `--system-prompt-file`, acceptées par Claude Code 2.1.318 lors d'un essai sans identifiants).

## Reports

- **Test live Claude Code** et **test live API Anthropic** : à jouer quand la connexion et la clé existent (voir ci-dessus).
- **Cache OpenRouter chez Xiaomi** : un seul appel live, donc cache non vérifié ; à contrôler sur la première séance MiMo (`cache_read_tokens` non nul dès le 2e appel). Écriture du cache toujours non tarifée (constat 1-2).
- **Usage du flux Claude Code** : comparer, à la première séance réelle, la somme des `model_call` à l'`usage` de l'événement `result` (jetons de sortie possiblement partiels dans les événements `assistant`). Les messages émis après le gel ne sont plus journalisés (journal clos).
- **Raisonnement MiMo** : les champs `reasoning` d'OpenRouter ne sont ni journalisés ni renvoyés au modèle ; à revoir si la première séance le demande.
- **Porte de coût** (médiane > 2 $ → 2 tentatives) : calcul sur le registre, story 1-8.
- **Tâches** : inscription au registre `tasks.registry` avec 1-7 (jouet) et 1-9 (S).
- Confirmation par Anaël de D4 (`max_session_usd = 5`) et D10 (effort `medium`, identifiants).
