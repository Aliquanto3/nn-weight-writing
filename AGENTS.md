## nn-weight-writing

Un LLM écrit tous les poids d'un petit réseau de neurones, sans gradient, d'après l'expérience de Jacob Lauritzen et Jorick Nuss (novembre 2026). Le résultat est comparé aux règles écrites en code, à l'entraînement standard et aux méthodes des dépôts voisins `slm-weight-editing` (édition de poids) et `mood-steering-slm` (steering), lus seulement depuis ici. Sources : `docs/SOURCES.md` ; pistes : `docs/PISTES.md`.

## Policy

- Dépôt public : jamais de poids, de jeux de données ni de sorties volumineuses dans un commit (`data/`, `models/`, `heldout/` sont ignorés).
- Protocole d'écriture (à préciser au cadrage, à ne pas contourner ensuite) :
  - l'agent qui écrit les poids n'exécute le réseau que par le harnais, qui compte et journalise chaque passe, dans un budget fixé avant la séance ;
  - aucun gradient ni entraînement pour la méthode « poids écrits » ;
  - les jeux d'évaluation restent dans `heldout/` ou hors du dépôt, et l'agent ne les lit jamais ; l'évaluation tourne après le gel des poids, par une commande à part.
- Jamais de push sur `main` : branche préfixée (`feat/`, `fix/`, `docs/`, `chore/`, `exp/`), PR, fusion par merge commit.
- Ne jamais figer une version de dépendance de mémoire : `uv add` résout la version réelle.
- Docs, commits et PR en français ; identifiants de code en anglais.

## Running and verifying

- `uv sync`, puis `uv run pytest`, `uv run ruff check .` et `uv run ruff format --check .` (ligne de 100).
- Toujours `uv run python`, jamais `python` nu.

## Conventions

- Commits : `Préfixe: description en français` (`Feat:`, `Fix:`, `Docs:`, `Chore:`, `Exp:`).
- Versionnage SemVer dans `pyproject.toml` et `__init__.py`, tag annoté et release GitHub à chaque lot livré.
