# Constat 1-3 : Judilibre, Conseil d'État et collecte des hallucinations

Date : 2026-11-05. Périmètre : accès à l'API Judilibre par PISTE, licence de réutilisation, source équivalente pour le Conseil d'État, collecte d'hallucinations de SLM par `slm-quality-bench` (CAP-1, pour CAP-10 et CAP-11). Le compte PISTE d'Anaël n'est pas encore ouvert : aucun appel réel à l'API n'a été fait.

## Verdict : provisoire — en attente du compte PISTE

Au sens de CAP-1 : feu vert avec réserve attendu, aucun blocage relevé.

| Point | Verdict partiel | En bref |
|---|---|---|
| 1. Accès Judilibre (PISTE) | provisoire — en attente du compte PISTE | Procédure, endpoints et champs établis par la documentation officielle ; authentification et quotas restent à confirmer par un appel réel. Un miroir public (Hugging Face, figé au 2025-03-20) permet d'avancer sans compte. |
| 2. Licence Judilibre | conforme avec réserves | Licence Ouverte 2.0 complétée par les CGU de la Cour de cassation (6 janvier 2022). Republier des références (sans texte ni nom) est permis, avec attribution, date de mise à jour et sans altération. Aucun usage prévu ne touche à l'identité des magistrats. |
| 3. Conseil d'État | conforme avec réserves | `opendata.justice-administrative.fr` (XML, Licence Ouverte 2.0, CGU du 18 janvier 2022), depuis le 30 septembre 2021 ; JADE (DILA, Licence Ouverte) pour les décisions plus anciennes publiées au Lebon ; ArianeWeb seulement pour des vérifications à la main. Pas de compte requis. |
| 4. Hallucinations via `slm-quality-bench` | conforme avec réserves | Le dépôt ne contient **aucune** fausse référence juridique (0 sur 14 campagnes, 243 Mo de générations). Il fournit l'infrastructure (client Ollama déterministe, ~35 SLM catalogués) mais pas de jeu de questions juridiques : une collecte dédiée est à écrire et à lancer sur la tour, avec Ollama (ressource d'Anaël). |

**`r_republish` : mettre `true`.** Les artefacts de R peuvent aller dans une release publique : la Licence Ouverte 2.0 permet de « communiquer, diffuser, redistribuer, publier » l'information, y compris à titre commercial (CGU Judilibre, § V), sous réserve de mentionner la source et la date de dernière mise à jour, de ne pas altérer les données et de respecter la loi Informatique et libertés. R ne garde que des métadonnées de référence (juridiction, chambre ou formation, siège, date, numéro, ECLI), sans texte ni nom de partie ou de magistrat. Avec `false`, `nnww publish` refuserait toute archive contenant les journaux des séances sur R (AD-18) et le lot 1 ne pourrait pas publier ces séances. Conditions dans la section 2 ; à reconfirmer seulement si les CGU affichées à l'ouverture du compte PISTE diffèrent de la version du 6 janvier 2022.

## 1. Accès à l'API Judilibre par PISTE

**Verdict partiel : provisoire — en attente du compte PISTE.**

### Inscription et clés

D'après les CGU Judilibre (§ XI.B) et la documentation de `pyjudilibre` :

1. Créer un compte nominatif sur PISTE (`piste.gouv.fr`, menu d'inscription) : nom, courriel, mot de passe, acceptation des CGU de PISTE, puis lien de validation reçu par courriel.
2. Dans « APIs > Acceptation des CGU des APIs », cocher **JUDILIBRE** pour les environnements **PROD** et **SANDBOX**, puis valider. C'est cette acceptation qui vaut acceptation des CGU Judilibre et de la Licence Ouverte 2.0 (CGU, § II.C).
3. Créer une application (« Applications > Créer une application » ; nom libre).
4. Modifier l'application, sélectionner **JUDILIBRE** dans le tableau du bas, appliquer.
5. Relever l'**API Key** (onglet principal de l'application) et, si besoin, l'identifiant et le secret OAuth.

**Authentification : deux sources officielles divergent.** La spécification OpenAPI publiée par la Cour de cassation déclare un schéma `apiKey` dans l'en-tête `KeyId` ; les CGU (§ XI.C) écrivent que l'accès se fait « après authentification par le protocole Oauth 2.0 lors de chaque requête ». PISTE propose les deux. Le test ci-dessous essaie d'abord `KeyId`, puis OAuth (`client_credentials` sur `https://oauth.piste.gouv.fr/api/oauth/token`, ou `https://sandbox-oauth.piste.gouv.fr/api/oauth/token` en bac à sable, d'après des clients tiers ; non confirmé par une source officielle consultée).

Les clés sont « strictement réservées à [l']application » et ne doivent jamais être rendues publiques (CGU, § XI.C) ; en cas de fuite, les réinitialiser sur PISTE et prévenir la Cour de cassation ou l'AIFE (§ XI.E). Elles vont en variable d'environnement seulement, comme les autres secrets du projet (spine, conventions de configuration).

### Endpoints utiles pour obtenir de vraies références

Bases : `https://api.piste.gouv.fr/cassation/judilibre/v1.0` (production) et `https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0` (bac à sable). L'API est en **version bêta** : ni disponibilité, ni complétude, ni fraîcheur garanties (CGU, § XI.A et XI.D).

| Endpoint | Usage pour R | Limites documentées (OpenAPI) |
|---|---|---|
| `GET /scan` | Extraction en masse des références d'une juridiction, d'une chambre, d'une période (`jurisdiction`, `chamber`, `date_start`, `date_end`, `publication`…), curseur `search_after`. | `batch_size` ≤ 1 000 ; la description évoque un total de 1 000 résultats « pour les connexions non authentifiées » : le plafond réel avec compte est à mesurer. |
| `GET /export` | Ancienne extraction par lots (`batch`). | Marqué `deprecated` ; `batch_size` ≤ 1 000. |
| `GET /search` | Vérifier une référence : le texte de `query` porte aussi sur le numéro de pourvoi. Filtres `jurisdiction`, `chamber`, `date_start`, `date_end`. | `page_size` ≤ 50 ; 10 000 résultats au plus par requête. Pas de filtre dédié au numéro ni à l'ECLI. |
| `GET /decision?id=…` | Fiche complète d'une décision. | Renvoie aussi le texte intégral : à ne pas conserver (section 2). |
| `GET /taxonomy?id=chamber&context_value=cc` | Valeurs admises des chambres, formations, juridictions (`cc`, `ca`, `tj`, `tcom`…). | — |
| `GET /stats` | Couverture par juridiction et par période. | — |
| `GET /transactionalhistory?date=…` | Créations, mises à jour et suppressions depuis une date (tenue à jour). | `page_size` ≤ 500. |
| `GET /healthcheck` | Test de connexion. | — |

Champs d'une décision utiles au normaliseur : `jurisdiction`, `chamber`, `formation`, `location` (siège, pour les cours d'appel), `decision_date`, `number` et `numbers` (numéros de pourvoi, forme `99-13.701`), `ecli`, `publication`, `type`, `solution`, `update_date`. Ils figurent dans le schéma OpenAPI et, à l'identique, dans le miroir Hugging Face (34 colonnes).

### Quotas

Non publiés. Les CGU (§ XI.D) prévoient des limites par seconde, minute ou jour, en nombre de requêtes ou en bande passante, par application ou par méthode, consultables dans PISTE : « API Sélectionnées > Actions > Consulter les quotas ». Le dépôt `judilibre-search` annonce qu'ils « seront prochainement sur le portail PISTE ». **En attente du compte PISTE.**

### Couverture

Cour de cassation : environ 550 000 décisions, de 1860 à aujourd'hui pour les décisions publiées (miroir HF : 553 075 décisions, 1860-08-01 au 2025-03-19). Cours d'appel : chambres civiles, sociales et commerciales, systématiquement depuis le 15 avril 2022, avec un fonds antérieur partiel (le miroir remonte à 1996). Pas de décisions pénales des cours d'appel avant leur ouverture prévue (date reportée selon la presse juridique). Judilibre ne couvre **pas** la justice administrative. Chiffres à confirmer par `/stats`.

### Repli sans compte : miroir Hugging Face

`antoinejeannot/jurisprudence` republie Judilibre sous `etalab-2.0` (Parquet et JSONL, une configuration par juridiction : Cour de cassation 1,7 Go, cours d'appel 2,9 Go, tribunaux judiciaires 0,8 Go), mêmes champs que l'API. Dernière version : **v2025.03.20**, plus mise à jour depuis. Il suffit pour préparer le normaliseur et un premier tirage de vraies références antérieures au 2025-03-19 ; il ne suffit pas pour vérifier l'absence d'une référence datée d'après, ni pour la fraîcheur exigée par les CGU. Lire seulement les colonnes de métadonnées (projection Parquet), jamais `text`.

### Procédure de test, à jouer à l'ouverture du compte PISTE

Variables d'environnement (noms proposés, jamais commitées) : `JUDILIBRE_KEY_ID` pour l'API Key ; `PISTE_CLIENT_ID` et `PISTE_CLIENT_SECRET` pour OAuth. Commandes Git Bash, bac à sable d'abord, puis production en remplaçant la base :

```bash
BASE=https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0

# T1 — connexion par KeyId : attendu HTTP 200
curl -s -o /dev/null -w "%{http_code}\n" -H "KeyId: $JUDILIBRE_KEY_ID" "$BASE/healthcheck"

# T2 — si T1 renvoie 401/403 : OAuth client_credentials, puis même appel avec le jeton
TOKEN=$(curl -s -X POST https://sandbox-oauth.piste.gouv.fr/api/oauth/token \
  -d grant_type=client_credentials -d client_id="$PISTE_CLIENT_ID" \
  -d client_secret="$PISTE_CLIENT_SECRET" -d scope=openid | sed -E 's/.*"access_token":"([^"]+)".*/\1/')
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $TOKEN" "$BASE/healthcheck"

# T3 — chambres de la Cour de cassation
curl -s -H "KeyId: $JUDILIBRE_KEY_ID" "$BASE/taxonomy?id=chamber&context_value=cc"

# T4 — référence connue (Perruche, Ass. plén., 17 nov. 2000, n° 99-13.701, à confirmer) :
#      attendu jurisdiction=cc, decision_date=2000-11-17, number=99-13.701
curl -s -H "KeyId: $JUDILIBRE_KEY_ID" "$BASE/search?query=99-13.701&jurisdiction=cc&page_size=5"

# T5 — numéro inventé : vérifier qu'aucun résultat n'a ce numéro exact dans number/numbers
#      (la recherche plein texte peut renvoyer des résultats approchés : la vérification
#       d'absence compare les champs, pas le total)
curl -s -H "KeyId: $JUDILIBRE_KEY_ID" "$BASE/search?query=99-99.999&jurisdiction=cc&page_size=5"

# T6 — couverture
curl -s -H "KeyId: $JUDILIBRE_KEY_ID" "$BASE/stats?jurisdiction=cc"

# T7 — extraction en masse : plafond réel avec compte (1 000 au total ?)
curl -s -H "KeyId: $JUDILIBRE_KEY_ID" \
  "$BASE/scan?jurisdiction=cc&date_start=2019-01-01&date_end=2019-12-31&batch_size=1000"
```

T8 : relever dans PISTE les quotas (« Consulter les quotas ») et la version des CGU Judilibre affichée. Consigner les codes HTTP, le mode d'authentification retenu, le plafond de `/scan`, les quotas et la version des CGU dans ce constat, puis passer le verdict à « conforme » ou « conforme avec réserves ». Ne jamais coller d'en-tête ni de jeton dans le constat ou un journal (AD-18 refuse le motif `Bearer `).

## 2. Licence de réutilisation des données Judilibre

**Verdict partiel : conforme avec réserves.**

Textes : CGU « pour la réutilisation des données issues des décisions de justice de l'ordre judiciaire diffusées en open data par la Cour de cassation », version du 6 janvier 2022 (sur PISTE) ; Licence Ouverte 2.0 (Etalab) ; COJ art. L. 111-13 et R. 111-10 à R. 111-13 ; CRPA art. L. 321-1, L. 322-1, L. 322-2, L. 324-1, L. 326-1 ; Code pénal art. 226-18, 226-24, 226-31. Les citations du COJ et du CRPA ci-dessous viennent des CGU, qui les reproduisent ; le texte consolidé sur Légifrance n'a pas été relu (Incertitudes).

| Obligation (source) | Texte | Application à R |
|---|---|---|
| Licence (CGU § I, II.C, XIII) | Réutilisation « subordonnée à l'acceptation sans réserve de la licence ouverte […] version 2.0 et des présentes [CGU] » ; en cas de contradiction, les CGU priment. | Les CGU s'appliquent « quel que soit le mode d'accès » (§ II.B) : aussi au miroir Hugging Face. |
| Droit de réutilisation (CRPA L. 321-1 ; LO 2.0, citée § V) | Libre de « la reproduire, la copier, de l'adapter […], de la communiquer, la diffuser, la redistribuer, la publier […], de l'exploiter à titre commercial ». Gratuit (CRPA L. 324-1, § XI). | Publier les références dans une release : permis. Les envoyer à un LLM (MiMo, Anthropic) dans une séance : permis. |
| Non-altération (CRPA L. 322-1, § V) | Ne pas altérer les données, ne pas dénaturer leur sens ; « doivent être mentionnés, pour chaque décision de justice réutilisée, le nom de la juridiction et la formation qui l'a rendue, son siège et la date de son prononcé ». | Chaque vraie référence garde juridiction, chambre ou formation, siège (`location` pour une cour d'appel) et date, sans retouche. Les fausses références ne sont jamais présentées comme venant de Judilibre (étiquette et source explicites), sinon la réutilisation « induirait en erreur des tiers quant au contenu de l'information » (LO 2.0, citée § V). |
| Attribution (§ V ; LO 2.0) | Mentionner que les données proviennent de la base Open Data tenue par la Cour de cassation, « quel que soit le support », et la date de dernière mise à jour. | Mention dans `NOTICE`, les notes de release et le manifeste de R ; date d'extraction et `update_date` de chaque décision conservées. |
| Tenue à jour (§ V, XII) | Obligation de tenir ses données à jour « en sa qualité de responsable de traitement » ; délai de 72 h entre deux mises à jour **recommandé**. | Une release est un instantané daté : l'indiquer. L'obligation vise surtout les données personnelles, absentes de R. Réserve : une décision retirée de Judilibre après la release y resterait citée ; risque faible pour des métadonnées sans nom. |
| Interdiction du profilage (COJ L. 111-13 al. 3, § VI) | « Les données d'identité des magistrats et des membres du greffe ne peuvent faire l'objet d'une réutilisation ayant pour objet ou pour effet d'évaluer, d'analyser, de comparer ou de prédire leurs pratiques professionnelles réelles ou supposées », sous peine des sanctions des art. 226-18, 226-24 et 226-31 du code pénal. | Non concerné : R ne lit ni ne garde le texte (où figurent les noms des magistrats), ni aucun champ d'identité. Interdire `text`, `zones` et `text_highlight` dans le normaliseur. |
| Données personnelles (CRPA L. 322-2, § VII) | Réutilisation soumise à la loi du 6 janvier 1978 et au RGPD ; le réutilisateur est responsable de son traitement. | Pas de donnée personnelle dans R si le texte est exclu. Les noms de parties inventés par un SLM (« Dupont c/ Martin ») sont retirés par le normaliseur. |
| Pseudonymisation (COJ L. 111-13 al. 2 et R. 111-13, § IX et X) | Le réutilisateur ne peut ni lever ni ajouter d'occultation de sa propre initiative ; il signale tout défaut d'occultation. | Non concerné sans texte. |
| Sanctions (CRPA L. 326-1, § XII) | Manquement : interruption temporaire ou définitive de l'accès, action en réparation. | — |
| Clés (§ XI.C, XI.E) | Clés jamais publiques. | Variables d'environnement ; scan d'AD-18 (section Report, R6). |

**Conditions de `r_republish = true` :**

1. R ne contient que des métadonnées de référence : juridiction, chambre ou formation, siège, date, numéro, ECLI, publication, `update_date`. Ni `text`, ni `zones`, ni nom de partie ou de magistrat.
2. Attribution dans `NOTICE` et les notes de release, prête à copier : « Vraies références : base Open Data Judilibre de la Cour de cassation, Licence Ouverte 2.0 (https://www.etalab.gouv.fr/licence-ouverte-open-licence), extraction du AAAA-MM-JJ ; données Conseil d'État : base Open Data du Conseil d'État (opendata.justice-administrative.fr) et JADE (DILA), Licence Ouverte 2.0. Fausses références : générées par des SLM, ne correspondent à aucune décision. »
3. Chaque ligne porte sa classe et sa source (`judilibre`, `ce-opendata`, `jade`, `slm:<tag>`) ; aucune fausse référence n'est attribuée à une base publique.
4. Les vraies références ne sont pas modifiées (pas de fausse référence fabriquée par retouche d'une vraie : elles viennent toutes des SLM).
5. Version des CGU relevée à l'ouverture du compte PISTE (T8) ; si elle a changé, relire les § V, VI et XIII avant de publier.

Le miroir Hugging Face, qui republie depuis 2024 le texte intégral de plus d'un million de décisions sous `etalab-2.0`, montre que cette lecture de la licence est courante ; ce n'est pas une preuve de conformité.

## 3. Source équivalente pour le Conseil d'État

**Verdict partiel : conforme avec réserves.**

| Source | Accès | Couverture | Format | Licence |
|---|---|---|---|---|
| Open data de la justice administrative, `opendata.justice-administrative.fr` | Libre, sans compte ni API : moteur de recherche et archives zip par juridiction, année et mois | Conseil d'État depuis le 30 septembre 2021 (en ligne le lendemain, du mardi au samedi) ; CAA depuis le 31 mars 2022 ; TA depuis le 30 juin 2022 | XML. Champs : `Numero_Dossier`, `Date_Lecture`, `Numero_ECLI`, `Formation_Jugement`, `Code_Juridiction` (`CE`), `Nom_Juridiction`, `Code_Publication` (A Lebon, B tables, C, D, Z), `Type_Decision`, `Date_Mise_Jour`, `Texte_Integral`… | Licence Ouverte 2.0 et CGU du 18 janvier 2022 |
| JADE (DILA), `echanges.dila.gouv.fr/OPENDATA/` | Libre (HTTPS ou FTPS) | Conseil d'État : décisions publiées au Lebon depuis 1965 ; CAA depuis 1989 ; Tribunal des conflits | XML | Licence Ouverte |
| ArianeWeb (`conseil-etat.fr`) | Moteur de recherche web, sans API ni téléchargement en masse | Plus de 270 000 décisions du CE et des CAA, dont celles d'avant le 30 septembre 2021 | Pages web | Conditions non relues |

Les CGU du Conseil d'État reprennent celles de la Cour de cassation : Licence Ouverte 2.0 (§ II.C et XIII) ; mention de la source et de la date de dernière mise à jour, précisée comme « uniquement celle à laquelle le réutilisateur aura chargé la décision » ; numéro, juridiction, formation, siège et date conservés avec chaque décision (§ V) ; interdiction du profilage des magistrats et greffiers (CJA art. L. 10, mêmes peines du code pénal, § VI) ; occultation « socle » des noms (§ IX). Les conditions de `r_republish = true` de la section 2 valent à l'identique.

Réserves : pas d'API, donc vérification d'absence sur un index local construit depuis les archives mensuelles (et JADE pour l'historique) ; les décisions du CE non publiées au Lebon et antérieures au 30 septembre 2021 ne sont dans aucune base téléchargeable, donc une référence de cette période n'est vérifiable que si elle est au Lebon (sinon : « non vérifiable », exclue). Format d'une référence : `CE, 10 juillet 2020, n° 428409`, ECLI de forme `ECLI:FR:CECHR:2020:428409.20200710`. Le CE ne passe pas par PISTE pour ces sources ; l'API Légifrance (sur PISTE) couvre aussi JADE, mais n'est pas nécessaire.

## 4. Collecte d'hallucinations via `slm-quality-bench`

**Verdict partiel : conforme avec réserves** — faisable, mais rien n'existe encore.

### Ce que le dépôt contient

Relevé en lecture seule sur `f6e77e5` (2026-11-05) :

- **Aucune fausse référence juridique.** Sur les 14 campagnes de `data/quality_bench/campaigns/` (243 Mo de `generation.jsonl`), zéro occurrence de « Cour de cassation », « Conseil d'État », « Cass. », « ECLI » ; les 24 « pourvoi » et 21 motifs `NN-NN.NNN` sont des mots de listes et des coordonnées géométriques.
- Les sept usages du banc (raisonnement, consignes, outils, extraction, RAG, abstention, rédaction) n'ont aucune question de jurisprudence. Les questions privées d'abstention et d'extraction contiennent des articles de contrats et de règlements, pas de références de décisions.
- La liste des sources est **fermée** (`questions/schema.py`, `SOURCES`), chaque source avec un correcteur : ajouter des questions juridiques au banc demande un changement de code dans `slm-quality-bench`.

### Ce qu'il sait produire

- Client Ollama (`slm_quality_bench/ollama/client.py`) : `/api/chat` en streaming, `temperature = 0`, graine fixée, versions d'Ollama vérifiées.
- Catalogue de ~35 SLM (`models.yaml`), de 350 M à 35 B paramètres, familles Qwen, Gemma, Ministral, Granite, Phi, LFM, Nemotron, Bonsai… ; aucun de la famille de Sonnet ni de MiMo, donc pas de circularité avec les modèles qui écrivent les détecteurs.
- Campagnes reprenables, JSONL en ajout seul, manifeste, contrôle du GPU, libellé de machine (`tour-rtx3050`).

### Comment en tirer ~300 hallucinations pour 1-12

1. **Jeu de requêtes figé avant la collecte** (pré-enregistré, sans tri a posteriori) : ~40 thèmes juridiques × 2 juridictions (Cour de cassation, Conseil d'État), en deux tournures : demande directe (« Citez un arrêt de la Cour de cassation sur [thème], avec la chambre, la date et le numéro de pourvoi ») et question naturelle (« Quelle jurisprudence s'applique à [situation] ? »), plus écologique.
2. **Modèles** : 8 à 10 SLM ≤ 4 B de familles différentes (par exemple `qwen3.5:0.8b`, `qwen3.5:2b`, `qwen3.5:4b`, `gemma4:e2b-it-qat`, `gemma4:e4b-it-qat`, `ministral-3:3b`, `phi4-mini:3.8b`, `granite4.2:3b`, `lfm3:1.7b-q4_K_M`, `nemotron-3-nano:4b`), piste `think_off`, plafond ~512 tokens, mêmes réglages déterministes que le banc.
3. **Volume estimé** (non mesuré) : 80 requêtes × 10 modèles = 800 générations, 1 à 2 références par réponse, 15 à 30 % de refus ou de réponses sans référence : ~600 à 1 300 références brutes, ~400 à 900 après déduplication. Assez pour ~300 hallucinations vérifiées, même si un tiers des références citées existent. Durée estimée : 1 à 2 h sur la tour (RTX 3050).
4. **Extraction** : parseur de références (juridiction, chambre, date, numéro, ECLI) sur le texte brut, en gardant le brut et le modèle d'origine ; noms de parties retirés.
5. **Vérification** : une référence est une hallucination si elle est incohérente (date impossible, chambre inexistante, numéro mal formé…), ou si elle est cohérente et absente de la base, dans la fenêtre de couverture. Une référence hors fenêtre (Cour de cassation non publiée ancienne, CE d'avant 2021 hors Lebon, cour d'appel d'avant 2022) est « non vérifiable » et exclue. Une référence qui existe sort du jeu.

Emplacement : la collecte tourne sur Ollama, que la spec exclut du projet (« pas d'Ollama ni de GPU »). Deux options : une commande `collect` dans `slm-quality-bench` (une story de ce dépôt), ou un script hors du paquet `nnww`, lancé une fois sur la tour, dont la sortie est figée avec son sha256. Dans les deux cas, `nn-weight-writing` ne lit qu'un fichier figé. **Ressource d'Anaël** : Ollama et le GPU de la tour, sans conflit avec une campagne en cours (`wsp-s1-20261105` date du jour).

Licences des sorties : les modèles retenus sont sous Apache 2.0, MIT ou des licences propriétaires ouvertes (Gemma, LFM, Nemotron) ; aucune source consultée n'indique qu'elles revendiquent les sorties, mais ce point n'a pas été relu modèle par modèle (Incertitudes).

## Conséquences pour 1-12 (pré-étude R, porte des 30 %)

- Dépend de la collecte (section 4) : story ou script de collecte, puis Ollama sur la tour. À demander à Anaël en même temps que le compte PISTE.
- La classification ne demande pas de base pour les incohérentes, mais la **vérification des cohérentes** en demande une : Judilibre (compte PISTE, ou miroir HF jusqu'au 2025-03-19) et l'open data administratif. Sans compte PISTE, 1-12 peut avancer sur les références datées d'avant le 2025-03-19 et sur le Conseil d'État.
- Grille d'incohérence fixée avant de voir les données (format, calendrier, chronologie pourvoi-décision, chambre ou formation existante, cohérence de l'ECLI, « autre »), puis rapprochée des 15 types de Nuss pour mesurer leur recouvrement.
- Intervalle : sur n = 300, l'intervalle de Wilson à 95 % fait environ ± 5 points autour de 30 %. Une part estimée entre 25 et 35 % ne tranche pas la porte sans règle fixée d'avance (Report, R4).
- Dédupliquer par référence normalisée ; garder le modèle d'origine pour vérifier qu'aucune famille ne domine.

## Conséquences pour 1-13 (jeu R)

- Vraies références : Judilibre par `/scan` (compte PISTE) ou miroir HF en attendant ; Conseil d'État par l'open data administratif et JADE. Tirage stratifié pour que juridiction, chambre et période des vraies suivent celles des fausses : sinon la date ou la juridiction trahit la classe, même après le normaliseur commun.
- Vérification d'absence (CAP-11) : égalité exacte sur le numéro normalisé, puis date et chambre, jamais le seul total d'une recherche plein texte (T5), et seulement dans la fenêtre de couverture.
- Volume : ~300 à quelques centaines de fausses références. Une courbe C jusqu'à N = 8 192 (CAP-7) est impossible sur R sans une collecte bien plus large (Report, R3).
- Publication : R ne se régénère pas par graine (il dépend d'un instantané Judilibre et d'une collecte figée). Avec `r_republish = true`, le jeu R (métadonnées seules) va en asset de release avec son manifeste et sa date d'extraction, pour que tout tiers puisse réévaluer (Success signal).
- Normaliseur : liste blanche de champs ; refuser `text`, `zones`, `text_highlight` et les noms de parties.

## Incertitudes

- Authentification (KeyId ou OAuth), URL du jeton, quotas et plafond réel de `/scan` : à confirmer par T1 à T8.
- Version des CGU Judilibre : celle lue date du 6 janvier 2022 (PDF « V8 » hébergé par PISTE) ; une version plus récente peut exister. Les CGU de PISTE (AIFE) n'ont pas été lues.
- Textes du COJ, du CJA et du CRPA cités d'après les CGU, pas relus sur Légifrance dans leur version consolidée au 2026-11-05.
- Conditions de réutilisation d'ArianeWeb non relues (il n'est pas proposé comme source de données).
- Couverture exacte de Judilibre par juridiction et période : d'après le miroir HF (mars 2025) et la presse, à remesurer par `/stats`.
- Licences des sorties des SLM : non relues modèle par modèle.
- Rendement de la collecte (taux de refus, références par réponse, part de références existantes) : estimation, non mesurée.

## Report

Corrections de spec proposées, sans modification des fichiers de spec :

- **R1 — `jeux-de-donnees.md`, section R.** Préciser : sources Conseil d'État (`opendata.justice-administrative.fr` et JADE), miroir HF `antoinejeannot/jurisprudence` en repli figé ; champs gardés (métadonnées seules, ni texte ni nom) ; fenêtre de couverture et classe « non vérifiable » exclue ; tirage stratifié des vraies sur la distribution des fausses.
- **R2 — AD-18.** L'exclusion de `data/` « que les graines suffisent à régénérer » ne vaut pas pour R. Ajouter le jeu R (métadonnées, étiquettes, sources, manifeste daté) aux assets de release quand `r_republish = true`, et l'attribution de la section 2 dans `NOTICE`. Valeur à écrire dans `config/publish.toml` : `r_republish = true`.
- **R3 — CAP-7 sur R.** Une courbe C jusqu'à N = 8 192 suppose des milliers de fausses références réelles. Proposer : sur R, C jusqu'au N disponible, ou entraînement sur S et évaluation sur R (robustesse hors distribution, déjà une mesure de CAP-12), ou une collecte élargie décidée en 1-12.
- **R4 — Porte des 30 % (`methodes-et-lots.md`).** Fixer avant 1-12 : unité (référence normalisée dédupliquée), règle de décision (estimation ponctuelle, ou borne de l'intervalle de Wilson), traitement des « non vérifiables ».
- **R5 — Contrainte « pas d'Ollama ni de GPU ».** Préciser que la collecte d'hallucinations tourne hors du projet (dans `slm-quality-bench` ou un script unique sur la tour) et que le projet ne lit qu'un fichier figé avec son sha256. Ajouter à `invoke_dev_with` de 1-12 : collecte préalable, ressource Ollama d'Anaël.
- **R6 — Secrets.** Ajouter `JUDILIBRE_KEY_ID` (ou `PISTE_CLIENT_ID` et `PISTE_CLIENT_SECRET`) à la convention de configuration du spine. La clé PISTE n'a pas de préfixe repérable : `nnww publish` devrait aussi refuser une archive contenant la valeur de toute variable de secret connue.
- **R7 — CAP-11.** « Vérifiée absente de Judilibre » ne couvre pas les références du Conseil d'État : écrire « vérifiée absente de Judilibre ou des bases de la justice administrative, dans leur fenêtre de couverture ».
- **R8 — `docs/SOURCES.md`, § 6.** Ajouter la source Conseil d'État, le miroir HF et la licence (Licence Ouverte 2.0 et CGU), et retirer la ligne « À vérifier pendant le cadrage » une fois ce constat fusionné.

## Sources (consultées le 2026-11-05)

- Cour de cassation, CGU « pour la réutilisation des données issues des décisions de justice de l'ordre judiciaire diffusées en open data », version du 6 janvier 2022 : <https://piste.gouv.fr/images/cgu/CGU_open_data_V8.pdf>
- Licence Ouverte / Open Licence 2.0, Etalab : <https://www.etalab.gouv.fr/licence-ouverte-open-licence>
- Dépôt `judilibre-search` de la Cour de cassation (README, URL, KeyId, licence) : <https://github.com/Cour-de-cassation/judilibre-search>
- Spécification OpenAPI de Judilibre : <https://raw.githubusercontent.com/Cour-de-cassation/judilibre-search/master/public/JUDILIBRE-public.json>
- Portail PISTE : <https://piste.gouv.fr>
- `pyjudilibre`, documentation et procédure PISTE : <https://pyjudilibre.readthedocs.io/en/latest/>, <https://pyjudilibre.readthedocs.io/en/latest/piste-set-up/>
- Miroir Judilibre sur Hugging Face, v2025.03.20 : <https://huggingface.co/datasets/antoinejeannot/jurisprudence>
- Conseil d'État, page « Données ouvertes » : <https://www.conseil-etat.fr/decisions-de-justice/donnees-ouvertes-open-data>
- Open data de la justice administrative, accueil, CGU (18 janvier 2022) et aide (champs XML) : <https://opendata.justice-administrative.fr/>, <https://opendata.justice-administrative.fr/cgu.html>, <https://opendata.justice-administrative.fr/aide.html>
- JADE, fiche data.gouv.fr : <https://www.data.gouv.fr/datasets/jade/> ; téléchargement : <https://echanges.dila.gouv.fr/OPENDATA/>
- Calendrier de l'open data judiciaire (cours d'appel au 15 avril 2022) : <https://www.lexisveille.fr/open-data-des-decisions-de-cours-dappel-cest-parti>, <https://www.actu-juridique.fr/breves/juridictions/open-data-des-decisions-de-justice-ouverture-a-lensemble-des-juridictions-de-lordre-judiciaire/>
- Clients tiers montrant l'URL du jeton OAuth PISTE : <https://pylegifrance.github.io/pylegifrance/en/concepts/piste-oauth/>
- Dépôt voisin `slm-quality-bench`, lu localement sur le commit `f6e77e5` : `README.md`, `slm_quality_bench/questions/schema.py`, `slm_quality_bench/models.yaml`, `slm_quality_bench/ollama/client.py`, `slm_quality_bench/campaigns/`, `data/quality_bench/campaigns/*/generation.jsonl`, `data/quality_bench/private/`.
