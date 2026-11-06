# Story 1-11 (première partie) : témoins C et F sur S et S-réservé

Date : 2026-11-06. CPU seulement (12 coeurs), aucun appel payant (`budget/ledger.csv` intact).

## Protocole

- Jeux : `uv run python scripts/jeux_temoins.py --seed 0 --train 32768` (générateur `legal` v1, graine 0, hors commit). Même générateur que `nnww datagen legal`, seul le jeu d'entraînement passe de 8 192 à 32 768 ; le réservé (flux k = 0, 4 000 références, 15 types, copie identique pour les deux tâches) ne dépend pas de la taille des autres jeux. Aucun `raw` commun entre réservé et entraînement ni entre réservé et paquet de séance (garde du générateur, AD-16, recompté à la revue sur les jeux de 32 768) ; le jeu d'entraînement de S-réservé ne contient aucun des 5 types tenus à l'écart. Le run de N exemples prend les N premiers du jeu mélangé (S : `data/legal_s/train`, 15 types ; S-réservé : `data/legal_s_reserved/train`, 10 types connus). `train` refuse un jeu dont `dataset.json` déclare une autre tâche.
- C : `legal.chars@1` (3 060 entrées), une couche cachée relu de 32, sortie identity de 2 : 98 018 paramètres. F : `legal.fields@2` (2 408 entrées), **même couche cachée de 32** : 77 154 paramètres (`config/train.toml`, `[tasks.legal_s]` et `[tasks.legal_s_reserved]`). `legal.fields@2` garde l'en-tête et le numéro en caractères (2 244 entrées, comme `@1`) et donne les champs extraits en one-hot : jour 1 à 31, mois 1 à 12, année de la décision (1980 à 2039), présence d'une année AA en tête du numéro, année AA ramenée sur la même plage. Aucune information calculée que C n'aurait pas (ni « date valide », ni « bissextile », ni écart précalculé) : F teste la représentation, pas un travail fait à la place du réseau. `legal.fields@1` (scalaires normalisés) est gardé pour la traçabilité, voir l'annexe.
- Entraînement : Adam, lr 0,01, lot de 64, entropie croisée, **100 époques fixes**. Choix fait sur une validation tirée du jeu d'entraînement, jamais sur `heldout/` (AD-12) : `scripts/choix_epoques.py`, apprentissage sur les 8 192 premiers exemples de `data/<tâche>/train`, validation sur les 4 096 derniers (disjoints), graines 0 et 1, paliers relevés dans une seule passe. Tableau ci-dessous : de 100 à 400 époques, la validation gagne au plus 1,0 point sur une graine, 0,4 point en moyenne sur les huit lignes (meilleur palier au-delà de 100) ; 100 époques sont sur le plateau et C n'a pas été rejoué. N = 64, 256, 1 024, 8 192, 32 768 ; graines 0, 1, 2 pour tous les N (aucun run n'approche 10 min : 36 s au plus).
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
- F (`legal.fields@2`) suit C : il le devance à N = 1 024 (4,2 points sur S : 66,8 contre 62,6 % ; 2,7 points sur S-réservé : 66,9 contre 64,2 %), l'égale à 8 192 (84,1 contre 83,7 % ; 83,0 contre 83,6 %), et reste à 1,2 point sous C à 32 768 sur S (93,4 contre 94,6 %), à égalité sur S-réservé (86,1 %). Les types tenus à l'écart échouent autant avec F qu'avec C (21 à 23 % au-delà de 8 192). Réponse à la question de F : extraire les champs de la date et du numéro accélère un peu l'apprentissage aux petits N, mais n'explique pas un écart de plus de quelques points ; un écart A − C plus grand ne viendra pas de la représentation des entrées. Réserve : un seul réglage de F (même couche cachée et mêmes hyperparamètres que C).
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

### Passe 2 (2026-11-06, SHA revu 70b0bb7)

Branche à jour de `origin/main` (2d3eeef), relu `224f1a6..70b0bb7` (équivalent rebasé de `d6df200..70b0bb7`).

- `legal.fields@2` : aucun champ calculé ; « présence d'une AA » est le marqueur d'extraction du motif `^\d{2}[-/]` (le séparateur est lu aussi par C), redondant avec le groupe AA dans la plage. Plage 1980-2039 recomptée sur les deux jeux de 32 768 : décisions 2001-2029, AA 1986-2029, aucun groupe vide ; hors plage, groupe à 0 (documenté, testé). `@1` lisible par `legacy_encoders`, versionnage AD-4 correct : rien à signaler.
- `choix_epoques.py` : ne lit que `data/<tâche>/train`, refuse un chemin sous `heldout/` ; 0 `raw` commun entre les 8 192 premiers et les 4 096 derniers, 0 doublon dans les jeux : rien à signaler.
- Refus d'un jeu d'une autre tâche : jouets sans `composition.task` épargnés ; `tests/test_train.py`, `test_boundary.py`, `test_train_legal.py`, `test_legal_encoders.py` verts, ruff propre : rien à signaler.
- Chiffres : les deux tableaux de résultats et l'annexe reproduits à l'identique par `scripts/temoins_c_f.py table` (`--lot 1` et `--lot 1/annexe-fields1`).
- Nit, low, revue : « devance de 4 points à N = 1 024 sur les deux tâches » (2,7 points sur S-réservé) et « 0,6 point en moyenne » (0,4 sur les huit lignes). Corrigé dans la Lecture et le Protocole.
- Nit, low, revue : le plateau des 100 époques n'est montré qu'à N = 8 192 ; à N = 64 ou 256, 100 époques ne font que 100 à 400 pas d'Adam, et la lecture « F accélère aux petits N » en dépend. Reporté (réserve de protocole, à tester en 1-14 si les petits N servent à une conclusion).
- Complexité : 0 constat.

## Seconde partie : réentraînement des architectures Sonnet 5.5 et Fable 5.1 (18 séances A de 1-10)

Commande : `nnww retrain` (fonction `retrain`, via `scripts/reentrainement.py`), N = 8 192 premiers exemples de `data/<tâche>/train` (celui de la tâche de la séance), graines 0, 1, 2, hyperparamètres de `config/train.toml` de la tâche. Empreinte de la séance vérifiée d'abord, poids de la séance hachés pour l'empreinte (`verify_frozen`), jamais utilisés comme initialisation, `blocks` écartés du manifeste (format de témoin fermé : correctif `9efb27e`). Exactitude mesurée comme en première partie (`baselines.curve.measure`, 4 000 références du réservé, moyenne ± écart-type de population sur 3 graines). Séances de `1-10s` (lecture seule) : 18 séances A, 54 runs, enregistrements bruts `runs/1/reentrainement.jsonl` (hors commit). MiMo n'a gelé aucune séance A (arrêté sur S, voir `docs/experiences/1-10-s-mimo.md`) : cette section ne couvre que Sonnet et Fable. Les séances B n'ont pas de réseau.

Écart = moyenne réentraînée − exactitude de la séance (points). « C 8 192 » = C de référence de la première partie (98 018 paramètres).

| Modèle | Tâche | Case | Tent. | Paramètres | Séance A (%) | Réentraîné, 3 graines (%) | Écart (pts) | C 8 192 (%) |
|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | legal_s | A-program 10^4 | 1 | 30632 | 68.6 | 86.0 ± 0.9 | +17.4 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s | A-program 10^4 | 2 | 30632 | 60.7 | 86.0 ± 0.9 | +25.3 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s | A-program 10^4 | 3 | 30632 | 61.2 | 86.0 ± 0.9 | +24.8 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s | A-program 10^5 | 1 | 171530 | 94.9 | 83.8 ± 0.7 | -11.1 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s | A-program 10^5 | 2 | 306302 | 85.8 | 83.1 ± 0.8 | -2.6 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s | A-program 10^5 | 3 | 245042 | 93.0 | 83.2 ± 0.4 | -9.9 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s | A-literal 10^4 | 1 | 30632 | 58.0 | 86.0 ± 0.9 | +28.0 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s | A-literal 10^4 | 2 | 30632 | 66.3 | 86.0 ± 0.9 | +19.7 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s | A-literal 10^4 | 3 | 12254 | 56.4 | 83.1 ± 0.8 | +26.8 | 83,7 ± 0,7 |
| Fable 5.1 | legal_s | A-program 10^4 | 1 | 30632 | 92.2 | 86.0 ± 0.9 | -6.2 | 83,7 ± 0,7 |
| Fable 5.1 | legal_s | A-program 10^5 | 1 | 276349 | 98.4 | 61.5 ± 16.3 | -36.9 | 83,7 ± 0,7 |
| Fable 5.1 | legal_s | A-literal 10^4 | 1 | 30632 | 87.9 | 86.0 ± 0.9 | -1.9 | 83,7 ± 0,7 |
| Sonnet 5.5 | legal_s_reserved | A-program 10^5 | 1 | 98018 | 89.0 | 83.6 ± 0.5 | -5.4 | 83,6 ± 0,5 |
| Sonnet 5.5 | legal_s_reserved | A-program 10^5 | 2 | 131711 | 89.6 | 82.7 ± 0.3 | -7.0 | 83,6 ± 0,5 |
| Sonnet 5.5 | legal_s_reserved | A-program 10^5 | 3 | 196034 | 87.8 | 82.9 ± 0.4 | -4.8 | 83,6 ± 0,5 |
| Sonnet 5.5 | legal_s_reserved | A-literal 10^4 | 1 | 30632 | 80.3 | 82.4 ± 1.6 | +2.2 | 83,6 ± 0,5 |
| Sonnet 5.5 | legal_s_reserved | A-literal 10^4 | 2 | 12254 | 56.4 | 83.1 ± 1.2 | +26.7 | 83,6 ± 0,5 |
| Sonnet 5.5 | legal_s_reserved | A-literal 10^4 | 3 | 21443 | 65.4 | 83.3 ± 0.4 | +18.0 | 83,6 ± 0,5 |


S-réservé, détail du réentraînement (types tenus à l'écart séparés ; C de référence à 8 192 : vraies 96,8 ± 0,9, 10 connus 93,8 ± 0,9, 5 tenus 23,6 ± 0,9) :

| Case | Tent. | Séance A | vraies | 10 connus | 5 tenus |
|---|---|---|---|---|---|
| A-program 10^5 | 1 | 89.0 | 96.8 ± 0.9 | 93.8 ± 0.9 | 23.6 ± 0.9 |
| A-program 10^5 | 2 | 89.6 | 95.8 ± 0.3 | 92.5 ± 0.5 | 23.6 ± 0.4 |
| A-program 10^5 | 3 | 87.8 | 96.6 ± 0.2 | 92.4 ± 0.7 | 22.8 ± 0.6 |
| A-literal 10^4 | 1 | 80.3 | 97.2 ± 1.0 | 92.2 ± 3.6 | 18.7 ± 2.0 |
| A-literal 10^4 | 2 | 56.4 | 96.6 ± 0.7 | 92.1 ± 3.5 | 24.5 ± 1.4 |
| A-literal 10^4 | 3 | 65.4 | 96.8 ± 0.8 | 95.7 ± 1.0 | 18.1 ± 2.4 |


Constats factuels :

- Les trois tentatives Sonnet de A-program 10^4 sur S, deux des trois de A-littéral 10^4 sur S et l'A-littéral et l'A-program 10^4 de Fable ont la même architecture (3 060 → 10 → 2, 30 632 paramètres) : leur réentraînement est identique (86,0 ± 0,9 %, mêmes graines, mêmes données). Cette architecture réentraînée dépasse C de référence (83,7 %) de 2,3 points avec 3 fois moins de paramètres.
- Sonnet, 10^4 sur S : séances A à 56-69 %, réentraînées à 83-86 % (+17 à +28 points). Sur ces architectures, le gel de A-programme et A-littéral reste loin de ce que la forme permet.
- Sonnet, 10^5 sur S : séances A à 85,8-94,9 %, réentraînées à 83,1-83,8 %, soit autant que C (83,7 %), alors que les paramètres vont de 171 530 à 306 302. Les poids écrits dépassent de 2,6 à 11,1 points ceux obtenus par gradient sur la même forme à N = 8 192.
- Fable, 10^4 sur S : A-programme 92,2 % contre 86,0 % réentraîné (poids écrits au-dessus de 6,2 points) ; A-littéral 87,9 % contre 86,0 % (+1,9).
- Fable, 10^5 sur S : la séance est à 98,4 %, le réentraînement à 61,5 ± 16,3 % (graines : 50,0 %, 84,6 %, 50,0 %). L'architecture est 3 060 → 89 → 31 → 33 → 2 → 2, activation `relu` à toutes les couches, dont un goulet de 2 unités `relu` (33 → 2 puis 2 → 2). Les graines 0 et 2 prédisent une classe constante (50,0 %, biais de sortie de la dernière couche négatifs) ; la graine 1 (84,6 %) a un biais de sortie à +3,5. Mécanisme observé : unités `relu` mortes au goulet, prédiction constante ; non retravaillé ici.
- S-réservé, Sonnet : A-program 10^5 à 87,8-89,6 %, réentraînement à 82,7-83,6 %, soit C (83,6 %) ; A-littéral 10^4 de 56,4 à 80,3 % contre 82,4-83,3 % réentraîné. Sur les types tenus à l'écart, le réentraînement donne 18 à 25 % comme C (23,6 %), tandis que les séances B de 1-10 (même moitié) retrouvaient t09 et t11 par déduction : l'écart des séances A sur ces types n'est pas mesuré ici (seule l'exactitude globale de la séance est reprise).

Question de la méthode C, « l'écart vient-il des poids ou de la forme du réseau ? » : constats à N = 8 192 seulement, un seul point ; la conclusion revient à 1-14.

- Sonnet 10^4 sur S et A-littéral 10^4 de S-réservé : la séance A est sous la même forme réentraînée (jusqu'à +28 points au tableau, convention réentraîné − séance).
- Sonnet 10^5, Fable 10^4, S-réservé A-program : la séance A est au-dessus de la même forme réentraînée (de −2,6 à −11,1 points au tableau). C passe à 94,6 % à 32 768 sur S : l'avance de la séance sur C dépend de N.
- Les formes gelées réentraînées à 8 192 sont dans le bruit de C de référence (σ 0,3 à 0,8), sauf le cas Fable 10^5 (goulet `relu` mort) et le 86,0 % de la forme 3 060 → 10 → 2 au-dessus de C.
- Séparer poids et forme demanderait de réentraîner à d'autres N (la forme seule) et de comparer aux séances à N équivalent ; non fait ici.
