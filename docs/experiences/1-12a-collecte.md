# 1-12a — Collecte des hallucinations juridiques de SLM

## Objet

Produire, par Ollama, les réponses brutes de 10 SLM à des questions de jurisprudence française
(Cour de cassation, Conseil d'État), pour que 1-12 en extraie des références et les classe. Script
unique `scripts/collecte_hallucinations.py` (bibliothèque standard), hors du paquet
`nn_weight_writing` (test dédié). Le projet ne lit que les fichiers figés ci-dessous. Les sorties
sont dans `data/r/collecte/` (ignoré par git, jamais commité).

## Réglages

`/api/chat`, aucun message système, `stream: false`, `think: false`, options
`temperature: 0`, `seed: 0`, `num_predict: 512`. Ollama 0.40.14. Une ligne JSONL par génération
(modèle, digest, prompt, réponse brute, `done_reason`, compteurs de tokens, durées, horodatage UTC,
réglages), en ajout seul, reprenable. GPU libre avant le lancement (`nvidia-smi` : 7 MiB utilisés ;
`ollama ps` vide).

Digests (début) : qwen3.5:0.8b f3817196d142 ; qwen3.5:2b 324d162be6ca ; qwen3.5:4b 96f38c742e0a ;
gemma4:e2b-it-qat 07ea59a47401 ; gemma4:e4b-it-qat ee6656371218 ; ministral-3:3b f04aa1c738f6 ;
phi4-mini:3.8b 78fad5d182a7 ; granite4.2:3b 40577dc168a3 ; lfm3:1.7b-q4_K_M b36a103fe2f8 ;
nemotron-3-nano:4b 6cc467f05439 (complets dans `manifest.json`).

## Empreintes (sha256)

- `scripts/collecte/requetes.json` (160 requêtes, figé avant toute génération) :
  `ee1e6749b51edaba9340644c6433fdc50fb59cbadfeaa5095b066f9f1c36efb4`
- `pilote.jsonl` : `b4a03eaf2100dd12b2768757276e2b7e861331a83d1f9b2d6016e8d9926d2392`
- `collecte.jsonl` : `2fffdf02a6a2b1672059f8e339c61e56e5d84db31875ca3ab9697c8997c9f999`
- `manifest.json` : `2f64eb8fc5113ac8f7fda2c7f868a0447763ae0b830649e6add7a33de76462be`

## Requêtes

40 thèmes de Cour de cassation et 40 de Conseil d'État, chacun en tournure « directe » et
« naturelle ». Les 20 premiers thèmes de chaque juridiction forment le noyau (80 requêtes), les 20
suivants la réserve (80). Identifiants `cass-001-directe`…, `ce-040-naturelle`.

## Règle de taille (écrite avant le pilote, appliquée sans retouche)

Estimation des références distinctes = (motifs par génération du pilote) × (part distincte du
pilote) × (nombre de générations). Si le noyau × 10 modèles (800 générations) donne ≥ 600 :
collecte sur le noyau ; sinon noyau + réserve (1 600). Si même 1 600 donnent moins de 600, on
collecte quand même les 1 600 et on le dit (la porte se jouera sur le n atteint). Elle est codée
dans `choisir_ensemble` (commit initial du script, avant le pilote).

## Pilote

10 requêtes du noyau (5 cassation, 5 CE ; cass-001-directe, cass-004-naturelle, cass-008-directe,
cass-012-naturelle, cass-017-directe, ce-002-naturelle, ce-006-directe, ce-009-naturelle,
ce-014-directe, ce-019-naturelle) × 3 modèles (qwen3.5:2b, gemma4:e4b-it-qat, ministral-3:3b) =
30 générations.

- 69 motifs, soit 2,3 par génération ; 48 distincts, part distincte 0,696 ; 11 réponses sans motif
  (36,7 %).
- Par modèle (motifs/génération ; sans motif) : qwen3.5:2b 1,7 ; 4/10. gemma4:e4b-it-qat 0,7 ; 6/10.
  ministral-3:3b 4,5 ; 1/10.
- Durée : 283 s de mur (9,4 s par génération, chargements compris).
- Estimation : 2,3 × 0,696 × 800 = 1 280 ≥ 600, donc **noyau** (800 générations). Projection de
  durée : 800 × 9,4 s ≈ 2,1 h.

## Collecte complète (noyau, 800 générations)

Du 2026-11-07 06:23 UTC à 08:10 UTC, soit environ 1 h 47 de mur (1,24 h de temps cumulé Ollama). Un
arrêt à 07:57 : HTTP 500 d'Ollama (« prediction aborted, token repeat limit reached », sur
nemotron-3-nano:4b, cass-014-directe, déterministe à `temperature 0`). Correctif dans le script :
l'erreur est consignée (`done_reason: "error"`, champ `error`, réponse vide) et la collecte
continue ; reprise ensuite sans perte. 4 générations en erreur, toutes nemotron-3-nano:4b
(cass-014-directe, ce-002-directe, ce-009-directe, ce-019-directe). `done_reason` : 482 `length`,
314 `stop`, 4 `error`.

Comptes du compteur grossier (générations ; motifs ; distincts ; part distincte ; sans motif) :

| Modèle | gén. | motifs | distincts | part | sans motif |
|---|---|---|---|---|---|
| qwen3.5:0.8b | 80 | 102 | 66 | 0,65 | 34 |
| qwen3.5:2b | 80 | 147 | 67 | 0,46 | 33 |
| qwen3.5:4b | 80 | 107 | 65 | 0,61 | 26 |
| gemma4:e2b-it-qat | 80 | 36 | 12 | 0,33 | 61 |
| gemma4:e4b-it-qat | 80 | 40 | 11 | 0,28 | 56 |
| ministral-3:3b | 80 | 230 | 130 | 0,57 | 19 |
| phi4-mini:3.8b | 80 | 118 | 46 | 0,39 | 52 |
| granite4.2:3b | 80 | 148 | 63 | 0,43 | 32 |
| lfm3:1.7b-q4_K_M | 80 | 131 | 74 | 0,56 | 22 |
| nemotron-3-nano:4b | 80 | 389 | 83 | 0,21 | 11 |
| Cour de cassation | 400 | 893 | 320 | 0,36 | 164 |
| Conseil d'État | 400 | 555 | 297 | 0,54 | 182 |
| Total | 800 | 1 448 | 574 | 0,40 | 346 |

Le rendement réel (574 motifs distincts tous types confondus, dates comprises) est inférieur à
l'estimation du pilote (1 280) : la part distincte baisse avec le nombre de générations et le pilote
surestimait les motifs par génération. La règle a été appliquée sans retouche ; le noyau a été
retenu, et la réserve (800 générations de plus, ~2 h) n'a pas été collectée. Les 574 distincts
mélangent pourvois, numéros de requête, ECLI, « Cass. … chambre » et dates : le nombre de références
complètes (juridiction, numéro, date) sera connu à l'extraction de 1-12, probablement inférieur à
600. À décider par l'orchestrateur : la consigne interdit une collecte supplémentaire après
mesure de p, mais n'a pas prévu ce cas pour la taille.

## Compteur de rendement : grossier

`compter_motifs` ne sert qu'à dimensionner. Motifs : pourvoi `NN-NN.NNN`, numéro de requête CE à
5 ou 6 chiffres (après « requête » ou « n° »), ECLI, « Cass. … chambre », dates complètes.
Réponse sans motif = refus ou absence de référence. Normalisation grossière (minuscules, espaces).
Ce n'est pas l'extracteur de 1-12 : il compte aussi des dates et numéros qui ne sont pas des
références de décisions, et il peut rater des formes inhabituelles.

## Incertitudes

- Compteur grossier (ci-dessus) ; le rendement en références complètes reste à mesurer.
- Licences des sorties : non relues modèle par modèle.
- Noms de parties inventés présents dans le brut, à retirer par le normaliseur de 1-12/1-13.
- 482 réponses sur 800 tronquées à 512 tokens (`length`) : une référence peut être coupée.
- `num_predict` 512 et mêmes réglages pour tous ; les modèles à raisonnement sont en `think: false`.
- Le pilote a été lancé avec la version initiale du script (sans gestion de l'erreur 500) ; il n'a
  eu aucune erreur.
