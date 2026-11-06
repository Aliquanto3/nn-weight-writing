---
story: "1-9"
title: Générateurs de S et S-réservé
status: review
branch: feat/1-9-generateurs-s
---

# Story 1-9 : Générateurs de S et S-réservé

## Objet

Générateur reproductible par graine des jeux S (15 types d'incohérence) et S-réservé (10 types connus, 5 vus seulement à l'évaluation), tâches `legal_s` et `legal_s_reserved` inscrites au registre, encodeurs fixes et jeux réservés hors de portée de l'agent (CAP-9 ; AD-2, AD-4, AD-12, AD-16 ; constat `docs/verifications/1-1-reconstruction-s.md`). Aucune séance, aucun entraînement : séances en 1-10, témoins C et F en 1-11, scores par type et ablation en 1-14.

Cette spec tranche toutes les décisions : l'implémentation n'invente ni format, ni fait, ni texte montré à l'agent. Les faits juridiques sont dans `src/nn_weight_writing/tasks/legal/facts.toml` (déjà écrit, chaque fait avec sa source et son statut), que le code lit sans en recopier les valeurs.

## Décisions de l'orchestrateur (reprises telles quelles)

- CAP-1 sur S : feu vert avec réserve (Anaël, 2026-11-06). Réserves (types, format, proportions, chiffre de référence divergent) au rapport du lot 1, pas ici.
- Proportions : vraies et fausses à parts égales, types uniformes parmi les fausses, juridictions à parts égales ; journalisées dans `dataset.json` (précision en D6 : la parité des juridictions cède à l'uniformité des types quand elle est impossible).
- Tailles : 4 000 références d'évaluation dans `heldout/`, 40 exemples non annotés dans le paquet de l'agent, 8 192 exemples annotés pour le témoin C (1-11), hors de portée de l'agent.
- Chaque type porte son identifiant et son statut (attesté ou reconstruit) dans les métadonnées du générateur ; `type_id` dans `labels.jsonl`.
- Test obligatoire : la description de tâche de S-réservé ne nomme aucun des 5 types tenus à l'écart et n'en emploie pas le vocabulaire.

## Décisions de relecture (orchestrateur, 2026-11-06)

Issues du second avis sur cette spec. Elles prévalent sur le texte des sections D1 à D8 là où elles diffèrent (les sections concernées sont alignées ci-dessous).

- **O1** (orchestrateur, 2026-11-06) : `--dataset` de `nnww session` ne se garde pas par un nom `train`, contournable par un chemin (`../../heldout/legal_s/eval`). Tout nom de jeu (et de tâche) qui compose un chemin est validé par `^[a-z0-9_]+$` (`tasks/registry.py`, `examples_path` et ses appelants, `datasets/toy.generate`) : aucun séparateur, aucun `..`. `nnww session` n'accepte en plus que la liste blanche des jeux de séance de la tâche (`TaskSpec.session_datasets` : `session` pour `legal_s` et `legal_s_reserved`, `toy` pour les jouets, nom actuel gardé). `train` garde son message dédié (code 2). Les jeux de séance de test nommés `toy-dev` deviennent `toy`.
- **O2** (orchestrateur, 2026-11-06) : l'écart pourvoi (ou appel) – décision des vraies suit la distribution observée de `facts.toml` jusqu'à son maximum observé, pas 0–4 : Cour de cassation 0 à 6 ans, cours d'appel 0 à 8 ans (poids de queue minuscules). Les seuils de t08 et t13 restent à 10 ans ou plus. La ligne de `facts.toml` « aucune vraie entre 5 et 9 ans » est supprimée. Test : des vraies à 5 et 6 ans existent dans un grand tirage.
- **O3** (orchestrateur, 2026-11-06) : t12, la moitié « fête légale » ne tire que les fêtes mobiles (lundi de Pâques, Ascension) ; lundi de Pentecôte exclu comme avant. Les fêtes fixes ne servent qu'au vérificateur (une vraie n'y tombe jamais). L'autre moitié (dimanche) est inchangée.
- **O4** (orchestrateur, 2026-11-06) : identifiants d'encodeur `legal.chars@1` et `legal.fields@1` gardés (famille `legal`, nécessaire au transfert S → S-réservé → R). **Amendement de AD-4** : « une famille de tâches au même encodage déclare `{famille}.{encodeur}@{version}` ; la tâche reste dans le manifeste ». `dataset.json` porte la tâche. Le manifeste gelé d'une séance est de format fermé (AD-3) : plutôt que de l'étendre, l'évaluation (`evaluation/score.py`, `score_frozen`) lit la tâche de la séance (premier événement `open` du journal) ou du témoin (`run.json`, nouveau champ `task` de `RunRecord`, écrit par `freeze_run`) et refuse un réseau dont la tâche diffère de celle du jeu évalué (`ValueError`), en plus du contrôle de l'encodeur. L'option d'évaluation croisée journalisée (réseau de S évalué sur S-réservé ou R) n'est pas implémentée : **laissée à 1-14**.
- **O5** (orchestrateur, 2026-11-06) : le test de `easter` compare à une table écrite à la main, indépendante du module (2008-03-23, 2011-04-24, 2015-04-05, 2019-04-21, 2020-04-12, 2024-03-31, 2025-04-20, 2026-04-05) et à un second algorithme écrit dans le test (Meeus/Jones/Butcher) pour 2001 à 2029.
- **O6** (orchestrateur, 2026-11-06) : t15, le vérificateur n'applique les règles de jour (t12 et voisines) qu'aux dates valides ; un 29 février non bissextile ne viole que t15. Pas de redessin biaisé du tirage de t15.
- **O7** (orchestrateur, 2026-11-06) : `legal.fields@1`, les années (indices 2 246 et 2 248) sont normalisées par `(année − 1980) / 50`, bornées à [0, 1].
- **O8** (orchestrateur, 2026-11-06) : D1, règle de rédaction des sièges corrigée : noms officiels de la taxonomie gardés tels quels (« Saint-Denis de la Réunion » compris).
- **O9** (orchestrateur, 2026-11-06) : `test_order_and_ids_do_not_leak_label` est déterministe à graine fixe : mélange par le flux du jeu ; pour la graine 0, les labels ne sont ni triés ni strictement alternés.
- **O10** (orchestrateur, 2026-11-06) : numéro d'ordre des cours d'appel étendu à l'échantillon (21 304 observé) : plage [1, 24999], pour qu'un numéro de 20 000 ou plus ne devienne pas un indice de classe pour R.
- **À confirmer par Anaël** : part de 45 % de la Cour de cassation dans les fausses de S-réservé (D6), et phrase propre à S-réservé de la description (D7). Gardées telles quelles.

## D1 — Format des références

**Un seul style, abrégé, canonique**, que le normaliseur de R (1-13) produira à l'identique pour ses vraies et ses fausses :

| Juridiction | Gabarit | Exemple |
|---|---|---|
| Cour de cassation (`cc`) | `Cass. {chambre}, {date}, n° {AA}-{NN}.{NNN}` | `Cass. ass. plén., 17 novembre 2000, n° 99-13.701` |
| Conseil d'État (`ce`) | `CE, {formation}, {date}, n° {NNNNNN}` | `CE, 5e ch., 12 mars 2019, n° 412345` |
| Cour d'appel (`ca`) | `CA {siège}, {date}, n° {AA}/{NNNNN}` | `CA Saint-Denis de la Réunion, 3 juin 2021, n° 19/01234` |

- `{date}` : `{jour} {mois} {année}`, jour sans zéro initial et `1er` pour le 1, mois en minuscules (`janvier février mars avril mai juin juillet août septembre octobre novembre décembre`), année sur 4 chiffres. `n° ` s'écrit avec le signe degré U+00B0 et une espace.
- Chambres de la Cour de cassation : `civ. 1re`, `civ. 2e`, `civ. 3e`, `com.`, `soc.`, `crim.`, `ch. mixte`, `ass. plén.`.
- Formations du Conseil d'État : `Ass.`, `Sect.`, `{k}e ch.` ou `{k}e sous-sect.` pour k de 1 à 10 (`1re ch.`, `1re sous-sect.` pour k = 1).
- Sièges de cour d'appel : noms officiels de `facts.toml` (`[cours_appel]`), tels quels (O8).

**Champs gardés : juridiction, formation (ou siège), date, numéro.** Motifs (mesures Judilibre du 2026-11-06, `facts.toml` `[excluded_fields]`) :

- **ECLI écarté** : vide pour 999 décisions sur 1 000 de la Cour de cassation en 1997, pour toutes les décisions de cours d'appel échantillonnées, et sur Perruche (1-3, T4). R ne pourrait pas le porter de façon égale pour vraies et fausses.
- **Solution écartée** : « other » pour 91 % des décisions de cours d'appel en 2023, absente de l'open data du Conseil d'État.
- **Publication écartée** : vide pour toutes les cours d'appel, nomenclature différente au Conseil d'État.
- **Chambre de cour d'appel écartée** : texte libre hétérogène dans Judilibre (« Pôle 1 - Chambre 11 », « 5ème CH (référés) »), vide en 2005 ; impossible à vérifier, donc à générer sans fabriquer de fausses vraies.

Un seul style parce que le normaliseur de R réécrit tout dans un style unique (AD-16) : plusieurs styles dans S ajouteraient un indice de surface que R n'aurait pas. Forme abrégée parce que c'est celle des citations et des hallucinations de LLM. Conséquence : les types 13 à 15 du constat 1-1 (solution, publication, ECLI) sont remplacés par trois types reconstruits sur les champs gardés (D2).

**Fenêtre** : vraies références du 2 janvier 2001 au 31 octobre 2026 pour les trois juridictions (même fenêtre partout, pour que la date ne trahisse pas la juridiction). Borne basse : dix sous-sections au Conseil d'État vérifiées à partir de 2001 (CJA, R. 122-1). Corpus arrêté au **1er novembre 2026**.

## D2 — Les 15 types

Une vraie référence ne viole aucune règle ; une fausse en viole **exactement une**, celle de son type. Chaque type a un identifiant `t01` à `t15`, repris de la numérotation du constat 1-1 (13 à 15 remplacés).

| id | Nom (`name`) | Statut | Juridictions | Ce que le générateur altère | Règle du vérificateur (violée si…) | S-réservé |
|---|---|---|---|---|---|---|
| t01 | `appeal_after_decision` | attesté | cc | AA du pourvoi = année de la décision + k, k ∈ [1, 3] | année du pourvoi > année de la décision | connu |
| t02 | `impossible_date` | attesté (second rang) | toutes | (mois, jour) remplacé par un tirage uniforme parmi 30 et 31 février, 31 avril, 31 juin, 31 septembre, 31 novembre ; année inchangée | jour > maximum du mois (février : 29) | connu |
| t03 | `unknown_cassation_chamber` | attesté | cc | chambre tirée dans `nonexistent` (`civ. 4e`, `civ. 5e`, `com. 2e`, `soc. 2e`, `crim. 2e`, `ch. fiscale`) | chambre ni dans `chambers` ni dans le lexique des formations du CE | connu |
| t04 | `unknown_appeal_court` | reconstruit | ca | siège tiré dans `fake_seats` (20 sièges de tribunal judiciaire sans cour d'appel) | siège absent des 36 de `all_seats` | **tenu à l'écart** |
| t05 | `other_order_formation` | reconstruit | cc, ce | cc : formation du CE tirée uniformément parmi `Ass.`, `Sect.`, `{k}e ch.` (k de 1 à 10) ; ce : chambre de la Cour de cassation tirée parmi les 8 | cc : formation dans le lexique du CE ; ce : formation parmi les 8 chambres de la Cour de cassation | connu |
| t06 | `future_date` | reconstruit | toutes | date tirée parmi les jours ouvrés du 2 novembre 2026 au 31 décembre 2029, autres champs tirés comme pour une vraie de cette date | (année, mois, jour) > (2026, 11, 1) | connu |
| t07 | `formation_not_at_date` | reconstruit | ce | moitié : `{k}e ch.` avec une date ouvrée du 2 janvier 2001 au 20 avril 2016 ; moitié : `{k}e sous-sect.` avec une date ouvrée du 1er janvier 2017 au 31 octobre 2026 | `ch.` et (a, m, j) < (2016, 4, 21), ou `sous-sect.` et (a, m, j) > (2016, 12, 31) | **tenu à l'écart** |
| t08 | `appeal_too_old` | reconstruit | cc | écart entre l'année de la décision et celle du pourvoi tiré dans [10, 15] | année de la décision − année du pourvoi ≥ 10 | connu |
| t09 | `court_appeal_after_judgment` | reconstruit | ca | AA du numéro = année de l'arrêt + k, k ∈ [1, 3] | année de l'appel > année de l'arrêt | **tenu à l'écart** |
| t10 | `malformed_number` | reconstruit | toutes | numéro remplacé par une malformation tirée uniformément (table ci-dessous) | le numéro ne suit aucun des trois motifs | connu |
| t11 | `foreign_number_format` | reconstruit | toutes | numéro tiré au format valide d'une des deux autres juridictions, choisie uniformément (AA cohérent avec la date : écart tiré comme pour une vraie) | le numéro suit le motif d'une autre juridiction | **tenu à l'écart** |
| t12 | `non_working_day` | reconstruit | toutes | moitié : un dimanche de la fenêtre ; moitié : un lundi de Pâques ou un jeudi de l'Ascension de la fenêtre (O3) ; autres champs tirés pour cette date | date valide, et dimanche ou l'une des 11 fêtes légales (lundi de Pentecôte compris) | **tenu à l'écart** |
| t13 | `court_appeal_too_old` | reconstruit (remplace « solution ») | ca | écart entre l'année de l'arrêt et celle de l'appel tiré dans [10, 15] | année de l'arrêt − année de l'appel ≥ 10 | connu |
| t14 | `series_chamber_mismatch` | reconstruit (remplace « publication ») | cc | chambre tirée parmi les 6 non exemptées ; numéro d'ordre NN.NNN tiré dans [10000, 79999] pour `crim.`, dans [80000, 89999] pour une chambre civile | chambre civile (`civ. 1re` à `soc.`) et NNNNN ≥ 80000, ou `crim.` et NNNNN < 80000 | connu |
| t15 | `feb29_non_leap` | reconstruit (remplace « ECLI ») | toutes | date = 29 février d'une année non bissextile tirée uniformément dans [2001, 2026] ; autres champs tirés pour le 28 février de cette année | jour 29, mois 2, année non bissextile | connu |

**Écarts à Nuss** (à reprendre au rapport du lot 1) : t01 et t03 attestés par les republications, t02 par `docs/SOURCES.md` seul ; les 12 autres sont de notre fait. t07 transpose « décision antérieure à la création de la formation » sur le seul fait daté vérifiable dans la fenêtre (renommage des sous-sections du CE en chambres, 2016) : aucune chambre de la Cour de cassation n'a été créée après 2001. t13 à t15 remplacent solution, publication et ECLI, écartés en D1 : t13 prolonge t08 aux cours d'appel, t14 repose sur la numérotation des pourvois mesurée dans Judilibre, t15 sépare de t02 le cas qui demande la règle des années bissextiles. Le type « numéro de requête du CE incompatible avec l'année », proposé par le constat 1-1, est écarté faute de table vérifiée des numéros par année.

**Malformations de t10** (aucune ne doit suivre un des trois motifs : le vérificateur le contrôle) :

| Juridiction | Variantes (une tirée uniformément) |
|---|---|
| cc (`AA-NN.NNN`) | point retiré `AA-NNNNN` ; tiret retiré `AANN.NNN` ; numéro d'ordre à 6 chiffres `AA-NN.NNNN` ; année sur 1 chiffre `A-NN.NNN` |
| ce (`NNNNNN`) | 5 chiffres ; 7 chiffres ; point inséré `NNN.NNN` |
| ca (`AA/NNNNN`) | barre retirée `AANNNNN` ; numéro d'ordre à 6 chiffres `AA/NNNNNN` ; tiret au lieu de la barre `AA-NNNNN` |

Aucune variante ne retire un chiffre au numéro d'ordre d'une cour d'appel (`AA/NNNN`), parce que cette forme existe dans les vraies décisions anciennes (Judilibre 2005 et 2012).

**Les 5 tenus à l'écart : t04, t07, t09, t11, t12**, la proposition du constat 1-1 confirmée avec le format retenu. Ils portent sur le siège, la formation du CE, le numéro d'appel, le numéro et la date, présents dans toute référence de leur juridiction ; aucun ne dépend d'un champ optionnel. Les 3 attestés (t01 à t03) restent connus. Dépendances assumées : t09 transpose t01 et t13 ; t11 se déduit en partie des formats donnés par la description et par t10 ; t12 demande un calcul que les types connus n'enseignent pas.

## D3 — Faits juridiques vérifiés

Tous dans `src/nn_weight_writing/tasks/legal/facts.toml`, avec `status` (`primary`, `sample`, `convention`, `unverified`) et `source`. Le chargeur refuse d'utiliser une section `unverified`. Résumé :

| Fait | Source | Statut |
|---|---|---|
| 8 chambres et formations de la Cour de cassation, codes Judilibre | `/taxonomy?id=chamber&context_value=cc` ; justice.gouv.fr (six chambres) ; ch. mixte vue en 2001-2003 et ass. plén. en 2000 par `/search` | primary |
| Numéro de pourvoi `AA-NN.NNN`, AA = année d'enregistrement | `/scan` 2019 et 1997 (977 et 996 sur 1 000) ; Perruche | sample |
| Série pénale ≥ 80.000, civile en dessous ; ch. mixte et ass. plén. exemptées | `/scan` 2019 et 1997 : 0 exception sur 2 000 | sample |
| Écart pourvoi-décision de 0 à 6 ans observé (0 à 2 ans pour 95 %) | `/scan` 2019 et 1997, `/search` chambre mixte | sample |
| Section du contentieux : dix sous-sections dès 2001 | CJA R. 122-1, version du 2001-01-01 (Légifrance) | primary |
| Sous-sections renommées chambres, loi du 20 avril 2016 promulguée le 21, dix chambres | conseil-etat.fr, actualité du 29 avril 2016 | primary |
| Zone grise du 21 avril au 31 décembre 2016 (décret 2016-899 en vigueur le 3 juillet 2016, d'après la presse juridique) | — | convention : aucune formation numérotée tirée dans cette zone |
| Numéro du CE à 6 chiffres dans la fenêtre | 1-3 (n° 428409, 2020) ; Dalloz (n° 406606, 2019) ; Nicolo (n° 108243, 1989), citations doctrinales | primary (recoupé) |
| 36 cours d'appel | `/taxonomy?id=location&context_value=ca` | primary |
| 20 sièges de tribunal judiciaire sans cour d'appel | `/taxonomy?id=location&context_value=tj` | primary |
| RG `AA/NNNNN` | `/scan` 2023 (1 000 sur 1 000), 2012 (286 sur 300), 2005 (212 sur 300) | sample |
| 11 fêtes légales | Code du travail L. 3133-1, par service-public.gouv.fr F2405 | primary (Légifrance non ouvert par identifiant) |
| Pas de décision de la Cour de cassation le week-end ni un jour férié fixe | `/scan` 2019 et 1997 | sample |

**Non vérifié, hors du générateur** : date de création de la cour d'appel de Cayenne (Cayenne exclue des vraies, reste dans la liste des 36 pour t04) ; appariements des chambres réunies du CE (hors de S) ; table des numéros du CE par année (pas de type sur la valeur du numéro).

## D4 — Garde-fou contre les fausses vraies

- **Vérificateur de règles** `violations(ref) -> frozenset[str]` (`datasets/legal_rules.py`), écrit d'après la colonne « Règle » de D2 seule, indépendant du code qui altère. Il renvoie les `tXX` violés, plus `x_formation` pour une formation du CE hors des deux lexiques ou de rang hors de [1, 10] (jamais produit ; sert à détecter un défaut du générateur). Une chaîne qui ne se lit pas (`parse_reference` lève `ValueError`) est un défaut du générateur.
- **Contrôle à la génération** : chaque ligne tirée passe par le vérificateur ; une vraie doit donner `∅`, une fausse de type t exactement `{t}`. Sinon, ou si `raw` existe déjà dans un jeu tiré avant, la ligne est retirée avec le même générateur aléatoire, au plus 1 000 fois, puis `RuntimeError`. Les collisions attendues sont rares (par exemple t02 « 31 novembre 2026 » qui serait aussi future).
- **Exactement une violation**, pas plusieurs : `type_id` reste univoque, ce qu'exigent les scores par type de CAP-12 et la lisibilité par ablation (`methodes-et-lots.md`) ; les exemples cités par Nuss sont des erreurs simples.
- **Détail des règles** (l'ordre des tests ne compte pas) :
  - Motif du numéro : `cc` si `^\d{2}-\d{2}\.\d{3}$`, `ce` si `^\d{6}$`, `ca` si `^\d{2}/\d{5}$`, sinon aucun. t10 : aucun motif ; t11 : motif d'une autre juridiction.
  - Année d'un AA : l'unique année Y' ≡ AA (mod 100) dans [Y − 50, Y + 49], Y étant l'année de la décision.
  - t01, t08, t14 seulement pour une référence `cc` dont le numéro suit le motif `cc` ; t09, t13 seulement pour `ca` avec le motif `ca` ; t14 seulement pour une chambre de `civil` ou `criminal`.
  - t12 seulement si la date existe ; t06 et t07 comparent des triplets (année, mois, jour), date impossible comprise.
  - Fêtes légales : dates fixes et mobiles de `[holidays]` (Pâques par le comput grégorien). Un samedi, le Vendredi saint et le 26 décembre ne violent aucune règle ; aucune ligne ne les porte.
- **Tirage d'une vraie référence** (et base de chaque fausse) :
  - date uniforme parmi les jours ouvrés de la fenêtre : du lundi au vendredi, hors fêtes légales, Vendredi saint et 26 décembre ;
  - cc : chambre selon `chamber_weights`, écart selon `gap_weights` (0 à 6 ans, O2), numéro d'ordre uniforme dans `criminal_serial` pour `crim.`, dans `civil_serial` sinon ;
  - ce : formation selon `formation_weights`, k uniforme de 1 à 10, `sous-sect.` si la date ≤ 2016-04-20, `ch.` si ≥ 2017-01-01 ; dans la zone grise, `Ass.` (2/7) ou `Sect.` (5/7) ; numéro uniforme dans `number_range` ;
  - ca : siège uniforme parmi les 35 (`all_seats` sans `excluded_from_real`), écart selon `gap_weights` (0 à 8 ans, O2), numéro d'ordre uniforme dans `serial` ([1, 24999], O10), écrit sur 5 chiffres.
  - Une fausse part d'une vraie tirée pour sa juridiction, puis change le seul champ de son type (date forcée pour t06, t07, t12, t15, avant le tirage des autres champs).

## D5 — Encodeurs et décodeur (AD-4)

L'identifiant reprend `{task}.{encoder}@{version}` avec la **famille de tâches `legal`** comme `{task}` : `legal.chars@1` et `legal.fields@1`, communs à `legal_s`, `legal_s_reserved` et, plus tard, à R (amendement de AD-4, O4 : la tâche reste dans `dataset.json` et dans le contrôle de l'évaluation). Motif : un réseau écrit sur S doit pouvoir être évalué sur S-réservé et sur R (robustesse hors distribution, CAP-12) sans refus `encoder_mismatch`. Toute modification d'un encodeur incrémente sa version.

**`encode(raw)` — `legal.chars@1`, 3 060 valeurs `float32` 0 ou 1.** Pur, sans statistique, chaque entrée signifie « tel symbole à telle position de tel champ » :

1. `raw` doit être une chaîne ; mise en minuscules (`str.lower()`), après normalisation NFC.
2. Découpage par `rsplit(", ", 2)` en en-tête, date et numéro ; le dernier segment doit commencer par `n° ` (retiré) ; la date doit avoir exactement 3 jetons séparés par une espace. Sinon `ValueError`.
3. Cinq champs alignés à gauche, tronqués au-delà de leur longueur :

   | Champ | Positions | Première position |
   |---|---|---|
   | en-tête | 32 | 0 |
   | jour | 3 | 32 |
   | mois | 9 | 35 |
   | année | 4 | 44 |
   | numéro | 12 | 48 |

4. Alphabet de 50 symboles, dans cet ordre : `abcdefghijklmnopqrstuvwxyz0123456789 .,-/éèêàâîôûç` (a = 0, 0 = 26, espace = 36, `.` = 37, `,` = 38, `-` = 39, `/` = 40, `é` = 41 … `ç` = 49) ; symbole 50 pour tout autre caractère. Entrée d'indice `51 × position + symbole` à 1 ; position vide toute à 0.

Plus longs champs produits : en-tête `ca saint-denis de la réunion` (28), mois `septembre` (9), numéro de t10 (10).

**Architecture de référence pour C (1-11, à écrire dans `config/train.toml` par 1-11)** : une couche cachée `relu` de 32, sortie `identity` de 2, soit 3 060 × 32 + 32 + 32 × 2 + 2 = **98 018 paramètres**, du même ordre que Nuss (~97 000).

**`encode_prepared(raw)` — `legal.fields@1`, 2 249 valeurs `float32`, pour F.** Même découpage. En-tête en caractères (32 × 51, indices 0 à 1 631), numéro en caractères (12 × 51, indices 1 632 à 2 243), puis 5 valeurs extraites :

| Indice | Valeur |
|---|---|
| 2 244 | jour / 31 (`1er` = 1 ; jeton illisible : 0) |
| 2 245 | mois / 12 (nom inconnu : 0) |
| 2 246 | (année − 1980) / 50, borné à [0, 1] (jeton illisible : 0) |
| 2 247 | 1 si le numéro commence par `^\d{2}[-/]`, sinon 0 |
| 2 248 | (année du numéro − 1980) / 50, borné à [0, 1], avec AA ≥ 50 → 19AA, sinon 20AA ; 0 sans AA |

Ce sont des champs extraits, sans relation calculée entre eux : ni écart, ni jour de la semaine, ni validité. Architecture de F : la même cachée de 32 (2 249 × 32 + 32 + 66 = 72 066 paramètres).

**`decode(outputs)`** : 2 sorties dans l'ordre `real`, `fake` ; argmax, `real` en cas d'égalité (comme `ToyTask.decode`). Labels de `labels.jsonl` : `real` ou `fake` ; `type_id` : `real` pour une vraie, `t01` à `t15` pour une fausse.

## D6 — Noms, graines, versions, jeux et commandes

- **Tâches** : `legal_s` et `legal_s_reserved`, inscrites au registre (`tasks/registry.py`) comme les tâches jouet.
- **Générateur** : `generator = "legal"`, `GENERATOR_VERSION = 1` dans `dataset.json`. La version change avec `facts.toml`, les règles, les tirages ou les tailles.
- **Graine du lot 1 : 0** (`nnww datagen legal --seed 0`), à consigner au journal du run par 1-10. Un flux par jeu, `np.random.default_rng([seed, k])` : k = 0 évaluation, 1 séance S, 2 entraînement S, 3 séance S-réservé, 4 entraînement S-réservé. Les jeux sont tirés dans cet ordre, chacun refusant les `raw` déjà tirés : l'évaluation ne dépend pas de la taille des autres jeux.
- **Jeux écrits sous `--root`** (ignorés par git) :

  | Dossier | Taille | Types des fausses | Identifiants |
  |---|---|---|---|
  | `heldout/legal_s/eval/` | 4 000 | les 15 | `legal-e00001`… |
  | `heldout/legal_s_reserved/eval/` | 4 000 | les 15 : **copie octet pour octet** de `examples.jsonl` et `labels.jsonl` du précédent | mêmes |
  | `data/legal_s/session/` | 40 | les 15 | `legal-s00001`… |
  | `data/legal_s/train/` | 8 192 | les 15 | `legal-t00001`… |
  | `data/legal_s_reserved/session/` | 40 | les 10 connus | `legal-r00001`… |
  | `data/legal_s_reserved/train/` | 8 192 | les 10 connus | `legal-u00001`… |

- **Jeu de C hors de portée de l'agent** : `data/<task>/train/`, parce que `nnww train` refuse `heldout/` (1-7) et lit `data/<task>/<jeu>` avec ses étiquettes (AD-16). L'agent n'y accède pas : il ne lit que `bundle/` (AD-2), et le bac à sable refuse toute ouverture de fichier (AD-5). Garde ajoutée : `nnww session` refuse `--dataset train` (code de sortie 2, message `jeu d'entraînement des témoins, pas un jeu de séance`), pour qu'aucune séance ne reçoive 8 192 exemples.
- **Recouvrement (AD-16)** : les 5 jeux tirés sont deux à deux sans `raw` commun ; les identifiants le sont par leur préfixe. En particulier, aucune ligne de séance ou d'entraînement de S ou de S-réservé n'est dans l'évaluation commune.
- **Proportions**, pour chaque jeu de taille n (paire, sinon `ValueError`) :
  - n/2 vraies et n/2 fausses ;
  - quotas des types par `divmod(n/2, nombre de types)`, le reste aux premiers identifiants ;
  - juridiction des fausses, sans aléa : d'abord les types à une juridiction ; puis t05, partagé à parts égales entre cc et ce (cc d'abord pour un quota impair) ; puis chaque type à trois juridictions, dans l'ordre des identifiants, réparti au plus fort reste en proportion des déficits restants, déficits mis à jour après chaque type (cible `divmod(n/2, 3)`, le reste à cc puis ce ; déficit négatif compté 0 ; tous nuls : parts égales ; égalité de restes départagée dans l'ordre cc, ce, ca) ;
  - les vraies reprennent exactement le nombre de fausses de chaque juridiction : la juridiction ne dit rien de la classe.

  Pour S et l'évaluation, les fausses sont alors à un tiers par juridiction (à 1 près). Pour la séance et l'entraînement de S-réservé, c'est impossible avec des types uniformes : 4 des 10 types connus (t01, t03, t08, t14) ne valent que pour la Cour de cassation, qui reçoit 45 % des fausses (et autant des vraies). L'uniformité des types l'emporte, et l'écart est journalisé.
- **Ordre** : lignes mélangées par le flux du jeu (`rng.permutation`), identifiants attribués après le mélange, numérotés à partir de 1 sur 5 chiffres. Ni l'ordre ni l'identifiant ne disent la classe.
- **`dataset.json`** : `write_dataset` reçoit un argument optionnel `composition: dict | None = None`, écrit sous la clé `composition` seulement s'il est fourni (les jeux jouet restent identiques). Contenu : `task`, `split` (`eval`, `session`, `train`), `encoder` (`legal.chars@1`), `corpus_date`, `window` ([début, fin]), `facts_sha256` (sha256 des octets de `facts.toml`), `n_real`, `n_fake`, `by_type` (`{"t01": n, …}`), `by_jurisdiction` (`{"real": {"cc": n, "ce": n, "ca": n}, "fake": {…}}`), `types` (liste des 15 : `id`, `name`, `status` `attested` ou `reconstructed`, `jurisdictions`, `nuss` `attested`, `attested_secondary` ou `reconstructed`), `visible_types` (ids du vocabulaire de la tâche), `held_out_types` (`[]` pour S ; `["t04", "t07", "t09", "t11", "t12"]` pour S-réservé).
- **Commandes** :
  - `uv run nnww datagen legal --seed 0 [--root .]` écrit les 6 dossiers et les affiche ; refuse (code 1, `datagen refusé : …`) si l'un existe, **avant** d'écrire quoi que ce soit ; refuse `--n` et `--n-heldout` avec `legal` (code 2), les tailles étant fixées. Pour cela, leurs défauts passent à `None` dans l'analyseur, et le jouet garde 256 et 400 quand ils sont omis.
  - Pour mémoire (hors de 1-9) : `nnww session --task legal_s --dataset session …` (1-10) ; `nnww train legal_s --data data/legal_s/train --n 8192 --seed 0` (1-11).

## D7 — Description de tâche et vocabulaire (AD-2)

La description est la même pour A et B (test d'identité de CAP-3). Elle documente l'encodage, seule voie pour que l'agent écrive des poids qui le lisent. Texte exact, construit par `tasks/legal/task.py` :

`HEAD` (commun) :

> Chaque exemple est une référence de décision de justice française : Cour de cassation, Conseil d'État ou cour d'appel. Toutes sont écrites sous une seule forme, « juridiction et formation, date, n° numéro », par exemple « Cass. civ. 1re, 12 mars 2015, n° 13-27.123 », « CE, Sect., 12 mars 2015, n° 381234 » ou « CA Lyon, 12 mars 2015, n° 13/04567 ». La date s'écrit jour, mois en lettres, année, avec « 1er » pour le premier du mois. Le numéro a la forme AA-NN.NNN à la Cour de cassation (AA : deux derniers chiffres de l'année d'enregistrement du pourvoi), six chiffres au Conseil d'État, AA/NNNNN dans une cour d'appel (AA : deux derniers chiffres de l'année d'enregistrement de l'appel). Le corpus est arrêté au 1er novembre 2026.
>
> La moitié des références sont vraies, l'autre moitié fausses. Chaque fausse référence contient exactement une incohérence, détectable sans base de données.

Puis, sur la même ligne, après une espace :

- `legal_s` : « Son type est l'un des types du vocabulaire ci-dessous. »
- `legal_s_reserved` : « Les types d'incohérence connus sont ceux du vocabulaire ci-dessous. »

La seconde phrase ne prétend pas que la liste est complète, ce qui serait faux à l'évaluation, sans annoncer d'autres types ni en nommer aucun.

`TAIL` (commun), après une ligne vide :

> Classes : `real` (vraie) et `fake` (fausse). Le réseau a deux sorties, dans l'ordre real puis fake ; la prédiction est la sortie la plus forte, real en cas d'égalité. Les règles de la méthode B reçoivent la chaîne brute et renvoient `real` ou `fake`.
>
> Encodage des entrées du réseau (legal.chars@1, fixé par la tâche) : 3 060 valeurs 0 ou 1. La référence est mise en minuscules, puis découpée à ses deux dernières virgules : l'en-tête (juridiction et formation), la date, et le numéro, qui suit « n° ». La date est coupée à ses espaces en jour, mois et année. Cinq champs de caractères, alignés à gauche, sont remplis position par position et tronqués au-delà de leur longueur : en-tête, 32 positions à partir de la position 0 ; jour, 3 à partir de 32 ; mois, 9 à partir de 35 ; année, 4 à partir de 44 ; numéro, 12 à partir de 48 ; soit 60 positions. Chaque position a 51 entrées : une par symbole de l'alphabet « abcdefghijklmnopqrstuvwxyz0123456789 .,-/éèêàâîôûç » (symboles 0 à 49, l'espace est le symbole 36), et le symbole 50 pour tout autre caractère. L'entrée d'indice 51 × position + symbole vaut 1 si la position porte ce symbole ; une position vide est toute à 0.

**Vocabulaire fermé** (`{"id", "description"}`) : les 15 types pour `legal_s`, les 10 connus pour `legal_s_reserved`, dans l'ordre des identifiants. Textes exacts :

| id | description |
|---|---|
| t01 | Pourvoi postérieur à la décision : l'année AA du numéro de pourvoi est postérieure à l'année de la décision. |
| t02 | Date impossible : jour qui n'existe pas dans ce mois (30 ou 31 février, 31 avril, 31 juin, 31 septembre, 31 novembre). |
| t03 | Chambre inexistante de la Cour de cassation : rang ou nom de chambre qui n'existe pas (« civ. 4e », « com. 2e », « ch. fiscale »). |
| t04 | Cour d'appel inexistante : la ville citée est le siège d'un tribunal judiciaire sans cour d'appel (par exemple « CA Lille »). |
| t05 | Formation de l'autre ordre : formation du Conseil d'État citée pour la Cour de cassation (« Cass. Sect. », « Cass. 3e ch. »), ou chambre de la Cour de cassation citée pour le Conseil d'État (« CE, soc. »). |
| t06 | Décision future : date postérieure au 1er novembre 2026, date d'arrêt du corpus. |
| t07 | Formation du Conseil d'État qui n'existe pas à la date de la décision : « chambre » numérotée avant le 21 avril 2016 (on disait alors sous-section), ou « sous-section » après le 31 décembre 2016. |
| t08 | Pourvoi trop ancien : le pourvoi (année AA du numéro) est enregistré dix ans ou plus avant l'année de la décision. |
| t09 | Appel postérieur à l'arrêt : l'année AA du numéro de cour d'appel est postérieure à l'année de l'arrêt. |
| t10 | Numéro mal formé : tiret, point ou barre manquant ou remplacé, ou nombre de chiffres faux. |
| t11 | Numéro au format d'une autre juridiction : par exemple six chiffres à la Cour de cassation, ou AA-NN.NNN dans une cour d'appel. |
| t12 | Décision rendue un dimanche ou un jour férié (fêtes légales de l'article L. 3133-1 du code du travail). |
| t13 | Appel trop ancien : l'appel (année AA du numéro de cour d'appel) est enregistré dix ans ou plus avant l'arrêt. |
| t14 | Série du numéro de pourvoi incompatible avec la chambre : la chambre criminelle numérote ses pourvois à partir de 80.000 (partie NN.NNN), les chambres civiles, commerciale et sociale en dessous ; sans objet pour la chambre mixte et l'assemblée plénière. |
| t15 | Date du 29 février d'une année non bissextile. |

Le texte de t10 décrit l'altération sans dire « ne suit aucun format », qui tracerait la frontière avec t11 tenu à l'écart.

**Vocabulaire interdit dans S-réservé** (description et vocabulaire, après minuscules, accents retirés par NFKD et apostrophe typographique ramenée à `'`) ; termes simples en sous-chaîne, termes marqués `\b` en mot entier :

| Type tenu à l'écart | Termes |
|---|---|
| t04 | `siege`, `tribunal`, `cour d'appel inexistante`, `cours d'appel existantes`, `sans cour d'appel`, `ville`, et en mot entier chacun des 20 sièges de `fake_seats` |
| t07 | `sous-sect`, `creation`, `\bcreee?s?\b`, `reforme`, `2016`, `2017`, `anachron`, `n'existait pas`, `a la date` |
| t09 | `\brg\b`, `\brole\b`, `posterieur a l'arret`, `posterieure a l'arret`, `apres l'arret`, `appel posterieur` |
| t11 | `autre juridiction`, `format d'une autre`, `format d'un autre`, `croise` |
| t12 | `dimanche`, `ferie`, `week-end`, `weekend`, `samedi`, `jour de la semaine`, `jour ouvr`, `paques`, `noel`, `ascension`, `toussaint`, `pentecote`, `assomption`, `armistice`, `14 juillet`, `1er mai`, `chome`, `3133` |
| tous | `\bt04\b`, `\bt07\b`, `\bt09\b`, `\bt11\b`, `\bt12\b` |

La liste vit dans le test (`FORBIDDEN_TERMS`), pas dans le code de la tâche.

## D8 — Fichiers, tests, hors périmètre

**À créer** (côté séance : aucun de ces fichiers ne contient les chaînes `labels.jsonl` ni `heldout`, test AD-1) :

- `src/nn_weight_writing/tasks/legal/__init__.py` : exporte `TASK_S`, `TASK_S_RESERVED`, `TASKS`.
- `tasks/legal/facts.toml` : **déjà écrit**, à ne modifier que pour une erreur avérée (source à l'appui).
- `tasks/legal/facts.py` : `load_facts() -> Facts` (`tomllib`, chemin `Path(__file__).with_name("facts.toml")`), dataclass gelée, refus d'une section `unverified` lue par le code ; `facts_sha256()`.
- `tasks/legal/reference.py` : `Reference` (dataclass gelée : `jurisdiction`, `formation`, `day`, `month`, `year`, `number`), `format_reference`, `parse_reference` (`ValueError` hors du gabarit de D1 : en-tête `Cass. `, `CE, ` ou `CA `), `MONTHS`.
- `tasks/legal/types.py` : `ErrorType` (dataclass : `id`, `name`, `status`, `nuss`, `jurisdictions`, `description`), `TYPES` (les 15 de D2 et D7), `HELD_OUT = ("t04", "t07", "t09", "t11", "t12")`, `KNOWN`.
- `tasks/legal/encoders.py` : `encode_chars`, `encode_fields`, constantes `ALPHABET`, `SLOTS`, `N_CHARS = 3060`, `N_FIELDS = 2249`.
- `tasks/legal/task.py` : `LegalTask` (dataclass gelée, mêmes attributs que `ToyTask` pour que 1-11 réutilise `baselines/train.py` : `name`, `description`, `classes = (("real", "référence vraie"), ("fake", "référence fausse"))`, `class_ids`, `n_inputs = 3060`, `encoder_id = "legal.chars@1"`, `encode`, `decode` ; plus `vocabulary` = types visibles, `prepared_encoder_id = "legal.fields@1"`, `encode_prepared`, `n_prepared_inputs = 2249`), descriptions de D7.
- `src/nn_weight_writing/datasets/legal_rules.py` : `violations(ref, facts) -> frozenset[str]`, `legal_holidays(year)`, `easter(year)`, `is_working_day(date)`.
- `src/nn_weight_writing/datasets/legal.py` : `Sizes` (`eval=4000`, `session=40`, `train=8192`), `generate_rows(seed, sizes) -> dict[str, list[Row]]` (clés `eval`, `s_session`, `s_train`, `r_session`, `r_train`), `generate(*, seed, root, sizes=Sizes()) -> list[Path]` (6 dossiers), `composition(...)`.
- Tests : `tests/test_legal_reference.py`, `tests/test_legal_rules.py`, `tests/test_legal_encoders.py`, `tests/test_legal_task.py`, `tests/test_legal_datasets.py`.

**À modifier** :

- `datasets/io.py` : argument `composition` (D6).
- `tasks/registry.py` : `_register_legal()` inscrit les deux tâches (`TaskSpec(name, description, task, tuple(task.vocabulary))`) ; docstring mise à jour.
- `cli.py` : `datagen legal` (D6), défauts `None` de `--n`/`--n-heldout`, refus de `--dataset train` dans `_session`.

Ni `baselines/`, ni `config/train.toml`, ni `session/`, ni les specs de `_bmad-output/specs/` ne changent.

**Tests nommés** (Given / When / Then) :

`test_legal_reference.py`

- `test_format_and_parse_round_trip` — Given une `Reference` par juridiction (dont Perruche), When `format_reference` puis `parse_reference`, Then même `Reference` et chaînes égales aux exemples de D1.
- `test_first_day_and_month_names` — Given le 1er août 2015, Then `1er août 2015`.
- `test_parse_refuses_non_canonical` — Given `Cass. civ. 1re 12 mars 2015 n° 13-27.123` (sans virgules), une date à 2 jetons, un en-tête `TA Lyon`, When `parse_reference`, Then `ValueError`.

`test_legal_rules.py`

- `test_hand_written_references` — Given chaque ligne du tableau ci-dessous, When `violations`, Then l'ensemble attendu.
- `test_holidays_match_service_public` — Given 2026 et 2027, When `legal_holidays`, Then lundi de Pâques 2026-04-06 et 2027-03-29, Ascension 2026-05-14, lundi de Pentecôte 2026-05-25, plus les 8 dates fixes.
- `test_century_resolution` — Given AA = 99 et décision de 2000, Then 1999 ; AA = 27 et 2026, Then 2027 ; AA = 86 et 2001, Then 1986.
- `test_unverified_fact_is_refused` — Given un `facts.toml` temporaire où une section utilisée est `unverified`, When `load_facts(path)`, Then `ValueError`.

| `raw` | Attendu |
|---|---|
| `Cass. ass. plén., 17 novembre 2000, n° 99-13.701` (Perruche) | ∅ |
| `Cass. ch. mixte, 21 février 2003, n° 99-18.759` (Judilibre, écart 4 ans) | ∅ |
| `CE, 5e ch., 12 mars 2019, n° 412345` | ∅ |
| `CE, 3e sous-sect., 14 octobre 2010, n° 321456` | ∅ |
| `CE, Sect., 15 juin 2016, n° 389012` (zone grise) | ∅ |
| `CA Saint-Denis de la Réunion, 3 juin 2021, n° 19/01234` | ∅ |
| `Cass. civ. 1re, 12 mars 2015, n° 06-27.123` (écart 9 ans) | ∅ |
| `Cass. civ. 1re, 14 mars 2015, n° 13-27.123` (samedi) | ∅ |
| `Cass. civ. 1re, 3 avril 2015, n° 13-27.123` (Vendredi saint) | ∅ |
| `Cass. civ. 1re, 12 mars 2015, n° 16-27.123` | {t01} |
| `Cass. soc., 30 février 2012, n° 10-14.567` | {t02} |
| `Cass. civ. 4e, 12 mars 2015, n° 13-27.123` | {t03} |
| `CA Lille, 12 mars 2015, n° 13/04567` | {t04} |
| `Cass. Sect., 12 mars 2015, n° 13-27.123` | {t05} |
| `CE, soc., 12 mars 2015, n° 381234` | {t05} |
| `CA Lyon, 4 mars 2027, n° 26/01234` | {t06} |
| `CE, 4e ch., 12 mars 2015, n° 381234` | {t07} |
| `CE, 4e sous-sect., 12 mars 2019, n° 412345` | {t07} |
| `Cass. crim., 12 mars 2015, n° 03-81.234` | {t08} |
| `CA Lyon, 12 mars 2015, n° 16/04567` | {t09} |
| `CA Lyon, 12 mars 2015, n° 1304567` | {t10} |
| `Cass. com., 12 mars 2015, n° 13-27123` | {t10} |
| `Cass. com., 12 mars 2015, n° 381234` | {t11} |
| `CA Lyon, 12 mars 2015, n° 13-27.123` | {t11} |
| `Cass. civ. 2e, 14 juillet 2015, n° 14-12.345` | {t12} |
| `CE, 2e ch., 15 mars 2020, n° 431234` (dimanche) | {t12} |
| `Cass. civ. 2e, 25 mai 2015, n° 14-12.345` (lundi de Pentecôte) | {t12} |
| `CA Lyon, 12 mars 2015, n° 04/04567` | {t13} |
| `Cass. crim., 12 mars 2015, n° 14-27.123` | {t14} |
| `Cass. soc., 12 mars 2015, n° 14-81.234` | {t14} |
| `CE, 1re ch., 29 février 2019, n° 412345` | {t15} |
| `Cass. civ. 1re, 12 mars 2015, n° 16-87.123` | {t01, t14} |

`test_legal_encoders.py`

- `test_chars_layout` — Given `Cass. civ. 1re, 12 mars 2015, n° 13-27.123`, When `encode_chars`, Then forme (3060,), `float32`, exactement 33 uns (14 d'en-tête, 2 de jour, 4 de mois, 4 d'année, 9 de numéro) ; `x[51*0 + 2] == 1` (« c ») ; `x[51*32 + 27] == 1` (« 1 » du jour) ; `x[51*48 + 27] == 1` (« 1 » du numéro) ; `x[51*30:51*32]` nul (fin d'en-tête vide).
- `test_chars_other_symbol_and_truncation` — Given un en-tête de 40 caractères et une virgule d'en-tête CE, Then positions 32 et au-delà de l'en-tête ignorées, virgule au symbole 38, `°` absent.
- `test_encoders_are_pure` — Given la même chaîne deux fois et après d'autres appels, Then tableaux égaux.
- `test_encoders_refuse_non_canonical` — Given un numéro sans `n° ` ou un objet non chaîne, Then `ValueError` ou `TypeError`.
- `test_fields_layout` — Given Perruche, When `encode_fields`, Then forme (2249,), `x[2244] == 17/31`, `x[2245] == 11/12`, `x[2246] == (2000-1980)/50`, `x[2247] == 1`, `x[2248] == (1999-1980)/50` (tolérance float32).
- `test_decode_argmax_and_tie` — Given [0.2, 0.9], [0.9, 0.2], [0.5, 0.5], Then `fake`, `real`, `real`.
- `test_reference_architecture_size` — Then 3060 × 32 + 32 + 32 × 2 + 2 == 98 018.

`test_legal_task.py`

- `test_reserved_description_names_no_held_out_type` (**obligatoire**) — Given description et descriptions du vocabulaire de `legal_s_reserved`, When normalisées (D7), Then aucun terme de `FORBIDDEN_TERMS` n'y figure, et les ids du vocabulaire sont exactement les 10 connus.
- `test_forbidden_terms_are_relevant` — Given le vocabulaire de `legal_s`, Then la description de chaque type tenu à l'écart contient au moins un de ses termes interdits (la liste n'est pas vide de sens).
- `test_s_vocabulary_and_metadata` — Then 15 entrées `t01`…`t15` ; statuts : t01 à t03 `attested`, les autres `reconstructed` ; `nuss` de t02 `attested_secondary`.
- `test_descriptions_differ_by_one_sentence` — Then les deux descriptions sont égales une fois retirée la phrase propre à chacune (D7) ; t06 cite `1er novembre 2026` et `load_facts().corpus_date` vaut 2026-11-01.
- `test_registry_and_bundle` — Given le registre, Then `get_task("legal_s")` et `get_task("legal_s_reserved")` ont l'encodeur `legal.chars@1` ; `materialize_bundle` sur un jeu de séance généré écrit `task.json` avec ce vocabulaire.

`test_legal_datasets.py` (tailles réelles : la génération complète prend quelques secondes ; une fixture de module la fait une fois)

- `test_reals_violate_nothing_and_fakes_exactly_their_type` — Given les 5 jeux tirés avec la graine 0, Then pour chaque ligne `violations(parse_reference(raw))` vaut ∅ si `real`, `{type_id}` sinon.
- `test_same_seed_same_bytes_other_seed_differs` — Given deux `generate` en graine 0 sous deux racines et un en graine 1, Then mêmes octets pour les 6 dossiers en graine 0, `examples.jsonl` différent en graine 1.
- `test_eval_independent_of_other_sizes` — Given `Sizes(eval=4000, session=10, train=100)`, Then lignes d'évaluation identiques à celles des tailles par défaut.
- `test_splits_pairwise_disjoint` — Then aucun `raw` commun entre deux des 5 jeux, aucun `id` commun entre jeux de séance ou d'entraînement et évaluation, pour S comme pour S-réservé.
- `test_reserved_eval_is_s_eval_with_all_15_types` — Then `examples.jsonl` et `labels.jsonl` des deux dossiers d'évaluation sont identiques octet pour octet, et chaque type y a au moins 133 fausses.
- `test_reserved_session_and_train_hold_only_known_types` — Then aucune ligne de t04, t07, t09, t11, t12 dans `data/legal_s_reserved/`.
- `test_proportions` — Then dans chaque jeu : n/2 `real` ; chaque type à 1 près de son quota ; par juridiction, autant de vraies que de fausses ; S et évaluation : fausses à un tiers par juridiction, à 1 près ; t05 présent côté cc et côté ce dans l'évaluation. Valeurs exactes des fausses par juridiction (cc, ce, ca), calculées par un prototype de l'algorithme de D6 : évaluation 667, 667, 666 ; séance S 7, 7, 6 ; entraînement S 1 366, 1 365, 1 365 ; séance S-réservé 9, 6, 5 ; entraînement S-réservé 1 844, 1 103, 1 149.
- `test_order_and_ids_do_not_leak_label` — Then les identifiants se suivent de 1 à n, et, pour la graine 0 (mélange par le flux du jeu), dans chaque jeu la suite des labels n'est ni triée ni strictement alternée (O9).
- `test_dataset_json_composition` — Then `generator` `legal`, `version` 1, `seed` 0, `composition` conforme à D6, `facts_sha256` égal à `facts_sha256()`, `held_out_types` vide pour S et égal aux 5 pour S-réservé.
- `test_session_file_is_a_bundle_source` — Then `read_examples` lit `data/legal_s/session/examples.jsonl` (clés `id` et `raw` seules) et refuse `labels.jsonl`.
- `test_generate_refuses_existing_before_writing` — Given `heldout/legal_s/eval/` déjà présent, When `generate`, Then `FileExistsError` et aucun des 5 autres dossiers créé.
- `test_odd_size_refused` — Given `Sizes(session=41)`, Then `ValueError`.
- `test_cli_datagen_legal` — Given `nnww datagen legal --seed 0 --root tmp`, Then code 0 et 6 chemins affichés ; relancé, code 1 ; avec `--n 10`, code 2 ; `datagen parity --seed 0` sans `--n` garde 256 et 400.
- `test_cli_session_refuses_train_dataset` — Given `nnww session --task legal_s --dataset train …`, Then code 2 avant toute ouverture de séance (aucun dossier sous `runs/`).

Réalignement : `tests/test_boundary.py` couvre `tasks/legal/` sans changement (parcours de `tasks/`) ; `tests/test_datasets.py` (jouet) doit rester vert après le changement des défauts de `datagen`.

**Vérification** : `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -q --tb=short` (suite complète une fois avant la PR).

**Hors de 1-9** :

- Séances A et B sur S et S-réservé, graine consignée au journal du run (1-10).
- `config/train.toml` pour `legal_s` et `legal_s_reserved` (cachée de 32, N de la courbe), généralisation de `baselines/train.py` au registre (`get_task` du jouet aujourd'hui) et F avec `encode_prepared` (1-11).
- Normaliseur de R vers le gabarit de D1, avec filtre `type = arret` pour les cours d'appel, puisque les ordonnances tombent aussi un dimanche ou un jour férié (1-13).
- Lecture de `heldout/<task>/eval/` par l'évaluation, scores par type et par statut (attesté ou reconstruit), précision et exactitude, ablation (1-14).
- Correction de `jeux-de-donnees.md` (section S : format, types 13 à 15 remplacés, renvoi à cette spec) et réserves au rapport du lot 1 (1-14).
- Fêtes locales d'outre-mer (abolition de l'esclavage) : absentes des règles ; une vraie de cour d'appel ultramarine peut tomber ce jour-là, sans effet sur S.

## Revue de la spec

Second avis : décisions O1 à O10 en tête de spec. Reviewer : à compléter.

## Tests ajoutés par les décisions

O1 : chemin relatif, `train` et `eval` refusés, jouet inchangé ; O2 : vraies à 5 et 6 ans ; O3 : t12 mobile ; O4 : refus d'une tâche différente ; O5 : table de Pâques ; O6 : 29 février hors t12 ; O7 : bornes de `fields` ; O10 : numéros d'ordre ≥ 20 000.

## Écarts d'implémentation

- `Sizes` ne valide pas à la construction : `generate_rows` (donc `generate`) lève `ValueError` pour une taille impaire ou inférieure à 2 (`Sizes(session=41)` se construit, comme dans le test nommé).
- O1 : `TaskSpec.session_datasets` (défaut `("toy",)`, `("session",)` pour les deux tâches legal) porte la liste blanche ; `nnww session` refuse avant tout (code 2) `train`, tout nom hors `[a-z0-9_]+` et tout jeu hors liste.
- O4 : `RunRecord.task` (défaut vide, donc un `run.json` ancien est refusé par `score_frozen`) et le premier événement `open` du journal donnent la tâche du réseau ; le manifeste gelé reste inchangé (AD-3). Évaluation croisée journalisée : reportée à 1-14.
- Graine 0 : `nnww datagen legal --seed 0` donne 4 000 / 40 / 8 192, 6 dossiers sans recouvrement ; préfixes sha256 de `dataset.json` : eval `0a76a818cd11`, eval réservé `25bc55ad1984`, séance S `5fcbc7e0296d`, entraînement S `2360a52e7dc6`, séance R `4d0af15e5628`, entraînement R `654549f97903`.
