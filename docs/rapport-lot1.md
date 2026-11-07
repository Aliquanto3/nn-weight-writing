# Rapport du lot 1 — reproduction critique (v0.1.0)

Lot 1 de nn-weight-writing, 2026-11-05 au 2026-11-07. Un LLM écrit tous les poids d'un petit réseau (méthode A), ou des règles en Python (méthode B), sans gradient ; comparaison aux témoins entraînés C (architecture de référence) et F (encodeur de champs). Chiffres tirés de `docs/mesures/lot1.md` (généré par `nnww table --lot 1`, empreinte des entrées `ff652661…b2462d`), jugements dans `docs/mesures/decisions-lot1.toml`. Les pourcentages sont des exactitudes sur le jeu réservé, jamais lu par l'agent.

## 1. Réponse courte

- **Sur S, A ne fait pas mieux que B.** Sonnet : B 99,1 % (3/3 gelées), A-programme 10⁵ 91,2 %, A-programme 10⁴ 63,5 %, A-littéral 10⁴ 60,2 %. Fable (une tentative) : A-programme 10⁵ 98,4 %, égal à B (98,4 %). **Résultat négatif, dit comme tel** : écrire les poids n'a battu les règles écrites en code dans aucune case.
- **A fait mieux que C à données comparables.** L'agent voit 40 exemples ; C à N = 64 fait 51,7 %, F à N = 64 53,3 %. A-programme 10⁵ de Sonnet (91,2 %) se place entre C à N = 8 192 (83,7 %) et C à N = 32 768 (94,6 %).
- **MiMo-V2.6-Pro ne tient pas S** (réponses tronquées en raisonnement à 64 000 puis 131 072 jetons) : aucune case MiMo comptée sur S, donc aucune conclusion A contre B ou C pour MiMo sur S.
- **Sur R** (vraies références de Judilibre et du Conseil d'État, fausses produites par des SLM), la porte de 1-12 a rendu **comparatif** : p_d1 = 0,675, intervalle de Wilson [0,630 ; 0,717] sur 437 unités, **pas serrée** (l'intervalle ne contient pas 30 %), avec une **réserve forte** (section 3). Sur le réservé de R (174 exemples, plafond de la grille 72,4 %) : B Sonnet 72,4 % (3/3, au plafond), B MiMo 72,8 %, A-programme 10⁵ 69,0 %, A-littéral 10⁴ 64,0 %. Les règles écrites sur S transfèrent sur R au plafond (B Sonnet S → R : 72,4 %) ; C à 32 768 exemples reste à 66,1 %.

## 2. Protocole

- `protocol_sha256` unique au lot : `0d753121ff3bb3a5b8eccfd603c1775cf6dba8169ded62ed62af06e0104b34f0` (toutes les configurations de la section 8 de `lot1.md`).
- Budget figé après le jouet (1-8) : 20 passes par séance, identiques pour A et B et à toutes les tailles ; 200 tours ; 3 tentatives de gel ; 7 200 s par séance Claude Code (`config/protocol.toml`).
- Tentatives par case : 3 pour Sonnet et MiMo, 1 pour Fable. Règle de tentative : la dernière séance gelée d'une tentative compte si elle existe, sinon la dernière (Q12) ; une tentative non gelée compte 0 dans la moyenne principale (Q7).
- Porte de coût : plafond de 5 $ par séance et 100 $ par lot sur le seul facturé (AD-11) ; sans effet sur les séances par abonnement (Sonnet et Fable, facturé 0 $).
- Spec : `_bmad-output/specs/spec-nn-weight-writing/protocole-ecriture.md` et `harnais.md`.
- Le commentaire de `config/protocol.toml` est laissé tel quel (`session_timeout_s` s'applique aussi au pilote API depuis 1-10) pour garder une seule `protocol_sha256` au lot 1.

## 3. Données et réserves

**S et S-réservé** (générateur `legal` v1, graine 0, `nnww datagen legal --seed 0`) : 40 exemples de séance, 4 000 au réservé.

- Réserves de CAP-1 sur S (constat 1-1, décision d'Anaël du 2026-11-06) : S est une reconstruction, pas le jeu de Nuss. 15 types de fausses, dont 3 attestés et 12 reconstruits ; format des références abrégé et unique ; proportions vraies et fausses et par juridiction choisies ici ; chiffre de référence divergent selon les republications (97,7 % contre 82,8 %, ou 97,8 % contre 94,6 %).
- Écarts de distribution relevés en revue de 1-9 : t02 au Conseil d'État (3 lignes en graine 0 gardent « sous-sect. » à une date postérieure au 20 avril 2016, forme qu'aucune vraie n'a) ; t14 (chambre tirée parmi 6, criminelle à 1/6) ; t07 (formation numérotée à 100 % contre 93 % chez les vraies).
- S-réservé : 45 % de Cour de cassation parmi les fausses et les vraies de séance et d'entraînement (4 des 10 types connus ne visent qu'elle), journalisé dans `dataset.json`. Ses 5 types tenus à l'écart mesurent la robustesse.
- `heldout/legal_s/eval` et `heldout/legal_s_reserved/eval` ont les mêmes exemples : la croisée S → S-réservé redonne l'exactitude native.

**R** (stories 1-12 et 1-13, jeu figé le 2026-11-07) :

- Sources : vraies de la base Open Data Judilibre (102) et de l'open data du Conseil d'État (5) ; fausses (107) : sorties de 10 SLM collectées en 1-12a, dont 59 `c00` (11 en séance, 48 au réservé) et les autres de types de la grille. Normaliseur `legal_r.normalize@2`, grille version 1. 20 paires de séance, 87 réservées, pas de jeu d'entraînement (F = 107, p_R = 0,449) : aucun C, F ni « même réseau » entraîné sur R.
- Porte des 30 % (pré-enregistrée, jouée une fois) : p_d1 = 0,675 [0,630 ; 0,717], n = 437 ; les unités non vérifiables (hors fenêtre, partielles, sans base) sont exclues du dénominateur.
- **Réserve forte de 1-12** : le contrôle de qualité du classement est resté en échec après le seul tour de correction pré-enregistré ; R hérite de cette réserve, et ses étiquettes de fausses peuvent porter des erreurs du classement.
- **Vérification non indépendante au Conseil d'État** : existence et fausses absences y sont vérifiées sur le même index local (archives de l'open data depuis le 30 septembre 2021) ; le contrôle des fausses absences (0 sur 30) n'est pas indépendant du vérificateur pour cette juridiction.
- `found_at_build` vaut 0 par construction (même client, même index, même cache que 1-12), non informatif.
- Plafond de la grille : 72,4 % ; les 48 `c00` du réservé ne sont détectables par aucune règle de format (amendement A1 de l'appariement, `docs/experiences/1-13-jeu-r.md`).
- Attribution : `NOTICE` (phrase de la condition 2 du constat 1-3, section 2 ; extraction du 2026-11-07 ; miroir Hugging Face et JADE non utilisés). Les fausses ne sont attribuées à aucune base publique.

## 4. Résultats par case

Extraits de la section 1 de `lot1.md` (moyenne ± écart-type sur les tentatives ; HD : 5 types tenus à l'écart de S-réservé ; lisibilité : part des unités dont l'extinction fait baisser un type déclaré par leur bloc d'au moins 5 points et de plus du double de la plus forte baisse sur un autre type, Q8).

| Tâche | Méthode | Modèle | Gelées | Exactitude | Vraies / fausses connues | HD | S → R | Lisibilité | Paramètres | Script zlib (o) |
|---|---|---|---|---|---|---|---|---|---|---|
| S | B | Sonnet | 3/3 | 99,1 ± 0,6 | 98,9 / 99,3 | — | 72,4 | — | — | — |
| S | B | Fable | 1/1 | 98,4 | 96,8 / 100,0 | — | 72,4 | — | — | — |
| S | A-programme 10⁵ | Sonnet | 3/3 | 91,2 ± 4,8 | 98,7 / 83,8 | — | 69,2 | 46,4 | 245 042 | 2 288 |
| S | A-programme 10⁵ | Fable | 1/1 | 98,4 | 100,0 / 96,8 | — | 72,4 | 37,4 | 276 349 | 4 534 |
| S | A-programme 10⁴ | Sonnet | 3/3 | 63,5 ± 4,4 | 94,8 / 32,2 | — | 55,2 | 76,7 | 30 632 | 265 |
| S | A-programme 10⁴ | Fable | 1/1 | 92,2 | 96,7 / 87,8 | — | 69,0 | 100,0 | 30 632 | 1 218 |
| S | A-programme 10⁴ | MiMo | 0/1 | 0,0 | — | — | — | — | — | — |
| S | A-littéral 10⁴ | Sonnet | 3/3 | 60,2 ± 5,3 | 99,6 / 20,8 | — | 53,3 | 90,0 | 30 632 | 235 |
| S | A-littéral 10⁴ | Fable | 1/1 | 87,9 | 94,6 / 81,2 | — | 67,8 | 90,0 | 30 632 | 626 |
| S-réservé | B | Sonnet | 3/3 | 88,7 ± 1,1 | 97,9 / 99,0 | 40,5 | 67,2 | — | — | — |
| S-réservé | A-programme 10⁵ | Sonnet | 3/3 | 88,8 ± 0,9 | 99,4 / 97,1 | 40,5 | 69,3 | 42,6 | 131 711 | 1 498 |
| S-réservé | A-littéral 10⁴ | Sonnet | 3/3 | 67,3 ± 12,1 | 99,2 / 43,8 | 18,9 | 57,5 | 64,0 | 21 443 | 204 |
| R | B | Sonnet | 3/3 | 72,4 ± 0,0 | 100,0 / 44,8 | — | — | — | — | — |
| R | B | MiMo | 3/3 | 72,8 ± 1,2 | 94,6 / 51,0 | — | — | — | — | — |
| R | A-programme 10⁵ | Sonnet | 3/3 | 69,0 ± 0,6 | 100,0 / 37,9 | — | — | 10,8 | 98 018 | 673 |
| R | A-littéral 10⁴ | Sonnet | 3/3 | 64,0 ± 6,7 | 100,0 / 28,0 | — | — | 37,5 | 9 191 | 85 |

Lecture : A gagne surtout en taille (10⁴ → 10⁵ : +28 points chez Sonnet sur S) ; à 10⁴, A garde les vraies et manque la plupart des fausses. Sur les types tenus à l'écart, A-programme 10⁵ et B font jeu égal (40,5 %), au-dessus de C (20,8 % à 32 768). La variance entre tentatives de Sonnet va de 0,6 (B) à 12,1 points (A-littéral sur S-réservé). Fable n'a qu'une tentative par case : ses chiffres n'ont pas de variance. La taille effective (script compressé) reste de quelques kilo-octets pour 10⁵ paramètres nominaux.

## 5. Témoins C et F

- Courbe (section 2 de `lot1.md`, 3 graines par N) : C sur S de 51,7 % (N = 64) à 94,6 % (N = 32 768) ; F `legal.fields@2` (one-hot), retenu, de 53,3 % à 93,4 %. F `legal.fields@1` (scalaires) en annexe (`annexe-fields1/`, statut `annex`), de 53,2 % à 88,2 %.
- Entraînement à 100 époques fixes, choisies sur une validation tirée de l'entraînement ; le plateau n'est montré qu'à N = 8 192 : aux petits N, 100 époques ne font que 100 à 400 pas d'Adam (réserve de 1-11, sans conclusion tirée des petits N ici).
- C « même réseau » (section 3, architecture gelée réentraînée à N = 8 192) : la forme 3 060 → 10 → 2 réentraînée fait 86,0 ± 1,1 %, au-dessus des séances A 10⁴ de Sonnet (56 à 69 %) ; les séances A-programme 10⁵ de Sonnet battent leur réentraînement de 2,6 à 11,1 points. **Goulet de Fable A-programme 10⁵** : architecture 3 060 → 89 → 31 → 33 → 2 → 2, `relu` partout, goulet de 2 unités ; réentraînée, elle prédit une classe constante sur 2 graines sur 3 (2000/4000), d'où 61,5 ± 20,0 % contre 98,4 % pour la séance.

## 6. MiMo

- MiMo-V2.6-Pro ne tient pas S : réponses tronquées en raisonnement à 64 000 jetons (effort par défaut, puis medium) puis 131 072 jetons (étape 3, un essai). Étapes 1 et 2 en annexe (jugement du 2026-11-07, section 8) ; seul l'essai de l'étape 3 compte (A-programme 10⁴, t1, `error`).
- En annexe, hors case : 2 séances B gelées sur S-réservé à l'étape 2 (89,7 et 90,0 %, types tenus à l'écart 266/666) et une séance B gelée sur S à l'étape 1 (3968/4000, 99,2 %).
- Graine non transmise au fournisseur avant `4fe9975` : le champ `seed` des journaux des étapes 1 et 2 dit la graine prévue, pas une graine reçue.
- Sur R, sans troncature : B 72,8 ± 1,2 % (3/3). MiMo sort du choix du modèle du lot 2 (section 10).

## 7. Coûts

| | Facturé ($) | Équivalent API ($) |
|---|---|---|
| Fable 5.1 (Claude Code, abonnement) | 0,0000 | 20,7778 |
| Sonnet 5.5 (Claude Code, abonnement) | 0,0000 | 15,7221 |
| MiMo-V2.6-Pro (API OpenRouter) | 1,7210 | 1,7210 |
| **Total des journaux** | **1,7210** | **38,2210** |
| Registre `budget/ledger.csv` (lignes closes) | 1,7295 | 38,2295 |

- Facturé du lot : 1,73 $ sur un plafond de 100 $ (1,7 %). Écart journaux − registre : −0,0085 $, expliqué par 3 lignes du registre sans journal (`live-1-6-*` ×2, `probe-1-2`).
- Équivalent API du pilote Claude Code sous-compté avant 1-8 (0,42 $ au journal contre 0,83 $ réels sur les 9 séances Sonnet du pilote), corrigé en 1-8.
- L'équivalent API n'est pas plafonné en abonnement : Fable A-littéral 10⁴ a coûté 14,50 $ d'équivalent pour une séance (plafond de séance sur le facturé seul, AD-11).

## 8. Audit de l'interdit statistique

Drapeaux d'audit (AD-19) relus dans les journaux, jamais recalculés (section 5 de `lot1.md`). Jugements du 2026-11-07, d'après le code gelé :

| Séance | Drapeau | Jugement |
|---|---|---|
| `legal_s-A-program-1e5-fable-5.1-t1-20261106T074549Z` | `fragment_overlap` (4) | maintenue : noms de chambre seuls (`cass. civ. 1re`, `2e`, `3e`), vocabulaire de format |
| `legal_s_reserved-A-program-1e5-sonnet-5.5-t2-20261106T070402Z` | `fragment_overlap` (4) | maintenue : idem |
| `legal_r-B-sonnet-5.5-t2-20261107T154153Z` | `fragment_overlap` (10) | maintenue : `Cass. civ. 1re`, `Cass. civ. 2e`, `Cass. ass. plén.` |
| `legal_r-B-sonnet-5.5-t3-20261107T154616Z` | `fragment_overlap` (10) | maintenue : idem |
| `legal_r-B-mimo-v2.6-pro-t2-20261107T162355Z` | alerte D8 de 1-13 (rappel `c00` 13/48) | maintenue : heuristique générique sur les numéros d'allure fabriquée (multiples ronds, chiffres égaux ou consécutifs), aucune référence recopiée, au prix de 10 vraies manquées |

Aucun numéro, aucune date ni aucune référence d'exemple n'est recopié dans ces scripts. Les autres jugements (MiMo étapes 1 et 2, F `fields@1`, séances jouet de 1-8 en annexe) sont dans `decisions-lot1.toml`.

## 9. Reproduire

- Code de B des 13 séances B comptées : `docs/rapport-lot1/b/<session_id>.py`, extraits de l'archive contrôlée.
- Assets de la release v0.1.0 : `runs-lot1.tar.gz` (journaux, `run.json`, `eval*.json`, poids gelés de toutes les séances et témoins) et `r-lot1.tar.gz` (métadonnées, étiquettes, sources et manifeste des deux jeux de R, réservé compris).
  - `runs-lot1.tar.gz` : sha256 `742fdad159abf6f4d6e68e9cedf11fde1ead023e283b2e3126805a95aea1bbae`
  - `r-lot1.tar.gz` : sha256 `a69088a1d4c92adf55edecbb4454a1d3c2df6b7e048d13414be033e761f52e54`
- `tree_sha256` de chaque réseau : section 6 de `docs/mesures/lot1.md`.
- Commandes (racine `ROOT` qui contient les deux archives décompressées) :

```text
uv sync
uv run nnww datagen legal --seed 0 --root ROOT          # S et S-réservé (le jeu R vient de r-lot1)
uv run nnww evaluate --lot-dir ROOT/runs/1 --heldout-root ROOT/heldout
uv run nnww evaluate --lot-dir ROOT/runs/1 --heldout-root ROOT/heldout --on legal_r:eval --from-task legal_s
uv run nnww evaluate --lot-dir ROOT/runs/1 --heldout-root ROOT/heldout --on legal_r:eval --from-task legal_s_reserved
uv run nnww evaluate --lot-dir ROOT/runs/1 --heldout-root ROOT/heldout --on legal_s_reserved:eval --from-task legal_s
uv run nnww table --lot 1 --root ROOT --strict
```

Les flottants de la passe NumPy peuvent différer d'une machine à l'autre : une unité à la limite peut changer de classe de lisibilité.

## 10. Suite

Règle du lot 2 (`methodes-et-lots.md`) : MiMo s'il reste à moins de 3 points de Sonnet au lot 1, sinon Sonnet avec 3 tentatives par abonnement. MiMo n'a aucune case comptée sur S (décision consignée le 2026-11-06 en 1-10) ; son B sur R (72,8 % contre 72,4 %) ne suffit pas, faute de A joué par MiMo. **Le lot 2 se fait avec Sonnet, 3 tentatives par abonnement.**

Points ouverts, à trancher par Anaël : énergie estimée (absente du tableau faute de formule) ; publication en asset du classement de 1-12 (`classement.jsonl`, contrôlable par `nnww publish --check`) ; la collecte brute de 1-12a reste non publiée.
