---
story: "1-7"
title: Tâches jouet et témoins
status: review
branch: feat/1-7-taches-jouet
---

# Story 1-7 : Tâches jouet et témoins

## Objet

Trois tâches jouet à solution exacte (parité, comparaison de nombres, petit automate), leurs jeux reproductibles avec jeu réservé, une solution écrite à la main, le témoin B exécutable et le témoin C PyTorch (CAP-6, CAP-7, CAP-8 ; AD-3, AD-4, AD-12, AD-13, AD-16, AD-17). Les séances A et B sur LLM et le calibrage du budget sont en 1-8.

## Livrables

- `tasks/toy/` : `ToyTask` (`encode`, `decode` par argmax, `vocabulary`, `encoder_id` `{task}.{encoder}@1`) et trois tâches. `parity` : 10 bits, `even`/`odd`. `compare` : « a b » entiers de 0 à 999, `less`/`equal`/`greater`, encodé `[a/1000, b/1000]`. `automaton` : 10 bits, contient `101` (automate à 4 états), `accept`/`reject`. Le vocabulaire fermé du paquet est la liste des classes ; `type_id` = `label` (pas de types d'erreur sur le jouet).
- `datasets/` : `toy.generate` (graine explicite, classes entrelacées puis coupées : `n` exemples de séance, `n_heldout` réservés, ni `id` ni `raw` communs), `io.write_dataset` (`examples.jsonl`, `labels.jsonl`, `dataset.json` avec sha256), `nnww datagen <task|all> --seed S [--n 256] [--n-heldout 400] [--root .]` vers `data/<task>/toy/` et `heldout/<task>/toy/` (ignorés par git). Ids `parity-d00001` (séance), `parity-h00001` (réservé).
- `evaluation/labels.py` (lecteur d'étiquettes, hors séance) et `evaluation/score.py` (`score_frozen` : `verify_frozen` puis chargement et exactitude ; `accuracy`).
- `baselines/handmade.py` : poids calculés à la main (somme alternée d'indicateurs `relu(s-k+1)-relu(s-k)` ; différences `relu(±d)`, `relu(±d-1)` ; fenêtres `relu(x_i-x_{i+1}+x_{i+2}-1)` puis `min(somme,1)`). `baselines/common.py` : `freeze_run` (`frozen/` + `run.json`, `run_id` AD-12). `baselines/rules.py` : règles B (`predict(raw)`) exécutées par `sandbox.run` profil B ; `score_rules`.
- Témoin C : `baselines/torch_layers.py` (registre PyTorch de `dense` et des 4 activations, import/export des poids au format AD-3), `baselines/train.py` (Adam, entropie croisée, `n` premiers exemples du jeu, graine), `config/train.toml` (architecture de référence par tâche : un cachée relu de 32/16/32), `nnww train <task> --data D --n N --seed S [--lot toy] [--runs-root runs]` -> `runs/<lot>/train/<task>-C-n<N>-s<S>/{run.json, frozen/, eval.json}` (`evaluate` appelé après le gel).
- PyTorch : `uv add --group train torch` (2.15.0, Python 3.14 : installation réussie). Source `pytorch-cpu` (marqueur Linux) dans `pyproject.toml` pour éviter la roue CUDA de PyPI ; macOS et Windows : roue PyPI CPU. Import paresseux depuis `cli._train`.
- CI : `uv sync --locked --group train` dans le job matriciel existant (3 OS) ; les tests torch s'exécutent donc partout, et se sautent (`importorskip`) sans le groupe.
- Tests : `test_toy_tasks`, `test_datasets`, `test_toy_witnesses`, `test_train`, `test_boundary` étendu (430 tests au total, ~13 s).

## Critères d'acceptation (tests)

- Solution à la main : exacte sur tout le domaine de parité et de l'automate (1 024 chaînes), sur bords et grille dense de comparaison, 100 % sur le jeu réservé par `score_frozen` (empreintes vérifiées) et `nnww evaluate` ; poids modifié refusé `fingerprint_mismatch`.
- Témoin B : règles acceptées par le filtre profil B, 100 % sur le jeu réservé via `sandbox.run`.
- Jeux : même graine, mêmes octets ; graines différentes, jeux différents ; aucun `id` ni `raw` commun ; équilibre des classes ; refus d'un jeu existant, d'un domaine trop petit.
- Témoin C : parité PyTorch/NumPy (4 activations, rtol 1e-5), format AD-17, déterminisme par graine, compare > 85 % sur le réservé (mesuré 96 %).
- AD-13 : seuls `baselines/train.py` et `baselines/torch_layers.py` importent torch ; `cli` sans import de `baselines` en tête ; import de `cli` et du côté séance ne charge pas torch (sous-processus).

## Décisions

- Le réseau de la solution à la main est testé hors évaluation par la même fonction que C et A (`score_frozen`) ; les mesures complètes de `eval.json` restent en 1-14.
- `compare` plafonne la classe `equal` à 1 000 paires (domaine) ; au-delà les autres classes complètent.
- Sur le jouet, C n'a de sens qu'avec N <= taille du jeu de séance (`n_values` = 64 et 256) ; mesuré, seed 0 : parité 45 %/52 %, comparaison 93 %/96 %, automate 68 %/90 % (N=64/256).

## Reports

- 1-8 : séances A et B sur LLM, `bundle/` du jouet via `materialize_bundle` (la tâche fournit `description`, `encoder_id`, `vocabulary`), calibrage du budget.
- 1-11 : courbe C complète (N jusqu'à 8 192, F), « même réseau » (AD-17).
- 1-14 : mesures de `eval.json` (réservé, par type, ablation).
- Pas de `nnww` pour exécuter le témoin B en `runs/` ; B n'est ici qu'une fonction (`score_rules`), la séance B est en 1-8/1-10.
