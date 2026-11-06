# Story 1-11 (première partie) : témoins C et F sur S et S-réservé

Date : 2026-11-06. CPU seulement (12 coeurs), aucun appel payant (`budget/ledger.csv` intact).

## Protocole

- Jeux : `uv run python scripts/jeux_temoins.py --seed 0 --train 32768` (générateur `legal` v1, graine 0, hors commit). Même générateur que `nnww datagen legal`, seul le jeu d'entraînement passe de 8 192 à 32 768 ; le réservé (flux k = 0, 4 000 références, 15 types, copie identique pour les deux tâches) ne dépend pas de la taille des autres jeux. Aucun `raw` commun entre réservé et entraînement (garde du générateur, AD-16). Le run de N exemples prend les N premiers du jeu mélangé (S : `data/legal_s/train`, 15 types ; S-réservé : `data/legal_s_reserved/train`, 10 types connus).
- C : `legal.chars@1` (3 060 entrées), une couche cachée relu de 32, sortie identity de 2 : 98 018 paramètres. F : `legal.fields@1` (2 249 entrées), **même couche cachée de 32** : 72 066 paramètres. L'architecture de référence convient à `legal.fields@1`, aucune architecture F distincte n'est fixée (`config/train.toml`, `[tasks.legal_s]` et `[tasks.legal_s_reserved]`).
- Entraînement : Adam, lr 0,01, lot de 64, entropie croisée, **100 époques fixes** (400 par défaut du jouet jugé inutile : à N = 8 192, 100 et 300 époques donnent la même exactitude à 0,1 point, essai sur graine 0 ; 300 époques coûtent 3 fois plus). N = 64, 256, 1 024, 8 192, 32 768 ; graines 0, 1, 2 pour tous les N (aucun run au-delà de 8 192 n'approche 10 min : 36 s au plus, donc pas de réduction à 2 graines).
- Mesure : `scripts/temoins_c_f.py` (`baselines/curve.py`) ; `verify_frozen` (empreintes de `frozen/` et `tree_sha256`) d'abord, `heldout/<tâche>/eval/` lu ensuite ; contrôle que la tâche du `run.json` est celle du jeu. Moyenne et écart-type (population, 3 graines) en points d'exactitude. Enregistrements bruts : `runs/1/courbe-c-f.jsonl` (hors commit), les 60 runs sont gelés sous `runs/1/train/`.
- Groupes : « vraies » = les 2 000 vraies ; « fausses connues » = fausses des types t01-t03, t05, t06, t08, t10, t13-t15 (S-réservé : 1 334 fausses ; **le réservé porte bien tous les types**, y compris les 5 tenus à l'écart) ; « fausses tenues à l'écart » = fausses de t04, t07, t09, t11, t12 (666). Pour S, le réseau voit les 15 types à l'entraînement : sa colonne « fausses connues » ne couvre que les 10 mêmes types, par comparabilité, et les 5 autres ne sont pas hors distribution (non rapportés ici). Exactitude globale = 4 000 références.

## Résultats

### legal_s

| Méthode | N | Graines | Durée moy. (s) | Exactitude (%) | vraies | fausses des 10 types |
|---|---|---|---|---|---|---|
| C | 64 | 0,1,2 | 0.6 | 51.7 ± 0.1 | 55.9 ± 0.5 | 54.0 ± 0.5 |
| C | 256 | 0,1,2 | 0.5 | 55.4 ± 0.1 | 54.7 ± 1.1 | 59.4 ± 0.5 |
| C | 1024 | 0,1,2 | 1.4 | 62.6 ± 0.3 | 60.4 ± 0.5 | 69.9 ± 0.5 |
| C | 8192 | 0,1,2 | 9.2 | 83.7 ± 0.7 | 84.4 ± 1.9 | 89.2 ± 1.4 |
| C | 32768 | 0,1,2 | 36.4 | 94.6 ± 0.1 | 96.5 ± 0.4 | 98.7 ± 0.2 |
| F | 64 | 0,1,2 | 0.3 | 53.2 ± 0.2 | 53.3 ± 0.9 | 58.8 ± 0.2 |
| F | 256 | 0,1,2 | 0.4 | 55.6 ± 0.3 | 55.9 ± 0.7 | 57.3 ± 0.8 |
| F | 1024 | 0,1,2 | 1.2 | 62.3 ± 0.2 | 61.2 ± 0.8 | 66.5 ± 1.2 |
| F | 8192 | 0,1,2 | 7.9 | 72.0 ± 2.0 | 75.2 ± 1.9 | 72.0 ± 3.1 |
| F | 32768 | 0,1,2 | 31.5 | 88.2 ± 0.8 | 92.9 ± 1.5 | 88.6 ± 3.6 |

### legal_s_reserved

| Méthode | N | Graines | Durée moy. (s) | Exactitude (%) | vraies | fausses (10 types) | fausses tenues à l'écart |
|---|---|---|---|---|---|---|---|
| C | 64 | 0,1,2 | 0.3 | 54.3 ± 0.1 | 62.0 ± 0.2 | 51.0 ± 0.2 | 37.4 ± 0.6 |
| C | 256 | 0,1,2 | 0.5 | 58.0 ± 0.0 | 67.2 ± 0.3 | 56.7 ± 0.4 | 33.1 ± 0.5 |
| C | 1024 | 0,1,2 | 1.2 | 64.2 ± 0.2 | 70.6 ± 0.8 | 71.2 ± 0.1 | 31.1 ± 1.5 |
| C | 8192 | 0,1,2 | 8.5 | 83.6 ± 0.5 | 96.8 ± 0.9 | 93.8 ± 0.9 | 23.6 ± 0.9 |
| C | 32768 | 0,1,2 | 33.9 | 86.1 ± 0.5 | 99.5 ± 0.2 | 98.4 ± 0.1 | 20.8 ± 3.2 |
| F | 64 | 0,1,2 | 0.2 | 53.2 ± 0.1 | 52.6 ± 0.3 | 59.0 ± 0.5 | 43.4 ± 0.7 |
| F | 256 | 0,1,2 | 0.5 | 57.7 ± 0.3 | 64.5 ± 0.8 | 56.7 ± 0.8 | 39.1 ± 0.9 |
| F | 1024 | 0,1,2 | 1.1 | 61.9 ± 0.5 | 65.8 ± 0.7 | 66.5 ± 0.8 | 40.8 ± 1.4 |
| F | 8192 | 0,1,2 | 7.7 | 70.5 ± 0.6 | 79.7 ± 2.4 | 75.1 ± 2.2 | 33.9 ± 1.9 |
| F | 32768 | 0,1,2 | 30.7 | 80.5 ± 1.0 | 92.7 ± 0.5 | 87.1 ± 3.3 | 30.8 ± 0.4 |

## Lecture

- Durées : de 0,2 s (N = 64) à 36 s (N = 32 768) par run, C et F confondus.
- C monte lentement (52-55 % à N ≤ 256, 63 % à 1 024), puis 84 % à 8 192 et 94,6 % à 32 768 sur S : la courbe n'est pas saturée à 32 768. Sur S-réservé, C atteint 83,6 % puis 86,1 % : les vraies et les fausses des types connus dépassent 98 % à 32 768, mais les 5 types tenus à l'écart restent à 21 % (en dessous du hasard, une fausse de ces types est prise pour une vraie : le réseau a appris « tout ce qui ne viole pas un des 10 types est vrai »).
- F n'aide pas : à N ≥ 8 192, F est nettement sous C (72,0 contre 83,7 % à 8 192 sur S, 88,2 contre 94,6 % à 32 768), à égalité sous 1 024. Hypothèse non testée : les champs extraits sont 5 scalaires normalisés noyés parmi 2 244 entrées binaires, alors que C lit les chiffres de la date en one-hot. Un seul réglage de F (même architecture, mêmes hyperparamètres que C) a été essayé : la conclusion vaut pour cette architecture, pas pour F en général.
- Point où C rattrape les séances A de 1-10 : laissé à 1-14 (séances pas encore mesurées).

## Seconde partie (non jouée)

Réentraînement de chaque architecture écrite en 1-10 à N = 8 192 depuis des poids aléatoires :

```
uv run --group train nnww retrain runs/1/<session_id> --data data/<task>/train --n 8192 --seed <s> --lot 1
```

Vérifie les empreintes de la séance gelée, ne lit que son manifeste, entraîne depuis des poids aléatoires (hyperparamètres de `config/train.toml` de la tâche), gèle sous `runs/1/train/<session_id>-retrain-n8192-s<s>/` (`run.json` porte `dataset.retrained_from`). Mesure ensuite par `baselines.curve.measure(run_dir, tâche, heldout/<tâche>/eval)`. Réserves : le jeu `data/<task>/train` doit être celui de 8 192 ou plus ; un manifeste d'une séance qui n'utilise ni `legal.chars@1` ni `legal.fields@1` est refusé.
