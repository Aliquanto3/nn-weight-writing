# Story 1-12 : pré-étude R et porte des 30 %

Phase A (méthode et faits de la base réelle) : 2026-11-07. Phase B (classement, contrôle de qualité, porte) : à venir, sur le code du commit « grille figée ». Aucun appel payant, ni Ollama ni GPU. `data/r/collecte/` n'a pas été lu pendant la phase A.

## Références

- Spec (pré-enregistrement) : `_bmad-output/implementation-artifacts/stories/1-12-pre-etude-r.md`, commit `9e05ec1`, décisions P0-P12 reportées en `0aa98d8`.
- Commit « grille figée » : cité dans le compte rendu de la phase A et dans `config/r_gate.toml` (`grid_commit`) ; `classer` refuse de tourner sur un autre `HEAD` ou sur un arbre modifié.
- Empreinte du manifeste de 1-12a : à consigner en phase B (`--manifeste-sha256`).

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

**Échantillons.** Cour de cassation : `/scan` abrégé, `date_type=creation`, 12 lots mensuels de 84 pour 2005, 2012, 2019 et 2024 (3 862 décisions, des mois en ont moins de 84). Cours d'appel : arrêts (`type=arret`) de 2023 et 2025, mêmes lots (2 016). Conseil d'État : les 40 134 décisions de l'index. Champs de la version abrégée de `/scan` : `chamber`, `decision_date`, `ecli`, `formation`, `id`, `jurisdiction`, `location`, `number`, `numbers`, `publication`, `type` (ni texte, ni résumé ; pas d'`update_date`). Le test `live` confirme Perruche (`cc`, `pl`, 2000-11-17, `99-13.701`) par `/scan` abrégé et l'absence de `99-99.999` par égalité de champ.

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

À écrire après `porte` : entonnoir des comptes, p_d1 et intervalle, décision, « serrée », grandeurs de D7, recouvrement avec les 15 types, contrôle de qualité, réserves, sha256 du classement, attribution (condition 2 de 1-3).
