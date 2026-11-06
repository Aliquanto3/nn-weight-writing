# Story 1-11 (première partie) : témoins C et F sur S et S-réservé

Date : 2026-11-06. CPU seulement (12 coeurs), aucun appel payant (`budget/ledger.csv` intact).

## Protocole

- Jeux : `uv run python scripts/jeux_temoins.py --seed 0 --train 32768` (générateur `legal` v1, graine 0, hors commit). Même générateur que `nnww datagen legal`, seul le jeu d'entraînement passe de 8 192 à 32 768 ; le réservé (flux k = 0, 4 000 références, 15 types, copie identique pour les deux tâches) ne dépend pas de la taille des autres jeux. Aucun `raw` commun entre réservé et entraînement ni entre réservé et paquet de séance (garde du générateur, AD-16, recompté à la revue sur les jeux de 32 768) ; le jeu d'entraînement de S-réservé ne contient aucun des 5 types tenus à l'écart. Le run de N exemples prend les N premiers du jeu mélangé (S : `data/legal_s/train`, 15 types ; S-réservé : `data/legal_s_reserved/train`, 10 types connus). `train` refuse un jeu dont `dataset.json` déclare une autre tâche.
- C : `legal.chars@1` (3 060 entrées), une couche cachée relu de 32, sortie identity de 2 : 98 018 paramètres. F : `legal.fields@2` (2 408 entrées), **même couche cachée de 32** : 77 154 paramètres (`config/train.toml`, `[tasks.legal_s]` et `[tasks.legal_s_reserved]`). `legal.fields@2` garde l'en-tête et le numéro en caractères (2 244 entrées, comme `@1`) et donne les champs extraits en one-hot : jour 1 à 31, mois 1 à 12, année de la décision (1980 à 2039), présence d'une année AA en tête du numéro, année AA ramenée sur la même plage. Aucune information calculée que C n'aurait pas (ni « date valide », ni « bissextile », ni écart précalculé) : F teste la représentation, pas un travail fait à la place du réseau. `legal.fields@1` (scalaires normalisés) est gardé pour la traçabilité, voir l'annexe.
- Entraînement : Adam, lr 0,01, lot de 64, entropie croisée, **100 époques fixes**. Choix fait sur une validation tirée du jeu d'entraînement, jamais sur `heldout/` (AD-12) : `scripts/choix_epoques.py`, apprentissage sur les 8 192 premiers exemples de `data/<tâche>/train`, validation sur les 4 096 derniers (disjoints), graines 0 et 1, paliers relevés dans une seule passe. Tableau ci-dessous : de 100 à 400 époques, la validation gagne au plus 1,0 point sur une graine, 0,6 point en moyenne ; 100 époques sont sur le plateau et C n'a pas été rejoué. N = 64, 256, 1 024, 8 192, 32 768 ; graines 0, 1, 2 pour tous les N (aucun run n'approche 10 min : 36 s au plus).
- Mesure : `scripts/temoins_c_f.py` (`baselines/curve.py`) ; `verify_frozen` (empreintes de `frozen/` et `tree_sha256`) d'abord, `heldout/<tâche>/eval/` lu ensuite ; contrôle que la tâche du `run.json` est celle du jeu. Moyenne et écart-type (population, 3 graines) en points d'exactitude. Enregistrements bruts : `runs/1/courbe-c-f.jsonl` (hors commit, champ `encoder`), les 60 runs sont gelés sous `runs/1/train/` ; les 30 runs F de `legal.fields@1` sous `runs/1/annexe-fields1/`.
- Groupes : « vraies » = les 2 000 vraies ; « fausses connues » = fausses des types t01-t03, t05, t06, t08, t10, t13-t15 (1 334 ; **le réservé porte bien tous les types**, y compris les 5 tenus à l'écart) ; « fausses tenues à l'écart » = fausses de t04, t07, t09, t11, t12 (666). Pour S, le réseau voit les 15 types à l'entraînement : sa colonne « fausses connues » ne couvre que les 10 mêmes types, par comparabilité, et les 5 autres ne sont pas hors distribution (non rapportés ici). Exactitude globale = 4 000 références.

### Choix du nombre d'époques (validation tirée de l'entraînement, N = 8 192)

| Tâche | Méthode | Graine | 25 ép. | 50 ép. | 100 ép. | 200 ép. | 400 ép. |
|---|---|---|---|---|---|---|---|
| legal_s | C (legal.chars@1) | 0 | 80.5 | 82.3 | 82.6 | 81.6 | 82.8 |
| legal_s | C (legal.chars@1) | 1 | 83.9 | 85.0 | 84.5 | 85.5 | 85.5 |
| legal_s | F (legal.fields@2) | 0 | 82.7 | 81.7 | 82.4 | 82.8 | 83.3 |
| legal_s | F (legal.fields@2) | 1 | 84.2 | 84.7 | 84.8 | 85.2 | 84.9 |
| legal_s_reserved | C (legal.chars@1) | 0 | 95.9 | 96.4 | 96.6 | 96.7 | 96.6 |
| legal_s_reserved | C (legal.chars@1) | 1 | 94.7 | 96.4 | 96.3 | 96.3 | 96.5 |
| legal_s_reserved | F (legal.fields@2) | 0 | 95.9 | 94.8 | 95.6 | 95.7 | 96.2 |
| legal_s_reserved | F (legal.fields@2) | 1 | 95.2 | 95.6 | 95.8 | 95.7 | 95.4 |

La validation de S-réservé ne contient que les 10 types connus (elle vient du jeu d'entraînement) : elle ne dit rien des types tenus à l'écart, et c'est voulu.

## Résultats

### legal_s

| Méthode | N | Graines | Durée moy. (s) | Exactitude (%) | vraies | fausses des 10 types |
|---|---|---|---|---|---|---|
| C | 64 | 0,1,2 | 0.6 | 51.7 ± 0.1 | 55.9 ± 0.5 | 54.0 ± 0.5 |
| C | 256 | 0,1,2 | 0.5 | 55.4 ± 0.1 | 54.7 ± 1.1 | 59.4 ± 0.5 |
| C | 1024 | 0,1,2 | 1.4 | 62.6 ± 0.3 | 60.4 ± 0.5 | 69.9 ± 0.5 |
| C | 8192 | 0,1,2 | 9.2 | 83.7 ± 0.7 | 84.4 ± 1.9 | 89.2 ± 1.4 |
| C | 32768 | 0,1,2 | 36.4 | 94.6 ± 0.1 | 96.5 ± 0.4 | 98.7 ± 0.2 |
| F | 64 | 0,1,2 | 0.6 | 53.3 ± 0.2 | 53.0 ± 0.8 | 60.3 ± 1.1 |
| F | 256 | 0,1,2 | 0.4 | 56.1 ± 0.4 | 58.2 ± 1.2 | 58.8 ± 0.9 |
| F | 1024 | 0,1,2 | 1.2 | 66.8 ± 0.3 | 67.7 ± 0.3 | 72.6 ± 1.0 |
| F | 8192 | 0,1,2 | 8.0 | 84.1 ± 1.4 | 86.0 ± 0.9 | 88.1 ± 2.0 |
| F | 32768 | 0,1,2 | 29.5 | 93.4 ± 0.4 | 94.2 ± 1.0 | 97.5 ± 0.5 |

### legal_s_reserved

| Méthode | N | Graines | Durée moy. (s) | Exactitude (%) | vraies | fausses (10 types) | fausses tenues à l'écart |
|---|---|---|---|---|---|---|---|
| C | 64 | 0,1,2 | 0.3 | 54.3 ± 0.1 | 62.0 ± 0.2 | 51.0 ± 0.2 | 37.4 ± 0.6 |
| C | 256 | 0,1,2 | 0.5 | 58.0 ± 0.0 | 67.2 ± 0.3 | 56.7 ± 0.4 | 33.1 ± 0.5 |
| C | 1024 | 0,1,2 | 1.2 | 64.2 ± 0.2 | 70.6 ± 0.8 | 71.2 ± 0.1 | 31.1 ± 1.5 |
| C | 8192 | 0,1,2 | 8.5 | 83.6 ± 0.5 | 96.8 ± 0.9 | 93.8 ± 0.9 | 23.6 ± 0.9 |
| C | 32768 | 0,1,2 | 33.9 | 86.1 ± 0.5 | 99.5 ± 0.2 | 98.4 ± 0.1 | 20.8 ± 3.2 |
| F | 64 | 0,1,2 | 0.3 | 54.9 ± 0.1 | 58.4 ± 0.5 | 56.5 ± 0.3 | 41.4 ± 0.1 |
| F | 256 | 0,1,2 | 0.4 | 60.0 ± 0.3 | 71.7 ± 0.3 | 58.9 ± 0.5 | 26.8 ± 0.8 |
| F | 1024 | 0,1,2 | 1.1 | 66.9 ± 0.2 | 75.8 ± 0.2 | 74.2 ± 0.6 | 25.8 ± 0.3 |
| F | 8192 | 0,1,2 | 7.7 | 83.0 ± 0.2 | 96.5 ± 0.4 | 92.8 ± 0.2 | 22.9 ± 0.4 |
| F | 32768 | 0,1,2 | 28.3 | 86.1 ± 0.5 | 99.8 ± 0.1 | 98.0 ± 0.4 | 21.3 ± 2.8 |

## Lecture

- Durées : de 0,2 s (N = 64) à 36 s (N = 32 768) par run, C et F confondus.
- C monte lentement (52-55 % à N ≤ 256, 63 % à 1 024), puis 84 % à 8 192 et 94,6 % à 32 768 sur S : la courbe n'est pas saturée à 32 768. Sur S-réservé, C atteint 83,6 % puis 86,1 % : les vraies et les fausses des types connus dépassent 98 % à 32 768, mais les 5 types tenus à l'écart restent à 21 % (en dessous du hasard, une fausse de ces types est prise pour une vraie : le réseau a appris « tout ce qui ne viole pas un des 10 types est vrai »).
- F (`legal.fields@2`) suit C : il le devance de 4 points à N = 1 024 sur les deux tâches (66,8 contre 62,6 % sur S, 66,9 contre 64,2 % sur S-réservé), l'égale à 8 192 (84,1 contre 83,7 % ; 83,0 contre 83,6 %), et reste à 1,2 point sous C à 32 768 sur S (93,4 contre 94,6 %), à égalité sur S-réservé (86,1 %). Les types tenus à l'écart échouent autant avec F qu'avec C (21 à 23 % au-delà de 8 192). Réponse à la question de F : extraire les champs de la date et du numéro accélère un peu l'apprentissage aux petits N, mais n'explique pas un écart de plus de quelques points ; un écart A − C plus grand ne viendra pas de la représentation des entrées. Réserve : un seul réglage de F (même couche cachée et mêmes hyperparamètres que C).
- Point où C rattrape les séances A de 1-10 : laissé à 1-14 (séances pas encore mesurées).

## Seconde partie (non jouée)

Réentraînement de chaque architecture écrite en 1-10 à N = 8 192 depuis des poids aléatoires :

```
uv run --group train nnww retrain runs/1/<session_id> --data data/<task>/train --n 8192 --seed <s> --lot 1
```

Vérifie les empreintes de la séance gelée, ne relit que son manifeste, refuse un jeu d'une autre tâche que celle de la séance, entraîne depuis des poids aléatoires (hyperparamètres de `config/train.toml` de la tâche), gèle sous `runs/1/train/<session_id>-retrain-n8192-s<s>/` (`run.json` porte `dataset.retrained_from`). Mesure ensuite par `baselines.curve.measure(run_dir, tâche, heldout/<tâche>/eval)`. Réserves : le jeu `data/<task>/train` doit être celui de 8 192 ou plus ; un manifeste d'une séance qui n'utilise ni `legal.chars@1` ni `legal.fields@2` (ou `@1`) est refusé.

## Annexe : F avec `legal.fields@1` (premier passage, remplacé)

Premier passage de F, avec `legal.fields@1` (2 249 entrées, 72 066 paramètres) : jour / 31, mois / 12 et années (décision et AA) en scalaires normalisés `(année − 1980) / 50`, bornés à [0, 1]. Ce codage rend quasi inapprenables pour un MLP de 32 unités les types qui comparent deux champs à un an près (t01, t09 : un an vaut 0,02), la bissextilité (t15) et les conjonctions jour × mois ou année × mois (t02, t06). Le second avis de la revue l'a mesuré sur le jeu d'entraînement à N = 8 192, F@1 contre C, exactitude des fausses par type : t01 0,15 / 0,54 ; t02 0,43 / 0,89 ; t06 0,56 / 0,95 ; t09 0,26 / 0,43 ; t15 0,52 / 0,95. La conclusion « F n'aide pas » du premier compte rendu mesurait ce codage, pas la représentation des entrées : F a été refait avec `legal.fields@2`. Runs gelés : `runs/1/annexe-fields1/` (toujours mesurables, `legal.fields@1` reste lu).

| Tâche | N | Exactitude (%) | vraies | fausses des 10 types | fausses tenues à l'écart |
|---|---|---|---|---|---|
| legal_s | 64 | 53.2 ± 0.2 | 53.3 ± 0.9 | 58.8 ± 0.2 | |
| legal_s | 256 | 55.6 ± 0.3 | 55.9 ± 0.7 | 57.3 ± 0.8 | |
| legal_s | 1024 | 62.3 ± 0.2 | 61.2 ± 0.8 | 66.5 ± 1.2 | |
| legal_s | 8192 | 72.0 ± 2.0 | 75.2 ± 1.9 | 72.0 ± 3.1 | |
| legal_s | 32768 | 88.2 ± 0.8 | 92.9 ± 1.5 | 88.6 ± 3.6 | |
| legal_s_reserved | 64 | 53.2 ± 0.1 | 52.6 ± 0.3 | 59.0 ± 0.5 | 43.4 ± 0.7 |
| legal_s_reserved | 256 | 57.7 ± 0.3 | 64.5 ± 0.8 | 56.7 ± 0.8 | 39.1 ± 0.9 |
| legal_s_reserved | 1024 | 61.9 ± 0.5 | 65.8 ± 0.7 | 66.5 ± 0.8 | 40.8 ± 1.4 |
| legal_s_reserved | 8192 | 70.5 ± 0.6 | 79.7 ± 2.4 | 75.1 ± 2.2 | 33.9 ± 1.9 |
| legal_s_reserved | 32768 | 80.5 ± 1.0 | 92.7 ± 0.5 | 87.1 ± 3.3 | 30.8 ± 0.4 |

## Revue

### Passe 1 (2026-11-06, SHA revu 224f1a6)

Branche rebasée sur `origin/main` (PR #22) sans conflit avant la revue.

- Important, medium, second avis 1 : `legal.fields@1` code jour, mois et années en scalaires, F mesurait ce codage. Corrigé : `legal.fields@2` (one-hot, sans drapeau calculé), `@1` gardé lisible, courbe F rejouée (30 runs), `@1` en annexe.
- Important, medium, second avis 2 : choix des 100 époques sans jeu de mesure nommé, aucune trace dans le code ni l'historique (invérifiable, sélection possible sur le réservé). Corrigé : `scripts/choix_epoques.py`, validation tirée du jeu d'entraînement ; 100 époques confirmées sur le plateau, C non rejoué.
- Important, medium, second avis 4 : `train` et `retrain` acceptaient un jeu de l'autre tâche juridique (même encodeur, mêmes classes). Corrigé : refus si `dataset.json` déclare une autre tâche (exigé pour les tâches juridiques), test ajouté.
- Nit, low, second avis 3 : `retrain` chargeait aussi les poids de la séance. Corrigé : relecture du seul manifeste après `verify_frozen` (qui hache tout `frozen/`, nécessaire).
- Important, medium, revue : la reprise de `scripts/temoins_c_f.py` sautait un run déjà enregistré par (tâche, méthode, N, graine) : un F d'une nouvelle version d'encodeur aurait été sauté en silence. Corrigé : champ `encoder` dans chaque enregistrement, clé de reprise par encodeur.
- Étanchéité train / réservé recomptée sur les jeux de 32 768 (aucun `raw` commun, aucun type tenu à l'écart dans l'entraînement de S-réservé) ; dénominateurs par groupe et isolement de PyTorch (test `test_session_side_never_loads_torch`) : rien à signaler.
- Complexité : 0 constat (enregistrements ajoutés en O(1), reprise par ensemble).
