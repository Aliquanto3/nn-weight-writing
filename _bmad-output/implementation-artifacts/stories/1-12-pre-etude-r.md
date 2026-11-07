---
story: "1-12"
title: Pré-étude R et porte des 30 %
status: review
branch: feat/1-12-pre-etude-r
---

# Story 1-12 : pré-étude R et porte des 30 %

## Objet

Classer les hallucinations juridiques collectées par 1-12a en **incohérentes** (défaut détectable sans base) et **cohérentes absentes** (bien formées, vérifiées absentes de la base dans sa fenêtre de couverture), chiffrer la part p avec son intervalle de Wilson à 95 %, publier le classement et décider, selon la règle R4 de `methodes-et-lots.md`, si R est un **comparatif** ou une **mesure de plafond** (CAP-10 ; AD-4 amendé, AD-16, AD-18 ; constat `docs/verifications/1-3-judilibre-hallucinations.md`).

**Cette spec est le pré-enregistrement.** Elle a été écrite le 2026-11-07 pendant que la collecte 1-12a tournait, sans lire ni ouvrir `data/r/collecte/`. Seuls le script de collecte et le jeu de requêtes figé (`scripts/collecte_hallucinations.py`, `scripts/collecte/requetes.json`, branche `exp/1-12a-collecte-hallucinations`) ont été lus, pour connaître le format des sorties. La grille, les domaines de validité des règles, les classes, les fenêtres de couverture, le calcul de la porte et le contrôle de qualité sont fixés ici. L'implémentation n'en change aucun. Si l'un est impossible à tenir, elle le consigne en écart et le décide avant la phase B (D9).

## Décisions reprises telles quelles

- Règle R4 (orchestrateur, 2026-11-07, à confirmer par Anaël), dans `methodes-et-lots.md` :
  - unité : la référence normalisée et dédupliquée (juridiction, numéro normalisé, date) ; une référence qui existe sort du compte ;
  - les non vérifiables sont exclues du dénominateur et publiées à part ;
  - p = incohérentes / (incohérentes + cohérentes absentes), intervalle de Wilson à 95 % ;
  - p < 30 % → plafond, p ≥ 30 % → comparatif ; la décision se prend sur l'estimation ponctuelle et elle est « serrée » si l'intervalle contient 30 % ;
  - pas de collecte supplémentaire après avoir vu p.
- Judilibre : production, en-tête `KeyId` (`JUDILIBRE_KEY_ID`), moins de 10 requêtes par seconde, `x-rate-limit` lu, égalité exacte sur les champs et jamais le total d'une recherche (T5, `relaxed`) ; normaliseur à liste blanche, sans `text`, `zones` ni `text_highlight` (1-3).
- `r_republish = true` (`config/publish.toml`, 2026-11-07).
- Le format D1 de 1-9 est le format de sortie du normaliseur commun : `Reference`, `format_reference` (`tasks/legal/reference.py`). Il garde juridiction, formation ou siège, date et numéro. L'ECLI n'y figure pas.

## D1 — Phases et garde-fous du pré-enregistrement

La story se déroule en **deux phases** sur la même branche :

- **Phase A, sans les hallucinations** : code, tests, faits de R mesurés **sur la base réelle seulement** (D3, D4), revue (`second-avis` puis `reviewer`). Elle finit par un commit dit « grille figée », dont le SHA est cité dans le compte rendu. Personne ne lit `data/r/collecte/` pendant la phase A : ni le développeur, ni les tests, ni les fixtures.
- **Phase B, sur la collecte figée** : classement, vérification, porte, contrôle de qualité (D7), compte rendu. Le code utilisé est celui du commit « grille figée ». Seule une correction de l'extraction est permise, un tour au plus, dans les conditions de D7.

Garde mécanique : `scripts/pre_etude_r.py classer` exige `--grille-figee <sha>`. Il refuse de tourner (code 2) si `HEAD` diffère de ce SHA ou si l'arbre de travail n'est pas propre (`git status --porcelain` non vide, fichiers ignorés exclus). Il exige aussi `--manifeste-sha256 <hex>`, la valeur consignée par 1-12a dans son compte rendu (`docs/experiences/`). Il refuse si l'empreinte du `manifest.json` lu diffère.

**Entrée.** Seul `collecte.jsonl` est classé. `pilote.jsonl` est exclu : ses générations viennent de 3 des 10 modèles, sur des requêtes de l'ensemble final, avec les mêmes réglages déterministes, et le compter doublerait des citations. Le chemin est un argument (`--collecte`), puisque la sortie figée vit dans `data/r/collecte/` du dépôt principal, hors du worktree. Champs lus dans chaque ligne : `request_id`, `model`, `digest`, `response`, `done_reason`, `timestamp_utc`. `prompt` et `settings` sont relus seulement pour contrôler leur égalité avec `requetes.json`.

## D2 — Emplacement du code

Côté évaluateur (AD-1) : `datasets/` peut importer `tasks/`, jamais l'inverse. Aucun module de séance n'importe ce qui suit.

**Dans le paquet**, sous-paquet `src/nn_weight_writing/datasets/legal_r/`, que 1-13 réutilise pour les vraies comme pour les fausses :

| Module | Rôle | Noms |
|---|---|---|
| `frozen.py` | Lecture de la collecte figée : sha256 de chaque fichier vérifié contre `manifest.json` **avant** de décoder une ligne. Refus si un fichier manque, si l'empreinte diffère ou si une ligne est tronquée. | `Generation` (dataclass gelée), `read_collection(directory, *, manifest_sha256) -> list[Generation]`, `CollectionError` |
| `extract.py` | Extracteur de références dans un texte brut (D3). | `ExtractedRef`, `extract_references(text) -> list[ExtractedRef]` |
| `normalize.py` | Normaliseur commun. Les champs extraits d'une réponse de SLM, les métadonnées Judilibre et celles de l'open data administratif passent tous par la même fonction `normalize` (AD-16). | `RefFields`, `NormalizedRef`, `normalize(fields) -> NormalizedRef`, `fields_from_extracted`, `fields_from_judilibre`, `fields_from_ce_opendata`, `normalize_number`, `canonical_cc_chamber`, `canonical_ce_formation`, `canonical_seat`, `ALLOWED_FIELDS`, `FORBIDDEN_FIELDS`, `NORMALIZER_ID = "legal_r.normalize@1"` |
| `r_facts.toml`, `r_facts.py` | Faits propres à R, au format de `facts.toml` (`status`, `source`) : alias des sièges et des formations, codes ECLI, fenêtres de couverture fixes, règles désactivées par D4. Le chargeur refuse une section `unverified`. `facts.toml` n'est pas modifié, ce qui changerait `facts_sha256` et la version du générateur de S. | `RFacts`, `load_r_facts()`, `r_facts_sha256()` |
| `grid.py` | Grille d'incohérence (D4). | `Rule` (dataclass : `id`, `category`, `nuss`, `domain`, `basis`), `RULES`, `incoherences(ref, *, generation_date, facts, r_facts) -> frozenset[str]`, `GRID_VERSION = 1` |
| `judilibre.py` | Client de l'API Judilibre (D5) : transport injectable, cache de métadonnées, débit, quotas. | `JudilibreClient`, `key_from_env()`, `project_decision(meta) -> dict`, `RateLimitState`, `JudilibreError`, `BASE_URL` |
| `ce_index.py` | Index local de l'open data du Conseil d'État : lecture des XML d'une archive zip en flux, métadonnées seules. | `parse_archive(path) -> Iterator[dict]`, `CeIndex` (`load`, `save`, `lookup(number)`) |
| `existence.py` | Vérification d'existence (D5) et fenêtres de couverture. | `CoverageWindow`, `coverage_windows(...)`, `Verification`, `check_existence(ref, *, client, ce_index, windows) -> Verification` |
| `classify.py` | Unités dédupliquées, citation canonique, classes, écriture du classement (D6). | `Citation`, `Unit`, `build_units(...)`, `classify_unit(...)`, `write_classement(path, units)`, `CLASSEMENT_SCHEMA = 1` |
| `gate.py` | Porte R4 (D7). | `wilson(k, n, z=1.959963984540054) -> tuple[float, float]`, `GateResult`, `gate(incoherent, coherent_absent) -> GateResult`, `leave_one_out(...)` |

**En scripts** (`scripts/`), parce qu'ils téléchargent, orchestrent ou n'ont lieu qu'une fois :

- `scripts/index_ce_opendata.py` : téléchargement des archives mensuelles du Conseil d'État et construction de `data/r/ce_index/` (D5).
- `scripts/pre_etude_r.py` : sous-commandes `mesurer-base` (phase A, base réelle seule), `classer`, `echantillons`, `porte` (phase B).

Le paquet n'appelle ni Ollama ni aucun téléchargement en masse. Le seul accès réseau du paquet est `JudilibreClient` (`urllib`, comme `providers/probe.py`), dont le transport est injecté : les tests n'ouvrent aucune connexion. La clé n'est lue que par `key_from_env()`, appelée dans la sous-commande. Si `JUDILIBRE_KEY_ID` est absente de l'environnement, `scripts/pre_etude_r.py` lit la seule ligne `JUDILIBRE_KEY_ID=` du fichier passé par `--env-file` (défaut `.env` du dépôt principal), sans l'exporter dans `os.environ`. `JUDILIBRE_KEY_ID` est ajoutée à `SECRET_ENV_VARS` (`journal/writer.py`).

## D3 — Extracteur, normaliseur, déduplication

**Extraction** (`extract_references`), déterministe, à base de motifs, sans modèle :

1. **Ancres.** Une référence commence à une mention de juridiction et va jusqu'à l'ancre suivante, la fin de phrase ou 200 caractères. Une ancre est « Cour de cassation », « Cass. », « Cass », « Conseil d'État » ou « Conseil d'Etat », « CE », « cour d'appel de|d'|du X », « CA X », un ECLI, ou une autre juridiction (tribunal, TA, CAA, Conseil constitutionnel, Tribunal des conflits, CEDH, CJUE, CJCE). Un numéro de pourvoi ou de requête sans juridiction devant lui ouvre aussi une référence, de juridiction inconnue. Une réponse peut contenir plusieurs références, chacune avec au plus une date et un numéro. Une date ou un numéro de plus ouvre une nouvelle référence de même juridiction (liste « Cass. civ. 1re, 3 mai 2000, n° … ; 5 juin 2001, n° … »).
2. **Champs.**
   - Juridiction : `cc`, `ce`, `ca`, `other` ou `None`.
   - Formation : seulement le segment reconnu par les motifs de chambre ou de formation, jamais le texte libre qui l'entoure.
   - Siège : pour `ca`.
   - Date : `12 mars 2015`, `1er mars 2015`, mois abrégé (`janv.`, `févr.`, `sept.`…), `12/03/2015`, `12.03.2015`, `2015-03-12`. L'année a 4 chiffres. Le jour et le mois restent des entiers, même invalides : `30 février` donne (30, 2).
   - Numéro : le jeton qui suit `n°`, `nº`, `no`, `numéro`, `pourvoi`, `req.` ou `requête` (`[0-9][0-9./\- ]*[0-9]`), ou un motif nu `\d{2}-\d{2}\.\d{3}` ou `\d{2}/\d{5}`.
   - ECLI : `ECLI:` suivi de son reste, mis en majuscules.
3. **Gardés** : `raw` (le passage cité), `start`, `end`, plus le modèle et la requête d'origine, portés par `Citation`. **Retirés** : tout nom de partie ou d'affaire (« Dupont c/ Martin », « arrêt Perruche », « société X »). Aucun champ de `ExtractedRef` hors de `raw` ne porte de texte libre. `raw` ne sort jamais de `data/r/pre_etude/interne/`, qui n'est pas publié (D8).

**Normalisation** (`normalize`), identique pour une vraie et une fausse :

- **Liste blanche.** `RefFields` n'accepte que `ALLOWED_FIELDS` : `jurisdiction`, `formation_text`, `seat_text`, `day`, `month`, `year`, `number_text`, `ecli`, `source`, `source_id`, `decision_type`, `publication`, `update_date`. `fields_from_judilibre` et `fields_from_ce_opendata` projettent sur cette liste. Un dictionnaire qui contient une clé de `FORBIDDEN_FIELDS` (`text`, `zones`, `text_highlight`, `highlights`, `summary`, `themes`, `titlesAndSummaries`, `visa`, `rapprochements`, `timeline`, `files`, `Texte_Integral`) est accepté en entrée, mais sa valeur n'est ni copiée ni écrite.
- **Numéro** (`normalize_number`) : les espaces sont retirés, rien d'autre. Ni le tiret, ni le point, ni la barre ne sont ajoutés ou réparés : un numéro mal formé le reste, et la grille le juge. Pour `ce`, les points séparateurs de milliers ne sont pas retirés non plus (`108.243` reste mal formé dans le domaine de R-F1).
- **Chambre de la Cour de cassation** (`canonical_cc_chamber`). Les formes en toutes lettres ou abrégées (« première chambre civile », « 1re civ. », « civ. 1 », « Civ. 1ère », « chambre commerciale, financière et économique », « Crim. », « Ass. plén. », « chambre mixte ») et les codes Judilibre (`civ1` … `pl`, par l'inverse de `facts.chambers`) donnent l'une des 8 formes de D1.
  - Un rang ou un nom de chambre qui n'existe pas donne sa forme canonique inexistante : « 4e chambre civile » → `civ. 4e` ; « chambre sociale 2 » → `soc. 2e` ; « chambre fiscale » → `ch. fiscale`. Elle est jugée par R-O1.
  - Une formation du Conseil d'État citée pour la Cour de cassation donne sa forme de D1 (`Sect.`, `3e ch.`) et relève de R-O2.
  - « Civ. » sans rang, « chambre des requêtes », « chambres réunies », `ordo`, `allciv` et `other` donnent `None`, au statut `unparsed`. Les règles de formation ne s'appliquent pas à `None`.
- **Formation du Conseil d'État** (`canonical_ce_formation`). Elle couvre les formes de SLM et les valeurs de `Formation_Jugement`.
  - `Ass.` (Assemblée du contentieux) et `Sect.` (Section du contentieux).
  - `{k}e ch.` et `{k}e sous-sect.` ; `1re` pour k = 1.
  - `{k}e et {m}e ch. réunies` et `{k}e et {m}e sous-sect. réunies` (formes ajoutées à D1 pour R, triées par rang croissant).
  - `juge des référés` ; tout le reste donne `None`.
  - Un rang hors de [1, 10] garde sa forme et relève de R-O5.
- **Siège de cour d'appel** (`canonical_seat`) : correspondance après minuscules et retrait des accents, plus les alias de `r_facts.toml` (« Aix » → `Aix-en-Provence`, « Saint-Denis », « La Réunion » → `Saint-Denis de la Réunion`, codes `location` Judilibre). Un siège qui n'est pas dans les 36 garde le nom cité, mis en forme de titre. R-O3 le juge.
- `NormalizedRef` : `jurisdiction`, `formation` (forme canonique ou `None`), `day`, `month`, `year` (entiers ou `None`), `number` (normalisé ou `None`), `ecli` (ou `None`), `source`, `source_id`. Méthodes :
  - `key()` → `(jurisdiction, number, (year, month, day))` ;
  - `is_complete()` : juridiction dans `cc`, `ce`, `ca`, numéro présent, jour, mois et année présents ;
  - `to_reference()` → `Reference` de D1, ou `None` si la référence n'est pas complète ou n'a pas de formation.

**Déduplication.**

- Unité = `key()`. Les citations d'une même clé, quels que soient le modèle et la requête, forment une seule unité. Une même clé citée deux fois dans une réponse compte une citation.
- **Citation canonique** : la première dans l'ordre fixe suivant : modèle dans l'ordre de `MODELES` du script 1-12a, puis `request_id`, puis `start`. Elle fixe la formation et l'ECLI de l'unité. Les unités dont les citations divergent de classe (une incohérente, une cohérente) sont comptées et publiées (`class_conflict`). La classe reste celle de la citation canonique.

**Références partielles.** Sans juridiction, sans numéro, ou sans jour, mois et année complets : classe `partial`. Elles sont **exclues du numérateur et du dénominateur**, comptées et publiées, avec, à titre d'information, le nombre de celles que la grille trouverait incohérentes. Motif : une cohérente partielle ne peut pas être vérifiée, donc compter les incohérentes partielles et pas les cohérentes gonflerait p. De plus, R (format D1) exige une référence complète.

**Hors périmètre.** Juridiction `other` (tribunal judiciaire, TA, CAA, Conseil constitutionnel, Tribunal des conflits, juridictions européennes) : classe `out_of_scope`, exclue et comptée. R ne couvre que les trois juridictions de S.

## D4 — Grille d'incohérence (fixée ici, avant les données)

Une règle s'applique dans son **domaine**. Deux domaines :

- **U (universel)** : logique ou calendaire, toute date.
- **F (factuel)** : la règle repose sur un fait de `facts.toml` vérifié sur la fenêtre de S. Elle ne s'applique que si la décision est datée dans [2001-01-02, date de génération]. Avant 2001, ces règles ne jugent pas, et la référence ne devient incohérente que par une règle U.

« Date de génération » : la date UTC de `timestamp_utc` de la génération qui porte la citation canonique.

Réutilisation de 1-9 :

- Pour une référence complète avec formation canonique, `incoherences` appelle `violations(to_reference(), facts)` de `datasets/legal_rules.py`, convertit les `tXX` en règles R par la colonne `nuss`, puis filtre par domaine. Elle retire t06 et t12, recalculés ci-dessous, et `x_formation`.
- Pour une référence sans formation, elle applique les seules règles qui n'en dépendent pas, avec les fonctions de `legal_rules` : `number_jurisdictions`, `number_year`, `is_leap`, `legal_holidays`, `_MAX_DAY` (exposé sous le nom public `MAX_DAY`, renommage sans changement de valeur).
- Un test vérifie, sur toute référence complète, l'égalité entre les règles dérivées de S et `violations()` filtré.

| Règle | Catégorie | Domaine | Violée si… | Type de Nuss (1-9) | Base |
|---|---|---|---|---|---|
| R-C1 | calendrier | U | jour > maximum du mois (février : 29) | t02 | logique |
| R-C2 | calendrier | U | 29 février d'une année non bissextile | t15 | logique |
| R-C3 | calendrier | U | date postérieure à la date de génération (triplets, date impossible comprise) | t06 (date d'arrêt remplacée par la date de génération) | logique |
| R-C4 | calendrier | F | date valide, dimanche ou l'une des 8 fêtes légales fixes ; `cc` toute formation, `ce` formations collégiales seulement (`Ass.`, `Sect.`, chambres et sous-sections, réunies comprises) ; jamais `ca` | t12 (restreint) | `holidays.sample` : aucune décision de la Cour de cassation un dimanche ni une fête fixe. Les fêtes mobiles ne sont pas mesurées et les cours d'appel rendent des ordonnances le week-end : exclues. |
| R-H1 | chronologie | F | `cc`, numéro au motif `cc`, année du pourvoi > année de la décision | t01 | `cassation.number` |
| R-H2 | chronologie | F | `cc`, motif `cc`, écart ≥ 10 ans | t08 | empirique (max observé 6) |
| R-H3 | chronologie | F | `ca`, motif `ca`, année de l'appel > année de l'arrêt | t09 | `cours_appel.number` |
| R-H4 | chronologie | F | `ca`, motif `ca`, écart ≥ 10 ans | t13 | empirique (max observé 8) |
| R-F1 | format | F | numéro qui ne suit aucun des trois motifs | t10 | `*.number.pattern` |
| R-F2 | format | F | numéro au motif d'une autre juridiction seulement | t11 | idem |
| R-O1 | formation | F | `cc`, formation canonique inexistante (rang ou nom absent des 8, hors lexique du CE) | t03 | `cassation` |
| R-O2 | formation | F | formation de l'autre ordre (`cc` avec une formation du CE, `ce` avec une chambre de la Cour de cassation) | t05 | `cassation`, `conseil_etat` |
| R-O3 | formation | F | `ca`, siège absent des 36 | t04 | `cours_appel` |
| R-O4 | formation | F | `ce`, formation numérotée inexistante à la date : `ch.` (réunies comprises) avant le 2016-04-21, `sous-sect.` (réunies comprises) après le 2016-12-31 ; zone grise non jugée | t07, étendu aux formations réunies | `conseil_etat` (renommage de 2016) |
| R-O5 | formation | F | `ce`, rang de formation hors de [1, 10] | aucun (`x_formation` de S) | `conseil_etat.numbered_max` |
| R-E1 | ECLI | U | ECLI hors de la structure `^ECLI:FR:[A-Z0-9]{1,7}:\d{4}:[A-Z0-9.]{1,25}$` | aucun (type 15 du constat 1-1, écarté de S) | norme ECLI (conclusions du Conseil, JO C 127 du 29 avril 2011) |
| R-E2 | ECLI | mesuré | code de juridiction de l'ECLI dans l'ensemble mesuré d'une **autre** juridiction (un code inconnu ne viole rien) | idem | D4, mesure |
| R-E3 | ECLI | U | année de l'ECLI ≠ année de la décision | idem | norme ECLI |
| R-E4 | ECLI | mesuré | `ce` : partie ordinale ≠ `{numéro}.{AAAAMMJJ}` de la référence | idem | mesure (forme de 1-3 : `ECLI:FR:CECHR:2020:428409.20200710`) |
| R-E5 | ECLI | mesuré | `cc` : préfixe de chambre de la partie ordinale incompatible avec la chambre citée | idem | mesure |
| R-A1 | autre | F | série du numéro de pourvoi incompatible avec la chambre | t14 | `cassation.number` |

**« Autre » est une liste fermée** : R-A1 seulement. Toute autre incohérence vue au contrôle de qualité (D7) est notée `observation`, publiée, et n'est jamais comptée. Elle sert à estimer la sous-estimation de p.

**Règles mesurées (R-E2, R-E4, R-E5) et contrôle de spécificité**, joués en phase A par `pre_etude_r.py mesurer-base` sur des références **réelles** seulement :

- **Échantillons.**
  - Cour de cassation : `/scan` `abridged=true`, `date_type=creation`, un lot de 1 000 pour 2005, 2012, 2019 et 2024.
  - Cours d'appel : `type=arret`, 1 000 en 2023 et 1 000 en 2025.
  - Conseil d'État : toutes les décisions de l'index (D5).
- **Faits ECLI.** Codes de juridiction observés par juridiction (R-E2). Pour le CE, part des ECLI dont l'ordinal vaut `{numéro}.{AAAAMMJJ}` (R-E4). Pour la Cour de cassation, table préfixe ↔ chambre (R-E5).
  - Une règle mesurée n'est adoptée que si sa forme vaut pour au moins 99 % des références réelles qui portent un ECLI. Sinon elle est désactivée.
  - Valeurs, comptes et source écrits dans `r_facts.toml` (`status = "sample"`).
- **Spécificité.** Chaque référence réelle passe par `fields_from_judilibre` ou `fields_from_ce_opendata`, puis `normalize`, puis `incoherences` (date de génération = date de la mesure).
  - Une règle qui signale plus de 0,5 % des références réelles d'une juridiction est **désactivée pour cette juridiction** (`disabled_rules` de `r_facts.toml`, avec le taux mesuré). Elle n'est jamais réécrite.
  - Le taux résiduel de faux positifs par juridiction est publié.
- **Rappel de la vérification.** 20 références réelles par juridiction, tirées des mêmes échantillons (graine `[0, 5]`), passent par `check_existence`. Si moins de 19 sur 20 sont trouvées, les cohérentes de cette juridiction sont `unverifiable` (`verification_unreliable`).

**Recouvrement avec les 15 types de S** : part des unités incohérentes dont au moins une règle a un type de Nuss, part de celles qui relèvent d'un type attesté (t01 à t03), et part de celles qui n'ont que des règles sans type (ECLI, R-O5, formations réunies). Comptes par règle et par type publiés.

## D5 — Vérification d'existence

**Qui est vérifié.** Toute unité complète dont la date est valide, non future et dans la fenêtre de sa juridiction, **cohérente ou incohérente**. Une incohérente trouvée existante signale un faux positif de la grille (D7).

**Égalité exacte sur les champs, jamais sur un total.**

- Une unité **existe** si un enregistrement de la base a le même numéro normalisé (`number` ou un élément de `numbers`), la même date et la même formation canonique, ou le même siège pour `ca`. Pour une unité sans formation : numéro et date.
- Numéro et date égaux mais formation différente : l'unité n'existe pas telle que citée. Elle reçoit `partial_match = "formation"` et sa classe reste celle de la grille.
- Numéro trouvé à une autre date : `partial_match = "date"`, informatif.

**Cour de cassation et cours d'appel : Judilibre** (Swagger 1.0.0 relu le 2026-11-07, sha256 `4592c1ec…95674d` ; base de production `https://api.piste.gouv.fr/cassation/judilibre/v1.0`, établie par T1).

- **Test d'existence** : `GET /scan?jurisdiction={cc|ca}&date_start=D&date_end=D&date_type=creation&abridged=true&batch_size=1000`, avec `&location={code}` pour `ca` (code tiré de `GET /taxonomy?id=location&context_value=ca`), en suivant `next_batch` jusqu'à `null`. La liste complète des décisions de ce jour, comparée champ par champ, rend la recherche plein texte et son assouplissement (`relaxed`) inutiles. Une requête par (juridiction, date, siège) distincts : quelques centaines au total.
- **Diagnostic** pour une unité absente : `GET /search?query={numéro}&jurisdiction={cc|ca}&page_size=50`, forme de T4 et T5, pour `partial_match = "date"`. Pages suivies tant que `next_page` existe, 5 au plus. Le `total` n'est jamais lu comme une preuve.
- **Contrôle en phase A** (test `live`) : Perruche (`cc`, 2000-11-17, `99-13.701`) est trouvée par `/scan` `abridged=true`, et `number`, `numbers`, `chamber` et `decision_date` sont présents dans la version abrégée.
  - Si la version abrégée n'a pas ces champs : `abridged=false`, réponse projetée en mémoire par `project_decision` avant toute écriture.
  - Écart à consigner.
- **Client.**
  - En-tête `KeyId` seulement. La clé n'apparaît ni dans `repr`, ni dans une exception, ni dans le cache, ni dans une sortie.
  - Au moins 0,12 s entre deux requêtes (moins de 10 par seconde).
  - `x-rate-limit` lu à chaque réponse (`RateLimitState`) : pause d'une seconde si un compteur à fenêtre courte a `remaining` ≤ 2 ; arrêt (`JudilibreError`) si le compteur journalier tombe sous 1 000.
  - HTTP 429 : trois essais à 2, 4 puis 8 s, puis erreur. HTTP 423 (« activité suspecte ») : arrêt immédiat, sans nouvel essai, et message à l'orchestrateur.
  - Dernier `x-rate-limit` consigné dans le résumé.
- **Cache local** : `data/r/cache/judilibre/{sha256 de la requête canonique}.json`. La requête canonique est le chemin plus les paramètres triés, sans la clé.
  - Chaque fichier contient la requête, l'horodatage, le statut HTTP, `x-rate-limit`, les champs de page (`total`, `relaxed`, `batch`, présence de `next_batch` ou `next_page`) et les résultats projetés par `project_decision`.
  - Champs gardés : `id`, `jurisdiction`, `chamber`, `formation`, `location`, `number`, `numbers`, `ecli`, `decision_date`, `type`, `publication`, `update_date`. Aucun autre champ n'est écrit.
  - Une requête en cache n'est pas rejouée. `--rafraichir` l'est, et il est journalisé.

**Conseil d'État : open data de la justice administrative**, index local.

- **Index.** `scripts/index_ce_opendata.py` télécharge les archives mensuelles du Conseil d'État (`opendata.justice-administrative.fr`, Licence Ouverte 2.0) du mois de septembre 2021 au dernier mois publié. L'URL exacte est relevée sur la page de téléchargement par l'implémentation.
  - `parse_archive` lit chaque XML en flux (`zipfile`, `xml.etree.ElementTree.iterparse`) et ne garde que `Numero_Dossier`, `Date_Lecture`, `Numero_ECLI`, `Formation_Jugement`, `Code_Publication`, `Type_Decision` et `Date_Mise_Jour`.
  - Sorties : `data/r/ce_index/index.jsonl` et `data/r/ce_index/manifest.json` (sha256 et taille de chaque archive, date de téléchargement).
  - L'archive est supprimée après indexation, puisqu'elle contient le texte intégral.
- **Coût en téléchargement.**
  - Non mesuré. Estimé de l'ordre de quelques centaines de Mo pour environ 62 mois : environ 10 000 décisions par an, XML avec texte, compression zip.
  - Le script télécharge d'abord un mois, mesure, extrapole, puis demande `--confirmer` si l'estimation dépasse 2 Go.
- **Pas de JADE en 1-12.**
  - JADE ne couvre avant le 30 septembre 2021 que les décisions publiées au Lebon. On ne peut pas savoir si une décision inventée « aurait été » publiée : une cohérente de cette période est non vérifiable qu'elle soit dans JADE ou non.
  - JADE ne change donc pas p. Son coût est de 1,2 Go (`Freemium_jade_global_20250713-140000.tar.gz`, relevé sur `echanges.dila.gouv.fr/OPENDATA/JADE/` le 2026-11-07), plus environ 330 incréments quotidiens de 0,2 à 1 Mo.
  - Il reste ouvert à 1-13 si son tirage des vraies l'exige.
- **Conséquence publiée** : les incohérentes du Conseil d'État antérieures au 30 septembre 2021 ne sont pas vérifiées. Une décision réelle mal jugée par la grille n'y serait pas repérée, et le contrôle de D7 en couvre le risque.

**Fenêtres de couverture** (`coverage_windows`), fixées par règle, calculées en phase A sur la base réelle et publiées :

| Juridiction | Début | Fin |
|---|---|---|
| `cc` | première année Y telle que chaque année de Y à 2025 compte au moins 50 % de la médiane des comptes de 2022 à 2025 (`GET /stats?jurisdiction=cc&keys=year`) | `max_decision_date` de `/stats` − 90 jours |
| `ca` | 2022-04-15 (diffusion systématique des arrêts civils, sociaux et commerciaux, 1-3) | `max_decision_date` (`/stats?jurisdiction=ca`) − 90 jours |
| `ce` | 2021-09-30 | date de lecture la plus récente de l'index − 30 jours |

- Une cour d'appel dont la formation citée désigne une matière pénale (« correctionnel », « pénal », « instruction », « criminelle ») est hors fenêtre, puisque Judilibre ne diffuse pas encore le pénal des cours d'appel.
- Une cohérente hors fenêtre, ou dont la vérification échoue (réseau, `verification_unreliable`), est `unverifiable`, avec son motif : `before_window`, `after_window`, `penal_ca`, `verification_unreliable` ou `api_error`.
- Une incohérente hors fenêtre reste incohérente (R4 : elle n'a pas besoin de base).
- **Repli si l'API tombe** en phase B : miroir Hugging Face `antoinejeannot/jurisprudence` v2025.03.20, colonnes de métadonnées seules, avec une fin de fenêtre ramenée au 2025-03-19. Ce repli se décide et se consigne avant d'être utilisé, jamais après avoir vu p.

**Tests sans réseau.**

- Transport injecté : un `fetch(url, headers) -> (status, headers, body)` factice lit des réponses enregistrées dans `tests/fixtures/legal_r/judilibre/`.
- Ces réponses sont réduites à la liste blanche :
  - Perruche, d'après T4 ;
  - un numéro inventé, d'après T5 (`relaxed` true) ;
  - un jour à deux lots, pour `next_batch` ;
  - un 429 suivi d'un 200, et un 423 ;
  - un `x-rate-limit` bas ;
  - une réponse qui contient `text` et `zones`, pour vérifier qu'ils ne sont pas écrits.
- Le Conseil d'État est testé par une archive zip de trois XML écrits à la main au schéma de l'open data, avec `Texte_Integral`.
- Le seul test réseau est marqué `live` (désélectionné par défaut) et rejoue T4, T5 et le contrôle de la version abrégée.

## D6 — Classes, classement publié

**Ordre de décision**, pour chaque unité, d'après sa citation canonique :

1. juridiction `other` → `out_of_scope` ;
2. référence incomplète → `partial` ;
3. `rules = incoherences(...)` ;
4. vérifiée et trouvée (D5) → `exists`, quelles que soient ses règles. Si `rules` n'est pas vide, elle reçoit aussi `grid_false_positive = true` ;
5. `rules` non vide → `incoherent` ;
6. vérifiée et absente → `coherent_absent` ;
7. sinon → `unverifiable` (motif).

`p = n(incoherent) / (n(incoherent) + n(coherent_absent))`.

**Classement publié** : `data/r/pre_etude/classement.jsonl`. Il n'est pas commité (AGENTS.md : `data/` est ignoré, et c'est l'ébauche des fausses de R). Il est publiable puisque `r_republish = true`. 1-14 le met en asset de la release v0.1.0 (D8), et son sha256 est cité dans le compte rendu. Une ligne par unité, `ensure_ascii=False`, triée par `unit_id` :

| Champ | Contenu |
|---|---|
| `schema` | 1 |
| `unit_id` | `r-u00001`… (rang dans l'ordre trié des clés) |
| `jurisdiction`, `formation`, `year`, `month`, `day`, `number`, `ecli` | champs normalisés (`null` si absents) |
| `canonical` | `format_reference(to_reference())`, ou `null` |
| `class` | `incoherent`, `coherent_absent`, `exists`, `unverifiable`, `partial`, `out_of_scope` |
| `rules` | règles violées (D4), triées |
| `nuss_types` | types `tXX` correspondants |
| `unverifiable_reason`, `partial_match`, `grid_false_positive`, `class_conflict` | voir D5 et D6 |
| `verification` | `{"source": "judilibre" \| "ce-opendata" \| null, "checked_at": …, "cache_key": …, "found_id": … ou null}` |
| `citations` | `[{"model": …, "digest": 12 premiers caractères, "request_id": …}]`, ordre canonique |
| `source` | `"slm"` : aucune unité n'est attribuée à une base publique (condition 3 de 1-3) |
| `versions` | `{"normalizer": "legal_r.normalize@1", "grid": 1, "r_facts_sha256": …, "facts_sha256": …}` |

Le classement ne contient ni texte de réponse, ni passage cité, ni nom. Les passages (`raw`, `start`, `end`) vont dans `data/r/pre_etude/interne/extraction.jsonl`, jamais publié. `data/r/pre_etude/resume.json` porte les comptes, p, l'intervalle, la décision, les tables de D7 et les empreintes. Les fichiers d'entrée et de sortie ont leur sha256 dans `data/r/pre_etude/manifest.json`.

## D7 — Porte, répartition, contrôle de qualité

**Porte** (`gate`), stricte application de R4 :

- p et intervalle de Wilson (z = 1,959963984540054) ;
- `decision = "comparatif"` si p ≥ 0,30, sinon `"plafond"` ;
- `tight = low ≤ 0,30 ≤ high` ;
- si le dénominateur est nul : `ValueError` et décision à Anaël ;
- dénominateur inférieur à 100 : décision prise, réserve « effectif faible » au compte rendu et notification à Anaël.

**Grandeurs publiées en plus**, qui ne changent pas la décision. Une grandeur qui tombe de l'autre côté de 30 % que p ajoute la réserve « sensibilité » au compte rendu, ce que R4 n'appelle pas « serrée » :

- `p_window` : p restreint aux unités datées dans la fenêtre de leur juridiction, incohérentes comprises. Elle corrige l'asymétrie qui exclut les cohérentes anciennes et garde les incohérentes anciennes.
- `p_d1` : p sans les unités dont toutes les règles sont des règles ECLI, invisibles dans le format D1 de R (D8).
- Part des incohérentes dont la seule règle est de format (R-F1, R-F2), et part de celles qui ne tiennent qu'à une règle empirique (R-H2, R-H4).
- Par juridiction : p, intervalle et effectifs.
- Par modèle : p de ses unités, dédupliquées dans le modèle, avec intervalle.
- Par famille (préfixe du nom : `qwen3.5`, `gemma4`, `ministral-3`, `phi4-mini`, `granite4.2`, `lfm3`, `nemotron-3-nano`) :
  - part du dénominateur, une unité citée par k familles comptant 1/k pour chacune ;
  - `leave_one_out` : p sans les unités citées par cette seule famille.
  - « Aucune famille ne domine » si chaque part est ≤ 50 % et si aucun p sans une famille ne passe de l'autre côté de 30 %. Sinon, réserve « famille dominante » au compte rendu, avec le nom de la famille.

**Contrôle de qualité**, joué par le `reviewer` en phase B contre les règles de cette spec, d'après les réponses brutes et `extraction.jsonl`. Tirages par `numpy.random.default_rng([0, k])` sur les identifiants triés, sans remise, par `pre_etude_r.py echantillons` :

| Contrôle | Taille | Critère d'acceptation |
|---|---|---|
| Classe des unités du dénominateur (k = 1) | 60 (toutes s'il y en a moins) | ≤ 2 erreurs qui font passer une unité d'incohérente à cohérente ou l'inverse, ou hors du dénominateur ; ≤ 6 erreurs de champ sans effet sur la classe |
| Unités exclues (`partial`, `unverifiable`, `out_of_scope`) (k = 2) | 20 | ≤ 2 unités qui auraient dû entrer au dénominateur |
| Rappel de l'extraction (k = 3) | 30 réponses avec au moins une référence extraite et 10 sans | ≤ 3 références complètes manquées au total |
| Fausses absences (k = 4) | 30 `coherent_absent` (toutes s'il y en a moins) | recherche à la main sur Légifrance, ArianeWeb (CE) et le web ouvert ; ≤ 1 trouvée |
| Revue exhaustive | toutes les unités `grid_false_positive` et `partial_match = "formation"` | jugement unité par unité, consigné |

- **Échec d'un critère** : un seul tour de correction est permis, et il ne touche que l'extracteur ou le normaliseur.
  - On peut aussi y corriger un écart du code à une règle écrite ici. On ne change ni règle, ni seuil, ni fenêtre.
  - Tout est rejoué, et de nouveaux échantillons sont tirés avec k + 10.
  - p avant et après la correction sont publiés tous les deux.
  - Second échec : décision prise, réserve forte au compte rendu, et notification à Anaël.
- **Fausses absences.** Si f = trouvées / tirées > 0, `p_corr = I / (I + C·(1 − f))` est publié comme sensibilité. Sans outil web chez le reviewer, ce contrôle revient à Anaël.
- **Observations** : les incohérences vues hors grille sont comptées (D4), jamais ajoutées.

**Décision.** Le script imprime une ligne prête pour le journal du run : `1.12 · décision · porte R : p = 0,xx [0,xx ; 0,xx] sur n, comparatif|plafond[, serrée][, réserves …]`. L'orchestrateur la journalise (`invoke_dev_with` de 1-12). La valeur va aussi dans `config/r_gate.toml`, commité et écrit par `pre_etude_r.py porte`, sans saisie à la main :

```toml
decision = "comparatif"  # ou "plafond"
p = 0.0; low = 0.0; high = 0.0; n = 0; tight = false
reserves = []
classement_sha256 = "…"; grid_commit = "…"; spec_commit = "…"
```

Ce fichier n'est pas `protocol.toml`. Ce dernier est empreinté par séance (`protocol_sha256` dans l'événement `open`), et le changer ferait croire à un changement de protocole des séances de S. Écart à la table « Capability → Architecture » du spine, qui place la décision dans `protocol.toml` : point à valider par Anaël (ci-dessous).

## D8 — Livrables, contrat avec 1-13 et 1-14

**Livrables de 1-12** :

- code et tests de D2 ;
- `r_facts.toml` ;
- `docs/experiences/1-12-pre-etude-r.md`, avec :
  - méthode et SHA de cette spec et du commit « grille figée » ;
  - empreinte du manifeste de 1-12a ;
  - entonnoir des comptes : générations, références extraites, unités, classes ;
  - p, intervalle, décision, « serrée » ;
  - grandeurs de D7, recouvrement avec les 15 types, fenêtres, spécificité et rappel de la phase A, résultats du contrôle de qualité ;
  - réserves, sha256 du classement ;
  - attribution de la condition 2 de 1-3 ;
- `config/r_gate.toml`.

**Ce qui revient à 1-13** et n'est pas fait ici :

- Jeu R : `examples.jsonl`, `labels.jsonl`, `dataset.json` ; tirage stratifié des vraies sur la juridiction, la formation et la période des fausses ; vraies du Conseil d'État, avec JADE si besoin.
- Choix des fausses retenues dans R :
  - celles sans formation, que D1 ne peut pas écrire ;
  - celles dont la seule incohérence est l'ECLI, qui paraissent cohérentes en D1 ;
  - `exists` exclues d'office.
- Séances A et B, témoins C (point « même réseau ») et F sur R.
- Test CAP-11 : vraies et fausses passent par `normalize`.

**Contrat réutilisé par 1-13** (versionné, tout changement incrémente la version) :

- `normalize`, `RefFields`, `NormalizedRef.key()` et `to_reference()`, `NORMALIZER_ID` ;
- `fields_from_judilibre`, `fields_from_ce_opendata`, `project_decision` ;
- `JudilibreClient` et son cache ;
- `CeIndex` et `parse_archive` ;
- `check_existence` et `coverage_windows` ;
- schéma 1 du classement (`class`, `rules`, `canonical`) ;
- `config/r_gate.toml`.

Une fausse de R reprend `unit_id` et `canonical` du classement.

**Pour 1-14** : `nnww publish` joint `classement.jsonl` et `resume.json`. Il refuse `data/r/pre_etude/interne/`, `data/r/collecte/` et `data/r/cache/`.

## Décisions après second avis (P0-P12)

Décisions de l'orchestrateur du 2026-11-07, prises avant le gel de la grille et sans avoir vu `data/r/collecte/`. Elles priment sur les sections D1 à D8 et sur les critères d'acceptation là où elles s'en écartent.

- **P0 (Anaël) — porte sur p_d1.** La porte se décide sur **p_d1** : p sans les unités dont toutes les règles sont des règles ECLI (R-E1 à R-E5), puisque l'ECLI est absent du format D1 de R. p, p_window et les autres sensibilités sont publiées sans effet sur la décision. Si p_d1 et p_window tombent de part et d'autre de 30 %, la décision suit p_d1 et devient « serrée », avec réserve. Remplace le point 2 des « Points qui reviennent à Anaël ».
- **P1 — ordre de la phase B.** `classer` écrit le classement sans calculer aucune part. Le reviewer fait le contrôle de qualité de D7 sur ce classement. Au plus un tour de correction (extracteur, normaliseur ou vérificateur d'existence), consigné. Ensuite seulement, `porte` calcule les parts, une seule fois. `porte` refuse de tourner (code 2) sans le verdict du contrôle consigné dans un fichier daté qui cite le sha256 du classement. Aucune part n'est calculée ni affichée avant ce verdict, pas même par `classer`. Tout le code de la phase B est donc écrit en phase A.
- **P2 — numéros canonisés.** Le normaliseur canonise les variantes de format sans ambiguïté, fixées ici et testées. Seule une forme non canonisable compte en R-F1. La vérification d'existence porte sur la forme canonique. Remplace la puce « Numéro » de D3 et AC6. Variantes, après remplacement des tirets typographiques (`‐ ‑ ‒ – — −`) par `-` et retrait des espaces :
  - `cc` : deux chiffres, `-` ou `.` ou rien, deux chiffres, `.` ou rien, trois chiffres → `AA-NN.NNN` (`99-13701`, `9913701`, `99 13.701`, `99 - 13.701`, `99.13.701` → `99-13.701`) ;
  - `ce` : espaces retirés seulement (`428 409` → `428409`) ; les points restent (`108.243` reste mal formé) ;
  - `ca` : espaces retirés seulement ; aucun zéro ajouté.
  Toute autre forme garde son texte sans espaces et la grille la juge.
- **P3 — partielles.** Les `partial` restent hors du numérateur et du dénominateur (l'unité de R4 demande la clé complète). Le nombre de partielles que la grille trouverait incohérentes est publié à part.
- **P4 — fenêtre.** La fenêtre de couverture reste celle de R4 : seules les cohérentes hors fenêtre sont non vérifiables. p_window est publié comme sensibilité (voir P0).
- **P5 — champ de l'étude.** Cour de cassation et Conseil d'État, les deux juridictions du jeu de requêtes figé. Les cours d'appel citées sont `out_of_scope`, comptées et publiées à part ; le rapport ne généralise pas aux cours d'appel. Le client Judilibre garde le code `ca` (1-13 peut s'en servir), mais `classer` ne vérifie aucune cour d'appel. Les règles propres aux cours d'appel (R-H3, R-H4, R-O3) restent dans la grille pour 1-13 et ne jouent pas dans p.
- **P6 — rappel de la vérification.** 60 vraies références par juridiction (`cc`, `ce`), tirées avec la graine `[0, 5]`, au moins 57 retrouvées (borne basse de Wilson ≈ 0,86) ; sinon, les cohérentes de la juridiction sont `unverifiable` (`verification_unreliable`). Remplace « 20 références, 19 sur 20 » de D4.
- **P7 — fausses absences.** Le contrôle est fait par le reviewer avec Judilibre `/search` (plein texte, lecture humaine des résultats) et l'open data du CE, pas par Anaël, avant `porte`. S'il trouve plus d'une décision existante parmi 30 « cohérentes absentes », le tour de correction de P1 porte sur le vérificateur. Remplace la dernière phrase de « Fausses absences » (D7) et le point 4 des « Points qui reviennent à Anaël ».
- **P8 — pas de repli.** Aucun repli sur le miroir Hugging Face en phase B (retire le dernier point de « Fenêtres de couverture », D5). Si plus de 1 % des requêtes d'existence finissent en `api_error` après les nouvelles tentatives prévues, `classer` s'arrête sans écrire de classement et le dit (code 3).
- **P9 — clé et journal.** La commande charge la ligne `JUDILIBRE_KEY_ID=` de `--env-file` dans `os.environ` du processus, pour que `redact()` du journal masque la clé dans tout ce que le script écrit. Un test prouve que la valeur n'apparaît dans aucun fichier écrit. Remplace « sans l'exporter dans `os.environ` » (D2).
- **P10 — contrat avec 1-13.** Le contrat de D8 liste aussi `incoherences`, `RULES`, `GRID_VERSION`, `load_r_facts` et `r_facts_sha256` (dont `disabled_rules`), et `read_collection`. Le refus de `interne/`, `collecte/` et `cache/` par `nnww publish` revient à 1-14a ; 1-12 n'implémente pas `publish`.
- **P11 — spécificité de toute règle mesurable.** Le seuil de 0,5 % sur les vraies vaut pour toute règle qui peut se mesurer sur des références réelles, pas seulement pour R-E2, R-E4 et R-E5 : `mesurer-base` passe toutes les règles sur toutes les vraies. Une règle sans aucun contrôle sur le réel est retirée ou justifiée par écrit dans la spec avant le gel.
- **P12 — emplacement de la décision.** La décision va dans `config/r_gate.toml`, pas dans `protocol.toml`. La table « Capability → Architecture » du spine est amendée dans la PR de 1-12. Règle le point 3 des « Points qui reviennent à Anaël ».

## Phase A : écarts consignés et justification de P11 (2026-11-07)

Décidés en phase A, sur la base réelle seule, sans avoir lu `data/r/collecte/`. Faits mesurés : `docs/experiences/1-12-pre-etude-r.md` et `r_facts.toml`.

**Écarts à la spec.**

- **E1 — échantillons.** `/scan` en 12 lots mensuels de 84 par année (1 008), et non un lot de 1 000 : trié par date décroissante, un lot unique ne prenait que la fin de l'année. Cour de cassation : 3 862 décisions (des mois en ont moins de 84) ; cours d'appel : 2 016.
- **E2 — R-E5.** La chambre mixte et l'assemblée plénière (`series_exempt` de `facts.toml`, qui jugent des pourvois civils comme pénaux) sont hors de la table préfixe ↔ chambre et de la règle. Avec elles, le préfixe `CR` d'une décision d'assemblée plénière (1 sur 2) faisait tomber l'adoption à 83 %. Sans elles : 2 502 ECLI, 100 %, règle adoptée.
- **E3 — extracteur, ajouts au rappel.** Ancres secondaires de chambre abrégée en tête (`Civ.`, `Crim.`, `Ass. plén.`, `Ch. mixte`), hors de toute référence ouverte ; formation écrite juste avant « de la Cour de cassation » ou « du Conseil d'État » ; numéro nu de 6 chiffres dans une référence du CE (citation à la Lebon : « CE, Ass., 20 oct. 1989, Nicolo, 108243 »), seulement après une virgule, un point-virgule ou une parenthèse et avant une ponctuation ou la fin (jamais « 250000 euros », revue passe 1) ; une formation de plus ouvre une nouvelle référence quand la courante a déjà une date ou un numéro ; fin de phrase = ligne vide ou ponctuation suivie d'une majuscule hors abréviation (une ligne simple ne coupe pas : réponses structurées sur plusieurs lignes) ; un rang de chambre ne prend jamais le jour d'une date (« soc. 12 mars »).
- **E4 — extracteur, garde-fous de spécificité.** Textes normatifs masqués (loi, décret, arrêté, directive, règlement, circulaire, ordonnance numérotée, avec leur numéro et leur date) ; un numéro a au moins 5 chiffres (écarte « Bull. civ. II, n° 45 ») ; une référence sans date, numéro ni ECLI n'est pas gardée.
- **E5 — R-C1** couvre aussi un mois hors de [1, 12] et un jour nul (date numérique impossible, « 12/13/2015 »), même catégorie, même type t02.
- **E6 — domaine M.** R-E2, R-E4 et R-E5 (domaine « mesuré ») jouent à toute date.
- **E7 — formations réunies de plus de deux chambres** : `3e, 8e, 9e et 10e ch. réunies` (3 décisions de l'index). Deux rangs : `{k}e et {m}e ch. réunies`, comme D3.
- **E8 — index du CE.** 63 archives (`CE_202109` à `CE_202611`), 119,6 Mo, 40 134 décisions. XML à préfixe `xsi` non lié (janvier 2024) lus par un repli à balises. L'index est construit dans `data/r/ce_index/` du worktree (hors commit) ; la phase B le reconstruit ou le passe par `--ce-index`, et son sha256 est consigné par `classer`.
- **E9 — verdict du contrôle (P1).** Fichier JSON passé à `porte --verdict` : `date` (AAAA-MM-JJ), `classement_sha256`, `verdict` (`accepte` ou `echec`), `tour` (0 ou 1), `fausses_absences` (`tirees`, `trouvees`, entiers obligatoires, `tirees` = taille du tirage k = 4), `motif` pour un échec. `porte` refuse (code 2) sans verdict, avec un autre sha256, un verdict non daté, un échec au tour 0 (plus d'une fausse absence trouvée vaut échec, P7, même « accepte »), un tour différent de celui du classement, un `r_facts.toml` ou `facts.toml` changé depuis `classer`, ou une seconde fois (`resume.json` ou entrée `porte` du journal `journal.jsonl`, en ajout seul). `classer` refuse un second passage, sauf une fois avec `--tour-correction <verdict en échec du tour 0>` ; le classement du tour 0 est gardé dans `tour0/` (et `interne/tour0/`), le motif et le SHA du code corrigé vont au manifeste et au journal. Plus aucun `classer` après `porte`.
- **E10 — `classer` n'écrit ni n'affiche aucun compte par classe** (P1 strict) : entonnoir (générations, références, unités) et taux d'`api_error` seulement. Les comptes par classe viennent avec `porte`.
- **E11 — rappel (P6)** tiré parmi les vraies datées dans la fenêtre de leur juridiction, pour `cc` et `ce` seulement (P5).
- **E12 — conséquence de P2 pour 1-13.** Deux malformations de t10 dans S (point ou tiret retiré d'un numéro de la Cour de cassation) sont canonisées par le normaliseur de R : elles n'y sont plus incohérentes. `test_grid_matches_violations` le vérifie explicitement.
- **E14 — siège inconnu non publié.** Un siège de cour d'appel hors des 36 garde le nom cité pour R-O3 (D3), mais `classement.jsonl` publie `formation` et `canonical` à `null` : le nom capté après « CA » peut être celui d'une partie (« CA Renault SA »). 1-13 retrouve la citation dans `interne/extraction.jsonl`.
- **E13 — tests.** `scripts/pre_etude_r.py` a un transport injectable (`FETCH`, frontière réseau) ; le dépôt du contrôle de la grille figée est celui du script (`REPO`, remplacé par les tests seuls), et le paquet importé doit en venir. L'option cachée `--depot`, qui contrôlait un autre dépôt que le code exécuté, est retirée (revue passe 1). Doubles partagés : `tests/legal_r_support.py`.

**Justification de P11.** Les 21 règles ont tourné sur les 46 012 vraies (Cour de cassation 3 862, cours d'appel 2 016, Conseil d'État 40 134) : aucune ne dépasse 0,5 %, aucune n'est désactivée ni retirée. Faux positifs résiduels : 0,026 %, 0 et 0,117 %. Deux cas sans contrôle sur le réel, justifiés et gardés :

- R-E1, R-E2 et R-E3 pour les cours d'appel : Judilibre ne leur donne aucun ECLI (0 sur 2 016). R-E1 et R-E3 sont des définitions de la norme ECLI (structure ; année = année de la décision), contrôlées sur 40 810 ECLI de la Cour de cassation et du CE ; les cours d'appel sont hors de p (P5).
- R-C3 (date postérieure à la génération) ne peut pas se produire sur une vraie : c'est une impossibilité logique, sans fait mesuré.

## Critères d'acceptation

**AC1 — sha256 avant lecture.** Given une collecte dont `collecte.jsonl` diffère d'un octet de son manifeste, ou un manifeste d'empreinte autre que `--manifeste-sha256`, When `read_collection` ou `pre_etude_r.py classer`, Then `CollectionError` ou code 2, avant qu'une ligne soit décodée.

**AC2 — garde de la grille figée.** Given un arbre de travail modifié ou `HEAD` ≠ `--grille-figee`, When `classer`, Then code 2, et rien n'est écrit sous `data/r/pre_etude/`.

**AC3 — extraction multiple et noms retirés.** Given une réponse écrite à la main qui cite « l'arrêt Perruche (Cass. ass. plén., 17 novembre 2000, n° 99-13.701) » puis « CE, 3e et 8e chambres réunies, 10 juillet 2020, req. n° 428409 », When `extract_references`, Then deux références aux champs attendus, et aucun champ autre que `raw` ne contient « Perruche ».

**AC4 — normaliseur commun.** Given Perruche en sortie de SLM, en métadonnées Judilibre (T4) et sous une forme abrégée (« Cass., AP, 17 nov. 2000, n° 99-13.701 »), When `normalize`, Then trois `NormalizedRef` de même `key()` et même `to_reference()`, égal à `Cass. ass. plén., 17 novembre 2000, n° 99-13.701`.

**AC5 — liste blanche.** Given une réponse Judilibre qui contient `text`, `zones`, `text_highlight` et `summary`, When `project_decision` puis l'écriture du cache, Then aucun de ces champs ni aucune de leurs valeurs dans les fichiers écrits.

**AC6 — numéro non réparé.** Given `n° 99-13701` et `n° 99 - 13.701`, When `normalize_number(…, "cc")`, Then `99-13701` (R-F1 en 2015) et `99-13.701`.

**AC7 — référence partielle.** Given « Cass. civ. 1re, 12 mars 2015 », sans numéro, When `classify_unit`, Then `partial`, hors du numérateur et du dénominateur.

**AC8 — grille et domaines.** Given le tableau de `test_grid_hand_written` et un `RFacts` de test où R-E4 et R-E5 sont désactivées et où `CCASS` est le seul code mesuré pour `cc`, When `incoherences`, Then l'ensemble attendu pour chaque ligne. Lignes au moins :

| Référence | Génération | Attendu |
|---|---|---|
| `Cass. civ. 4e, 12 mars 2015, n° 13-27.123` | 2026-11-07 | {R-O1} |
| `Cass. civ. 4e, 12 mars 1995, n° 93-12.345` | 2026-11-07 | ∅ (domaine F) |
| `Cass. soc., 30 février 1990, n° 88-14.567` | 2026-11-07 | {R-C1} |
| `Cass. civ. 1re, 15 mars 2015, n° 13-27.123` (dimanche) | 2026-11-07 | {R-C4} |
| `Cass. civ. 1re, 6 avril 2015, n° 13-27.123` (lundi de Pâques) | 2026-11-07 | ∅ |
| `CA Lyon, 15 mars 2015, n° 13/04567` (dimanche) | 2026-11-07 | ∅ |
| `CE, juge des référés, 15 mars 2020, n° 439674` (dimanche) | 2026-11-07 | ∅ |
| `CE, 3e et 8e ch. réunies, 12 mars 2014, n° 361234` | 2026-11-07 | {R-O4} |
| `CE, 12e ch., 12 mars 2019, n° 412345` | 2026-11-07 | {R-O5} |
| `CA Lille, 12 mars 2015, n° 13/04567` | 2026-11-07 | {R-O3} |
| `Cass. com., 4 juin 2026, n° 24-12.345` | 2026-05-01 | {R-C3} |
| `Cass. crim., 12 mars 2015, n° 14-27.123` | 2026-11-07 | {R-A1} |
| Perruche avec `ECLI:FR:CCASS:2001:AP00001` | 2026-11-07 | {R-E3} |
| `CE, 5e ch., 12 mars 2019, n° 412345` avec `ECLI:FR:CCASS:2019:…` | 2026-11-07 | {R-E2} |

**AC9 — cohérence avec 1-9.** Given toute référence complète à formation canonique datée dans la fenêtre de S, et les 5 jeux de S en graine 0, When `incoherences` et `violations`, Then mêmes règles après conversion (t06 et t12 à part, voir `test_grid_matches_violations`).

**AC10 — existence par égalité de champs.** Given un `/scan` enregistré du 2000-11-17 qui contient Perruche, When `check_existence` sur Perruche, sur `99-13.701` au 18 novembre 2000 et sur `Cass. civ. 1re, 17 novembre 2000, n° 99-13.701`, Then `exists`, absente avec `partial_match = "date"`, et absente avec `partial_match = "formation"`.

**AC11 — relaxed ignoré.** Given un `/search` enregistré avec `relaxed` true et `total` > 0 sans numéro égal, When le diagnostic, Then aucune correspondance.

**AC12 — débit, quotas, clé.** Given un transport factice qui horodate les appels et une clé `KeyId-fictive-123`, When 30 appels, Then intervalle minimal ≥ 0,12 s ; pause après un `remaining` ≤ 2 ; `JudilibreError` sous 1 000 au compteur journalier ; arrêt sans nouvel essai sur 423 ; la clé ne figure ni dans `repr`, ni dans une exception, ni dans le cache.

**AC13 — couverture.** Given des `/stats` enregistrés, When `coverage_windows`, Then fenêtres conformes à D5 ; une cohérente `ce` de 2019 → `unverifiable` (`before_window`) ; une incohérente `ce` de 2019 → `incoherent`.

**AC14 — porte.** Given 90 incohérentes et 210 cohérentes absentes, Then p = 0,30, [0,2509 ; 0,3541], comparatif, serrée. Given 89 et 211, Then plafond, serrée. Given 120 et 180, Then comparatif, non serrée. Given 0 et 0, Then `ValueError`.

**AC15 — classement publiable.** Given un classement écrit depuis des fixtures, Then chaque ligne n'a que les champs de D6, `source = "slm"`, et aucun passage cité ; `interne/extraction.jsonl` est le seul fichier qui porte `raw`.

**AC16 — tirages reproductibles.** Given les mêmes unités, When `echantillons` deux fois, Then mêmes identifiants ; d'autres identifiants avec k + 10.

**AC17 — compte rendu.** Given la phase B finie, Then `docs/experiences/1-12-pre-etude-r.md` et `config/r_gate.toml` portent les mêmes p, intervalle et décision que `resume.json`, et le compte rendu cite le SHA de cette spec, celui de la grille figée et le sha256 du classement.

## Fichiers et tests

**À créer** : les modules de D2 sous `src/nn_weight_writing/datasets/legal_r/` (`__init__.py` compris), `r_facts.toml`, `scripts/index_ce_opendata.py`, `scripts/pre_etude_r.py`, `tests/fixtures/legal_r/` (réponses écrites à la main, réponses Judilibre réduites, archive CE factice), `docs/experiences/1-12-pre-etude-r.md` (phase B), `config/r_gate.toml` (phase B).

**À modifier** :

- `datasets/legal_rules.py` : `MAX_DAY` public, valeurs inchangées.
- `journal/writer.py` : `JUDILIBRE_KEY_ID` dans `SECRET_ENV_VARS`.

Ni `facts.toml`, ni `protocol.toml`, ni `session/`, ni les specs ne changent.

**Tests nommés** :

- `tests/test_legal_r_frozen.py` : `test_sha256_checked_before_decoding`, `test_manifest_digest_mismatch_refused`, `test_truncated_line_refused`, `test_only_collecte_is_read`.
- `tests/test_legal_r_extract.py` : `test_two_references_one_response`, `test_party_names_not_in_fields`, `test_date_forms`, `test_number_after_markers`, `test_list_of_references_same_court`, `test_ecli_alone_gives_jurisdiction`, `test_other_jurisdictions_flagged`.
- `tests/test_legal_r_normalize.py` : `test_same_reference_three_sources`, `test_forbidden_fields_never_copied`, `test_number_not_repaired`, `test_cc_chamber_forms`, `test_ce_formation_forms_and_joined`, `test_seat_aliases`, `test_partial_reference`, `test_to_reference_is_d1`.
- `tests/test_legal_r_grid.py` : `test_grid_hand_written` (tableau d'AC8), `test_grid_matches_violations`, `test_domains`, `test_disabled_rule_not_applied`, `test_rules_table_complete` (chaque règle a catégorie, domaine et base).
- `tests/test_legal_r_judilibre.py` : `test_key_never_exposed`, `test_rate_limit_interval`, `test_rate_limit_header_pause_and_stop`, `test_429_retry_423_stop`, `test_cache_whitelist_and_reuse`, `test_scan_follows_next_batch`.
- `tests/test_legal_r_existence.py` : `test_exists_by_field_equality`, `test_partial_matches`, `test_relaxed_search_ignored`, `test_coverage_windows`, `test_ce_index_lookup`, `test_ce_archive_text_dropped`.
- `tests/test_legal_r_classify.py` : `test_class_order`, `test_dedup_and_canonical_citation`, `test_class_conflict_counted`, `test_classement_fields`, `test_samples_reproducible`.
- `tests/test_legal_r_gate.py` : `test_wilson_values`, `test_decision_and_tight`, `test_zero_denominator`, `test_leave_one_family_out`.
- `tests/test_legal_r_live.py` (marqué `live`) : `test_perruche_scan_abridged`, `test_invented_number_absent`.

**À réaligner** : `tests/test_boundary.py` (aucun module de séance n'importe `datasets.legal_r`), `tests/test_legal_rules.py` (renommage `MAX_DAY`).

**Vérification** : `uv run ruff check .`, `uv run ruff format --check .`, tests ciblés pendant le travail, puis la CI de branche.

## Hors périmètre

- Jeu R, séances, témoins sur R (1-13).
- Publication et release (1-14).
- Collecte supplémentaire, à aucun moment (R4).
- Toute règle nouvelle après le commit « grille figée ».

## Points qui reviennent à Anaël

1. **Confirmer R4**, encore marquée « à confirmer », avant la phase B.
2. **Porte sur p ou sur `p_d1` ?** R4 compte les incohérences d'ECLI. Or le format D1 de R écarte l'ECLI (1-9), si bien qu'une fausse dont seul l'ECLI est incohérent paraît cohérente à un détecteur sur R. Cette spec suit R4 (porte sur p) et publie `p_d1`. Si Anaël préfère `p_d1`, il faut le décider avant la phase B.
3. **Emplacement de la décision** : `config/r_gate.toml` plutôt que `protocol.toml`, comme le place la table du spine. Amender la table du spine.
4. **Fausses absences** : contrôle à la main sur le web. S'il n'y a pas d'outil web dans la revue, il revient à Anaël (30 recherches au plus).

## Incertitudes

- **Version abrégée de `/scan`** : le Swagger dit « sans texte intégral ni métadonnées détaillées » sans lister les champs. Elle est vérifiée par le test `live` de la phase A, avec un repli prévu (D5).
- **Open data administratif** : l'URL des archives et leur taille ne sont pas relevées (la page d'accueil ne les donne pas). Le coût estimé (quelques centaines de Mo) n'est pas mesuré.
- **Couverture de la Cour de cassation avant 2021** : la règle des 50 % de la médiane est un choix fixé ici. Ses trous résiduels sont mesurés par le contrôle des fausses absences.
- **Rendement et composition de la collecte** inconnus à l'écriture : part des références partielles, des cours d'appel et des références antérieures à 2001. Un dénominateur faible donne un intervalle large et sans doute une décision « serrée ».
- **Formation canonique des chambres réunies et du juge des référés** du CE : formes ajoutées pour R, absentes de S, sans effet sur `legal.chars@1`. 1-13 décide si elles entrent dans R.
- **Rappel de l'extracteur** : il est écrit d'après des exemples rédigés à la main. Seul le contrôle de qualité de la phase B le mesure.
- **Fêtes mobiles, samedi et jours fériés du CE** : non mesurés, donc hors de R-C4 sauf les formations collégiales du CE (dimanche et fêtes fixes), dont la spécificité est contrôlée sur l'index réel en phase A.

## Revue

### Passe 1 (2026-11-07, SHA revu 0e93767)

Base : `origin/main` (08a62c6) ancêtre de HEAD, pas de rebase. Second avis (Haiku) repris point par point.

- Important, medium, second avis 1 : `porte` acceptait « accepte » avec plus d'une fausse absence (P7). Corrigé : plus d'une trouvée vaut échec (`qc_failed`), refus au tour 0, réserve forte au tour 1 ; `fausses_absences` obligatoires et `tirees` égal au tirage k = 4.
- Important, medium, second avis 2 : « une seule fois » ne tenait qu'à `resume.json`, `classer` relançable à volonté. Corrigé : journal en ajout seul `journal.jsonl` ; second `classer` admis une fois, sur le verdict en échec du tour 0 avec `motif` (`--tour-correction`), tour 0 gardé dans `tour0/` ; `porte` refuse si le journal a déjà une porte, même sans `resume.json`, et si le tour du verdict diffère. Une suppression délibérée de tout `data/r/pre_etude/` reste possible : garde mécanique, pas une preuve.
- Important, medium, second avis 3 : `--depot` contrôlait un autre dépôt que le code exécuté. Corrigé : option retirée, contrôle sur le dépôt du script et paquet importé exigé sous ce dépôt.
- Important, medium, second avis 4 : quota journalier converti en `api_error`, requêtes poursuivies. Corrigé : `JudilibreError.quota`/`fatal`, relevé par `check_existence` (arrêt, code 3 dans `classer`).
- Important, medium, second avis 5 : `porte` relisait les fenêtres d'un `r_facts.toml` éventuellement changé. Corrigé : refus si `r_facts.toml` ou `facts.toml` diffère des empreintes du manifeste.
- Important, medium, second avis 6 : un nom de partie capté après « CA » était publié. Corrigé autrement que proposé (une liste fermée casserait R-O3 et D3) : siège inconnu non publié (E14).
- Important, medium, second avis 7 : nombre nu de 6 chiffres (montant) pris pour un numéro du CE. Corrigé (E3 précisé). Les mesures de phase A (spécificité, rappel) passent par les métadonnées réelles, pas par l'extracteur : `r_facts.toml` inchangé.
- Nit, low, second avis 8 : juridiction inconnue classée `out_of_scope` au lieu de `partial` (D6). Corrigé.
- Nit, low, second avis 9 : balises à espace de noms ignorées en silence. Corrigé : balises lues sans espace de noms, `ValueError` si une archive à XML ne donne aucune décision. Vérifié sur deux archives réelles (2024-01 : 348/348, 2025-06 : 602/602, comptes identiques au manifeste) : index et mesures inchangés.
- Nit, low, second avis 10 : `write_classement` et `write_extraction` sans `redact()`. Corrigé (`redact` passé par le script).
- Rejeté, low, second avis 11 : la suppression des archives existe (`shutil.rmtree(path.parent)` après `parse_archive`, `scripts/index_ce_opendata.py`).
- Nit, low, revue : un `api_error` du seul diagnostic `/search`, après un `/scan` qui établit l'absence, rend l'unité `unverifiable` ; conservateur et plafonné par P8. Non corrigé.
- Complexité, Nit, revue : `compute_gate` testait `r not in ecli_only` (liste de dictionnaires, O(n·m)). Corrigé par un ensemble d'`unit_id`. Aucun autre parcours complet par événement.
