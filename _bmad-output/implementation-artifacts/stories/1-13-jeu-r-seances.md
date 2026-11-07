---
story: "1-13"
title: Jeu R et séances sur R
status: review
branch: feat/1-13-jeu-r
---

# Story 1-13 : jeu R et séances sur R

## Objet

Construire le jeu **R** (`legal_r`) : vraies références de Judilibre et de l'open data du Conseil d'État, fausses tirées des hallucinations de SLM classées par 1-12, passées par le même normaliseur (CAP-11, AD-16). Puis jouer sur R les séances A et B et les témoins C (dont le point « même réseau ») et F, et évaluer sur R tous les réseaux et règles de S et S-réservé (`nnww evaluate --on`). Le plan des séances et la lecture du rapport suivent la décision de la porte de 1-12 (`config/r_gate.toml`) : **comparatif** ou **mesure de plafond**.

Références : SPEC.md (CAP-7, CAP-11, CAP-12) ; `jeux-de-donnees.md` (R) ; `methodes-et-lots.md` (lot 1, porte R4) ; spine AD-1, AD-2, AD-4 amendé, AD-12, AD-16, AD-17, AD-18 amendé ; constat `docs/verifications/1-3-judilibre-hallucinations.md` (section 2, conséquences pour 1-13, R1, R3, R7) ; spec et code de 1-12 (`feat/1-12-pre-etude-r`, grille figée `1a672a1`) ; spec de 1-14 (contrat de R, `publish`, rassemblement) ; comptes rendus de 1-9 à 1-11.

**Écrite le 2026-11-07, avant tout code, sans lire `data/r/collecte/` ni `data/r/pre_etude/`.** Le classement de 1-12 n'existe pas encore et l'issue de la porte n'est pas connue : chaque règle ci-dessous vaut pour les deux issues, et seule la section D8 en dépend.

## Décisions reprises telles quelles

- Porte décidée sur **p_d1** (P0 de 1-12, Anaël) : p sans les unités dont toutes les règles sont des règles ECLI ; décision et réserves dans `config/r_gate.toml`, écrit par `pre_etude_r.py porte` (P12).
- Contrat de 1-12 (D8, P10) réutilisé sans modification : `normalize`, `RefFields`, `NormalizedRef.key()` et `to_reference()`, `NORMALIZER_ID = "legal_r.normalize@1"`, `fields_from_judilibre`, `fields_from_ce_opendata`, `fields_from_extracted`, `project_decision`, `JudilibreClient` et son cache, `CeIndex`, `check_existence`, `coverage_windows`, `incoherences`, `RULES`, `GRID_VERSION`, `load_r_facts`, `r_facts_sha256`, schéma 1 du classement. Une fausse de R reprend `unit_id` et `canonical` du classement.
- Fenêtres de couverture mesurées en phase A de 1-12 (`r_facts.toml`) : Cour de cassation du 1989-01-01 au 2026-08-07, Conseil d'État du 2021-09-30 au 2026-10-07. Cours d'appel hors du champ de l'étude (P5) : elles sont `out_of_scope` dans le classement, donc absentes de R.
- Contrat de 1-14a pour R : tâche `legal_r` (déjà dans `r_tasks`) ; jeux `data/legal_r/<jeu>/` et `heldout/legal_r/<jeu>/` au format d'AD-16, plus `sources.jsonl` (`id`, `class` ∈ {`real`, `fake`}, `source` ∈ {`judilibre`, `ce-opendata`, `jade`, `slm:<tag>`}, mêmes `id` qu'`examples.jsonl`) ; `extraction_date` dans chaque `dataset.json` ; identifiants sans le préfixe `legal-r` (pris par S-réservé) ; `raw` de 160 caractères au plus, sans motif de nom de partie ; aucune clé `text`, `zones`, `text_highlight` ; `held_out_types` facultatif. L'archive de R publie le réservé (R2, Q1 de 1-14).
- Protocole du lot 1 inchangé : `pass_budget = 20` figé, `turn_limit = 200`, `max_session_usd = 5` (facturé seul, AD-11), `session_timeout_s = 7200`, `max_freeze_attempts = 3`, effort `medium` pour Sonnet et MiMo, `max_tokens = 131072` pour MiMo. `config/protocol.toml` n'est pas touché (une seule `protocol_sha256` au lot 1).
- Tailles des cases sur R (`protocole-ecriture.md`) : A-programme vers 10⁵, A-littéral vers 10⁴ (`--size-target 100000` et `10000`, fenêtre d'une demi-décade de 1-10a).
- Encodeur de famille `legal.chars@1` (AD-4 amendé) et `legal.fields@2` pour F, communs à `legal_s`, `legal_s_reserved` et `legal_r`.

## Décisions après second avis (S1 à S13)

Prises par l'orchestrateur le 2026-11-07, **avant la porte de 1-12**, et non revues après. Elles priment sur les sections D1 à D12 et les critères ci-dessous là où elles les contredisent.

- **S1 — Écart d'année du numéro.** Les vraies sont appariées aussi sur l'écart entre l'année de la décision et l'année du pourvoi ou de la requête lue dans le numéro (classes `0`, `1`, `2`, `3+`, et `none` pour un numéro sans année). La distribution de cet écart est publiée par classe (`dataset.json`, `year_gap`). Deux témoins triviaux sont entraînés sur l'entraînement de R et évalués sur son réservé : une régression logistique sur l'écart seul, une autre sur la longueur du `raw` seule ; leurs exactitudes réservées sont publiées comme **plancher d'indice** (une méthode qui ne fait pas mieux n'a rien appris au-delà de ces indices).
- **S2 — Trois tentatives par case dans les deux issues.** Comme au lot 1 (`methodes-et-lots.md`) : la colonne « mesure de plafond » de D8 passe de 3 à **9 séances Sonnet** (graines 0, 1, 2). Seule la lecture change entre les issues.
- **S3 — Points d'Anaël tranchés maintenant.** (1) incohérentes datées avant la fenêtre de couverture exclues (défaut) ; (2) MiMo en B seulement, plafond 2 $ facturés ; (3) 3 tentatives (S2) ; (4) amendements de CAP-7, CAP-11, de la section R de `jeux-de-donnees.md` et d'AD-17 rédigés dans la PR de cette story ; (5) vocabulaire et description de R de D6 ; (6) seuil d'arrêt à 80 fausses.
- **S4 — R4.** La porte sur p_d1 est déjà amendée dans `methodes-et-lots.md` par la PR d'état de l'orchestrateur : cette story la cite et ne la réécrit pas.
- **S5 — `corpus_date`.** `corpus_date` = date d'extraction des vraies (jour du tirage Judilibre et de l'index du CE), et non plus la date la plus ancienne de la collecte (D6 remplacé sur ce point). Garde et test : aucune vraie postérieure à `corpus_date` ; une fausse postérieure reste une date future (incohérente).
- **S6 — Type de jour.** Les vraies sont aussi appariées sur le type de jour de la date (`ouvre`, `samedi`, `dimanche_ou_ferie`). Une fausse sans vraie possible dans sa strate est exclue (`no_real_in_stratum`) et comptée dans l'entonnoir publié.
- **S7 — Aucun `raw` partagé avec S.** Aucun `raw` de R, vrai ou faux, n'égale un `raw` de S ou de S-réservé : garde sur les deux classes (une fausse égale est exclue, `raw_in_s`), test.
- **S8 — Mélange réel.** AC8 est renforcé par un test de mélange réel : l'ordre des classes n'est pas trié et la plus longue suite d'une même classe ne dépasse pas celle d'une permutation de graine fixée de même composition (borne calculée dans le test), en plus du critère des 4 premiers.
- **S9 — « Serrée ».** Au sens de `methodes-et-lots.md` amendé ; D8 ne dépend que de la décision (comparatif ou plafond), « serrée » ne change que le rapport.
- **S10 — Tirage par `/scan` du jour.** Les vraies de la Cour de cassation sont tirées par `/scan` du **jour cité** de la fausse (`date_start = date_end`, comme 1-12), plutôt que par chambre × année ; si le jour n'offre aucune vraie de la strate, les jours voisins de même type de jour dans la même année sont essayés dans un ordre fixé (écart journalisé). Coût mesuré en phase A sur un échantillon et projeté pour 300 fausses ; arrêt propre (code 3, rien d'écrit) et reprise par le cache si le quota tombe.
- **S11 — Arrêt de MiMo.** MiMo est arrêté sur R après trois séances de suite finies en troncature (comptées entre tentatives), consigné.
- **S12 — Non-altération (CRPA L. 322-1).** Les vraies gardent dans `sources.jsonl` leur numéro et leurs champs d'origine (`origin` : juridiction, chambre ou formation, date, numéro tels que la base les donne, sans texte ni nom) ; le `raw` n'en est qu'une mise en forme.
- **S13 — Vigilance de la revue de 1-12.** Le numéro nu du CE n'est reconnu qu'après une ponctuation ; aucune conséquence pour 1-13, qui part du classement.

## D1 — Phases et garde-fous

La story se déroule en deux phases sur `feat/1-13-jeu-r`.

- **Phase A, code sans données de R.** Code, tests, fixtures écrites à la main, revue (`second-avis` puis `reviewer`). Personne ne lit `data/r/collecte/` ni `data/r/pre_etude/` : ni le développeur, ni les tests. Elle finit par un commit « code du jeu R figé ».
- **Phase B, données.** Après la porte de 1-12 (`config/r_gate.toml` commité, PR de 1-12 fusionnée) : construction de R, commit « jeu R figé » (compte rendu partiel avec les sha256 des trois jeux), séances, témoins, évaluations, compte rendu, revue, PR.

**Base de la branche.** Le code de 1-13 importe `datasets/legal_r/` de 1-12, absent de `main` (94e22fe). La phase A part de `main` après la fusion de la PR de 1-12 (rebase de cette branche, qui ne porte alors que cette spec). Si l'orchestrateur veut lancer la phase A plus tôt, il fusionne `1a672a1` dans cette branche (merge commit, conflit connu du spine sur AD-18 résolu en faveur de `main`), sans jamais rebaser `feat/1-12-pre-etude-r` (décision du 2026-11-07, 08:49).

**Gardes mécaniques de `scripts/jeu_r.py construire`** (code 2, rien d'écrit) :

- `config/r_gate.toml` absent, ou son `classement_sha256` différent du sha256 du `classement.jsonl` lu ;
- `data/r/pre_etude/manifest.json` dont l'empreinte des sorties ne correspond pas aux fichiers lus (`classement.jsonl`, `interne/extraction.jsonl`), ou `resume.json` absent (porte non jouée) ;
- `r_facts_sha256()` ou `facts_sha256()` différent des `versions` du classement ;
- un des trois dossiers de sortie existe déjà et n'est pas vide (un jeu R se construit une fois ; une reconstruction est une décision consignée, ancien jeu déplacé à la main et jamais réutilisé) ;
- arbre de travail non propre (`git status --porcelain`, fichiers ignorés exclus) : le SHA du code qui construit R va dans `dataset.json`.

## D2 — Fausses de R

**Unités admises.** Les unités du **dénominateur de la porte** (P0) : classe `incoherent` avec au moins une règle hors ECLI (R-E1 à R-E5), ou classe `coherent_absent`. Sont exclues d'office, et comptées dans l'entonnoir publié :

| Motif d'exclusion (`excluded_reason`) | Unités |
|---|---|
| `not_in_gate` | `partial`, `unverifiable`, `out_of_scope`, `exists` (dont `grid_false_positive`) |
| `ecli_only` | `incoherent` dont toutes les règles sont des règles ECLI (hors de p_d1 ; cohérentes en format D1 et non vérifiées comme telles) |
| `not_d1` | `canonical` nul (formation `None`, mois hors de [1, 12]…), ou `canonical` qui ne relit pas par `parse_reference` ou que `encode_chars` refuse |
| `before_window` | date antérieure au début de la fenêtre de sa juridiction (comparaison sur l'année et le mois, la date pouvant être impossible) |
| `after_window_not_future` | date après la fin de la fenêtre et non postérieure à la date de génération (aucune ne devrait exister : une cohérente l'aurait été `unverifiable`) |
| `found_at_build` | trouvée existante à la revérification de D4 |

Les incohérentes datées après leur date de génération (R-C3, type t06) sont gardées : leur date est l'incohérence même.

**Pourquoi la fenêtre.** Une fausse ancienne (Cour de cassation avant 1989, Conseil d'État avant le 30 septembre 2021) n'a pas de vraie de même année dans une base exhaustive : sa seule année trahirait la classe, quel que soit le normaliseur (constat 1-3). Avec la fenêtre, chaque fausse de R est **soit vérifiée absente par égalité de champs** (D5 de 1-12, puis D4 ici), **soit impossible** (date invalide ou future) : c'est CAP-11 dans la rédaction de R7. L'effet sur la composition est publié : part des incohérentes dans R (`p_R`) à côté de p_d1, et nombre d'exclusions `before_window` par juridiction. Élargir R aux incohérentes anciennes (vraies appariées depuis Judilibre avant 1989 et depuis JADE pour le Conseil d'État) revient à Anaël (point 1).

**Chaîne de normalisation des fausses (CAP-11).** Pour chaque unité retenue, `construire` relit la citation canonique dans `interne/extraction.jsonl` (même ordre canonique que D3 de 1-12), recalcule `format_reference(normalize(fields_from_extracted(ref)).to_reference())` et refuse (code 2, `normalizer_mismatch`) si le résultat diffère de `canonical`. Le `raw` d'une fausse est `canonical`, jamais retouché. `interne/` n'est lu que par cette commande et n'est ni copié ni publié.

**Type d'une fausse** (`type_id` de `labels.jsonl`, `type_of(rules, nuss_types)`) :

- règles retenues = règles du classement hors ECLI, telles que la grille figée les a trouvées (pas de recalcul) ;
- `type_id` = le plus petit `tXX` des types de Nuss de ces règles ;
- `x01` si les règles retenues n'ont aucun type de Nuss (R-O5) ;
- `c00` pour une `coherent_absent`.

Toutes les règles et types d'une fausse vont dans `sources.jsonl` (`rules`, `nuss_types`), pas dans `labels.jsonl`, dont le format est fermé (`id`, `label`, `type_id`). Réserve publiée : une fausse de 1989 à 2000 dont la formation n'existe pas reste `c00`, puisque les règles F ne jugent pas avant 2001 (D4 de 1-12) ; sa classe reste juste.

## D3 — Vraies de R : tirage apparié

**Une vraie par fausse**, tirée pour lui ressembler sur tout ce qui n'est pas l'incohérence. R est équilibré, comme S : autant de vraies que de fausses dans chaque jeu.

Pour chaque fausse *f* (ordre des `unit_id`), dans sa juridiction :

1. **Année** : celle de *f* ; pour une fausse future (t06), une année tirée parmi celles des fausses non futures de la même juridiction ; pour une année sans vraie disponible dans la strate, l'année la plus proche dans la fenêtre (écart journalisé).
2. **Formation** : celle de *f* si elle existe à cette date dans la base réelle (chambre de la Cour de cassation ; formation du Conseil d'État, chambres réunies et juge des référés compris). Sinon (chambre inexistante, formation de l'autre ordre, rang hors de [1, 10]…), une formation tirée selon la distribution des formations existantes parmi les fausses de la même juridiction et de la même période.
3. **Décision** : tirée uniformément, sans remise, parmi les décisions de la base de cette juridiction, formation et année, dans la fenêtre de couverture, dont la normalisation donne une référence complète écrite en D1.

Tirages par `numpy.random.default_rng([seed, 0, i])` (*i* = rang de *f*), graine de construction 0.

**Bases** (lecture seule du contrat de 1-12) :

- Cour de cassation : `JudilibreClient`, `GET /scan?jurisdiction=cc&chamber={code}&date_start=AAAA-01-01&date_end=AAAA-12-31&date_type=creation&abridged=true&type=arret&batch_size=1000`, `next_batch` suivi jusqu'à la fin, une énumération par strate (chambre, année) ; cache `data/r/cache/judilibre/` du worktree, liste blanche de `project_decision` ; débit, quotas et refus 423 de 1-12. Ordre de grandeur : quelques centaines de requêtes.
- Conseil d'État : `CeIndex` de 1-12 (`data/r/ce_index/`, 40 134 décisions, `CE_202109` à `CE_202611`), passé par `--ce-index` avec le sha256 de son `manifest.json`, sans nouveau téléchargement. JADE n'est pas utilisé (aucune fausse avant la fenêtre).
- Projection de chaque décision par `fields_from_judilibre` ou `fields_from_ce_opendata`, puis `normalize`, puis `to_reference()` et `format_reference()` : le `raw` d'une vraie est la référence normalisée, sans autre modification (condition 4 de 1-3).

**Exclusions côté vraies**, avant tirage :

- toute décision dont le numéro normalisé est celui d'une fausse de R (une fausse à `partial_match = "formation"` ou `"date"` ne côtoie jamais la vraie dont elle est une copie) ;
- tout `raw` égal à un `raw` de S ou de S-réservé (graine 0 : séance, entraînement de 8 192 et de 32 768, réservé), à un exemple cité dans la description d'une tâche juridique, ou à un autre `raw` de R ;
- toute décision dont le `raw` dépasse 160 caractères ou que `encode_chars` refuse (aucune attendue).

**Sources des vraies** (`sources.jsonl`) : `source` = `judilibre` ou `ce-opendata`, `source_id` (identifiant Judilibre, ou `Numero_Dossier` et date pour le CE), `update_date` (`Date_Mise_Jour` pour le CE), `extracted_at`. **Sources des fausses** : `source = "slm:<modèle de la citation canonique>"` (par exemple `slm:qwen3.5:2b`), `unit_id`, `rules`, `nuss_types`, `class_conflict`. Aucune fausse n'est attribuée à une base publique (condition 3) ; aucun texte, nom ni passage cité n'y figure.

## D4 — Revérification à la construction

Avant le tirage des vraies, chaque fausse retenue dont la date est valide et dans la fenêtre repasse par `check_existence` (même client, même index, même cache) :

- trouvée → exclue (`found_at_build`), comptée, et signalée au compte rendu (décision ajoutée à la base depuis la classification, ou défaut du vérificateur) ;
- `api_error` → la construction s'arrête (code 3) sans rien écrire, comme P8 de 1-12 ;
- une fausse à date impossible ou future n'est pas interrogée (absente par construction).

Elle ne change jamais la classe ni la porte de 1-12 : elle ne fait que retirer des fausses de R.

## D5 — Découpage en séance, entraînement et réservé

Soit **F** le nombre de fausses retenues. Les paires (fausse, vraie appariée) sont réparties **par paire** : une vraie va toujours dans le jeu de sa fausse.

| F | Séance (`data/legal_r/session`) | Entraînement (`data/legal_r/train`) | Réservé (`heldout/legal_r/eval`) |
|---|---|---|---|
| F ≥ 120 | 20 paires (40 exemples, comme S) | ⌊(F − 20) / 2⌋ paires | F − 20 − ⌊(F − 20) / 2⌋ paires |
| 80 ≤ F < 120 | 20 paires | aucun (C et F sur R non joués) | F − 20 paires |
| F < 80 | R n'est pas construit ; arrêt, notification à Anaël (point 6) | | |

Exemples : F = 300 → 40, 280 et 280 exemples ; F = 200 → 40, 180, 180 ; F = 100 → 40, 0, 160.

- **Strates du découpage** : juridiction × classe visible (incohérente ou `c00`) × période (1989-2000, 2001-2015, 2016-2021, 2022 et après, future). Dans chaque strate, ordre tiré par `default_rng([seed, 1])`, puis répartition en tourniquet séance, réservé, entraînement jusqu'à ce que la séance ait ses 20 paires, puis réservé et entraînement en alternance. Le réservé a donc la même composition que l'entraînement, à une paire près par strate.
- **Ordre dans chaque jeu** : mélange par `default_rng([seed, 2, k])` (*k* = 0 séance, 1 entraînement, 2 réservé). Le N d'un témoin prend les N premiers exemples du jeu mélangé (comme 1-11).
- **Identifiants** : `jr-s00001` (séance), `jr-t00001` (entraînement), `jr-e00001` (réservé), dans l'ordre mélangé : l'identifiant ne dit pas la classe. Préfixe `jr-`, distinct de `legal-` (S et S-réservé).
- **Étanchéité** (AD-2, AD-16) : l'agent ne voit que le paquet de séance, matérialisé depuis `data/legal_r/session/examples.jsonl` ; `TaskSpec.session_datasets = ("session",)` refuse `--dataset train` ou `eval` (O1 de 1-9) ; aucun `id`, `raw` ni numéro normalisé n'est commun à deux jeux de R ; aucun `raw` de R n'est un `raw` de S. Le pilote Claude Code n'a aucun outil intégré (AD-14) et le bac à sable n'a ni fichier ni réseau (AD-5) : `data/r/`, `heldout/` et Judilibre restent hors de portée de la séance.

**`dataset.json`** de chaque jeu (`write_dataset`, clé `composition`) : `task = "legal_r"`, `split`, `encoder = "legal.chars@1"`, `generator = "legal_r"`, `version = 1`, `seed = 0`, `extraction_date` (date UTC de l'énumération Judilibre), `extraction_dates` (`judilibre`, `ce-opendata` = date de téléchargement de l'index), `corpus_date` (D6), fenêtres, `classement_sha256`, `r_gate` (décision, p_d1, intervalle, `tight`), `normalizer`, `grid`, `r_facts_sha256`, `facts_sha256`, `code_commit`, `ce_index_sha256`, `swagger_sha256` (Swagger Judilibre relu, jamais copié), effectifs par classe, juridiction, formation, période, type et famille de modèle, `p_R`, entonnoir des exclusions, `visible_types`. **Pas de `held_out_types`** : aucun type du vocabulaire n'est tenu à l'écart ; `c00` et `x01` se lisent dans `by_type` d'`eval.json`. `files` porte aussi le sha256 de `sources.jsonl`.

## D6 — Tâche `legal_r`

Dans `tasks/legal/` (côté séance, AD-1 : aucun import de `datasets/`) :

- `TASK_R = LegalTask("legal_r", …)`, inscrite au registre par `_register_legal` avec `session_datasets = ("session",)` ; codec identique à S (`encode` = `encode_chars`, `encode_prepared` = `encode_fields_v2`, `decode` réel puis faux, `legacy_encoders`).
- `LegalTask` gagne deux champs à valeur par défaut, `head` (défaut : `HEAD` de S) et `type_overrides` (descriptions remplacées par identifiant), et lit son vocabulaire dans `TYPES` plus `R_EXTRA_TYPES`. **Les descriptions et vocabulaires de `legal_s` et `legal_s_reserved` restent identiques à l'octet** (test sur le sha256 du prompt système des séances de 1-10).
- **Vocabulaire visible de R** : les 12 types de S qui visent la Cour de cassation ou le Conseil d'État (t01, t02, t03, t05, t06, t07, t08, t10, t11, t12, t14, t15 ; t04, t09 et t13 ne visent que les cours d'appel, absentes de R), avec leurs descriptions de S, sauf t06 dont la date d'arrêt devient `corpus_date`, plus `x01` (« Autre incohérence détectable sans base de données, hors des types ci-dessus »). `x01` est dans `R_EXTRA_TYPES`, pas dans `TYPES` (la composition de S ne change pas). `c00` n'est pas un type d'incohérence et n'est pas montré.
- **`corpus_date`** = date UTC la plus ancienne de `timestamp_utc` dans la collecte, lue dans `resume.json` ou le manifeste de 1-12 (pas dans `collecte/`). Aucune vraie n'est postérieure (fin de fenêtre antérieure) ; toute fausse t06 l'est. Elle est fixée à la construction et écrite dans `dataset.json` ; la description de la tâche la lit dans une constante du module (`R_CORPUS_DATE`), posée par le commit « jeu R figé ». Le prompt de R n'existe donc qu'à partir de ce commit, et aucune séance n'est lancée avant.
- **Description de R** (`HEAD_R`, fixée ici, dans l'esprit de `HEAD`) :
  - références de la Cour de cassation et du Conseil d'État seulement, mêmes formes et mêmes exemples de formats que S (sans la cour d'appel), formations réunies et juge des référés du Conseil d'État cités parmi les formes possibles ;
  - « Le corpus est arrêté au {corpus_date}. » ;
  - « La moitié des références sont vraies, tirées des bases publiques ; l'autre moitié sont des références citées par de petits modèles de langage et absentes de ces bases. Une fausse peut présenter une ou plusieurs incohérences du vocabulaire ci-dessous, une autre incohérence, ou aucune incohérence visible. » ;
  - rien sur la part des fausses sans incohérence visible, ni sur les modèles, ni sur la porte.
  - `TAIL` de S inchangé (classes, sorties, encodage).
  La description est la même quelle que soit l'issue de la porte : seul le plan des séances change (D8).

## D7 — Séances A et B sur R

Règles du lot 1 et de 1-10, sans changement :

- Pilote Claude Code (abonnement, 0 $ facturé) pour Sonnet 5.5 ; `NNWW_CLAUDE_CWD_ROOT='C:\nnww-cwd'` posé dans chaque commande, configuration dédiée `~/.nnww/claude-config`, aucune `ANTHROPIC_API_KEY`. Pilote API (OpenRouter, facturé) pour MiMo-V2.6-Pro, `.env` chargé dans la commande seulement (`set -a; . ./.env; set +a`), valeurs jamais affichées.
- `nnww session --task legal_r --dataset session --method {B|A-program|A-literal} --model {sonnet-5.5|mimo-v2.6-pro} --attempt n --seed n-1 --lot 1`, avec `--size-target 100000` (A-programme) ou `10000` (A-littéral).
- Budget de passes 20, plafonds et effort du protocole ; une coupure par limite d'usage termine la séance en `error`, rejouée avec la même tentative et la même graine, jamais reprise ; une séance refusée avant lancement par un défaut du harnais est rejouée après correctif, consigné comme en 1-10.
- Pas de Fable sur R (SPEC : une tentative sur S seulement).
- **MiMo** : 1-10 a montré que MiMo ne tient pas S (réponses tronquées en raisonnement à 64 000 et 131 072 jetons ; 2 séances B gelées sur 6, sur S-réservé). Proposition par défaut (point 2) : **B seulement**, au réglage de 1-10 (131 072, effort medium, graine transmise), arrêt de MiMo après trois fins tronquées de suite, résultat consigné ; aucune case A. Plafond facturé de 1-13 : **2 $**.
- Drapeaux d'audit (AD-19) relevés par séance ; les séances signalées sont listées pour jugement en 1-14b, jamais jugées ici.

## D8 — Selon l'issue de la porte

Tout ce qui précède est commun aux deux issues : même jeu R, même description, même protocole, mêmes témoins. Seuls le nombre de séances et la lecture changent.

| | **Comparatif** (p_d1 ≥ 30 %) | **Mesure de plafond** (p_d1 < 30 %) |
|---|---|---|
| Sonnet 5.5 | B, A-programme 10⁵, A-littéral 10⁴ : **3 tentatives** (graines 0, 1, 2), 9 séances | mêmes cases, **3 tentatives** (graines 0, 1, 2), 9 séances (S2) |
| MiMo | B, 3 tentatives (si point 2 accepté) | aucune séance |
| Témoins | identiques (D9) | identiques (D9) |
| S → R | identique (D10) | identique (D10) |
| Mesure principale | exactitude sur le réservé de R, écart entre tentatives, A contre B contre C à données égales | **plafond** et **part du plafond atteinte** ; exactitude sur le sous-ensemble détectable |
| Lecture au compte rendu | classement des méthodes sur R, avec le plafond en repère | pas de classement des méthodes ; R dit jusqu'où un détecteur sans base peut aller sur de vraies hallucinations |

Grandeurs publiées dans les deux cas, calculées depuis `by_type` d'`eval.json` (aucune saisie) :

- **plafond** du réservé = (vraies + fausses de type autre que `c00`) / total : exactitude d'un détecteur sans base parfait au sens de la grille ; borne basse du vrai plafond, puisque la grille peut manquer des incohérences (observations de 1-12) ;
- **part du plafond atteinte** = (exactitude − 0,5) / (plafond − 0,5) ;
- **exactitude détectable** = sur les vraies et les fausses autres que `c00` ;
- rappel sur `c00` (attendu proche de 0 pour un détecteur sans base ; un rappel élevé est une alerte : mémoire du modèle ou recopie, à juger en 1-14b).

Si la porte est « serrée », la décision suit p_d1 (R4) et le compte rendu le dit ; le plan reste celui de la colonne de la décision.

## D9 — Témoins C, F et « même réseau » sur R

PyTorch par `uv run --group train`, CPU seul (AD-13).

- **`config/train.toml`**, section ajoutée `[tasks.legal_r]` : `hidden = [32]`, `epochs = 100`, `n_values = [64, 256]` ; architecture de référence de S (3 060 × 32 + 32 + 32 × 2 + 2 = 98 018 paramètres pour C, 77 154 pour F). Aucun réglage choisi sur R : les 100 époques de 1-11 sont reprises, le réservé de R n'est jamais lu pour régler quoi que ce soit.
- **Courbe C et F** (R3, option 1) : N = 64, 256 et **N_max** = taille de `data/legal_r/train` (seulement les N ≤ N_max), graines 0, 1, 2. `uv run --group train python scripts/temoins_c_f.py run --tasks legal_r --n 64 256 <N_max> --seeds 0 1 2`. Sans jeu d'entraînement (80 ≤ F < 120) : non joués, consigné.
- **Point « même réseau »** (AD-17) : chaque séance A de R gelée est réentraînée depuis des poids aléatoires sur `data/legal_r/train`, à **N = N_max** au lieu de 8 192 (impossible sur R : écart à CAP-7 consigné, R3), graines 0, 1, 2 : `uv run --group train nnww retrain runs/1/<séance> --data data/legal_r/train --n <N_max> --seed s --lot 1`.
- **Entraîner sur S, évaluer sur R** (R3, option 2) : D10.
- Tous les témoins sont évalués par `nnww evaluate`, comme les séances (pas de mesure parallèle) ; `courbe-c-f.jsonl` n'est qu'un relevé de travail.

## D10 — Évaluations

Dans le worktree, après le gel de toutes les séances :

```
uv run nnww evaluate --lot-dir runs/1 --heldout-root heldout --from-task legal_r
```

Évaluation croisée **S → R**, dans l'emplacement rassemblé (D11), avec le code de cette branche (seul à connaître `legal_r`), lancée depuis le worktree :

```
uv run nnww evaluate --lot-dir C:\Users\Utilisateur\nnww-artefacts\runs\1 \
    --heldout-root C:\Users\Utilisateur\nnww-artefacts\heldout --from-task legal_s --on legal_r:eval
uv run nnww evaluate --lot-dir C:\Users\Utilisateur\nnww-artefacts\runs\1 \
    --heldout-root C:\Users\Utilisateur\nnww-artefacts\heldout --from-task legal_s_reserved --on legal_r:eval
```

Elles couvrent les séances A et B gelées de 1-8 à 1-10 sur S et S-réservé, les témoins C et F de 1-11 à tous les N et les réentraînements. Chaque réseau écrit `eval-cross-legal_r-eval.json` (`cross: true`) à côté de son `eval.json`, qui n'est pas touché. 1-14b les régénère à l'identique (AD-9). L'évaluation R → S n'est pas demandée.

## D11 — Rassemblement et publication à blanc

Depuis la racine du dépôt principal, après les évaluations natives :

```
uv run python scripts/rassembler_runs.py --to C:\Users\Utilisateur\nnww-artefacts --from .claude/worktrees/1-13
```

Ajout seul (`runs/1/` de R, `data/legal_r/`, `heldout/legal_r/`) ; `data/r/` et les `eval*.json` exclus par le script. 1-13 ne régénère aucun jeu de S : aucun conflit attendu ; s'il y en a un, `--only runs heldout` et consigné.

Puis, depuis le worktree :

```
uv run nnww publish 1 --root C:\Users\Utilisateur\nnww-artefacts --dry-run --notice <NOTICE de test>
uv run nnww publish 1 --root C:\Users\Utilisateur\nnww-artefacts --dry-run --notice <fichier vide>
```

Le `NOTICE` de test, dans le dossier temporaire de la session, reprend mot pour mot l'attribution de la condition 2 de 1-3 avec `extraction du <extraction_date>` et la date de l'open data du CE ; il n'est pas commité (`NOTICE` revient à 1-14b). Attendu : aucun refus avec le premier ; `r_attribution_missing` seul avec le second, qui prouve le contrôle ; archive de R construite (trois jeux de `legal_r`, `sources.jsonl` compris). Sorties résumées au compte rendu (nombres de séances, témoins, membres, `raw` réservés contrôlés), sans écrire d'archive.

## D12 — Coût et durée estimés

| Poste | Facturé | Équivalent API | Durée |
|---|---|---|---|
| Séances Sonnet, comparatif (9) | 0 $ | ~6 $ (B ~0,05 $, A-programme 10⁵ ~0,30 $, A-littéral 10⁴ 0,7 à 2,4 $ par séance, d'après 1-10) | ~1 h 30 en série |
| Séances Sonnet, plafond (3) | 0 $ | ~2 $ | ~20 min |
| MiMo B ×3 (comparatif, point 2) | 0,15 à 0,40 $ (plafond 2 $) | idem | 20 à 75 min (troncatures possibles à ~25 min) |
| Requêtes Judilibre (quelques centaines) et index CE réutilisé | 0 $ | — | ~10 min |
| Témoins C, F, réentraînements (N ≤ ~300, CPU) | hors budget | — | quelques minutes |
| Évaluations natives et croisées (~200 dossiers) | — | — | ~10 à 20 min |
| Agents (dev-story Opus pour une story pivot, second avis Haiku, reviewer Opus, phase A puis phase B) | abonnement | ~8 à 15 $ (estimation, non mesurée) | phase A ~1 h 30 ; phase B ~3 h (comparatif) ou ~2 h (plafond) |

Lot 1 : 1,27 $ facturés au registre avant 1-13 (78 clôtures) ; après 1-13, au plus ~3,3 $ sur 100 $.

## Critères d'acceptation

**AC1 — porte jouée d'abord.** Given un `config/r_gate.toml` absent, ou dont `classement_sha256` diffère du classement passé, ou un `resume.json` absent, When `jeu_r.py construire`, Then code 2 et aucun dossier `legal_r` créé (`test_build_requires_gate_and_matching_classement`).

**AC2 — fausses du dénominateur seulement.** Given un classement de fixtures avec une unité de chaque classe, une incohérente ECLI seule, une incohérente de 1975, une incohérente future, une `canonical` nulle, When `select_fakes`, Then seules l'incohérente à règle visible dans la fenêtre, l'incohérente future et la `coherent_absent` sont retenues, et l'entonnoir compte chaque autre motif de D2 (`test_select_fakes_gate_denominator_and_window`).

**AC3 — même normaliseur (CAP-11).** Given Perruche en sortie de SLM (extraction de fixture) et en métadonnées Judilibre (T4), When la chaîne des fausses de D2 et celle des vraies de D3, Then deux `raw` identiques, `Cass. ass. plén., 17 novembre 2000, n° 99-13.701`, produits par le même appel `normalize` (espion qui compte les appels des deux chemins) ; Given une `canonical` de classement qui diffère du recalcul, Then code 2 `normalizer_mismatch` (`test_same_normalizer_for_real_and_fake`, `test_canonical_mismatch_refused`).

**AC4 — vraies non retouchées (condition 4).** Given le jeu construit depuis les fixtures, When chaque vraie est relue avec son `source_id` dans le cache, Then son `raw` égale `format_reference(normalize(fields_from_*(meta)).to_reference())` et `parse_reference(raw)` rend la juridiction, la formation, la date et le numéro de la base (`test_real_rows_match_their_source`).

**AC5 — sources (condition 3).** Given le jeu construit, Then `sources.jsonl` a les mêmes `id` qu'`examples.jsonl`, chaque vraie une source publique, chaque fausse `slm:<modèle>`, et `check_sources` de `publish` ne rend aucune violation (`test_sources_follow_condition_3`).

**AC6 — appariement.** Given 30 fausses de fixtures (Cour de cassation et CE, une chambre inexistante, une future, une à `partial_match = "formation"`), When `match_reals`, Then chaque vraie a la juridiction et l'année de sa fausse (année tirée pour la future), la formation de sa fausse quand elle existe, aucune vraie n'a le numéro d'une fausse, et deux exécutions de même graine donnent les mêmes paires (`test_match_reals_follows_fakes`, `test_no_real_shares_a_fake_number`, `test_match_reals_reproducible`).

**AC7 — découpage et étanchéité (AD-16).** Given F = 300, 100 et 79 fausses de fixtures, When `split_pairs`, Then 20/140/140, 20/0/80 paires et refus (code 2) ; aucun `id`, `raw` ni numéro commun entre deux jeux ; chaque vraie dans le jeu de sa fausse ; moitié de vraies dans chaque jeu ; aucun `raw` de R égal à un `raw` de S de graine 0 (`test_split_sizes`, `test_split_no_overlap`, `test_no_raw_shared_with_s`).

**AC8 — identifiants opaques.** Given le jeu construit, Then les `id` suivent `jr-[ste]\d{5}`, ne commencent pas par `legal-`, et leur ordre ne suit pas la classe (au moins une vraie et une fausse parmi les 4 premiers de chaque jeu de fixtures, graine 0) (`test_ids_prefix_and_shuffle`).

**AC9 — contrat de publication.** Given le jeu construit, Then chaque `dataset.json` porte `extraction_date`, chaque `raw` a au plus 160 caractères et aucun motif de nom de partie, aucune clé `text`, `zones` ni `text_highlight` n'existe dans les trois jeux ; `check_content(..., strict=True)` ne rend rien (`test_r_dataset_publishable`).

**AC10 — tâche et frontière.** Given le registre, Then `legal_r` est inscrite, d'encodeur `legal.chars@1`, de jeux de séance `("session",)`, de vocabulaire à 13 entrées (12 types et `x01`) sans `c00` ni t04, t09, t13, et sa description ne contient ni « exactement une incohérence » ni « cour d'appel » ; `nnww session --task legal_r --dataset eval` est refusé ; `tests/test_boundary.py` reste vert (aucun module de séance n'importe `datasets/`) (`test_legal_r_task_registered`, `test_legal_r_session_dataset_whitelist`).

**AC11 — S inchangé.** Given les tâches `legal_s` et `legal_s_reserved`, Then leur description, leur vocabulaire et le sha256 de leur prompt système égalent ceux des séances de 1-10 (valeur relevée dans un journal de 1-10 et figée dans le test) (`test_s_task_prompts_unchanged`).

**AC12 — types des fausses.** Given des règles `{R-O1, R-C4}`, `{R-O5}`, `{R-E3}` seul, et une `coherent_absent`, When `type_of`, Then `t03`, `x01`, exclue en amont (ECLI seul), `c00` (`test_type_of_fake`).

**AC13 — revérification.** Given une fausse retenue que le cache de fixtures trouve existante, et une autre dont la requête rend `api_error`, When `construire`, Then la première est exclue `found_at_build`, et avec la seconde la construction s'arrête (code 3) sans écrire (`test_build_recheck_existence`).

**AC14 — évaluation croisée et témoins.** Given un réseau de `legal_s` de fixtures et le réservé de R de fixtures, When `nnww evaluate --on legal_r:eval`, Then `eval-cross-legal_r-eval.json` porte `cross: true`, `target.task = "legal_r"`, et `by_type` compte `c00` ; When `nnww train legal_r --data data/legal_r/train --n 64 --seed 0`, Then un `run.json` de tâche `legal_r` (`test_cross_eval_s_to_r`, `test_train_legal_r`).

**AC15 — sur les données réelles (phase B, constat, pas un test).** Given R construit, Then le compte rendu donne l'entonnoir, F, `p_R` à côté de p_d1, les sha256 des trois jeux et du classement, les tableaux des séances (statut, passes, exactitude, plafond, part du plafond, coût facturé et équivalent, drapeaux), des témoins et de S → R ; `nnww publish --dry-run` ne refuse rien avec le `NOTICE` de test.

## Fichiers

**À créer**

- `src/nn_weight_writing/datasets/legal_r/dataset.py` : `FakeRow`, `RealRow`, `Pair`, `Selection` (`fakes`, `excluded: dict[str, int]`), `select_fakes(classement, *, extraction, windows, generation_dates) -> Selection`, `type_of(rules, nuss_types) -> str`, `match_reals(fakes, pool, *, seed) -> list[Pair]`, `split_pairs(pairs, *, seed) -> dict[str, list[Pair]]`, `write_r_dataset(directory, pairs, *, split, meta) -> Path`, `R_DATASET_VERSION = 1`, `R_ID_PREFIX = "jr-"`, `MIN_FAKES = 80`, `RBuildError`.
- `src/nn_weight_writing/datasets/legal_r/pool.py` : `RealCandidate`, `cc_candidates(client, chamber_code, year) -> list[RealCandidate]`, `ce_candidates(index, formation, year, window) -> list[RealCandidate]` (projection, normalisation, D1).
- `scripts/jeu_r.py` : sous-commande `construire --pre-etude-dir --r-gate --ce-index --ce-index-sha256 --seed 0 --env-file [--root .]` (gardes de D1, D4, écritures de D5, résumé `data/r/jeu_r/resume.json` et `manifest.json`, jamais publiés) ; transport injectable comme `pre_etude_r.py`.
- `tests/fixtures/legal_r/jeu_r/` : classement, extraction, cache Judilibre et index CE écrits à la main (aucune donnée réelle de la collecte).
- `tests/test_legal_r_dataset.py`, `tests/test_legal_r_task.py`.
- `docs/experiences/1-13-jeu-r.md` (phase B).

**À modifier**

- `src/nn_weight_writing/tasks/legal/task.py` : champs `head` et `type_overrides` de `LegalTask`, `HEAD_R`, `SENTENCE_R`, `R_CORPUS_DATE`, `TASK_R` ; `tasks/legal/types.py` : `R_EXTRA_TYPES` (`x01`), `R_VISIBLE` ; `tasks/legal/__init__.py` : `TASK_R` dans `TASKS`.
- `src/nn_weight_writing/datasets/io.py` : `write_dataset(..., extra_files: dict[str, bytes] | None = None)` pour `sources.jsonl`, empreinte dans `files` ; comportement inchangé sans l'argument.
- `src/nn_weight_writing/cli.py` : `legal_r` dans les choix de `train` (bloc `train` seulement ; `datagen` n'est pas étendu, R ne se régénère pas par graine).
- `config/train.toml` : section `[tasks.legal_r]`.
- `budget/ledger.csv` : lignes écrites par les séances.
- Specs, amendements à valider par Anaël (point 4) : `SPEC.md` (success de CAP-7 : « sur R, C jusqu'au N disponible et entraînement sur S évalué sur R » ; success de CAP-11 : rédaction de R7) ; `jeux-de-donnees.md`, section R (R1 : sources, champs, fenêtre, appariement, découpage) ; spine, AD-17 (point « même réseau » à N_max sur R).

**À réaligner** : `tests/test_boundary.py`, `tests/test_legal_task.py` (tâches du registre, descriptions de S), `tests/test_train_legal.py` et `tests/test_cli_session.py` (choix de `train`, liste blanche des jeux de séance).

**À ne pas toucher** (1-14b suit) : `src/nn_weight_writing/{publish,report,evaluation}/`, `scripts/rassembler_runs.py`, `config/publish.toml` (`r_tasks` déjà juste), `config/protocol.toml`, `config/models.toml`, `docs/mesures/`, `NOTICE`, `docs/rapport-lot1.md`, `docs/SOURCES.md`, les modules de 1-12 sous `datasets/legal_r/` (contrat versionné, grille figée), `r_facts.toml`, `facts.toml`, `config/r_gate.toml`, `_bmad-output/implementation-artifacts/run-autonome.md`, `sprint-status.yaml`. Aucun jeu ni journal commité (`data/`, `heldout/`, `runs/` ignorés).

**Vérification** : `uv run ruff check .`, `uv run ruff format --check .`, tests ciblés, puis la CI de branche.

## Hors périmètre

- Jugement des séances signalées, tableau du lot, `NOTICE`, rapport, release v0.1.0 (1-14b).
- Toute collecte nouvelle, toute règle de grille nouvelle, tout changement de la porte.
- R en cours d'appel ; R réservé non publié (lot ultérieur).

## Points qui reviennent à Anaël

Tranchés le 2026-11-07 par l'orchestrateur (S3) : défauts retenus pour 1, 2, 5 et 6, 3 tentatives pour 3, amendements rédigés dans la PR pour 4.

1. **Fenêtre de R.** Par défaut, les incohérentes antérieures à la fenêtre sont exclues (sinon l'année trahit la classe) ; R ne mesure alors que des hallucinations datées dans la fenêtre. Option : les garder, avec des vraies de même année tirées de Judilibre avant 1989 et de JADE (1,2 Go) pour le Conseil d'État avant le 30 septembre 2021 ; leur absence ne serait établie que par l'incohérence.
2. **MiMo sur R.** Par défaut, B seulement, 3 tentatives en comparatif, aucune en plafond, arrêt après trois troncatures. Option : aucune séance MiMo sur R.
3. **Mesure de plafond à 1 tentative par case.** Option : 3, comme en comparatif (0 $ facturé, ~1 h et ~4 $ équivalent de plus).
4. **Amendements de spec** : CAP-7 et CAP-11 (R3, R7), section R de `jeux-de-donnees.md` (R1), AD-17 (même réseau à N_max sur R).
5. **Vocabulaire et description de R** : 12 types de S plus `x01`, t06 daté par `corpus_date`, phrase « une fausse peut ne présenter aucune incohérence visible », sans la part des cohérentes.
6. **Seuil d'arrêt** : moins de 80 fausses retenues, R n'est pas construit et la décision revient à Anaël.

## Incertitudes

- **F inconnu** : effectifs du dénominateur et part des incohérentes antérieures à la fenêtre (citations d'arrêts anciens et célèbres, fréquentes chez un SLM) inconnus avant la porte. Les tailles de D5 et l'intervalle d'exactitude en dépendent (± 6 points à 95 % pour 115 paires réservées).
- **Composition par juridiction** : si le Conseil d'État n'a que quelques fausses dans sa fenêtre (2021-2026), R sera surtout un jeu de la Cour de cassation ; publié, sans rééquilibrage.
- **Plafond de la grille** : borne basse ; des incohérences hors grille (observations de 1-12) peuvent être détectées par une méthode et compter comme « au-delà du plafond » sur des `c00`.
- **Mémoire du modèle** : Sonnet peut connaître des décisions réelles (Perruche) ; une règle B qui embarquerait une liste de numéros vrais relève de l'audit (littéraux limités à 512 nombres), jugée en 1-14b. Un rappel élevé sur `c00` le signalerait.
- **Formes nouvelles pour S** : chambres réunies et juge des référés du Conseil d'État, absents de S, peuvent faire chuter les réseaux de S évalués sur R (mesure hors distribution, lue comme telle).
- **Judilibre** : API en bêta ; `type=arret` et `chamber` sur `/scan` abrégé non relus dans une réponse réelle par cette spec (Swagger seulement) ; repli s'ils manquent : `abridged=false` projeté en mémoire, comme D5 de 1-12, écart consigné.
- **`baselines.curve.measure`** regroupe les fausses par types connus de S ; ses colonnes ne valent pas pour R. Seuls les `eval.json` de `nnww evaluate` comptent.
- **Base de la branche** : dépend de la date de fusion de 1-12 (D1).
- **Coût des agents** : estimation non mesurée ; à relever par `/agent-cost-kit:mesurer-couts` en fin de story.

## Phase A — réalisation (2026-11-07)

Code, tests et mesure du coût, sans lire `data/r/collecte/` ni `data/r/pre_etude/`, sans séance ni témoin. Grille figée de 1-12 fusionnée (`1a672a1`, merge commit) ; aucun module de 1-12 modifié.

**Livré.** `datasets/legal_r/dataset.py` (sélection, revérification, appariement, découpage, écriture), `pool.py` (candidates du jour, point d'appel unique au normaliseur), `floor.py` (plancher de S1) ; `scripts/jeu_r.py` (`construire`, `plancher`, `mesurer-cout`) ; tâche `legal_r` (`HEAD_R`, `SENTENCE_R`, `R_CORPUS_DATE`, `x01`) ; `write_dataset(extra_files=…)` ; `legal_r` dans `nnww train` et garde de séance sur `R_CORPUS_DATE` (blocs `1-13` de `cli.py`) ; `[tasks.legal_r]` ; amendements de CAP-7, CAP-11, de la section R de `jeux-de-donnees.md` et d'AD-17 (S3, point 4).

**Coût Judilibre mesuré** (`mesurer-cout`, 12 jours ouvrés tirés dans la fenêtre de la Cour de cassation, graine 0) : 15 requêtes réseau en tout (12 `/scan` du jour d'une page chacun, 3 `/search` d'une page), 0,30 s par requête, quota journalier restant 999 860. Projection pour 300 fausses, toutes de la Cour de cassation (borne haute) : 5,7 requêtes par fausse (4,7 jours essayés en moyenne, plus la recherche de la revérification), soit ~1 700 requêtes et ~9 min ; pire cas 300 × (15 + 1) = 4 800 requêtes, ~24 min. L'index du CE ne coûte aucune requête.

**Écarts à la spec, décidés en phase A :**

- Judilibre classe `other` l'essentiel des décisions récentes (2023 : 140 `other` sur 142 ; 2026 : 172 sur 177) : `type=arret` aurait vidé R après 2020. Tous les types sont gardés, comme à la vérification d'existence de 1-12 ; le type reste dans `origin`. Le repli prévu aux incertitudes (filtre en mémoire) est donc sans filtre.
- `select_fakes` n'a pas de paramètre `generation_dates` : une fausse est future si la grille figée lui a trouvé R-C3 (comparaison faite par 1-12 à sa date de génération).
- Pool par jour (S10) : `cc_day_candidates(client, day)` et `CeDays(index).candidates(day)` remplacent `cc_candidates(client, chamber, year)` et `ce_candidates(…)`. Jour visé, puis voisins de même type de jour dans la même année, dans la fenêtre et au plus `corpus_date`, 15 jours interrogés au plus (`MAX_DAY_TRIES`) ; sans vraie, la fausse est exclue (`no_real_in_stratum`), sans repli sur une autre année. Une date impossible vise le dernier jour du mois, type `ouvre`.
- Classe d'écart d'année (S1) : un écart négatif (t01) va dans `0`, la classe la plus proche ; numéro du CE ou hors motif : `none`.
- Formation « existante » = aucune règle de formation de la grille (R-O1, R-O2, R-O4, R-O5) ; sinon tirée parmi les formations existantes des fausses de même juridiction et période.
- Découpage : les 20 paires de séance sont réparties entre strates au prorata (plus forts restes), puis réservé et entraînement alternent d'une strate à l'autre, réservé d'abord ; tailles exactes de D5.
- Revérification : une `unverifiable` autre qu'`api_error` est exclue (`recheck_unverifiable`), comptée.
- S7 : une fausse égale à un `raw` de S est exclue (`raw_in_s`) ; `--s-root` doit contenir des jeux sous `data/` et `heldout/` pour `legal_s` et `legal_s_reserved` (refus `s_missing` sinon).
- `type_overrides` est une suite de paires (la tâche reste hachable) ; `R_CORPUS_DATE = None` jusqu'au commit « jeu R figé » : le prompt montre « (date d'arrêt du corpus non fixée) » et `nnww session --task legal_r` est refusé (code 2).
- `swagger_sha256` : `--swagger` facultatif, aucun Swagger dans le dépôt (valeur nulle sinon).
- Fixtures : écrites par `tests/legal_r_jeu_support.py` (règles fixées dans le code, aucune donnée réelle) plutôt que des fichiers sous `tests/fixtures/legal_r/jeu_r/` ; Perruche reprend la réponse enregistrée de 1-12.
- `tests/test_boundary.py` réaligné : le nom de tâche `legal_r` est admis côté séance, jamais le paquet `datasets.legal_r`.

**Reste pour la phase B.** Après la porte : `construire` (avec `--s-root` sur les jeux de S rassemblés et `--cache` sur le cache de 1-12), commit « jeu R figé » avec `R_CORPUS_DATE`, `plancher`, séances (D7, D8 amendé par S2 et S11), témoins C, F et « même réseau » (D9), évaluations native et croisée (D10), rassemblement et publication à blanc (D11), compte rendu `docs/experiences/1-13-jeu-r.md`. Points de vigilance : t12 (dimanches et fêtes) presque sans vraie de même type de jour, donc surtout exclu (`no_real_in_stratum`, à publier) ; une fausse future (R-C3) datée avant `corpus_date` n'est plus visiblement future dans la description de R (à compter) ; le numéro du CE n'a pas d'année, mais suit l'ordre d'enregistrement : un indice numéro contre année est possible et peut mériter un troisième plancher.
