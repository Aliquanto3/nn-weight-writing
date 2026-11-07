---
story: "1-14"
title: Mesures, rapport du lot 1 et v0.1.0
status: review (1-14a partie 1) ; partie 2 à faire ; en attente de 1-13 (1-14b)
branch: feat/1-14-mesures-publication
---

# Story 1-14 : Mesures, rapport du lot 1 et v0.1.0

## Objet

Régénérer par commande, depuis les seuls journaux, `run.json` et `eval*.json`, le tableau des mesures du lot 1 (CAP-12), publier les drapeaux d'audit par séance, assembler l'archive contrôlée des artefacts (AD-18), puis rédiger le rapport et livrer la release v0.1.0 (CAP-13). Décisions suivies : AD-4 (amendement : évaluation croisée laissée à 1-14), AD-7, AD-8, AD-9, AD-11, AD-12, AD-17, AD-18, AD-19 ; constat 1-3 (section 2, R2, R6) ; `config/publish.toml` (`r_republish = true` depuis le 2026-11-07).

La story est coupée en deux :

- **1-14a, outillage, maintenant, en parallèle de 1-13** : mesures dans `eval.json`, ablation et lisibilité, évaluation croisée, `nnww table`, `nnww publish`, script de rassemblement des artefacts. Elle tourne sur les journaux existants de 1-8, 1-10 et 1-11 et accepte sans changement de code les séances et témoins de R que 1-13 ajoutera.
- **1-14b, après 1-13** : jugement des séances signalées, `docs/rapport-lot1.md`, `NOTICE`, release v0.1.0, brouillon du billet remis à Anaël.

Cette spec tranche les noms, les formats et les règles. L'implémentation n'invente ni colonne, ni code de refus, ni chemin.

## Existant à réutiliser, sans le refaire

| Existant | Où | Usage en 1-14a |
|---|---|---|
| Vérification de gel et d'empreintes, `eval.json` sans mesures | `evaluation/verify.py` (`verify_frozen`, `evaluate`, `EvalRefusalCode`) | `evaluate` gagne les mesures ; `verify_frozen` reste la première étape, avant toute lecture du réservé |
| `EvalRecord`, `RunRecord` (`metrics` vide, « mesures : story 1-14 ») | `evaluation/schema.py` | `EvalRecord` passe en version 2 |
| Exactitude, alignement, tâche du réseau | `evaluation/score.py` (`accuracy`, `check_alignment`, `run_task`, `score_frozen`) | réutilisés tels quels ; `score_frozen` n'est pas modifié (il garde son refus de l'évaluation croisée, utilisé par les tests et par 1-13) |
| Étiquettes | `evaluation/labels.py` (`read_labels`) | tel quel |
| Exactitude de B par `sandbox.run` profil B, par type | `scripts/exactitude_reserve.py` (`predict`, `by_type`) | logique reprise dans `evaluation/measures.py` ; le script reste en place, inchangé |
| Groupes vraies / connues / tenues à l'écart, encodeur des témoins F | `baselines/curve.py` (`measure`, `_group`), `baselines/train.py` (`_encode_for`) | non importables par `evaluation/` (PyTorch, AD-13) : la règle est réécrite dans `evaluation/measures.py`, les groupes viennent de `dataset.json` (ci-dessous) |
| Drapeaux d'audit `fragment_overlap` et boucles (1-10) | `sandbox/audit.py`, champ `flags` des événements `script_run` | lus dans les journaux, jamais recalculés |
| Lecteur de journal | `journal/reader.py` (`read_records`, `find_last`) | seul lecteur des journaux pour `report/` et `publish/` |
| Registre | `budget/ledger.py` (`read`) | contrôle croisé des coûts du lot, lecture seule |
| Sorties de scripts `courbe-c-f.jsonl`, `reentrainement.jsonl` | `runs/1/` de 1-11 | **pas** une entrée du tableau (AD-7 : journaux, `run.json`, `eval.json`, sans autre entrée) ; servent seulement de valeurs de contrôle dans les tests d'acceptation |

## Emplacement réel des artefacts et rassemblement

Relevé le 2026-11-07 (lecture seule, aucun fichier modifié) :

| Worktree | Contenu de `runs/1/` | `heldout/` | Taille |
|---|---|---|---|
| `.claude/worktrees/1-8` | 10 séances jouet MiMo (9 gelées, 1 rejouée), `eval.json` v1 vides | `parity`, `compare`, `automaton` (`toy`) | 1,1 Mo |
| `.claude/worktrees/1-8s` | 10 séances jouet Sonnet (9 gelées, 1 rejouée) | idem | 0,7 Mo |
| `.claude/worktrees/1-10s` | 39 séances Sonnet et Fable sur S et S-réservé (25 gelées, 14 en `error` rejouées) | `legal_s/eval`, `legal_s_reserved/eval` | 12 Mo |
| `.claude/worktrees/1-10m` | 16 séances MiMo (3 gelées), trois étapes de réglage | idem | 0,6 Mo |
| `.claude/worktrees/1-11` | `train/` (114 témoins C, F, « même réseau »), `annexe-fields1/train/` (30 F `legal.fields@1`), `courbe-c-f.jsonl`, `reentrainement.jsonl` | idem | 50 Mo |

Aucune séance dans la racine du dépôt ni dans `1-10a`, `1-12`, `1-12a`. Les noms de séance sont uniques (horodatage) : aucune collision attendue entre worktrees ; les `heldout/` doivent être identiques octet pour octet (mêmes graines).

**Proposition : un seul emplacement hors dépôt, `C:\Users\Utilisateur\nnww-artefacts\`** (disque C:, 98 Go libres ; D: n'a que 74 Mo), au format d'AD-12 :

```text
nnww-artefacts/
  runs/1/<session_id>/...          # séances de 1-8, 1-10, puis 1-13
  runs/1/train/<run_id>/...        # témoins de 1-11, puis 1-13
  runs/1/annexe-fields1/train/...  # annexe F fields@1 de 1-11 (chemin conservé)
  heldout/<task>/<dataset>/...
  data/<task>/<dataset>/...        # sans data/r/ (collecte brute de 1-12a)
  provenance.jsonl                 # une ligne par fichier copié
  dist/lot1/                       # sortie de nnww publish
```

Rassemblement par **`scripts/rassembler_runs.py`** (hors du paquet, comme les scripts de 1-11) :

```text
uv run python scripts/rassembler_runs.py --to C:\Users\Utilisateur\nnww-artefacts \
    --from .claude/worktrees/1-8 .claude/worktrees/1-8s .claude/worktrees/1-10s \
           .claude/worktrees/1-10m .claude/worktrees/1-11 [--dry-run]
```

- Copie (jamais de déplacement) de `runs/`, `heldout/` et `data/` de chaque source, `data/r/` exclu, `eval.json` et `eval-cross-*.json` exclus (régénérés à destination par `nnww evaluate`).
- Deux phases : plan complet d'abord, copie ensuite seulement si aucun conflit. Un fichier déjà présent à destination avec le même sha256 est sauté ; un sha256 différent est un conflit, listé, et rien n'est copié (code 1).
- Aucune écriture dans les sources : le script les ouvre en lecture seule.
- `provenance.jsonl` (ajout seul) : `{"src": <worktree>, "path": <chemin relatif>, "sha256": ..., "ts": ...}` par fichier copié.
- Relançable : 1-14b l'appelle avec le worktree de 1-13, sans toucher au reste.

## 1-14a — Outillage

### Noms à créer

| Fichier | Contenu |
|---|---|
| `src/nn_weight_writing/evaluation/measures.py` | `measure(run_dir, heldout_dir) -> dict` (mesures natives), `measure_cross(run_dir, task, heldout_dir) -> dict`, `encoder_for(task, encoder_id)`, `predict_b(run_dir, examples)`, `dataset_identity(heldout_dir) -> dict` |
| `src/nn_weight_writing/evaluation/ablation.py` | `forward_masked(manifest, weights, x, off: set[tuple[int, int]])`, `ablate(manifest, weights, blocks, inputs, labels, decode) -> dict` |
| `src/nn_weight_writing/report/__init__.py`, `report/collect.py`, `report/table.py`, `report/decisions.py` | découverte et lecture des artefacts ; agrégation et rendu ; lecture du fichier de décisions |
| `src/nn_weight_writing/publish/__init__.py`, `publish/archive.py`, `publish/checks.py` | assemblage déterministe, contrôles et codes de refus |
| `scripts/rassembler_runs.py` | rassemblement ci-dessus |
| `tests/test_evaluation_measures.py`, `tests/test_report_table.py`, `tests/test_publish.py`, `tests/test_rassembler_runs.py` | tests nommés plus bas |
| `docs/mesures/lot1.md`, `docs/mesures/lot1.json` | tableau généré sur les artefacts rassemblés (sans R), commité ; régénéré en 1-14b |

Fichiers modifiés : `cli.py`, `evaluation/verify.py`, `evaluation/schema.py`, `config.py` (ajout de `PublishConfig` et `load_publish` en fin de fichier), `config/publish.toml` (ajout de `r_tasks`). Tests à réaligner : `tests/test_evaluation.py`, `tests/test_toy_witnesses.py` (ils appellent `evaluate` et `nnww evaluate` sans jeu réservé : le comportement « vérification seule, `metrics` vide » doit rester).

Dépendances : celles du spine. `evaluation` → `network`, `sandbox`, `journal`, `tasks` ; `report` → `journal`, `budget` ; `publish` → `journal`. Écart assumé, à reporter au spine (points ouverts) : `report` et `publish` importent aussi `evaluation.schema` (dataclasses et constantes seules), conformément à la convention « producteurs et lecteurs importent le même module ». Aucune nouvelle dépendance de paquet (`tarfile`, `gzip`, `tomllib`, `statistics` de la bibliothèque standard) : `pyproject.toml` n'est pas touché en 1-14a.

### Commandes et options

```text
nnww evaluate RUN_DIR [RUN_DIR ...] | --lot-dir DIR
              [--heldout-root PATH] [--dataset NAME] [--on TASK:DATASET] [--from-task TASK]
nnww table --lot N [--root PATH] [--out DIR] [--decisions FILE] [--ledger FILE] [--strict]
nnww publish N [--root PATH] [--out DIR] [--config FILE] [--notice FILE] [--dry-run]
```

**`nnww evaluate`** (AD-9, étendu) :

- `--heldout-root` : racine des jeux réservés. Si l'option est donnée, les mesures sont obligatoires (jeu absent : refus `no_heldout`). Si elle est omise, `heldout/` du répertoire courant est utilisé s'il existe ; sinon vérification seule, `metrics` vide et un avertissement sur stderr (comportement actuel, gardé pour les tests existants).
- Jeu natif : `heldout/<tâche>/<jeu>/`, la tâche venant du premier `open` du journal ou de `run.json` (`run_task`). `--dataset` le nomme ; sans lui, le seul sous-dossier de `heldout/<tâche>/` (`toy` pour le jouet, `eval` pour S et S-réservé), refus `ambiguous_dataset` s'il y en a plusieurs.
- `--lot-dir DIR` : évalue chaque dossier gelé sous `DIR` selon AD-12 (`DIR/<session_id>/` avec journal, `DIR/**/train/<run_id>/` avec `run.json`) ; une séance sans `freeze` est listée « non gelée », sans erreur. `--from-task` filtre sur la tâche du réseau.
- `--on TASK:DATASET` : évaluation croisée, écrite dans `eval-cross-<TASK>-<DATASET>.json` à côté de `eval.json` (noms validés par `validate_name`, donc le tiret sépare sans ambiguïté). Refus `cross_same_task` si `TASK` est la tâche du réseau ; refus `encoder_mismatch` si l'encodeur du manifeste n'est pas un encodeur de `TASK` (`encoder_id`, `prepared_encoder_id` ou `legacy_encoders`). B est évalué sur les chaînes brutes de `TASK`.
- Nouveaux codes de `EvalRefusalCode` : `no_heldout`, `ambiguous_dataset`, `heldout_fingerprint`, `cross_same_task`, `encoder_mismatch`, `task_mismatch`. `heldout_fingerprint` : les sha256 de `examples.jsonl` et `labels.jsonl` diffèrent de ceux de `dataset.json` du jeu réservé (vérifié avant lecture des étiquettes).
- Code de sortie : 0 si tout est évalué (les « non gelée » de `--lot-dir` ne comptent pas), 1 au premier refus d'un dossier (les autres continuent, tous les refus sont imprimés), 2 sur erreur d'usage.

**`EvalRecord` version 2** (`EVAL_SCHEMA_VERSION = 2`) : champ ajouté `target: dict` (`task`, `dataset`, `examples_sha256`, `labels_sha256`, `written_task`, `cross` : bool), et `metrics` :

```text
metrics = {
  "accuracy": {"correct": int, "n": int},
  "by_label": {label: {"correct": int, "n": int}},
  "by_type":  {type_id: {"correct": int, "n": int}},
  "held_out_types": [type_id, ...],        # dataset.json du jeu évalué, [] si absent
  "ood": {"correct": int, "n": int} | null, # exemples dont type_id est dans held_out_types
  "ablation": {...} | null,                 # A natif seulement (voir Lisibilité)
  "error": str | null                       # réseau ou règles en échec : aucune exactitude
}
```

`held_out_types` se lit dans `dataset.json` (clé `composition.held_out_types`, à défaut clé de premier niveau `held_out_types`). S-réservé : les 5 types tenus à l'écart ; S : liste vide, donc `ood` nul. Une ligne `eval.json` en version 1 ou à `metrics` vide est « non évaluée » pour le tableau. Déterminisme d'AD-9 tenu : mesures en entiers, taux arrondis à 6 décimales, clés triées, seul `ts` varie.

**Lisibilité par ablation** (methodes-et-lots.md), calculée par `evaluation/ablation.py` pour toute séance A dont le gel porte des blocs :

- Éteindre une unité `[couche, indice]` = forcer sa sortie après activation à 0 pour tous les exemples ; les couches suivantes sont recalculées (`forward_masked`, écrite dans `evaluation/`, `network/` n'est pas modifié).
- Pour chaque bloc déclaré au gel, puis pour chaque unité : taux de baisse par type `drop(t) = (correct_complet(t) − correct_éteint(t)) / n(t)`, sur tous les `type_id` du jeu évalué (vraies comprises, `real`).
- Une unité « touche surtout le type déclaré » si sa baisse maximale est strictement positive et si l'un des types qui l'atteignent (égalités comprises, comparaison exacte en fractions) figure dans les `types` de son bloc. Une unité sans baisse positive est « neutre ».
- Score = unités sur le type déclaré / unités cachées (les blocs forment une partition des unités cachées, AD-8 ; les neutres restent au dénominateur).
- `ablation = {"blocks": [{"index", "types", "units", "accuracy", "by_type"}], "units": [{"unit", "block", "max_drop", "max_drop_types"}], "legibility": {"units", "on_declared", "neutral", "score"}}`. Nul pour B, C, F, pour une évaluation croisée et pour un réseau en échec.

**`nnww table`** (CAP-12) : lit `<root>/runs/<N>/` (défaut `--root .`), écrit `<out>/lot<N>.md` et `<out>/lot<N>.json` (défaut `--out docs/mesures`), sans horodatage : deux exécutions sur les mêmes entrées donnent les mêmes octets. Entrées : journaux, `run.json`, `eval.json`, `eval-cross-*.json`, `frozen/manifest.json` (encodeur, pour les témoins), le fichier de décisions s'il existe, `budget/ledger.csv` (contrôle). Rien d'autre.

### Règles d'agrégation

- **Case de séance** : clé `(tâche, méthode, size_target, modèle, config)`. `config` = 8 premiers caractères hexadécimaux du sha256 du JSON canonique de `{driver, provider, effort, max_tokens, pass_budget, protocol_sha256, system_prompt_sha256, sampling}` de l'événement `open` (champ absent = `null`). Les étapes de réglage de MiMo (effort par défaut, puis medium) et le jouet avant et après recalibrage tombent ainsi dans des cases distinctes.
- **Tentative comptée** : dans une case, pour chaque `attempt`, la séance au `open.ts` le plus récent ; les précédentes sont « rejouées » (AD-14 : une séance perdue est rejouée, jamais reprise). Une tentative comptée sans gel compte comme tentative non gelée.
- **Décisions** (`--decisions`, défaut `docs/mesures/decisions-lot<N>.toml`, absent en 1-14a) : seule entrée non mesurée, elle porte des décisions datées, jamais des mesures :

  ```toml
  [[session]]
  id = "legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z"
  status = "kept"        # kept | excluded | annex | replayed
  audit = "judged"       # obligatoire pour une séance à drapeaux comptée
  date = "2026-11-08"
  reason = "fragments de format de juridiction, aucun exemple recopié"
  ref = "run-autonome.md, journal du 2026-11-08, décision"
  ```

  `excluded`, `annex` et `replayed` retirent la séance des agrégats ; elle reste dans le détail avec son statut. Un `id` inconnu des artefacts : erreur (code 1). Toutes les décisions appliquées sont recopiées dans une section du tableau.
- **Exactitude réservée** : moyenne des tentatives comptées gelées et évaluées, écart-type d'échantillon (n − 1) si au moins 2, étendue ; liste par tentative (`-` si non gelée, `inv.` si `metrics.error`). La colonne « gelées » (`k/n`) dit sur combien de tentatives la moyenne porte.
- **Témoins** (AD-17) : clé `(tâche, baseline, encodeur, N, chemin)` ; `encodeur` lu dans `frozen/manifest.json`, `chemin` = sous-dossier de `runs/<N>/` avant `train/` (vide ou `annexe-fields1`) ; moyenne et écart-type sur les graines. Les `run.json` à `dataset.retrained_from` forment la table « même réseau », par séance d'origine.
- **Coûts** : par séance, sommes des `model_call` (`billed_usd`, `cost_equiv_usd`, jetons d'entrée, de sortie, lus et écrits au cache), durée de `end.totals.duration_s`. Par case : sommes et médiane par séance des tentatives comptées ; coût des rejouées à part. Lot : total de toutes les séances, par modèle et par pilote, comparé à la somme des lignes `closed` du registre pour le lot (écart affiché, séances présentes d'un seul côté comptées).
- **Drapeaux** : pour chaque séance, union des `flags` de ses `script_run`, par `kind` (nombre de `script_run` signalés, `count` maximal, `example_ids`). Une séance comptée à drapeaux sans décision `audit = "judged"` est marquée « à juger ».

### Format du tableau (`docs/mesures/lot<N>.md`)

En-tête : « Généré par `nnww table --lot N` ; ne pas éditer. » puis nombre de journaux, de `run.json`, d'`eval*.json` lus, et empreinte des entrées (sha256 des lignes `chemin sha256` triées). Nombres en français (virgule) : pourcentages à 1 décimale, dollars à 4 décimales (6 dans le JSON). `lot<N>.json` porte les mêmes lignes, valeurs brutes, `tree_sha256` complets.

1. **Cases** : Tâche · Méthode · Taille cible · Modèle · Config · Gelées (k/n) · Exactitude réservée (moy. ± é.-t.) · Par tentative · Vraies · Fausses connues · Tenues à l'écart (HD) · Croisée → `<tâche:jeu>` (une colonne par cible présente) · Lisibilité · Paramètres (nominal, médiane) · Taille effective (script, zlib ; médianes) · Passes (moy.) · Facturé ($, somme ; médiane) · Équivalent API ($, somme ; médiane) · Durée (min) · Drapeaux (séances) · Rejouées (n ; facturé).
2. **Témoins C et F** : Tâche · Témoin · Encodeur · Chemin · N · Graines · Exactitude (moy. ± é.-t.) · Vraies · Fausses connues · Tenues à l'écart · Croisée → `<tâche:jeu>`.
3. **C « même réseau » (N = 8 192)** : Séance d'origine · Exactitude de la séance · Réentraîné (moy. ± é.-t., graines) · Écart.
4. **Évaluations croisées** : Dossier · Tâche écrite · Cible · Exactitude · Vraies · Fausses · HD.
5. **Drapeaux d'audit par séance** : Séance · `script_run` (signalés / total) · Kinds (count) · Exemples (5 au plus) · Jugement (décision, date) ou « à juger ».
6. **Séances** (une ligne par séance, rejouées et annexes comprises) : Séance · Case · Tentative · Graine · Statut (comptée, rejouée, écartée, annexe) · Fin · Détail (60 caractères) · Passes · Tours · Refus (codes) · Jetons (entrée, sortie, cache lu, cache écrit) · Facturé · Équivalent API · Durée · `tree_sha256` (12 caractères) · Exactitude.
7. **Coûts du lot et registre** : par modèle et pilote, facturé et équivalent API ; total ; registre ; écart.
8. **Configurations** : identifiant → champs de l'`open`.
9. **Décisions appliquées**, **Non évalués** (dossiers gelés sans `eval.json` v2), **Avertissements** (heldout différent entre tentatives d'une case, `eval.json` dont `tree_sha256` diffère du gel).

`--strict` (exigé en 1-14b) : code 1 s'il reste une séance « à juger », un dossier gelé non évalué, ou un avertissement. Sans `--strict`, les mêmes points sont imprimés sur stderr, code 0.

### `nnww publish` (AD-18, R2 et R6 du constat 1-3)

`config/publish.toml` gagne une clé, sans toucher à `r_republish` ni à son commentaire :

```toml
# Tâches du jeu R (story 1-13) : leurs séances, témoins, évaluations croisées et jeux sont des
# artefacts de R au sens d'AD-18.
r_tasks = ["legal_r"]
```

`load_publish(path)` : `r_republish` doit être un booléen (absent ou d'un autre type : traité comme `false`) ; `r_tasks` une liste de noms valides (absente : erreur de configuration, code 2).

**Contenu** de `<out>/runs-lot<N>.tar.gz` (défaut `--out <root>/dist/lot<N>`), liste blanche sous `runs/<N>/` :

- séances : `journal.jsonl`, `system_prompt.md`, `frozen/*`, `eval.json`, `eval-cross-*.json` (séances en erreur comprises : journal seul) ;
- témoins (`**/train/<run_id>/`) : `run.json`, `frozen/*`, `eval.json`, `eval-cross-*.json` ;
- un membre `runs/<N>/SHA256SUMS` (sha256 de chaque membre, trié).

Toujours exclus : `bundle/`, tout ce qui n'est pas dans la liste blanche (`courbe-c-f.jsonl`, `reentrainement.jsonl`…), imprimés comme « ignorés ». `data/` et `heldout/` n'entrent jamais dans cette archive.

**Archive de R** `<out>/r-lot<N>.tar.gz`, seulement si `r_republish = true` et si `<root>/data/<t>/` ou `<root>/heldout/<t>/` existe pour une tâche `t` de `r_tasks` (R2) : `examples.jsonl`, `labels.jsonl`, `dataset.json`, `sources.jsonl` de chaque jeu de ces tâches, sous `data/` et `heldout/`, plus `SHA256SUMS`.

**Archives reproductibles** : membres triés, `mtime = 0`, `uid = gid = 0`, noms d'utilisateur vides, mode 0644, gzip à `mtime = 0` ; deux exécutions sur les mêmes entrées donnent le même sha256. `<out>/SHA256SUMS` liste les archives écrites.

**Refus** (`publish/checks.py`, `PublishRefusalCode`). Tous les contrôles tournent avant toute écriture ; toutes les violations sont imprimées (fichier, code, détail), rien n'est écrit, code 1. Aucun message ne contient la valeur d'un secret ni un `raw` réservé.

| Code | Règle exacte | Portée |
|---|---|---|
| `key_pattern` | un membre contient les octets `sk-ant-`, `sk-or-` ou `Bearer ` | les deux archives, tous les membres, binaires compris |
| `secret_value` | un membre contient la valeur d'une variable de `SECRET_ENV_VARS = ("JUDILIBRE_KEY_ID", "PISTE_CLIENT_ID", "PISTE_CLIENT_SECRET", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY")`, lue dans l'environnement au moment de la commande, en octets UTF-8 ou sous sa forme échappée JSON ; variable absente ou valeur de moins de 8 caractères ignorée ; le détail nomme la variable, jamais la valeur | les deux archives, tous les membres |
| `reserved_example` | un membre texte (`.jsonl`, `.json`, `.md`, `.py`, `.txt`) contient un `raw` d'un `examples.jsonl` de `<root>/heldout/*/*/`, cherché sous sa forme de littéral JSON (`json.dumps(raw, ensure_ascii=False)` et `ensure_ascii=True`, guillemets compris) ; les `raw` de moins de 12 caractères (seuil d'AD-19) sont sautés et leur nombre imprimé ; le détail donne tâche, jeu et `id` | archive des runs seulement (l'archive de R publie son réservé à dessein, R2) |
| `no_heldout` | `<root>/heldout/` absent ou vide : le contrôle précédent est impossible | archive des runs |
| `r_without_republish` | un membre est un artefact de R alors que `r_republish` n'est pas `true` : séance dont `open.task` est dans `r_tasks`, témoin dont `run.json.task` y est, `eval*.json` dont `target.task` y est | archive des runs ; l'archive de R n'est alors pas construite |
| `r_forbidden_field` | une clé `text`, `zones` ou `text_highlight`, à toute profondeur, dans un JSON ou une ligne JSONL de l'archive de R (condition 1 de la section 2) | archive de R |
| `r_source_mismatch` | `sources.jsonl` absent, `id` différents de ceux d'`examples.jsonl`, `class` hors `{real, fake}`, `source` hors `judilibre`, `ce-opendata`, `jade`, `slm:<tag>`, vraie dont la source est `slm:`, ou fausse attribuée à une base publique (condition 3) | archive de R |
| `r_attribution_missing` | le fichier `--notice` (défaut `NOTICE` à la racine du dépôt) ne contient pas « base Open Data Judilibre de la Cour de cassation » (condition 2) | archive de R |
| `output_exists` | `runs-lot<N>.tar.gz` existe déjà dans `--out` (pas d'écrasement) | sortie |

Les conditions 4 (vraies non retouchées) et 5 (CGU) ne se contrôlent pas sur l'archive : la 4 relève des tests de 1-13, la 5 est remplie (`r_republish = true`, 2026-11-07).

`--dry-run` : contrôles et listes (inclus, ignorés, raws sautés), aucune écriture, code 1 si un refus. Sortie normale : chemins des archives et de `SHA256SUMS`, nombres de séances, de témoins, de membres, archive de R construite ou non et pourquoi.

### Contrat partagé avec 1-13 (à envoyer maintenant)

1-14a fonctionne sans R ; pour que R entre sans changement de code, 1-13 respecte :

- tâche R nommée `legal_r`, inscrite au registre, encodeur de famille `legal.chars@1` (amendement d'AD-4) ; séances et témoins sous `runs/1/` selon AD-12 ; identifiants d'exemples distincts du préfixe `legal-r` déjà pris par les exemples de séance de S-réservé ;
- jeux `data/legal_r/<jeu>/` et `heldout/legal_r/<jeu>/` au format d'AD-16, plus `sources.jsonl` (`id`, `class`, `source`) à côté de `labels.jsonl` ; `dataset.json` avec la date d'extraction ; `held_out_types` dans `dataset.json` seulement si R tient des types à l'écart ;
- si 1-13 retient un autre nom, il le dit à l'orchestrateur, qui change `r_tasks` dans `config/publish.toml` (configuration, pas code).

### Ce qui est écrit où

| Écrit | Par | Où |
|---|---|---|
| copies des artefacts, `provenance.jsonl` | `scripts/rassembler_runs.py` | `C:\Users\Utilisateur\nnww-artefacts\` |
| `eval.json` v2, `eval-cross-<tâche>-<jeu>.json` | `nnww evaluate` | à côté de chaque dossier gelé, dans l'emplacement rassemblé |
| `lot1.md`, `lot1.json` | `nnww table` | `docs/mesures/` (commités) |
| `runs-lot1.tar.gz`, `r-lot1.tar.gz`, `SHA256SUMS` | `nnww publish` | `<root>/dist/lot1/` (jamais dans le dépôt) |
| `r_tasks` | dev de 1-14a | `config/publish.toml` |

Rien n'écrit dans les worktrees sources, dans un journal, ni dans `frozen/`.

### Critères d'acceptation

1. **Rassemblement sans écriture dans les sources.** Given les cinq worktrees, When `scripts/rassembler_runs.py --to <tmp> --from …` tourne deux fois, Then la seconde ne copie rien, aucun fichier source ne change (sha256 et mtime), `data/r/` et les `eval*.json` ne sont pas copiés ; Given un même chemin à deux contenus, Then code 1 et rien de copié (`test_gather_copies_without_touching_sources`, `test_gather_is_idempotent`, `test_gather_refuses_conflicting_file`, `test_gather_skips_eval_files_and_raw_collection`).
2. **Mesures natives.** Given une séance A-littéral gelée et son jeu réservé, When `nnww evaluate --heldout-root` tourne, Then `eval.json` v2 porte `accuracy`, `by_label`, `by_type`, `target` avec les sha256 du jeu, et deux exécutions ne diffèrent que par `ts` (`test_evaluate_writes_metrics_v2`, `test_evaluate_metrics_are_deterministic`).
3. **Vérification avant lecture du réservé.** Given un poids modifié après le gel, When on évalue, Then refus `fingerprint_mismatch` sans ouvrir `labels.jsonl` ; Given un `labels.jsonl` qui ne correspond plus à `dataset.json`, Then refus `heldout_fingerprint` (`test_evaluate_verifies_freeze_before_heldout`, `test_evaluate_refuses_heldout_not_matching_dataset_json`).
4. **B évalué par le bac à sable.** Given une séance B gelée, When on l'évalue, Then `rules.py` passe par `sandbox.run` profil B avec les seules chaînes brutes, et des règles en échec donnent `metrics.error` sans exactitude (`test_evaluate_b_through_sandbox`, `test_evaluate_b_failure_is_error_not_score`).
5. **Robustesse hors distribution.** Given un jeu dont `dataset.json` déclare `held_out_types`, Then `ood` compte exactement ces types ; Given S (liste vide), Then `ood` est nul (`test_ood_group_follows_dataset_json`).
6. **Lisibilité.** Given un réseau écrit à la main dont le bloc 0 détecte seulement le type `t01` et le bloc 1 seulement `t02`, When on évalue, Then score 1,0 ; blocs aux types déclarés échangés, Then 0,0 ; une unité sans effet compte neutre et reste au dénominateur (`test_legibility_matches_declared_blocks`, `test_legibility_swapped_blocks_scores_zero`, `test_neutral_unit_counts_in_denominator`).
7. **Évaluation croisée.** Given un réseau de `legal_s`, When `--on legal_s_reserved:eval`, Then `eval-cross-legal_s_reserved-eval.json` porte `cross: true`, `written_task: legal_s`, et `eval.json` n'est pas touché ; `--on legal_s:eval` sur ce réseau donne `cross_same_task` ; un encodeur étranger donne `encoder_mismatch` ; une tâche `legal_r` ajoutée au registre par un test est acceptée sans autre code (`test_cross_evaluation_writes_separate_file`, `test_cross_refuses_same_task`, `test_cross_refuses_foreign_encoder`, `test_cross_accepts_a_task_registered_later`).
8. **Tableau régénéré, sans saisie.** Given des artefacts de test (deux tentatives dont une rejouée, un témoin C sur deux graines, une séance à drapeaux), When `nnww table` tourne deux fois, Then mêmes octets, la rejouée est hors agrégats et listée, coût facturé et équivalent API sont dans des colonnes séparées (`test_table_is_byte_reproducible`, `test_table_counts_latest_session_per_attempt`, `test_table_separates_billed_and_equiv`, `test_table_reads_only_runs_and_ledger`).
9. **Séance signalée jugée avant conclusion.** Given une séance comptée à drapeaux sans décision, When `nnww table --strict`, Then code 1 et « à juger » ; avec une décision `audit = "judged"`, Then code 0 et jugement recopié ; un `id` inconnu dans le fichier de décisions donne code 1 (`test_strict_fails_on_unjudged_flagged_session`, `test_decision_unknown_id_is_error`, `test_excluded_session_leaves_aggregates`).
10. **Publication : les trois refus de `invoke_dev_with`.** Given une archive dont un journal contient `sk-or-…`, Then refus `key_pattern` et rien d'écrit (`test_publish_refuses_key_pattern`) ; Given un journal contenant le littéral JSON d'un `raw` de `heldout/`, Then refus `reserved_example` sans le `raw` dans le message (`test_publish_refuses_reserved_example`) ; Given une séance `legal_r` et un `publish.toml` de test à `r_republish = false`, Then refus `r_without_republish` (`test_publish_refuses_r_artifact_without_r_republish`).
11. **Publication : secrets, R, reproductibilité.** `test_publish_refuses_known_secret_value` (paramétré sur les 5 variables), `test_publish_refusal_never_prints_secret`, `test_publish_ignores_short_or_unset_secret`, `test_publish_skips_raws_under_12_chars`, `test_publish_excludes_bundle_and_lot_files`, `test_publish_archive_is_byte_reproducible`, `test_publish_sha256sums_match_members`, `test_publish_r_accepted_with_r_republish`, `test_publish_r_dataset_refuses_forbidden_fields`, `test_publish_r_dataset_refuses_fake_attributed_to_public_base`, `test_publish_r_dataset_requires_notice_attribution`, `test_publish_refuses_existing_output`, `test_publish_dry_run_writes_nothing`. Tous les tests passent un `publish.toml` temporaire : le fichier réel n'est jamais lu par les tests de refus.
12. **Frontière.** `report/` et `publish/` n'importent ni `session`, ni `providers`, ni `sandbox`, ni `baselines`, ni `torch` (`test_report_and_publish_follow_dependency_graph`, dans `tests/test_publish.py`, pour ne pas toucher `tests/test_boundary.py`) ; les tests existants de `test_boundary.py` restent verts.
13. **Sur les artefacts réels (acceptation, en fin de story, CPU seul).** Given l'emplacement rassemblé, When `nnww evaluate --lot-dir …/runs/1 --heldout-root …/heldout`, puis `nnww evaluate --lot-dir …/runs/1 --from-task legal_s --on legal_s_reserved:eval`, puis `nnww table --lot 1 --root …`, puis `nnww publish 1 --root … --dry-run`, Then : 9 + 9 séances jouet et 28 séances S gelées évaluées, 144 témoins évalués ; le tableau redonne les valeurs des comptes rendus : `legal_s-A-program-1e4-sonnet-5.5-t1-20261106T061605Z` 2744/4000, Fable A-programme 10⁵ 3935/4000, MiMo B S-réservé 3589 et 3600/4000, MiMo B `legal_s` étape 1 3968/4000 (case à effort par défaut), C `legal_s` N = 64 graine 0 2073/4000, réentraînement de la séance Sonnet A-programme 10⁴ t1 graine 0 3489/4000 ; les deux séances `fragment_overlap` de 1-10 sont « à juger » ; `--dry-run` ne refuse rien. Écarts éventuels : consignés dans la PR, pas corrigés à la main.

### Fichiers que 1-14a ne touche pas (1-13 avance en parallèle)

- Jeu R et tâches : `src/nn_weight_writing/datasets/**` (normaliseur, générateur de R), `src/nn_weight_writing/tasks/**` (dont `tasks/legal/*`, `tasks/registry.py`, `tasks/io.py`), `data/` et `heldout/` de tout worktree, en particulier `data/r/` et `data/legal_r/`.
- Harnais : `session/**`, `providers/**`, `sandbox/**`, `network/**`, `journal/**` (import seul), `budget/ledger.py`, `budget/ledger.csv`.
- Témoins : `baselines/**`, `config/train.toml`, `scripts/temoins_c_f.py`, `scripts/reentrainement.py`, `scripts/jeux_temoins.py`, `scripts/exactitude_reserve.py`, `scripts/collecte*`.
- Configuration : `config/models.toml`, `config/pricing.toml`, `config/protocol.toml` (une seule `protocol_sha256` au lot 1) ; dans `config/publish.toml`, seulement l'ajout de `r_tasks`.
- `evaluation/score.py`, `evaluation/labels.py` ; `pyproject.toml`, `uv.lock`, `__init__.py` (version : 1-14b).
- Dans `cli.py` : les blocs `datagen` et `train` de `build_parser` (1-13 y ajoute `legal_r`) ; 1-14a modifie seulement `_evaluate` et le bloc `evaluate`, et ajoute `_table`, `_publish` et leurs sous-commandes après le bloc `ledger`.
- Documents : `docs/experiences/**`, `docs/verifications/**`, `docs/SOURCES.md`, specs, spine, `run-autonome.md`, `sprint-status.yaml`, `tests/test_boundary.py`.

## 1-14b — Rapport et release (après 1-13)

### Étapes

1. Rassembler le worktree de 1-13 (`scripts/rassembler_runs.py`, avec `data/legal_r` et `heldout/legal_r`), puis `nnww evaluate --lot-dir` natif, et les évaluations croisées vers R de tous les réseaux et règles de `legal_s` et `legal_s_reserved` (`--on legal_r:<jeu>`), C et F compris (piste R3 du constat 1-3 : entraîner sur S, évaluer sur R).
2. Rendre les jugements (liste ci-dessous), chacun consigné comme `décision` au journal de `run-autonome.md` **et** dans `docs/mesures/decisions-lot1.toml`, avant toute conclusion.
3. `nnww table --lot 1 --strict` vert ; commit de `docs/mesures/lot1.md`, `lot1.json`, `decisions-lot1.toml`.
4. `NOTICE` : attribution de la section 2 du constat 1-3, mot pour mot, date d'extraction de R remplie (miroir HF seulement s'il a servi) ; mention de l'origine SLM des fausses.
5. `nnww publish 1 --root … --dry-run`, puis sans `--dry-run` ; sha256 de `runs-lot1.tar.gz` et `r-lot1.tar.gz` cités dans le rapport. Code de B : les `rules.py` des séances B comptées, extraits de l'archive contrôlée, copiés dans `docs/rapport-lot1/b/<session_id>.py` (CAP-13 : code de B dans le dépôt).
6. `docs/rapport-lot1.md` (contenu ci-dessous).
7. Version `0.1.0` dans `pyproject.toml` et `src/nn_weight_writing/__init__.py` (`test_version_matches_pyproject`), `uv lock`, PR, fusion par merge commit ; `git log -1` sur `main`.
8. Tag annoté `v0.1.0` sur le merge commit, `gh release create v0.1.0 runs-lot1.tar.gz r-lot1.tar.gz SHA256SUMS --title "v0.1.0 — lot 1, reproduction critique" --notes-file …` ; notes : réponse courte, tableau des cases, sha256, attribution de R (section 2), commande de réévaluation. Vérifier après envoi que les sha256 des assets téléchargés égalent `SHA256SUMS`.
9. Topic GitHub `status-*` du dépôt mis à jour (consigne globale), si Anaël le veut.
10. Brouillon du billet LinkedIn en réponse à Nuss remis à Anaël par notification, hors dépôt (`C:\Users\Utilisateur\nnww-artefacts\billet-lot1-brouillon.md`), **jamais publié par l'agent**.

### Jugements à rendre (avant les conclusions)

| Séance ou objet | Question | Source |
|---|---|---|
| `legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z` | `fragment_overlap` (2 `script_run`, 4 fragments) : vocabulaire de format ou recopie d'exemples ? | 1-10, `run-autonome.md` |
| `legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z` | `fragment_overlap` (« ass. civ. 1r », « ass. civ. 2e »…) : idem | 1-10 |
| séances de 1-13 signalées | idem, liste donnée par `nnww table` | 1-13 |
| étapes 1 et 2 de MiMo (effort par défaut, puis medium à 64 000 jetons) | annexes (`annex`) ou cases ? En particulier B `legal_s` étape 1 t3 (3968/4000), seule séance MiMo gelée sur S | `docs/experiences/1-10-s-mimo.md` |
| A-programme 10⁴ MiMo t1 | la règle « dernière séance » compte l'essai de l'étape 3 à la place de l'étape 2 (même `config`, `max_tokens` non journalisé à l'époque) : confirmer | idem |
| F `legal.fields@1` (`annexe-fields1/`) | `annex` | 1-11 |
| séances jouet de 1-8 | calibrage, hors conclusions (methodes-et-lots.md) : `annex` ou section à part | 1-8 |

### Contenu de `docs/rapport-lot1.md`

1. Réponse courte : sur S, A fait-il mieux que B et que C à données égales, pour Sonnet et MiMo ; verdict sur R (comparatif ou plafond, « serrée » si l'intervalle contient 30 %) ; résultat négatif dit comme tel.
2. Protocole : `protocol_sha256`, budget de passes figé (1-8), tentatives par case, porte de coût (sans effet par abonnement), lien vers la spec ; commentaire de `config/protocol.toml` laissé tel quel pour garder une seule empreinte.
3. Données et réserves (tous les reports de `run-autonome.md`, section « Reports au rapport du lot 1 ») :
   - réserves de CAP-1 sur S (15 types dont 3 attestés et 12 reconstruits, format, proportions, chiffre de référence divergent : 97,7 contre 82,8 %, ou 97,8 contre 94,6 %) ;
   - écarts de distribution de S relevés en revue de 1-9 (t02 au Conseil d'État, t14, t07) ;
   - S-réservé à 45 % de Cour de cassation ;
   - R : sources, normaliseur, porte des 30 % (p, intervalle de Wilson, non vérifiables), attribution.
4. Résultats par case (extraits de `lot1.md`) : exactitude, variance, robustesse (types tenus à l'écart, R), lisibilité, taille nominale et effective ; Fable une tentative.
5. Témoins C et F : courbe, F `legal.fields@2` retenu et `@1` en annexe, plateau des 100 époques montré à N = 8 192 seulement ; « même réseau », dont le goulet de 2 unités de Fable A-programme 10⁵ (prédiction constante sur 2 graines sur 3).
6. MiMo : ne tient pas S (troncatures à 64 000 puis 131 072 jetons), 2 séances B gelées sur S-réservé (89,7 et 90,0 %), sortie du choix du modèle du lot 2 ; graine non transmise avant `4fe9975`.
7. Coûts : facturé contre équivalent API, total du lot contre 100 $, contrôle du registre ; équivalent API du pilote Claude Code sous-compté avant 1-8 (0,42 contre 0,83 $), équivalent API non plafonné en abonnement (Fable A-littéral 10⁴ à 14,50 $).
8. Audit de l'interdit statistique : drapeaux par séance et jugements datés.
9. Reproduire : commandes, assets, sha256 des archives, `tree_sha256` de chaque réseau (renvoi à `lot1.md`).
10. Suite : choix du modèle du lot 2 selon la règle des 3 points.

Chaque report de `run-autonome.md` doit avoir sa place : la PR de 1-14b contient la liste des 10 reports cochés avec la section qui le traite.

## Points revenant à Anaël

1. Emplacement unique des artefacts : `C:\Users\Utilisateur\nnww-artefacts\` (et sa sauvegarde éventuelle) ; les worktrees restent intacts jusqu'à la fin du run.
2. Le fichier `docs/mesures/decisions-lot1.toml` porte des décisions (statuts, jugements), pas des mesures : accepté au regard de CAP-12 (« sans saisie manuelle ») ?
3. Moyenne d'exactitude sur les seules tentatives gelées, avec `k/n` affiché, plutôt qu'un échec compté 0 ou au hasard.
4. Définition retenue de la lisibilité (taux de baisse par type, égalités, unités neutres au dénominateur).
5. Release publique : l'agent crée-t-il le tag et la release, ou Anaël après relecture ? Billet : brouillon hors dépôt, publié par Anaël.
6. Énergie estimée (methodes-et-lots.md, PISTES) : absente du tableau faute de formule fixée ; à ajouter plus tard ou à écarter.
7. Collecte brute de 1-12a (`data/r/`) : non publiée par `nnww publish` ; à publier en asset ou non (licences des sorties de SLM non relues, constat 1-3).

## Incertitudes et points pour l'orchestrateur

- Contrat de R (`legal_r`, `sources.jsonl`, préfixe d'`id`) à envoyer à 1-13 dès maintenant ; si 1-13 a déjà choisi autrement, seul `r_tasks` change.
- Spine à amender (proposé, non fait ici) : flèches `report → evaluation.schema` et `publish → evaluation.schema` ; AD-18 complété par R2 (archive de R), R6 (`secret_value`, `JUDILIBRE_KEY_ID`, `PISTE_CLIENT_*` dans la convention de configuration), `system_prompt.md` et `eval-cross-*.json` dans l'archive, `r_tasks`.
- `reserved_example` ne contrôle pas les `raw` de moins de 12 caractères : tous les `raw` jouet (10 caractères au plus) échappent au contrôle. Admis, ces jeux se régénèrent par graine ; un seuil plus bas donnerait des faux positifs sur des chaînes binaires.
- Un `raw` réservé de S peut, par hasard, être écrit tel quel par un agent qui invente une référence : `reserved_example` refuserait alors l'archive ; c'est voulu (décision au cas par cas).
- Règle « dernière séance par tentative » : juste pour toutes les rejouées connues (1-8, 1-10 Sonnet et Fable), ambiguë seulement pour A-programme 10⁴ MiMo t1 (jugement listé).
- Les `heldout/` des worktrees sont supposés identiques (mêmes graines) ; le rassemblement le vérifie et refuse sinon.
- Les flottants de la passe NumPy peuvent différer d'une machine à l'autre ; une unité à la limite de l'égalité pourrait changer de classe de lisibilité. Le tableau est régénéré sur le poste d'Anaël.

## Décisions après second avis (orchestrateur, 2026-11-07)

Ces décisions priment sur le texte ci-dessus quand elles le contredisent.

- **Q1 — Archive de R.** `r-lot1.tar.gz` suit R2 du constat 1-3 : métadonnées, étiquettes, sources et manifeste daté du jeu R, réservé compris (le jeu R ne se régénère pas par graine et la publication sert à la réévaluation par un tiers, Success signal). Aucun `raw` au-delà de la référence normalisée elle-même, ni texte, ni nom. AD-18 du spine est amendé en ce sens dans la PR (R2, R6, `system_prompt.md`, `r_tasks`), avec les flèches `report → evaluation.schema` et `publish → evaluation.schema`. Tout lot ultérieur qui voudrait un R réservé le retire.
- **Q2 — Portée des contrôles de R.** Champs interdits, noms de parties, longueur de `raw` et source s'appliquent à chaque fichier de chaque archive, pas seulement à l'archive de R.
- **Q3 — Toute sortie publiée est contrôlée.** Les mêmes contrôles (secret, réservé, R) portent sur `docs/mesures/lot1.{md,json}`, `docs/mesures/decisions-lot1.toml`, puis en 1-14b `docs/rapport-lot1.md`, les notes de release et le billet. Une commande (`nnww publish --check PATH...`) le fait ; `nnww table` l'appelle sur ce qu'il écrit et échoue s'il refuse.
- **Q4 — Recherche du réservé normalisée.** Chaînes JSON décodées récursivement, échappements Python et JSON décodés, casse et espaces normalisés, puis recherche du `raw` complet normalisé. Tests : double échappement, littéral Python, retour à la ligne.
- **Q5 — `secret_value`.** Charge `.env` en plus de l'environnement ; liste = les 5 variables ci-dessus + `CLAUDE_CODE_OAUTH_TOKEN` + toute variable d'environnement dont le nom finit par `_KEY`, `_SECRET` ou `_TOKEN`. Affiche le nombre de valeurs contrôlées (jamais les valeurs) ; avertissement si aucune.
- **Q6 — Décisions et tableau.** Le fichier de décisions est admis (jugements consignés, `invoke_dev_with` de 1-14). Le tableau donne pour chaque case l'agrégat de toutes les séances **et** l'agrégat après décisions, et liste chaque séance exclue ou mise en annexe avec son motif. « Rien d'autre » est remplacé par la liste exacte des entrées : journaux, `run.json`, `eval.json`, `eval-cross-*.json`, `frozen/manifest.json` (témoins), le fichier de décisions, `budget/ledger.csv`.
- **Q7 — Moyenne d'exactitude.** Une tentative non gelée (échec de budget, erreur, gel invalide) compte 0 dans la moyenne principale d'exactitude réservée ; la moyenne sur les seules gelées, avec `k/n`, vient en colonne secondaire. (Remplace le point 3 de « Points revenant à Anaël ».)
- **Q8 — Lisibilité.** Une unité est lisible si son extinction fait baisser l'exactitude sur un type déclaré par son bloc d'au moins 5 points **et** d'au moins le double de la plus forte baisse sur un autre type ; égalité = non lisible. Comptes en entiers, part écrite en fraction exacte. Tests : `forward_masked` sans masque égale `layers.forward` ; un cas intermédiaire. (Remplace la règle « touche surtout le type déclaré ».)
- **Q9 — Réservé explicite.** Les mesures demandent `--heldout-root` explicite ; aucune lecture implicite de `heldout/` du répertoire courant. Tests existants inchangés dans leur attente.
- **Q10 — Contrôles de R sur `raw`.** Motifs de noms de parties (` c/ `, ` contre `, `M.`, `Mme`, `société …` dans une référence) et longueur maximale fixée ; `r_attribution_missing` vérifie aussi la date d'extraction et l'URL de la licence.
- **Q11 — Chemins refusés.** `publish` refuse aussi tout chemin sous `interne/`, `collecte/` ou `cache/` (contrat de 1-12) et toute collecte brute de 1-12a (non publiée au lot 1).
- **Q12 — Registre et tentatives.** Le total facturé se compare au plafond de 100 $ du lot sur `billed_usd` ; l'équivalent API (`cost_equiv_usd`) est donné à part. Règle de tentative : la dernière séance gelée d'une tentative compte si elle existe, sinon la dernière.
- **Q13 — Rebase avec 1-13.** 1-13 ajoute ses commandes à `cli.py` et sa configuration à `config.py` : les ajouts de 1-14 y restent groupés en blocs délimités. Emplacement des artefacts rassemblés : `C:\Users\Utilisateur\nnww-artefacts\` (validé).

## Réalisé : 1-14a, partie 1 (mesures, ablation, `nnww table`, décisions)

Livré : `EvalRecord` v2 (`target`, constantes de fichiers dans `evaluation/schema.py`, réexportées par `verify.py`), `evaluation/measures.py`, `evaluation/ablation.py`, `verify.evaluate(run_dir, heldout_root=None, *, dataset, on)` et `verify.lot_dirs`, `nnww evaluate` étendu, `report/` (`collect`, `decisions`, `table`, `render`), `nnww table`, `docs/mesures/decisions-lot1.toml`, `docs/mesures/lot1.{md,json}`. Tests : `tests/test_evaluation_measures.py`, `tests/test_report_table.py` (aides dans `tests/artefacts.py`) ; `test_evaluation.py` et `test_toy_witnesses.py` passent sans changement (Q9 : sans `--heldout-root`, vérification seule).

Écarts à la spec, assumés :

- `measure` et `measure_cross` rendent `(target, metrics)`. Le nouveau fichier `report/render.py` porte le rendu Markdown (`table.py` garde l'agrégation).
- Lisibilité (Q8) : `ablation.units[]` porte `declared_drop`, `other_drop` et `legible` en fractions exactes (`"1/20"`) ; `legibility = {units, legible, neutral, score: "k/n" non réduit, rate}`. « Le double » se lit au sens strict : une baisse déclarée égale à 2 × l'autre n'est pas lisible ; 5 points pile est lisible. Une unité hors de tout bloc compte au dénominateur, jamais lisible.
- Q7 : une tentative en erreur d'évaluation (`metrics.error`) compte 0, comme une non gelée ; une tentative gelée non évaluée rend la moyenne principale indéfinie (et fait échouer `--strict`).
- Décisions : statut `pending` ajouté (question « à juger », sans effet sur les agrégats, `--strict` échoue) ; section `[[group]]` (clés `task`, `config` pour les séances, `path` pour les témoins), une entrée `[[session]]` primant sur un groupe ; un groupe qui ne vise rien est une erreur, comme un `id` inconnu. `--decisions` vaut par défaut `<out>/decisions-lot<N>.toml` (donc `docs/mesures/…` par défaut, et jamais le fichier réel dans les tests).
- Le tableau ajoute la colonne « Par graine (correct/n) » aux témoins et au « même réseau », et le compte `correct/n` dans la section Séances, pour recouper les comptes rendus.
- `lot_dirs` classe un journal illisible parmi les gelées : `evaluate` le refuse alors (`no_freeze_record`) au lieu de le taire.

Vérification sur les artefacts (copie de lecture des worktrees 1-8, 1-8s, 1-10s, 1-10m, 1-11 dans un dossier temporaire, sans `bundle/` ni `eval*.json` ; aucune écriture dans les worktrees) : 190 dossiers évalués (46 séances gelées : 9 + 9 jouet, 28 S ; 144 témoins), 29 non gelées listées, croisée `legal_s → legal_s_reserved:eval` sans refus. Valeurs retrouvées : 2744/4000, 3935/4000 (Fable A-programme 10⁵), 3589 et 3600/4000, 3968/4000 (config `d4523fc4`, effort par défaut), C `legal_s` N = 64 s0 2073/4000, réentraînement s0 3489/4000. Les deux séances `fragment_overlap` de 1-10 sont « à juger ». Coûts : 1,2651 $ facturés (plafond 100 $), 34,5542 $ d'équivalent API ; registre : écart −0,0085 $, 3 lignes sans journal (`live-1-6-*`, `probe-1-2`).

Constats pour 1-14b : `heldout/legal_s/eval` et `heldout/legal_s_reserved/eval` ont les mêmes `examples.jsonl` et `labels.jsonl` (seul `dataset.json` diffère) : l'évaluation croisée S → S-réservé redonne l'exactitude native, avec en plus le groupe des types tenus à l'écart. Plusieurs réentraînements « même réseau » donnent les mêmes comptes (vraisemblablement : même architecture, même graine).

À faire en partie 2 (`nnww publish`, `scripts/rassembler_runs.py`) :

- Q3 : `publish/checks.py` expose les contrôles sur une liste de chemins (`nnww publish --check PATH...`) et `_table` (`cli.py`, bloc table) les appelle sur `lot<N>.md`, `lot<N>.json` et le fichier de décisions avant de rendre 0 ; aujourd'hui `nnww table` n'appelle aucun contrôle.
- Q1 : amender AD-18 du spine (R2, R6, `system_prompt.md`, `eval-cross-*.json`, `r_tasks`) et les flèches `report → evaluation.schema`, `report → config` (plafond du lot, lu par `config.load_protocol`), `publish → evaluation.schema`.
- Le test de frontière de `report/` est `test_report_follows_dependency_graph` (`tests/test_report_table.py`) ; `test_report_and_publish_follow_dependency_graph` reste à écrire pour `publish/`.
- `config.py` et `config/publish.toml` ne sont pas touchés en partie 1 (`PublishConfig`, `r_tasks` : partie 2) ; les ajouts à `cli.py` sont dans des blocs délimités (`# --- evaluate`, `# --- table`) pour le rebase avec 1-13 (Q13).
- Régénérer `docs/mesures/lot1.{md,json}` sur `C:\Users\Utilisateur\nnww-artefacts\` une fois le rassemblement fait (mêmes octets attendus si les entrées sont les mêmes ; l'empreinte comprend `budget/ledger.csv`).
