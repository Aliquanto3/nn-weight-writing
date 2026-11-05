# Run autonome — plan et état

Fichier d'état de l'orchestrateur, à relire en premier après chaque `/clear`. Lu par `/agent-cost-kit:avancement-run`. Stories : `_bmad-output/specs/spec-nn-weight-writing/stories.yaml` ; architecture : `_bmad-output/planning-artifacts/architecture/architecture-nn-weight-writing-2026-11-05/ARCHITECTURE-SPINE.md`.

## Périmètre

| Périmètre | Epics | Note |
|---|---|---|
| Dans le run | Epics 1 à 1 | Lot 1, stories 1-1 à 1-6 d'abord (demande d'Anaël, 2026-11-05) |
| Hors run | Epics 2 à 3 | Lots 2 et 3 ; stories 1-7 à 1-14 après 1-6, sur nouvelle demande |

Au plus 4 stories en développement à la fois, chacune dans son worktree (`.claude/worktrees/<story>`).
Plafond global : 5 agents actifs à la fois sous Windows (développement, revue et rebase confondus).

## Règles

- Types : `dev` (dev-story → second-avis → reviewer → intégration), `mixte` (code ou recherche par l'agent, puis « attente humaine »), `humaine` (jamais confiée à un agent). ★ = story pivot, dev-story sur Opus.
- Stories de recherche (1-1, 1-3, 1-4) : agent `general-purpose` (accès web), qui ne lance aucun sous-agent ; même chaîne second-avis → reviewer ensuite.
- Attentes humaines : clé OpenRouter (`OPENROUTER_API_KEY`, 1-2), compte PISTE (1-3), connexion unique de `CLAUDE_CONFIG_DIR=~/.nnww/claude-config` (1-6). Demandées par notification le 2026-11-05 ; le run avance sur le reste.
- Fichiers d'état du run (ce fichier) : jamais dans une PR de story. PR `chore/etat-run` à part ; `merge=union` dans `.gitattributes`.
- Suite complète : la CI de branche (`.github/workflows/ci.yml`, trois OS) la joue et sert de porte de fusion. Attente : `gh run watch <id> --interval 60`. En local : ruff et tests ciblés.
- Fusion par merge commit (`AGENTS.md`), via `scripts/file_prs.py` du kit ; journaliser `fusion` seulement après `MERGED` vérifié, puis `git log -1` sur `main`.
- `git worktree prune` avant chaque lancement ; worktrees supprimés en fin de run seulement.
- Heure du journal prise par `date` au moment d'écrire. `uv run python`, jamais `python` nu.
- Appels réels payants : seulement ceux que la story prévoit (1-2 sonde, 1-6 un appel live par pilote), coût au registre.

## Sessions autorisées à modifier le périmètre

- (aucune)

## Contrats partagés en cours

- 1-5 pose les modules partagés de la spine (`journal/schema.py`, `session/refusals.py`, `session/tools.py`, `network/manifest.schema.json`, `evaluation/schema.py`) ; 1-6 et 1-2 les importent sans les redéfinir.

## Brief

- **Tâche du run** : run autonome sur le lot 1 de `stories.yaml`, 1-1 à 1-6 d'abord ; 1-2 et 1-3 attendent la clé OpenRouter et le compte PISTE d'Anaël ; conforme à ARCHITECTURE-SPINE.md ; topic GitHub passé à `status-dev`.
- **Intention courante** : V0.
- **Plan des vagues restantes** : V0, V1, V2 ci-dessous.
- **Artefacts utiles** : constats dans `docs/verifications/` ; specs de story dans `_bmad-output/implementation-artifacts/stories/`.
- **Pièges rencontrés** : —

## Sprint 1 — Lot 1, reproduction critique (1-1 à 1-6)

| Vague | Stories en parallèle | Après | Fichiers ou écrans touchés |
|---|---|---|---|
| V0 | 1-1 · 1-3 (mixte) · 1-4 · 1-5 ★ | — | 1-1, 1-3, 1-4 `docs/verifications/` (un fichier chacune) ; 1-5 `src/nn_weight_writing/{session,sandbox,network,journal,evaluation}`, `cli.py`, `config/protocol.toml` |
| V1 | 1-6 ★ (mixte) | 1-6 ← 1-5 | `providers/`, `session/` pilotes, `budget/`, `config/{models,pricing}.toml` |
| V2 | 1-2 (mixte) | 1-2 ← 1-6 | `providers/` sonde, `docs/verifications/`, `budget/ledger.csv` |

## Journal

- 2026-11-05 22:07 · run · décision · périmètre 1-1 à 1-6, plafond 4 stories, CI de branche ajoutée par `chore/etat-run` · —
