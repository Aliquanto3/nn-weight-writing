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
- **Intention courante** : V0 presque finie (1-1, 1-2, 1-3 provisoire, 1-4 fusionnées) ; 1-5 en développement (Opus, high) ; puis 1-6.
- **Plan des vagues restantes** : V1 = 1-6 ★ (← 1-5, 1-2) ; elle écrit la ligne `closed` `probe-1-2` (0,00816209 USD) et suit la normalisation de 1-2 (`input = prompt_tokens - cached_tokens - cache_write_tokens`, fournisseur OpenRouter fixé).
- **Artefacts utiles** : constats dans `docs/verifications/` ; specs de story dans `_bmad-output/implementation-artifacts/stories/` ; décisions D1-D12 de 1-5 dans sa spec de story.
- **Attentes Anaël** : compte PISTE (1-3 T1-T8), Ollama + GPU pour la collecte (avant 1-12), connexion `CLAUDE_CONFIG_DIR` (1-6 live), décisions CAP-1 sur S (1-1) et MNIST A-D (1-4).
- **Pièges rencontrés** : `setup-uv` sans tag majeur (épingler la version exacte) ; `file_prs.py` lancé trop tôt après `gh pr create` saute la PR (« aucun contrôle ») : attendre ~30 s.

## Sprint 1 — Lot 1, reproduction critique (1-1 à 1-6)

| Vague | Stories en parallèle | Après | Fichiers ou écrans touchés |
|---|---|---|---|
| V0 | 1-1 · 1-2 · 1-3 (mixte) · 1-4 · 1-5 ★ | — | 1-1, 1-3, 1-4 `docs/verifications/` (un fichier chacune) ; 1-2 `providers/probe.py`, `docs/verifications/`, sans toucher `pyproject.toml` ; 1-5 `src/nn_weight_writing/{session,sandbox,network,journal,evaluation}`, `cli.py`, `config/protocol.toml`, `pyproject.toml` |
| V1 | 1-6 ★ (mixte) | 1-6 ← 1-5 ; 1-6 ← 1-2 | `providers/`, `session/` pilotes, `budget/` (ligne closed de la sonde 1-2 comprise), `config/{models,pricing}.toml` |

## Journal

- 2026-11-05 22:07 · run · décision · périmètre 1-1 à 1-6, plafond 4 stories, CI de branche ajoutée par `chore/etat-run` · —
- 2026-11-05 22:11 · run · fusion · #2 CI de branche + état, MERGED vérifié · 00f3622
- 2026-11-05 22:11 · run · décision · topic GitHub status-spec → status-dev · —
- 2026-11-05 22:11 · run · attente humaine · clé OpenRouter (1-2), compte PISTE (1-3), connexion CLAUDE_CONFIG_DIR (1-6) demandées · —
- 2026-11-05 22:11 · 1-1 · dev · lancé (general-purpose Opus, worktree) · —
- 2026-11-05 22:11 · 1-3 · dev · lancé (general-purpose Opus, worktree, mixte) · —
- 2026-11-05 22:11 · 1-4 · dev · lancé (general-purpose Sonnet, worktree) · —
- 2026-11-05 22:11 · 1-5 · décision · story à risque (bac à sable) : relecture de la spec par second-avis avant le code · —
- 2026-11-05 22:14 · 1-5 · second-avis · spec relue : 3 high (canal de résultat forgeable par re.enum.sys, alias d'ImportFrom, corpus incomplet), 10 medium, 4 low · —
- 2026-11-05 22:14 · 1-5 · décision · D1-D12 tranchées par l'orchestrateur (nonce de trame, alias filtrés, corpus étendu, délai 60 s, turn_limit 200, 3 gels au plus, mutations refusées après la dernière passe…), consignées dans la spec de story 1-5 · —
- 2026-11-05 22:14 · 1-5 · dev · lancé (dev-story Opus, effort high, worktree) · —
- 2026-11-05 22:14 · 1-4 · dev · fini, conforme avec réserves (licence MNIST non établie par source primaire) · 4d3f577
- 2026-11-05 22:14 · run · décision · Anaël part pour la nuit, run autonome sur tout ce qui est possible ; clé OpenRouter disponible en variable d'environnement · —
- 2026-11-05 22:14 · 1-2 · décision · 1-2 avancée en V0 (plus de dépendance à 1-6) : son verdict éclaire l'adaptateur OpenRouter de 1-6 ; coût de la sonde consigné dans le constat, ligne closed du registre écrite par 1-6 · —
- 2026-11-05 22:14 · 1-4 · second-avis · lancé · 4d3f577
- 2026-11-05 22:14 · 1-2 · dev · lancé (dev-story Sonnet, worktree, sonde ≤ 0,50 $) · —
- 2026-11-05 22:15 · 1-1 · dev · fini, conforme avec écarts (3 types attestés, 12 reconstruits ; post LinkedIn illisible) · abd8cb9
- 2026-11-05 22:15 · 1-1 · second-avis · lancé · abd8cb9
- 2026-11-05 22:16 · 1-1 · second-avis · 1 high (« 30 février » attesté par SOURCES.md seul), 3 medium, 3 low · abd8cb9
- 2026-11-05 22:16 · 1-1 · review · lancé (reviewer Opus) · abd8cb9
- 2026-11-05 22:17 · 1-4 · second-avis · 3 high (poids A-littéral et témoins C/E dérivés de MNIST, pixels MNIST dans les journaux publiés), 4 medium, 3 low · 4d3f577
- 2026-11-05 22:17 · 1-4 · review · lancé (reviewer Opus) · 4d3f577
- 2026-11-05 22:17 · 1-1 · review · 1 medium et 3 low corrigés, 3 rejetés ; verdict proposé, décision à Anaël · b7ee4eb
- 2026-11-05 22:17 · 1-1 · PR · ouverte · b7ee4eb
- 2026-11-05 22:17 · 1-2 · dev · fini, conforme avec réserves ; chat completions recommandé ; sonde 0,0045 $ facturés (7 appels) ; 14 tests verts · 7f61638
- 2026-11-05 22:17 · 1-2 · second-avis · lancé · 7f61638
- 2026-11-05 22:19 · 1-1 · CI · verte sur les trois OS (PR #3) · b7ee4eb
- 2026-11-05 22:19 · 1-4 · review · passe 1 : 7 Important corrigés, 2 low corrigés, 1 rejeté ; décision MNIST (A à D) à demander à Anaël avant 2-1 · 3b66577
- 2026-11-05 22:19 · 1-1 · review · passe 2 lancée (après correction d'un medium) · b7ee4eb
- 2026-11-05 22:19 · 1-4 · review · passe 2 lancée · 3b66577
- 2026-11-05 22:19 · 1-2 · second-avis · 5 medium (appels payants malgré /models en échec, input non normalisé, coûts et nombre d'appels incohérents, boucle d'outils non testée), 4 low ; aucune fuite de clé · 7f61638
- 2026-11-05 22:19 · 1-2 · review · lancé (reviewer Opus) · 7f61638
- 2026-11-05 22:23 · 1-1 · review · passe 2 : 0 Important, 1 low corrigé · 3942487
- 2026-11-05 22:23 · 1-1 · fusion · #3 fusionnée, MERGED vérifié · 3a3b2d3
- 2026-11-05 22:23 · 1-4 · review · passe 2 : 1 medium corrigé (report qui préjugeait l'option MNIST), 2 low notés · 5de27c5
- 2026-11-05 22:23 · 1-2 · review · passe 1 : 5 medium et 3 low corrigés, 1 rejeté ; sonde relancée (total facturé 0,00816 $, 12 appels) ; normalisation input hors cache pour 1-6 · 825fded
- 2026-11-05 22:23 · 1-3 · dev · fini, provisoire en attente du compte PISTE ; licences Judilibre et CE conformes avec réserves ; slm-quality-bench sans fausses références (collecte Ollama à écrire) · 74545f7
- 2026-11-05 22:23 · 1-4 · review · passe 3 lancée (Sonnet) · 5de27c5
- 2026-11-05 22:23 · 1-2 · review · passe 2 lancée · 825fded
- 2026-11-05 22:23 · 1-3 · second-avis · lancé · 74545f7
- 2026-11-05 22:26 · 1-4 · review · passe 3 : rien · 5de27c5
- 2026-11-05 22:26 · 1-4 · fusion · #4 fusionnée, MERGED vérifié · 235e7f7
- 2026-11-05 22:26 · 1-2 · review · passe 2 : 2 low corrigés, rebasée sur main · ad4226b
- 2026-11-05 22:26 · 1-2 · fusion · #5 fusionnée, MERGED vérifié · 7b88d0a
- 2026-11-05 22:26 · 1-3 · second-avis · 5 medium (r_republish décidé avant T8, fraîcheur du miroir HF, verdict prévisionnel, collecte non mesurée, dépendance 1-12 non signalée), 4 low · 74545f7
- 2026-11-05 22:26 · 1-3 · review · lancé (reviewer Opus) · 74545f7
- 2026-11-05 22:29 · 1-3 · review · passe 1 : 5 medium et 3 low corrigés, 1 rejeté ; rebasée ; accès Judilibre sans verdict jusqu'à T1-T8 · 46d35fa
- 2026-11-05 22:29 · 1-3 · review · passe 2 lancée (Sonnet) · 46d35fa
- 2026-11-05 22:30 · 1-3 · review · passe 2 : 1 low corrigé · 4d0df57
- 2026-11-05 22:30 · 1-3 · fusion · #6 fusionnée (constat provisoire), MERGED vérifié · 185f9b1
- 2026-11-05 22:30 · 1-3 · attente humaine · compte PISTE (tests T1-T8, version des CGU), Ollama et GPU de la tour pour la collecte avant 1-12, placement de la story de collecte (R9) · 185f9b1
- 2026-11-05 22:30 · 1-4 · attente humaine · décision MNIST (options A à D) avant 2-1 · 235e7f7
- 2026-11-05 22:30 · 1-1 · attente humaine · décision CAP-1 sur S (feu vert avec réserve proposé) · 3a3b2d3
