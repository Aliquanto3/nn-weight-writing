# Story 1-12 : pré-étude R et porte des 30 %

Phase A (méthode et faits de la base réelle) et phase B (classement, contrôle de qualité, tour de correction, porte) : 2026-11-07. Aucun appel payant, ni Ollama ni GPU. `data/r/collecte/` n'a pas été lu pendant la phase A. La porte a tourné une seule fois, le 2026-11-07 à 13:47 UTC.

## Références

Les renvois P0-P12, D1-D8 et E15 sont des sections de la spec de story citée ci-dessous. ECLI : identifiant européen de jurisprudence. SLM : petit modèle de langage. p : part d'incohérentes parmi les références vérifiables ; p_d1 : la même part sans les unités dont toutes les règles sont des règles ECLI, celle qui décide de la porte. Intervalle de Wilson : intervalle de confiance à 95 % d'une proportion, adapté aux petits effectifs.

- Spec (pré-enregistrement) : `_bmad-output/implementation-artifacts/stories/1-12-pre-etude-r.md`, commit `9e05ec1`, décisions P0-P12 reportées en `0aa98d8`.
- Spec à la porte : même fichier au commit `ab8e60d` (`spec_commit` de `config/r_gate.toml`). Ce commit ajoute la note E15 du tour de correction, sans changer ni règle, ni seuil, ni fenêtre.
- Commit « grille figée » initial : `1a672a13ebaf693865998707db729a098500c3a8` (tour 0). Code corrigé par le tour de correction : `ab8e60d225b28201cf87d114d0ef87e7465f968b` (tour 1 et porte, `grid_commit` de `config/r_gate.toml`). `classer` refuse de tourner sur un autre `HEAD` ou sur un arbre modifié.
- Manifeste de la collecte de 1-12a : sha256 `32434a5fd9a55de06226cfa4a1d7e10c910c9ff6a17870f5f9f80c6dc48e56b8` (`collecte.jsonl` : `5aae29d69b568ba97243b83552aec1a0236a98853e033c0cf8b4506e309c9b73`).
- Classement publiable (`data/r/pre_etude/classement.jsonl`) : hors dépôt, il part en asset de la release de 1-14 (D6, D8). sha256 du tour 0 : `5e3769b6e860e2ce5e6ef8cceec9a99969691b09887fb565bdff651d382167aa`. sha256 du tour 1, celui de la porte : `527869b523444148eae709919a079a092449d7eeba8746efd2f9c74ee4ca62de`.
- Index du CE : sha256 `456f290fb51d92bf8a08920b8f9b3034ee1975a0cff3976b74af0163ea36cfeb`.

## Méthode

**Entrée.** `collecte.jsonl` de 1-12a seul (`pilote.jsonl` exclu), lu par `read_collection` après contrôle de l'empreinte du manifeste puis de chaque fichier, avant de décoder une ligne. Réglages identiques entre générations et `prompt` égal à `requetes.json` contrôlés.

**Extraction** (`datasets/legal_r/extract.py`). Motifs fixes, sans modèle : ancres de juridiction (Cour de cassation, Conseil d'État, cours d'appel, autres juridictions), puis ancres secondaires hors de toute référence ouverte (chambre abrégée en tête, ECLI, numéro sans juridiction). Une référence va jusqu'à l'ancre suivante, une ligne vide, une fin de phrase ou 200 caractères ; une date, un numéro, un ECLI ou une formation de plus ouvre une nouvelle référence de même juridiction. Les textes normatifs (loi, décret, règlement (CE)…) sont masqués, un numéro a au moins 5 chiffres. Seul `raw` porte le passage cité ; il ne va que dans `data/r/pre_etude/interne/extraction.jsonl`, jamais publié.

**Normalisation** (`normalize.py`, `legal_r.normalize@1`). Même fonction pour une référence de SLM, une décision Judilibre et une décision de l'open data du CE ; liste blanche de champs. Numéros (P2) : variantes sans ambiguïté canonisées (`99-13701`, `9913701`, `99 13.701` → `99-13.701` ; `428 409` → `428409`), le reste gardé tel quel et jugé par la grille. Chambres et formations ramenées aux formes de D1 (inexistantes comprises), formations réunies du CE triées par rang.

**Unités.** Clé (juridiction, numéro normalisé, date) ; une clé citée deux fois dans une réponse compte une citation ; citation canonique dans l'ordre des modèles de 1-12a, puis `request_id`, puis position.

**Grille** (`grid.py`, version 1) : 21 règles de D4, domaines U (logique), F (faits de S, seulement dans [2001-01-02, date de génération]) et M (mesurées sur la base, toute date). Pour une référence complète à formation canonique, les règles de S viennent de `violations()` de 1-9 (test d'égalité sur les cinq jeux de S en graine 0).

**Classes** (D6) : `out_of_scope` (autres juridictions, cours d'appel par P5), `partial`, `exists`, `incoherent`, `coherent_absent`, `unverifiable` (motif). Vérification d'existence par égalité de champs : Judilibre `/scan` du jour (`abridged=true`), open data du CE par l'index local ; jamais le total d'une recherche.

**Porte** (P0) : décision sur p_d1 (sans les unités dont toutes les règles sont des règles ECLI), intervalle de Wilson à 95 % ; p, p_window, p_corr et les autres grandeurs publiées sans effet sur la décision. Ordre de la phase B (P1) : `classer` (aucune part), contrôle de qualité du reviewer (verdict daté qui cite le sha256 du classement, fausses absences par Judilibre `/search` et l'open data du CE, P7), au plus un tour de correction, puis `porte`, une seule fois.

## Faits de la base réelle (phase A, `mesurer-base` du 2026-11-07)

Écrits dans `src/nn_weight_writing/datasets/legal_r/r_facts.toml` (`status = "sample"`).

**Échantillons.** Cour de cassation : `/scan` abrégé, `date_type=creation`, 12 lots mensuels de 84 pour 2005, 2012, 2019 et 2024 (3 862 décisions, des mois en ont moins de 84). Cours d'appel : arrêts (`type=arret`) de 2023 et 2025, mêmes lots (2 016). Conseil d'État : les 40 134 décisions de l'index. Champs de la version abrégée de `/scan` : `chamber`, `decision_date`, `ecli`, `formation`, `id`, `jurisdiction`, `location`, `number`, `numbers`, `publication`, `type` (ni texte, ni résumé ; pas d'`update_date`). Le test `live` confirme un arrêt connu de l'assemblée plénière (`cc`, `pl`, 2000-11-17, `99-13.701`) par `/scan` abrégé et l'absence de `99-99.999` par égalité de champ.

**Index du Conseil d'État.** `scripts/index_ce_opendata.py` : 63 archives mensuelles (`CE_202109.zip` à `CE_202611.zip`, `opendata.justice-administrative.fr/DCE/`, Licence Ouverte 2.0), **119,6 Mo téléchargés** (le premier mois mesuré pesait 0,1 Mo ; estimation initiale « quelques centaines de Mo » non atteinte), 40 134 décisions, dernière lecture 2026-11-06. Archives supprimées après lecture. Des XML de janvier 2024 déclarent un préfixe `xsi` non lié : ils sont lus par un repli qui ne garde que les balises de métadonnées.

**Fenêtres de couverture.**

| Juridiction | Début | Fin | Base |
|---|---|---|---|
| `cc` | 1989-01-01 | 2026-08-07 | `/stats?keys=year` : médiane 2022-2025 = 16 314, seuil 8 157 ; 1988 (7 525) sous le seuil ; fin = 2026-11-05 − 90 j |
| `ca` | 2022-04-15 | 2026-07-31 | diffusion systématique (1-3) ; fin = 2026-10-29 − 90 j |
| `ce` | 2021-09-30 | 2026-10-07 | open data ; fin = 2026-11-06 − 30 j |

**Règles mesurées (ECLI).** R-E2 adoptée (codes disjoints : `CCASS` pour la Cour de cassation, `CEASS`, `CECHR`, `CECHS`, `CEFSP`, `CEORD`, `CESEC` et `INCONNU` pour le CE, aucun pour les cours d'appel ; 40 810 ECLI). R-E4 adoptée (ordinal `{numéro}.{AAAAMMJJ}` pour 37 888 ECLI du CE sur 37 889, 99,997 %). R-E5 adoptée (table C1, C2, C3, CO, SO, CR pour les six chambres hors chambre mixte et assemblée plénière ; 2 502 ECLI, 100 %).

**Spécificité** (toutes les règles sur toutes les vraies, P11). Aucune règle ne dépasse 0,5 % : aucune n'est désactivée. Faux positifs résiduels : Cour de cassation 0,026 % (1 sur 3 862 : R-F1, numéros joints mal découpés dans `numbers`), cours d'appel 0 sur 2 016, Conseil d'État 0,117 % (47 sur 40 134 : R-C4 sur 19 décisions de la 1re chambre lues le 11 novembre 2021, R-E1 sur 27 ECLI « Code Inconnu », R-E4 sur 1 décision de Section dont l'ECLI porte une autre date).

**Rappel de la vérification** (P6, 60 vraies par juridiction tirées dans la fenêtre, graine `[0, 5]`) : Cour de cassation 60 sur 60, Conseil d'État 60 sur 60 (seuil 57). Aucune juridiction n'est en `verification_unreliable`.

**Requêtes Judilibre de la phase A** : 112 par `mesurer-base` (72 lots d'échantillon, 2 `/stats`, 60 `/scan` du rappel et leurs diagnostics), plus 3 pour le test `live` et 10 de relevé du format le 2026-11-07 ; aucune erreur, aucun 429. Dernier `x-rate-limit` : 999 878 restantes sur le compteur journalier.

## Résultats (phase B)

### Décision

**Porte R : p_d1 = 0,675 [0,630 ; 0,717] sur 437 unités, décision « comparatif ».** La porte n'est pas serrée : la borne basse de l'intervalle de Wilson à 95 % est loin au-dessus de 30 %. **Réserve forte** : le contrôle de qualité a échoué au tour 0 puis, après le seul tour de correction permis, encore au tour 1 (voir plus bas). D7 prévoit ce cas : la décision est prise, avec cette réserve, et Anaël en est notifié.

Ces chiffres sont ceux de `data/r/pre_etude/resume.json` et de `config/r_gate.toml` (p = 0,675057, low = 0,629785, high = 0,717278, n = 437, `tight = false`). Aucune unité n'a pour seules règles des règles ECLI : p_d1 et p sont égaux (295 incohérentes sur 437).

Ligne de journal écrite par `porte` : `1.12 · décision · porte R : p = 0,68 [0,63 ; 0,72] sur 437, comparatif, réserves : réserve forte : contrôle de qualité en échec après le tour de correction`.

### p avant et après la correction (D7)

| Tour | Code | Classement | Incohérentes | Cohérentes absentes | p = p_d1 | Intervalle |
|---|---|---|---|---|---|---|
| 0 (avant correction) | `1a672a1` | `5e3769b6…67aa` | 209 | 111 | 0,653 (209/320) | [0,599 ; 0,703] |
| 1 (après correction, porte) | `ab8e60d` | `527869b5…62de` | 295 | 142 | 0,675 (295/437) | [0,630 ; 0,717] |

Le p du tour 0 est calculé après coup par `compute_gate` du script, sur le classement gardé dans `tour0/`, sans rien écrire dans `resume.json`, `journal.jsonl` ni `config/r_gate.toml`. Il est publié seul et ne change pas la décision. Au tour 0, p_window valait 0,586 [0,526 ; 0,643] sur 268 ; Cour de cassation 0,590 [0,524 ; 0,653] sur 222 ; Conseil d'État 0,796 [0,706 ; 0,864] sur 98. La correction a fait entrer 117 unités de plus au dénominateur, dont 86 incohérentes (74 %) : c'est un solde net. En brut, 124 unités sont entrées, dont 91 incohérentes (73 %), et 7 sont sorties, dont 6 incohérentes.

### Entonnoir

| Étape | Tour 0 | Tour 1 |
|---|---|---|
| Générations lues | 1 600 | 1 600 |
| Références extraites | 1 559 | 1 487 |
| Unités dédupliquées | 1 087 | 1 099 |
| `partial` (référence incomplète) | 667 | 531 |
| `out_of_scope` | 45 | 54 (cours d'appel 11, autres juridictions 43) |
| `unverifiable` (cohérentes hors fenêtre, `before_window`) | 55 | 77 |
| `exists` | 0 | 0 |
| `incoherent` | 209 | 295 |
| `coherent_absent` | 111 | 142 |
| Requêtes d'existence (`api_error`) | 268 (0) | 345 (0) |

Moins de références au tour 1 : le rappel du même numéro ne crée plus de référence, et une date ou un numéro écrit avant l'ancre rejoint sa référence au lieu d'en ouvrir une autre. Tour 1 : 4 unités en conflit de classe (`class_conflict`), 79 correspondances partielles sur la date (`partial_match = "date"`), 0 faux positif de la grille (`grid_false_positive`). 92 partielles seraient incohérentes d'après la grille ; elles restent hors de p (P3). Judilibre au tour 1 : 172 requêtes, 695 réponses du cache.

### Contrôle de qualité (D7)

Tirages par `pre_etude_r.py echantillons`, graine `[0, k]` au tour 0 et `[0, k + 10]` au tour 1. Les notes détaillées citent des réponses : elles restent dans `data/r/pre_etude/interne/` et ne sont pas publiées. Verdicts : `data/r/pre_etude/verdict-tour0-2026-11-07.json` et `verdict-tour1-2026-11-07.json` (sha256 du verdict du tour 0 : `4eb2e418…8de5`).

**Tour 0** (classement `5e3769b6…`, code `1a672a1`) : **échec**.

| Contrôle | Taille | Critère | Résultat |
|---|---|---|---|
| Classe des unités du dénominateur (k = 1) | 60 | ≤ 2 erreurs de classe ; ≤ 6 de champ | 2 et 3 : accepté, à la limite |
| Unités exclues (k = 2) | 20 | ≤ 2 qui auraient dû entrer | 3 : **échec** |
| Rappel de l'extraction (k = 3) | 30 réponses avec référence, 10 sans | ≤ 3 références complètes manquées | 17 : **échec** |
| Fausses absences (k = 4) | 30 | ≤ 1 trouvée | 0 : accepté (CE : non indépendant, voir Limites) |
| Revue exhaustive (`grid_false_positive`, `partial_match = "formation"`) | 0 unité | jugement unité par unité | vide |

Causes relevées : juridiction donnée dans l'introduction ou un titre, puis bloc « Date / Numéro » ; date écrite avant l'ancre ; tirets typographiques dans un numéro ; date lue dans un numéro. Le tour de correction (E15 de la spec) a porté sur l'extracteur et le normaliseur seulement.

**Tour 1** (classement `527869b5…`, code `ab8e60d`) : **second échec**.

| Contrôle | Taille | Critère | Résultat |
|---|---|---|---|
| Classe des unités du dénominateur (k = 11) | 60 | ≤ 2 erreurs de classe ; ≤ 6 de champ | 1 et 5 : accepté |
| Unités exclues (k = 12) | 20 | ≤ 2 qui auraient dû entrer | 4, dont 2 à la limite : **échec** |
| Rappel de l'extraction (k = 13) | 30 réponses avec référence, 10 sans | ≤ 3 références complètes manquées | 4 : **échec** |
| Fausses absences (k = 14) | 30 | ≤ 1 trouvée | 0 : accepté (CE : non indépendant, voir Limites) |
| Revue exhaustive | 0 unité | jugement unité par unité | vide |

### La réserve forte, expliquée

**Erreurs qui restent**, toutes dans l'extracteur :

1. la juridiction est nommée dans une phrase d'introduction, un titre sans ancre ou la phrase suivante, puis vient un bloc « Date / Numéro » : la référence reste sans juridiction, donc `partial` (cas non couvert par les deux héritages bornés d'E15) ;
2. une référence hérite de la mauvaise juridiction, nommée dans le récit : elle passe `out_of_scope` ;
3. la formation est écrite sur une ligne de bloc avant la date : elle n'est pas rattachée.

**Sens du biais : non établi.** Les erreurs observées dans les échantillons vont plutôt vers le haut (des unités exclues à tort seraient surtout des incohérentes), mais le rappel n'en dit rien et l'effectif est faible (4 exclusions, dont 2 à la limite, et 1 erreur de classe). La direction n'est donc pas établie. Observations :

- 3 des 4 unités exclues à tort du tirage k = 12 auraient été incohérentes : numéro mal formé (R-F1), formation inexistante (R-O2) ou date tombée un dimanche (R-C4). La quatrième porte un numéro de six chiffres, qui n'a pas la forme d'un numéro de pourvoi ;
- la seule erreur de classe du tirage k = 11 classe en `coherent_absent` une unité qui, formation rattachée, serait incohérente ;
- au tour de correction, les 117 unités récupérées étaient incohérentes à 74 %, contre 65 % pour les unités déjà au dénominateur.

**Nuances.**

- Le sens des références manquées par le rappel (k = 13) n'est pas mesuré : elles n'ont jamais été classées.
- Deux des quatre exclues à tort sont « à la limite » : ce sont des exemples donnés comme fictifs par le modèle, comptés comme au tour 0.
- Le contrôle ne dit pas combien d'unités manquent. 4 sur 20 donnent une part de 20 % [8 % ; 42 %] des exclues. Rapportée aux 585 exclues `partial` et `out_of_scope`, c'est de l'ordre de 120 unités [50 ; 245]. Ce n'est qu'un ordre de grandeur : le tirage k = 12 porte aussi sur les `unverifiable`.

**Effet sur la décision.** Pour que p_d1 passe sous 30 %, il faudrait ajouter au moins 547 cohérentes absentes sans aucune incohérente (295 / (437 + 547) < 0,30). C'est bien au-delà de la borne haute ci-dessus, et contraire au sens observé. Le chiffre de p est donc incertain, sans direction établie (les erreurs observées vont plutôt vers le haut, le rappel n'en dit rien), mais la décision « comparatif » n'en dépend pas.

### Sensibilités (sans effet sur la décision)

| Grandeur | Valeur | Côté de 30 % |
|---|---|---|
| p (ECLI compris) | 0,675 [0,630 ; 0,717], n = 437 | même |
| p_window (unités datées dans la fenêtre de leur juridiction) | 0,588 [0,536 ; 0,639], n = 345 | même |
| p_corr (fausses absences) | non calculé : 0 trouvée sur 30 (f = 0) | — |
| Incohérentes dont la seule règle est de format (R-F1, R-F2) | 80,3 % | — |
| Incohérentes qui ne tiennent qu'à une règle empirique (R-H2) | 0,7 % (2 sur 295) | — |

**Recouvrement avec les 15 types de Nuss.** Toutes les incohérentes ont au moins un type `tXX` ; 1,4 % portent un des types attestés t01 à t03. Règles violées : R-F1 256, R-C4 35, R-O2 20, R-F2 11, R-H2 3, R-A1 2, R-H1 2, R-O1 2, R-O4 2. Types : t10 256, t12 35, t05 20, t11 11, t08 3, t01 2, t03 2, t07 2, t14 2.

**Par famille** : part du dénominateur (une unité citée par k familles compte 1/k pour chacune) et p sans les unités citées par cette seule famille.

| Famille | Part | p sans elle (n) |
|---|---|---|
| ministral-3 | 22,4 % | 0,814 (339) |
| nemotron-3-nano | 21,5 % | 0,603 (343) |
| qwen3.5 | 17,8 % | 0,699 (359) |
| lfm3 | 14,6 % | 0,638 (373) |
| granite4.2 | 14,3 % | 0,635 (375) |
| phi4-mini | 6,2 % | 0,671 (410) |
| gemma4 | 3,1 % | 0,672 (424) |

Aucune famille ne domine : chaque part est sous 50 %, et p sans une famille va de 0,60 à 0,81, toujours au-dessus de 30 %.

### p par juridiction et par modèle

| Juridiction | p | Intervalle | Incohérentes / dénominateur |
|---|---|---|---|
| Cour de cassation (`cc`) | 0,581 | [0,523 ; 0,636] | 169 / 291 |
| Conseil d'État (`ce`) | 0,863 | [0,798 ; 0,910] | 126 / 146 |

Par modèle, une unité compte pour chaque modèle qui la cite (dédupliquée dans le modèle) :

| Modèle | p | Intervalle | n |
|---|---|---|---|
| nemotron-3-nano:4b | 0,94 | [0,87 ; 0,97] | 94 |
| granite4.2:3b | 0,90 | [0,81 ; 0,96] | 63 |
| lfm3:1.7b-q4_K_M | 0,89 | [0,79 ; 0,95] | 64 |
| qwen3.5:0.8b | 0,89 | [0,72 ; 0,96] | 27 |
| gemma4:e2b-it-qat | 0,89 | [0,57 ; 0,98] | 9 |
| phi4-mini:3.8b | 0,74 | [0,55 ; 0,87] | 27 |
| qwen3.5:2b | 0,72 | [0,52 ; 0,86] | 25 |
| gemma4:e4b-it-qat | 0,40 | [0,12 ; 0,77] | 5 |
| ministral-3:3b | 0,19 | [0,13 ; 0,28] | 98 |
| qwen3.5:4b | 0,08 | [0,02 ; 0,24] | 26 |

Deux modèles sont nettement sous 30 % : ministral-3:3b et qwen3.5:4b. Leurs références inventées sont le plus souvent bien formées, ce qui les rend plus difficiles à repérer par la seule forme. La porte porte sur l'ensemble des modèles, pas modèle par modèle. 1-13 devra en tenir compte dans le tirage des fausses de R.

### Limites

- **Conseil d'État : vérification non indépendante.** Pour le CE, l'existence et les fausses absences sont vérifiées sur le même index local, construit depuis l'open data (archives depuis le 30 septembre 2021). Le contrôle des fausses absences (0 sur 30) n'est donc pas indépendant du vérificateur pour cette juridiction. Les incohérentes du CE antérieures à la fenêtre ne sont pas vérifiées (D5).
- **Cours d'appel hors champ** (P5) : 11 unités `out_of_scope`. Ce compte rendu ne dit rien des références inventées de cours d'appel.
- **Rappel mesuré par échantillon** : 40 réponses par tour, dont 10 sans référence. Le nombre de références manquées sur l'ensemble de la collecte n'est pas connu.
- **Contrôle fait par un relecteur automatique** (le `reviewer`), contre les règles écrites de la spec. Fausses absences recherchées par Judilibre `/search` et l'open data du CE (P7), pas par Légifrance ni ArianeWeb.
- **p dépend de la grille** : 80 % des incohérentes ne tiennent qu'à un numéro mal formé. C'est une incohérence réelle (R4), mais elle est visible à la forme seule.

### Attribution (condition 2 de 1-3)

Vraies références consultées pour la vérification : base Open Data Judilibre de la Cour de cassation, Licence Ouverte 2.0 (https://www.etalab.gouv.fr/licence-ouverte-open-licence), extraction du 2026-11-07 ; données Conseil d'État : base Open Data du Conseil d'État (opendata.justice-administrative.fr), Licence Ouverte 2.0, dernière lecture le 2026-11-06. Fausses références : générées par des SLM, elles ne correspondent à aucune décision. Le classement ne contient que des métadonnées de référence, sans passage cité ni nom (D6, D8).
