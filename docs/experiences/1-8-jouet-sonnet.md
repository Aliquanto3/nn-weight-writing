# Story 1-8 (partie Sonnet) : séances sur le jouet

Date : 2026-11-06 (séances 04:25 à 04:31 UTC). Lot 1, 1 tentative par case, pilote Claude Code (`claude -p`, abonnement d'Anaël), modèle `sonnet-5.5` (`claude-sonnet-5-5`), effort `medium` (inchangé, décision d'Anaël en attente). Protocole inchangé : `pass_budget = 20`, `turn_limit = 200`, prompt système de 1-6. Environnement posé dans chaque commande : `NNWW_CLAUDE_CWD_ROOT='C:\nnww-cwd'`, configuration dédiée par défaut `~/.nnww/claude-config`, aucune `ANTHROPIC_API_KEY` (le flux affiche `apiKeySource: none`).

## Graines et versions

- Reproductibilité : séances antérieures à la taille cible (story 1-10a). Depuis, `nnww session` refuse une séance A sans `--size-target` (code 2) ; rejouer ces séances sur le commit cité ci-dessous.
- Jeux : `nnww datagen all --seed 0 --n 256 --n-heldout 400` régénérés dans le worktree (non commités) ; séances : `--seed 0`, tentative 1.
- Code : worktree `exp/1-8-jouet-sonnet` sur `main` b8b1a4b + deux correctifs du harnais (`aed4996`, `49ce9c0` après rebase sur `main` 925c602 ; `bf4c086`, `ef9f6cb` avant). Claude Code : celui du poste au 2026-11-06.

## Défauts du harnais trouvés (2, corrigés avant les séances, commits `Fix:` séparés)

1. `config_dir_problems` refusait la configuration dédiée d'Anaël. `plugins/` (cache des places de marché que Claude Code recrée à la connexion, aucun plugin installé : `installed_plugins.json` absent) était refusé en bloc, et `settings.json` valant `{"theme": "dark"}` aussi. Correctif `aed4996` : `plugins/` admis seulement si ses entrées sont parmi `known_marketplaces.json`, `marketplaces`, `installed_plugins.json` (table `plugins` vide) ; un plugin installé, un `cache/` de plugins ou un `installed_plugins.json` illisible sont refusés ; `settings.json` : liste blanche `$schema` et `theme` (apparence du terminal, sans effet sur le contexte ni les outils), toute autre clé refusée. Tests ajoutés (plugins absent / cache de place de marché seul / plugin installé refusé ; theme admis / autre clé refusée).
2. Après la première séance réelle, le dossier dédié a changé de contenu : le premier `claude -p` y a recréé `skills/synced/` (copie de 49 skills du compte claude.ai), `plugins/store/` et `plugins/synced/` (synchronisation du compte ; `syncClaudeAiSkills` est `false` dans `~/.claude/settings.json` mais absent de la configuration dédiée). La deuxième séance a été refusée avant lancement (`configuration Claude Code non dédiée : skills présent; plugins présent : ['store', 'synced']`, fin `error` au journal, registre `reserved` puis `closed` à 0 $ ; case rejouée, AD-14). Ces copies ne sont pas chargées : `skills` reste vide dans l'événement `init` (voir preuve), grâce à `--disable-slash-commands`. Correctif `49ce9c0` : `skills/synced`, `plugins/store` et `plugins/synced` admis, tout autre contenu de `skills/` toujours refusé ; la garde reste le contrôle de l'événement `init` à chaque séance. Le dossier d'Anaël n'a pas été modifié par nous. Possible, à décider : mettre `"syncClaudeAiSkills": false` dans le `settings.json` dédié (clé à ajouter à la liste blanche), ce qui évite aussi l'écriture de ces copies.

Le commit `49ce9c0` embarque les deux premières lignes de registre de la séance de parité (déjà écrites par le harnais à ce moment).

## Preuve de contamination nulle : événement `init` du flux `stream-json`

Relevé sur les 8 séances suivantes via un enveloppeur de `claude` (`--claude-command`, copie du flux sans le modifier) ; la première séance (parité, A-programme) a passé le même contrôle du pilote (`init_problems`) sans enveloppeur. Événement `system/init`, identique sur les huit :

- `tools` : `mcp__nnww__declare_network`, `mcp__nnww__freeze`, `mcp__nnww__run_on_examples`, `mcp__nnww__submit_script` (A-programme) ; aucun outil intégré.
- `mcp_servers` : `nnww`, `connected`, seul serveur.
- `skills` : `[]` ; `slash_commands` : `[]`.
- `plugins` : quatre plugins intégrés (`cc-plugin-agents-md`, `-telemetry`, `-privacy`, `-plugin-authoring`, `path: builtin`), aucun plugin tiers.
- `agents` : `claude`, `Explore`, `general-purpose`, `Plan`, `statusline-setup`, soit les agents intégrés de Claude Code (non vide donc) ; sans outil `Agent` ni outil intégré, ils sont inutilisables. Aucun agent utilisateur. `init_problems` contrôle désormais `agents` (revue, commit `5adf75b`) : tout agent hors de ces cinq intégrés est une contamination.
- `model: claude-sonnet-5-5`, `apiKeySource: none`.

## Résultats (9 cases)

Exactitude sur le réservé (400 exemples) par `uv run python scripts/exactitude_reserve.py runs/1/<session_id> ...` (vérification d'empreinte avant lecture du réservé). « Tours » = messages distincts du modèle. Facturé : 0 partout (abonnement) ; équivalent API : `cost_equiv_usd` du journal, sous-estimé, puis l'équivalent réel (voir l'anomalie). Drapeaux d'audit : aucun (`flags` vide dans les `script_run` ; A-littéral n'exécute pas de script).

| Tâche | Méthode | Statut | Passes /20 | Tours | Exactitude | Facturé ($) | Équivalent API, journal ($) | Drapeaux | Séance | `tree_sha256` (16 premiers) |
|---|---|---|---|---|---|---|---|---|---|---|
| parity | A-programme | freeze | 1 | 5 | 400/400 | 0 | 0,051617 | aucun | `parity-A-program-sonnet-5.5-t1-20261106T042528Z` | `8c9110f28ee7d439` |
| parity | A-littéral | freeze | 1 | 6 | 400/400 | 0 | 0,054344 | aucun | `parity-A-literal-sonnet-5.5-t1-20261106T042814Z` | `568a7b77e6193397` |
| parity | B | freeze | 0 | 2 | 400/400 | 0 | 0,022219 | aucun | `parity-B-sonnet-5.5-t1-20261106T042840Z` | `8256ddb7dda1b81e` |
| compare | A-programme | freeze | 1 | 6 | 400/400 | 0 | 0,053324 | aucun | `compare-A-program-sonnet-5.5-t1-20261106T042737Z` | `d523d21bbaa99d1b` |
| compare | A-littéral | freeze | 3 | 10 | 400/400 | 0 | 0,098564 | aucun | `compare-A-literal-sonnet-5.5-t1-20261106T042847Z` | `c86a1c4b3643306e` |
| compare | B | freeze | 0 | 1 | 400/400 | 0 | 0,017214 | aucun | `compare-B-sonnet-5.5-t1-20261106T042926Z` | `8cc4386a9bc120cd` |
| automaton | A-programme | freeze | 1 | 6 | 400/400 | 0 | 0,051003 | aucun | `automaton-A-program-sonnet-5.5-t1-20261106T042934Z` | `470f53a8b296d8bc` |
| automaton | A-littéral | freeze | 1 | 6 | 400/400 | 0 | 0,055017 | aucun | `automaton-A-literal-sonnet-5.5-t1-20261106T042957Z` | `9a568da85df13685` |
| automaton | B | freeze | 0 | 1 | 400/400 | 0 | 0,018582 | aucun | `automaton-B-sonnet-5.5-t1-20261106T043025Z` | `5cec9fa0f6217730` |

Séance perdue par le harnais, rejouée (AD-14) : `compare-A-program-sonnet-5.5-t1-20261106T042604Z`, refusée avant lancement (défaut 2), 0 tour, 0 $. Total des 9 séances : 0,421884 $ équivalent API au journal (sous-estimé), **0,828 $ équivalent réel estimé** (voir l'anomalie), 0 $ facturé. Registre : 20 lignes ajoutées (10 séances, réservation puis clôture), `billed_usd` = 0 partout, `cost_equiv_usd` journalisé à la clôture. Durées : 3 s (B) à 39 s (compare A-littéral) ; aucune fin en `pass_budget`, `turn_limit`, `money_budget`, `error` (hors séance refusée) ni limite d'usage de l'abonnement.

Refus du harnais en séance, tous corrigés par le modèle avant gel : `invalid_manifest` (11), `no_network_declared` (2), `network_has_weights` (1), `invalid_blocks` (1) ; aucun en B.

## Anomalie : le coût équivalent du journal sous-estime d'environ moitié

Pour les 8 séances enveloppées, le `total_cost_usd` de l'événement `result` de Claude Code vaut de 1,6 à 2,1 fois le `cost_equiv_usd` du journal : compare A-programme 0,1059 (journal 0,0533), parité A-littéral 0,1129 (0,0543), parité B 0,0377 (0,0222), compare A-littéral 0,1861 (0,0986), compare B 0,0319 (0,0172), automate A-programme 0,0990 (0,0510), A-littéral 0,1137 (0,0550), B 0,0338 (0,0186) ; total des 8 : 0,7209 $ contre 0,3703 $. Deux causes, relevées sur `result.usage` : (a) les `output_tokens` des événements `assistant` sont partiels (journal : 84 pour une séance dont l'`usage` final porte 2138, dont 862 de raisonnement) ; (b) Claude Code écrit le cache en tranche d'une heure (`ephemeral_1h_input_tokens`), comptée 4,00 $/Mtok pour Sonnet 5.5 dans son calcul, alors que `pricing.toml` retient 2,50 $ (tranche de 5 minutes, D9 de 1-6). Recomposé avec l'`usage` final, `result.total_cost_usd` est retrouvé au micro-dollar (0,105939 $ pour la première). Doubler les équivalents n'est pas un majorant : le rapport va jusqu'à 2,08 (parité A-littéral).

Équivalents réels (`result.total_cost_usd`, recomposé au tarif d'une heure et avec `result.usage`) :

| Séance | Journal ($) | Réel ($) | Rapport |
|---|---|---|---|
| parité A-programme | 0,051617 | 0,1074 (estimé, × 2,08) | 2,08 (max. observé) |
| parité A-littéral | 0,054344 | 0,1129 | 2,08 |
| parité B | 0,022219 | 0,0377 | 1,70 |
| compare A-programme | 0,053324 | 0,1059 | 1,99 |
| compare A-littéral | 0,098564 | 0,1861 | 1,89 |
| compare B | 0,017214 | 0,0319 | 1,85 |
| automate A-programme | 0,051003 | 0,0990 | 1,94 |
| automate A-littéral | 0,055017 | 0,1137 | 2,07 |
| automate B | 0,018582 | 0,0338 | 1,82 |
| **Total des 9** | **0,421884** | **0,828** (dont 0,1074 estimé) | 1,96 |

La séance de parité A-programme n'a pas été enveloppée : son `result` n'a pas été conservé et le journal ne permet pas le recalcul ; son réel est estimé par le rapport le plus haut observé (× 2,08), marqué comme tel. Les journaux des neuf séances restent tels quels (clos au gel, sous-estimés) : pour toute comparaison de coût (1-10, 1-14), prendre la colonne « Réel ».

Corrigé en revue (commit `5adf75b`) : le pilote garde le journal ouvert après le gel jusqu'à l'événement `result`, y verse l'écart avec `result.usage` dans un `model_call` de réconciliation (avec `total_cost_usd` dans l'échange), et tarifie l'écriture du cache d'une heure à `cache_write_1h` (Sonnet 5.5 : 4,00 $/Mtok, valeur retrouvée ici ; Fable 5.1 : 20,00 $, à confirmer sur la page de prix). Les séances à venir journalisent donc l'équivalent réel. Reste une limite : une séance tuée (délai, contamination) n'a pas de `result` et garde l'équivalent partiel.

## Étanchéité des paquets

Les dix `runs/1/*sonnet*/bundle/` ne contiennent que `task.json` (clés `description`, `encoder`, `task`, `vocabulary`) et `examples.jsonl`, identique octet pour octet à `data/<tâche>/toy/examples.jsonl` ; aucune ligne commune avec `heldout/<tâche>/toy/`, aucun `labels.jsonl`. Répertoire courant de `claude` : vide, sous `C:\nnww-cwd` (aucun fichier de mémoire dans les parents, contrôle du pilote).

## Recalibrage du budget de passes : données et recommandation

Passes utilisées sur 20, 18 cases (une tentative chacune, mêmes jeux, mêmes graines) :

| Méthode | Tâches (parity / compare / automaton) | MiMo | Sonnet |
|---|---|---|---|
| A-programme | 3 | 1 / 1 / 1 | 1 / 1 / 1 |
| A-littéral | 3 | 1 / 2 / 1 | 1 / 3 / 1 |
| B | 3 | 1 / 1 / 0 | 0 / 0 / 0 |

- Fins de séance : 18 gels sur 18 (plus une séance MiMo perdue par `max_tokens` et une séance Sonnet refusée par la configuration, toutes deux rejouées) ; aucune fin `pass_budget` ou `turn_limit`. Maximum observé : 3 passes (Sonnet, compare A-littéral), soit 15 % du budget ; moyenne 0,94 ; médiane 1. Exactitude 400/400 sur 18 cases : le jouet ne sépare ni les modèles ni les budgets.
- Une passe coûte un appel d'outil et une exécution sur les 256 exemples du paquet, négligeable (séances de 0,003 à 0,10 $ environ) : le budget ne protège pas le portefeuille, il borne la recherche par retour d'information, ce qui est le plus proche d'un entraînement que l'agent puisse faire sans gradient. C'est le seul rôle utile de la valeur.
- Les agents s'arrêtent d'eux-mêmes dès que le résultat est bon : une valeur haute ne coûte rien quand la tâche est facile. Une valeur trop basse fausserait S, bien plus dur que le jouet, où l'écart de A-littéral sur compare (2 et 3 passes, contre 1) suggère que les itérations augmentent avec la difficulté.
- Le jouet ne donne qu'une borne basse du besoin (3 passes) et ne permet pas d'estimer celui de S : toute valeur inférieure à ~10 risque de devenir contraignante sur S sans qu'aucune donnée le dise, alors qu'aucune donnée n'appelle non plus à dépasser 20.

**Recommandation : conserver `pass_budget = 20` pour la suite (valeur unique, tous modèles, toutes tâches).** Marge d'un facteur près de 7 sur le maximum du jouet, aucun surcoût (aucune case ne s'en approche), et pas de case où le budget, plutôt que la capacité, aurait tranché. Une case de S qui finirait en `pass_budget` se lit « budget atteint » et non échec de capacité (déjà le cas dans le protocole) ; la valeur ne se change pas en cours de lot. Une valeur de 10 serait défendable si Anaël veut limiter le retour d'information ; ces données ne la justifient pas.

## Ce qui reste

- `config/protocol.toml` non touché : la décision sur `pass_budget` revient à l'orchestrateur.
- Effort `medium` des modèles Claude : à confirmer par Anaël.
- Anomalies de coût du pilote Claude Code et contrôle des agents dans `init_problems` : corrigés en revue (`5adf75b`) ; tarif d'une heure de Fable 5.1 à confirmer.
