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

- Solution à la main : exacte sur tout le domaine de parité et de l'automate (1 024 chaînes), sur bords et grille dense de comparaison, 100 % sur le jeu réservé par `score_frozen` (empreintes vérifiées) ; `nnww evaluate` accepte le dossier gelé (exactitude dans `eval.json` : 1-14) ; poids modifié refusé `fingerprint_mismatch`.
- Témoin B : règles acceptées par le filtre profil B, 100 % sur le jeu réservé via `sandbox.run`.
- Jeux : même graine, mêmes octets ; graines différentes, jeux différents ; aucun `id` ni `raw` commun ; chaque jeu équilibré séparément (écart <= 1), aux tailles limites ; refus d'un jeu existant, d'une taille que le domaine ne permet pas d'équilibrer.
- Témoin C : parité PyTorch/NumPy (4 activations, rtol 1e-5), format AD-17, déterminisme par graine, compare > 85 % sur le réservé (mesuré 96 %).
- AD-13 : seuls `baselines/train.py` et `baselines/torch_layers.py` importent torch ; `cli` sans import de `baselines` en tête ; import de `cli` et du côté séance ne charge pas torch (sous-processus).

## Décisions

- Le réseau de la solution à la main est testé hors évaluation par la même fonction que C et A (`score_frozen`) ; les mesures complètes de `eval.json` restent en 1-14.
- Chaque jeu (séance, réservé) est équilibré séparément ; une taille non équilibrable est refusée (générateur v2). Maxima : parité 1 024 au total, automate 351 par classe (rejet), comparaison 1 000 `equal`, soit 3 000 au total.
- `nnww train` refuse un dossier sous `heldout/` ; `run.json` porte `dataset` (chemin relatif `data/<task>/<jeu>` et sha256 des deux fichiers).
- Sur le jouet, C n'a de sens qu'avec N <= taille du jeu de séance (`n_values` = 64 et 256) ; mesuré (générateur v2, `datagen --seed 0 --n 256 --n-heldout 400`, `train --seed 0`, Windows, CPU) : parité 46 %/48 %, comparaison 93 %/94 %, automate 74 %/91 % (N=64/256). Déterminisme garanti par graine sur une même plateforme ; entre OS, les noyaux CPU de torch peuvent différer à l'ulp (pas de `torch.use_deterministic_algorithms`), d'où des poids non identiques au bit près.

## Reports

- 1-8 : séances A et B sur LLM, `bundle/` du jouet via `materialize_bundle` (la tâche fournit `description`, `encoder_id`, `vocabulary`), calibrage du budget.
- 1-11 : courbe C complète (N jusqu'à 8 192, F), « même réseau » (AD-17).
- 1-14 : mesures de `eval.json` (réservé, par type, ablation).
- Pas de `nnww` pour exécuter le témoin B en `runs/` ; B n'est ici qu'une fonction (`score_rules`), la séance B est en 1-8/1-10.

## Revue

### Passe 1 (2026-11-05, SHA revu be9f7b9)

- Important, medium, second avis 1 : jeu réservé déséquilibré au-delà de l'épuisement d'une classe (comparaison 2000/2000 : 333/834/833 ; automate 400/400 : 249/151). Corrigé : quotas équilibrés par jeu, taille non équilibrable refusée, tests aux bornes exactes.
- Important, medium, second avis 2 : `nnww train` acceptait `heldout/<task>/toy` et `run.json` ne liait pas le jeu. Corrigé : refus sous `heldout/`, champ `dataset` (chemin relatif, sha256) dans `run.json`, tests.
- Rejeté, second avis 3 : la graine (AD-16 l'impose dans `dataset.json`) n'atteint pas `bundle/` : `materialize_bundle` ne recopie que `id`/`raw` et les champs fournis par la tâche ; la reconstruction par lecture du dépôt est hors du modèle de menace.
- Nit, low, second avis 4 : critère « 100 % par `nnww evaluate` » non mesuré par `evaluate`. Corrigé : spec réalignée (mesures en 1-14).
- Nit, low, second avis 5 : reproductibilité de C entre OS non garantie. Corrigé : documenté dans les décisions.
- Nit, low, second avis 6 : chiffres de C non reproductibles. Corrigé : remesurés avec graines et tailles précisées.
- Rejeté, low, second avis 7 : recouvrement entre graines différentes : `datagen` écrit séance et réservé d'un même tirage et refuse un jeu existant ; mélanger deux graines demande une manipulation manuelle.
- Nit, low, second avis 8 : `except ImportError` trop large dans `_train`. Corrigé : `ModuleNotFoundError` limité à `torch`.
- Rejeté, low, second avis 9 : coût CI de torch mesuré à 27-68 s par job, acceptable.
- Complexité : 0 constat (génération O(n), pas de structure qui grossit par événement).

### Passe 2 (2026-11-05, SHA revu c25759d)

- Aucun constat nouveau. Vérifié : bornes exactes (parité 512/512 accepté, 513/512 refusé ; automate 352/350 et 352/352 ; comparaison 1500/1501 et 1500/1502), séance et réservé disjoints (tranches consécutives de chaque classe), refus de `heldout/` éprouvé sur `HELDOUT/`, `heldout\`, `data/../heldout/` et `.\Heldout\compare\..` (Windows), version 2 cohérente (code, test, spec), CI verte sur les trois OS.
- Complexité : 0 constat.
