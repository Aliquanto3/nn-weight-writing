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
- Noyau seul (état figé du 2026-11-07, conservé dans `manifest-noyau.json`) : `collecte.jsonl`
  `2fffdf02a6a2b1672059f8e339c61e56e5d84db31875ca3ab9697c8997c9f999` (800 lignes), `manifest.json`
  `2f64eb8fc5113ac8f7fda2c7f868a0447763ae0b830649e6add7a33de76462be`.
- État final, noyau + réserve (voir « Réserve ») : `collecte.jsonl`
  `5aae29d69b568ba97243b83552aec1a0236a98853e033c0cf8b4506e309c9b73` (1 600 lignes, 4 051 136
  octets) ; `manifest.json`
  `32434a5fd9a55de06226cfa4a1d7e10c910c9ff6a17870f5f9f80c6dc48e56b8`. Les 800 premières lignes sont
  celles du noyau, inchangées (même sha256 sur les 2 012 985 premiers octets).

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

**Schéma mixte.** Les 746 premières lignes de `collecte.jsonl` (et les 30 de `pilote.jsonl`) ont
été écrites avant ce correctif : elles n'ont pas de clé `error`. Les 854 suivantes (à partir de
la ligne 747, nemotron-3-nano:4b cass-014-directe) l'ont, à `null` hors erreur. Un lecteur doit
lire `d.get("error")` ; le critère d'erreur fiable est `done_reason == "error"`, présent partout.

Comptes du compteur grossier (générations ; motifs ; distincts ; part distincte ; sans motif).
**Les générations en erreur (réponse vide) sont comptées dans « gén. » et dans « sans motif »**
dans les trois tableaux de ce compte rendu. Hors erreurs, voir la note sous chaque tableau.

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

Hors les 4 erreurs : nemotron-3-nano:4b 76 générations, 7 sans motif ; Cour de cassation 399, 163 ;
Conseil d'État 397, 179 ; total 796 générations, 342 sans motif (motifs et distincts inchangés).

Le rendement réel (574 motifs distincts tous types confondus, dates comprises) est inférieur à
l'estimation du pilote (1 280) : la part distincte baisse avec le nombre de générations et le pilote
surestimait les motifs par génération. La règle a été appliquée sans retouche ; le noyau a été
retenu. La réserve a ensuite été collectée sur décision d'Anaël (section suivante). Les 574 distincts
mélangent pourvois, numéros de requête, ECLI, « Cass. … chambre » et dates : le nombre de références
complètes (juridiction, numéro, date) sera connu à l'extraction de 1-12, probablement inférieur à
600. À décider par l'orchestrateur : la consigne interdit une collecte supplémentaire après
mesure de p, mais n'a pas prévu ce cas pour la taille.

## Réserve (décision d'Anaël)

**Motif.** La règle de taille a choisi le noyau, mais son estimation était trop haute (574 motifs
distincts au lieu de 1 280). Le 2026-11-07, Anaël a décidé de collecter aussi la réserve (les 80
requêtes `ensemble: reserve` de `requetes.json`, sha256 inchangé `ee1e6749…6efb4`) × les mêmes 10
modèles, mêmes réglages. **C'est un écart à la règle de taille pré-enregistrée**, décidé sur le
rendement seul : aucune classification ni aucune part n'avait été calculée. L'état figé du noyau
reste dans `manifest-noyau.json`.

**Déroulé.** 800 générations de plus, environ 1 h 45 de mur (6 284 s, sur la seconde exécution).
`manifest.json` porte désormais `ensemble: tout`, le motif de l'écart et `manifest_noyau`. 6
nouvelles erreurs HTTP 500 déterministes, toutes nemotron-3-nano:4b, consignées comme pour le noyau
(`done_reason: "error"`). Total : 1 600 générations, `done_reason` 960 `length`, 630 `stop`,
10 `error` (4 du noyau + 6 de la réserve).

**Incident.** Un premier lancement, sans `--sortie`, a écrit dans `data/r/collecte/` du worktree
(la sortie par défaut était relative au dossier courant : le script ne voyait pas le noyau figé).
Il a produit 161 lignes avant l'arrêt : qwen3.5:0.8b sur les 80 requêtes du noyau et les 80 de la
réserve, puis une ligne de qwen3.5:2b (cass-001-directe, noyau). Les « 81 lignes du noyau » sont
donc 80 de qwen3.5:0.8b et 1 de qwen3.5:2b. Fichier écarté (`regenere-par-erreur.jsonl`, hors
dépôt, jamais utilisé). Contrôle de reproductibilité gratuit (`temperature 0`, `seed 0`) : les
161 lignes ont une réponse et un `done_reason` identiques à ceux du fichier figé pour le même
couple (modèle, requête), 0 différence. La collecte retenue est la seconde exécution, avec
`--sortie` sur le dépôt principal ; les 80 lignes de réserve de qwen3.5:0.8b y ont été regénérées.
Correctif (revue) : sans `--sortie`, le script vise désormais `data/r/collecte/` du dépôt
principal (parent de `git rev-parse --git-common-dir`), même lancé depuis un worktree, et affiche
la sortie retenue. Une reprise retire aussi une dernière ligne tronquée avant d'ajouter.

Comptes de la réserve (compteur grossier ; les distincts sont comptés au sein de la réserve) :

| Modèle | gén. | motifs | distincts | part | sans motif |
|---|---|---|---|---|---|
| qwen3.5:0.8b | 80 | 123 | 74 | 0,60 | 34 |
| qwen3.5:2b | 80 | 145 | 90 | 0,62 | 32 |
| qwen3.5:4b | 80 | 96 | 62 | 0,65 | 31 |
| gemma4:e2b-it-qat | 80 | 19 | 8 | 0,42 | 67 |
| gemma4:e4b-it-qat | 80 | 48 | 16 | 0,33 | 55 |
| ministral-3:3b | 80 | 260 | 143 | 0,55 | 19 |
| phi4-mini:3.8b | 80 | 40 | 27 | 0,68 | 57 |
| granite4.2:3b | 80 | 167 | 69 | 0,41 | 26 |
| lfm3:1.7b-q4_K_M | 80 | 140 | 80 | 0,57 | 16 |
| nemotron-3-nano:4b | 80 | 251 | 69 | 0,27 | 18 |
| Cour de cassation | 400 | 700 | 326 | 0,47 | 173 |
| Conseil d'État | 400 | 589 | 298 | 0,51 | 182 |
| Réserve | 800 | 1 289 | 574 | 0,45 | 355 |

Hors les 6 erreurs : nemotron-3-nano:4b 74 générations, 12 sans motif ; Cour de cassation 397, 170 ;
Conseil d'État 397, 179 ; réserve 794 générations, 349 sans motif.

Total noyau + réserve (distincts sur l'ensemble) :

| Modèle | gén. | motifs | distincts | part | sans motif | erreurs |
|---|---|---|---|---|---|---|
| qwen3.5:0.8b | 160 | 225 | 130 | 0,58 | 68 | 0 |
| qwen3.5:2b | 160 | 292 | 143 | 0,49 | 65 | 0 |
| qwen3.5:4b | 160 | 203 | 115 | 0,57 | 57 | 0 |
| gemma4:e2b-it-qat | 160 | 55 | 15 | 0,27 | 128 | 0 |
| gemma4:e4b-it-qat | 160 | 88 | 22 | 0,25 | 111 | 0 |
| ministral-3:3b | 160 | 490 | 243 | 0,50 | 38 | 0 |
| phi4-mini:3.8b | 160 | 158 | 70 | 0,44 | 109 | 0 |
| granite4.2:3b | 160 | 315 | 111 | 0,35 | 58 | 0 |
| lfm3:1.7b-q4_K_M | 160 | 271 | 128 | 0,47 | 38 | 0 |
| nemotron-3-nano:4b | 160 | 640 | 129 | 0,20 | 29 | 10 |
| Cour de cassation | 800 | 1 593 | 564 | 0,35 | 337 | |
| Conseil d'État | 800 | 1 144 | 534 | 0,47 | 364 | |
| Total | 1 600 | 2 737 | 1 007 | 0,37 | 701 | 10 |

Hors les 10 erreurs : nemotron-3-nano:4b 150 générations, 19 sans motif ; Cour de cassation 796,
333 ; Conseil d'État 794, 358 ; total 1 590 générations, 691 sans motif. Les trois tableaux ont été
recalculés depuis le `collecte.jsonl` figé (sha256 `5aae29d6…9b73`) en revue : identiques.

Le nombre de références complètes reste à mesurer à l'extraction de 1-12 (les 1 007 distincts
mélangent toujours pourvois, numéros, ECLI, « Cass. … chambre » et dates).

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
- 960 réponses sur 1 600 tronquées (482 sur 800 pour le noyau seul) à 512 tokens (`length`) : une référence peut être coupée.
- `num_predict` 512 et mêmes réglages pour tous ; les modèles à raisonnement sont en `think: false`.
- Le pilote a été lancé avec la version initiale du script (sans gestion de l'erreur 500) ; il n'a
  eu aucune erreur.

## Revue

### Passe 1 (2026-11-07, SHA revu d564073)

- Important, medium, second avis : reprise après ligne tronquée, la ligne suivante s'y collait et
  `figer()` échouait. Corrigé (`reparer_fin` avant l'ajout, test). Données figées : 0 ligne invalide.
- Important, medium, second avis : les 10 erreurs HTTP 500 comptées « sans motif ». Corrigé :
  `rapport_pilote` les exclut ; le compte rendu le dit et donne les chiffres hors erreurs
  (tableaux recalculés depuis le fichier figé, identiques).
- Important, medium, second avis : sortie par défaut relative au dossier courant, cause de
  l'incident du worktree. Corrigé (racine du dépôt principal par `--git-common-dir`, test).
- Nit, low, second avis : `test_figer` mettait le vrai `requetes.json` en lecture seule. Corrigé
  (copie dans `tmp_path`).
- Rejeté, second avis : `think` non pris en charge. Ollama 0.40.14 le prend en charge.
- Nit, low, second avis : schéma mixte (746 lignes sans clé `error`). Documenté ; lectures en
  `.get`.
- Nit, low, second avis : « 81 lignes du noyau ». Expliqué (80 qwen3.5:0.8b + 1 qwen3.5:2b),
  vérifié sur le fichier écarté.
