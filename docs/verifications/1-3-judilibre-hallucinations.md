# Constat 1-3 : Judilibre, Conseil d'État et collecte des hallucinations

Date : 2026-11-05, complété le 2026-11-06. Périmètre : accès à l'API Judilibre par PISTE, licence de réutilisation, source équivalente pour le Conseil d'État, collecte d'hallucinations de SLM par `slm-quality-bench` (CAP-1, pour CAP-10 et CAP-11). Le compte PISTE d'Anaël est ouvert : T1 à T8 ont été joués le 2026-11-06 (section 1, « Résultats T1-T8 »).

## Verdict : feu vert avec réserve (vocabulaire de CAP-1)

Au sens de CAP-1 : **feu vert avec réserve** pour les quatre points, aucun blocage relevé. Le point 1 (accès Judilibre) a son verdict depuis T1-T8 : l'API répond en production par l'en-tête `KeyId`, `/scan` n'a pas de plafond total observé jusqu'au rang ~12 900 (non testé au-delà). La réserve d'ensemble porte sur l'API en bêta, sur les quotas lus dans un en-tête de réponse et non dans l'interface PISTE, sur la condition 5 de `r_republish` (une confirmation d'Anaël) et sur le rendement non mesuré de la collecte (point 4). Le miroir Hugging Face reste un repli, inutile tant que le compte répond.

| Point | Verdict partiel | En bref |
|---|---|---|
| 1. Accès Judilibre (PISTE) | feu vert avec réserve | Production : `KeyId` et OAuth `client_credentials` acceptés (HTTP 200) ; référence Perruche retrouvée, numéro inventé absent ; `/scan` par lots de 1 000 au plus, sans plafond total observé ; quota lu dans l'en-tête `x-rate-limit` (1 000 000 requêtes par jour, déduit). Bac à sable inaccessible avec l'application actuelle (production seule), sans effet sur le projet. API en bêta. |
| 2. Licence Judilibre | feu vert avec réserve | Licence Ouverte 2.0 complétée par les CGU de la Cour de cassation (6 janvier 2022). Republier des références (sans texte ni nom) est permis, avec attribution, date de mise à jour et sans altération. Aucun usage prévu ne touche à l'identité des magistrats. |
| 3. Conseil d'État | feu vert avec réserve | `opendata.justice-administrative.fr` (XML, Licence Ouverte 2.0, CGU du 18 janvier 2022), depuis le 30 septembre 2021 ; JADE (DILA, Licence Ouverte) pour les décisions plus anciennes publiées au Lebon ; ArianeWeb seulement pour des vérifications à la main. Pas de compte requis. |
| 4. Hallucinations via `slm-quality-bench` | feu vert avec réserve | Le dépôt ne contient **aucune** fausse référence juridique (0 sur 14 campagnes, 243 Mo de générations). Il fournit l'infrastructure (client Ollama déterministe, ~35 SLM catalogués) mais pas de jeu de questions juridiques : une collecte dédiée est à écrire et à lancer sur la tour, avec Ollama (ressource d'Anaël). |

**`r_republish` : `true` recommandé, sous les conditions 1 à 5 de la section 2.** La condition 5 (version des CGU relevée au compte PISTE, T8) n'est **pas remplie au sens strict** : l'API n'expose pas la version des CGU acceptée, et l'écran « Acceptation des CGU des APIs » n'est visible qu'avec le compte d'Anaël. Un indice public, qui n'est pas une preuve : le PDF des CGU hébergé par PISTE, relu le 2026-11-06, porte toujours « Version du 6 janvier 2022 » (V8) ; son `Last-Modified` du 2026-11-04 montre que le fichier a été republié récemment sans changer de version, mais ne dit pas quelle version le compte d'Anaël a acceptée. Il reste à Anaël de confirmer que c'est bien cette version qu'affiche son compte ; écrire `true` dans `config/publish.toml` seulement après cette confirmation, et au plus tard avant la première publication d'un artefact de R (1-14). Les artefacts de R peuvent aller dans une release publique : la Licence Ouverte 2.0 permet de « communiquer, diffuser, redistribuer, publier » l'information, y compris à titre commercial (CGU Judilibre, § V), sous réserve de mentionner la source et la date de dernière mise à jour, de ne pas altérer les données et de respecter la loi Informatique et libertés. R ne garde que des métadonnées de référence (juridiction, chambre ou formation, siège, date, numéro, ECLI), sans texte ni nom de partie ou de magistrat. Avec `false`, `nnww publish` refuserait toute archive contenant les journaux des séances sur R (AD-18) et le lot 1 ne pourrait pas publier ces séances. Si les CGU affichées à l'ouverture du compte PISTE diffèrent de la version du 6 janvier 2022, relire les § V, VI et XIII avant de confirmer.

## 1. Accès à l'API Judilibre par PISTE

**Verdict partiel : feu vert avec réserve** (T1-T8 joués le 2026-11-06, détail en fin de section). Réserves : API en bêta, sans garantie (CGU, § XI.A et XI.D) ; quotas déduits de l'en-tête `x-rate-limit`, pas encore relus dans PISTE ; `/scan` filtre par défaut sur la date de mise à jour (`date_type=creation` pour filtrer sur la date de décision) et renvoie `text` et `zones`, que le normaliseur doit écarter avant toute écriture ; ECLI absent sur des décisions anciennes ; bac à sable non accessible avec l'application actuelle.

### Inscription et clés

D'après les CGU Judilibre (§ XI.B) et la documentation de `pyjudilibre` :

1. Créer un compte nominatif sur PISTE (`piste.gouv.fr`, menu d'inscription) : nom, courriel, mot de passe, acceptation des CGU de PISTE, puis lien de validation reçu par courriel.
2. Dans « APIs > Acceptation des CGU des APIs », cocher **JUDILIBRE** pour les environnements **PROD** et **SANDBOX**, puis valider. C'est cette acceptation qui vaut acceptation des CGU Judilibre et de la Licence Ouverte 2.0 (CGU, § II.C).
3. Créer une application (« Applications > Créer une application » ; nom libre).
4. Modifier l'application, sélectionner **JUDILIBRE** dans le tableau du bas, appliquer.
5. Relever l'**API Key** (onglet principal de l'application) et, si besoin, l'identifiant et le secret OAuth.

**Authentification : deux sources officielles divergent.** La spécification OpenAPI publiée par la Cour de cassation déclare un schéma `apiKey` dans l'en-tête `KeyId` ; les CGU (§ XI.C) écrivent que l'accès se fait « après authentification par le protocole Oauth 2.0 lors de chaque requête ». PISTE propose les deux. Le test ci-dessous essaie d'abord `KeyId`, puis OAuth (`client_credentials` sur `https://oauth.piste.gouv.fr/api/oauth/token`, ou `https://sandbox-oauth.piste.gouv.fr/api/oauth/token` en bac à sable, d'après des clients tiers). **Tranché par T1-T2 (2026-11-06) :** en production, les deux modes sont acceptés (HTTP 200) ; qu'ils décomptent le même quota est une hypothèse, non mesurée (`x-rate-limit` n'a été relevé qu'en `KeyId`) ; l'URL du jeton de production est confirmée (jeton valable 3 600 s, `scope` renvoyé `openid resource.READ`). Mode retenu pour le projet : **`KeyId`** (`JUDILIBRE_KEY_ID` seul, sans jeton à renouveler) ; OAuth reste un repli.

Les clés sont « strictement réservées à [l']application » et ne doivent jamais être rendues publiques (CGU, § XI.C) ; en cas de fuite, les réinitialiser sur PISTE et prévenir la Cour de cassation ou l'AIFE (§ XI.E). Elles vont en variable d'environnement seulement, comme les autres secrets du projet (spine, conventions de configuration).

### Endpoints utiles pour obtenir de vraies références

Bases : `https://api.piste.gouv.fr/cassation/judilibre/v1.0` (production) et `https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0` (bac à sable). L'API est en **version bêta** : ni disponibilité, ni complétude, ni fraîcheur garanties (CGU, § XI.A et XI.D).

| Endpoint | Usage pour R | Limites documentées (OpenAPI) |
|---|---|---|
| `GET /scan` | Extraction en masse des références d'une juridiction, d'une chambre, d'une période (`jurisdiction`, `chamber`, `date_start`, `date_end`, `date_type`, `publication`…), curseur `searchAfter` (repris tel quel de `next_batch`). | `batch_size` ≤ 1 000 (1 001 refusé, HTTP 400) ; la description évoque un total de 1 000 résultats « pour les connexions non authentifiées » : avec compte, aucun plafond total observé jusqu'au rang ~12 900 (T7). Sans `date_type=creation`, la période porte sur `update_date`. Chaque décision arrive avec `text` et `zones` (~18 Mo par lot de 1 000). |
| `GET /export` | Ancienne extraction par lots (`batch`). | Marqué `deprecated` ; `batch_size` ≤ 1 000. |
| `GET /search` | Vérifier une référence : le texte de `query` porte aussi sur le numéro de pourvoi. Filtres `jurisdiction`, `chamber`, `date_start`, `date_end`. | `page_size` ≤ 50 ; 10 000 résultats au plus par requête. Pas de filtre dédié au numéro ni à l'ECLI. |
| `GET /decision?id=…` | Fiche complète d'une décision. | Renvoie aussi le texte intégral : à ne pas conserver (section 2). |
| `GET /taxonomy?id=chamber&context_value=cc` | Valeurs admises des chambres, formations, juridictions (`cc`, `ca`, `tj`, `tcom`…). | — |
| `GET /stats` | Couverture par juridiction et par période. | — |
| `GET /transactionalhistory?date=…` | Créations, mises à jour et suppressions depuis une date (tenue à jour). | `page_size` ≤ 500. |
| `GET /healthcheck` | Test de connexion. | — |

Champs d'une décision utiles au normaliseur : `jurisdiction`, `chamber`, `formation`, `location` (siège, pour les cours d'appel), `decision_date`, `number` et `numbers` (numéros de pourvoi, forme `99-13.701`), `ecli`, `publication`, `type`, `solution`, `update_date`. Ils figurent dans le schéma OpenAPI et, à l'identique, dans le miroir Hugging Face (34 colonnes).

### Quotas

Non publiés. Les CGU (§ XI.D) prévoient des limites par seconde, minute ou jour, en nombre de requêtes ou en bande passante, par application ou par méthode, consultables dans PISTE : « API Sélectionnées > Actions > Consulter les quotas ». Le dépôt `judilibre-search` annonce qu'ils « seront prochainement sur le portail PISTE ». **Relevé par T8 (2026-11-06)** : chaque réponse de production porte un en-tête `x-rate-limit` à deux compteurs, `{"window":70350,"type":"throttle","remaining":999983}` et `{"window":0,"type":"throttle","remaining":19}`, relevé en `KeyId` au dernier des 18 appels de production du jour. Lecture déduite, non documentée : **1 000 000 requêtes par jour** par application (1 000 000 − 999 983 = 17 décomptés pour 18 appels : l'écart d'un appel n'est pas expliqué, appel en cours non décompté ou appel OAuth sur un autre compteur ; `window` = secondes restantes jusqu'à 00:00 UTC, relevé à 04:27 UTC) et **environ 20 requêtes par seconde**. Que `KeyId` et OAuth décomptent le même compteur reste une hypothèse, non mesurée. À confirmer par Anaël dans « Consulter les quotas » ; d'ici là, le client du projet lit `x-rate-limit` et reste sous 10 requêtes par seconde.

### Couverture

Mesurée par `/stats` le 2026-11-06 (T6) : Cour de cassation **569 921 décisions**, du 1860-08-01 au 2026-11-04 ; cours d'appel **649 831**, jusqu'au 2026-10-29 (date minimale renvoyée « 0201-02-24 », une date aberrante de la base : le fonds réel commence en 1996 d'après le miroir) ; tribunaux judiciaires **771 922**, du 2023-12-14 au 2026-11-04. `/stats` sans paramètre renvoie les chiffres de la Cour de cassation. Pour mémoire, miroir HF : 553 075 décisions de la Cour de cassation au 2025-03-19. Cours d'appel : chambres civiles, sociales et commerciales, systématiquement depuis le 15 avril 2022, avec un fonds antérieur partiel. Pas de décisions pénales des cours d'appel avant leur ouverture prévue (date reportée selon la presse juridique). Judilibre ne couvre **pas** la justice administrative.

### Repli sans compte : miroir Hugging Face

Depuis T1-T8, le miroir n'est plus nécessaire ; il reste documenté comme repli si l'accès PISTE tombe. `antoinejeannot/jurisprudence` republie Judilibre sous `etalab-2.0` (Parquet et JSONL, une configuration par juridiction : Cour de cassation 1,7 Go, cours d'appel 2,9 Go, tribunaux judiciaires 0,8 Go), mêmes champs que l'API. Dernière version : **v2025.03.20**, plus mise à jour depuis. Il suffit pour préparer le normaliseur et un premier tirage de vraies références antérieures au 2025-03-19 ; il ne suffit pas pour vérifier l'absence d'une référence datée d'après. Une release bâtie sur le miroir dit que ses vraies références en viennent, avec sa date de dernière mise à jour (2025-03-20) : c'est la date que l'attribution exige (section 2, condition 2), la tenue à jour à 72 h n'étant qu'une recommandation. Lire seulement les colonnes de métadonnées (projection Parquet), jamais `text`.

### Procédure de test (jouée le 2026-11-06)

Variables d'environnement (jamais commitées ; dans `.env` à la racine du dépôt principal, ignoré par git) : `JUDILIBRE_KEY_ID` pour l'API Key ; `PISTE_CLIENT_ID` et `PISTE_CLIENT_SECRET` pour OAuth. Commandes Git Bash, bac à sable d'abord, puis production en remplaçant la base (et l'URL du jeton par `https://oauth.piste.gouv.fr/api/oauth/token`). Les secrets passent par l'entrée standard de `curl` (`-K -`, `--data @-`) et non par ses arguments, visibles dans la liste des processus ; jamais `curl -v` ni `set -x`, qui afficheraient les en-têtes envoyés. Les réponses ne sont lues que pour leurs codes et leurs champs de métadonnées :

```bash
# Bac à sable ; en production : BASE=https://api.piste.gouv.fr/cassation/judilibre/v1.0
BASE=https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0
TMP=$(mktemp -d)  # réponses lourdes de T7 ; rm -rf "$TMP" à la fin
# j : appel avec l'en-tête KeyId lu sur l'entrée standard
j() { printf 'header = "KeyId: %s"\n' "$JUDILIBRE_KEY_ID" | curl -s -K - "$@"; }

# T1 — connexion par KeyId : attendu HTTP 200
j -o /dev/null -w "%{http_code}\n" "$BASE/healthcheck"

# T2 — si T1 renvoie 401/403 : OAuth client_credentials, puis même appel avec le jeton.
#      URL du jeton en bac à sable relevée chez des clients tiers, non confirmée par une
#      source officielle : la vérifier dans PISTE avant l'appel.
TOKEN=$(printf 'grant_type=client_credentials&client_id=%s&client_secret=%s&scope=openid' \
    "$PISTE_CLIENT_ID" "$PISTE_CLIENT_SECRET" \
  | curl -s -X POST --data @- https://sandbox-oauth.piste.gouv.fr/api/oauth/token \
  | sed -nE 's/.*"access_token":"([^"]+)".*/\1/p')
if [ -z "$TOKEN" ]; then
  echo "T2 : pas de jeton (identifiants, URL ou scope) ; ne pas poursuivre"
else
  printf 'header = "Authorization: Bearer %s"\n' "$TOKEN" \
    | curl -s -K - -o /dev/null -w "%{http_code}\n" "$BASE/healthcheck"
fi
# Si seul T2 passe, remplacer l'en-tête de j par celui du jeton pour T3 à T7.

# T3 — chambres de la Cour de cassation
j "$BASE/taxonomy?id=chamber&context_value=cc"

# T4 — référence connue (Perruche, Ass. plén., 17 nov. 2000, n° 99-13.701, à confirmer) :
#      attendu jurisdiction=cc, decision_date=2000-11-17, number=99-13.701
j "$BASE/search?query=99-13.701&jurisdiction=cc&page_size=5"

# T5 — numéro inventé : vérifier qu'aucun résultat n'a ce numéro exact dans number/numbers
#      (la recherche plein texte peut renvoyer des résultats approchés : la vérification
#       d'absence compare les champs, pas le total)
j "$BASE/search?query=99-99.999&jurisdiction=cc&page_size=5"

# T6 — couverture
j "$BASE/stats?jurisdiction=cc"

# T7 — extraction en masse : plafond réel avec compte (1 000 au total ?). Réponse lourde
#      (texte intégral) : l'écrire dans un fichier temporaire, n'en lire que total,
#      next_batch et les champs de métadonnées, puis le supprimer. Page suivante :
#      j "$BASE/scan?<next_batch>" ; date_type=creation pour filtrer sur decision_date.
j -o "$TMP/scan.json" "$BASE/scan?jurisdiction=cc&date_start=2019-01-01&date_end=2019-12-31&batch_size=1000"
j -o /dev/null -w "%{http_code}\n" "$BASE/scan?jurisdiction=cc&date_start=2019-03-01&date_end=2019-03-01&batch_size=1001"

# T8 — quotas exposés par la réponse (en-têtes reçus, sans secret)
j -D - -o /dev/null "$BASE/healthcheck" | grep -i '^x-rate-limit'
```

T8 prévoyait aussi de relever dans PISTE les quotas (« Consulter les quotas ») et la version des CGU Judilibre affichée : ces deux relevés demandent l'interface du compte et restent à Anaël. Les codes HTTP, le mode d'authentification, le plafond de `/scan` et l'en-tête de quotas sont consignés ci-dessous, et le point 1 a reçu son verdict au sens de CAP-1. Aucun en-tête envoyé ni jeton n'a été collé dans le constat ou un journal (le journal masque les en-têtes d'authentification, AD-18).

### Résultats T1-T8 (2026-11-06, de 05:25 à 05:28, heure de Paris)

7 requêtes au bac à sable ; 18 appels à l'API de production et 3 demandes de jeton, dont 2 lots `/scan` de 1 000 et 3 petits lots (~36 Mo reçus, lus pour leurs métadonnées puis supprimés). Aucune valeur d'identifiant, aucun jeton ni en-tête envoyé n'a été affiché ni écrit.

**Bac à sable** (`https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0`, jeton `https://sandbox-oauth.piste.gouv.fr/api/oauth/token`) : **non accessible**, T3 à T7 non joués.

| Test | Résultat |
|---|---|
| T1 `KeyId`, `/healthcheck` | HTTP 400, corps vide ; `www-authenticate` : `error="invalid_request"`, « Unable to find token in the message ». Même réponse sans aucune authentification. |
| T2 OAuth, jeton | HTTP 400 `invalid_client` (identifiants dans le corps), puis HTTP 401 `invalid_client` (authentification Basic) : client inconnu du bac à sable. `/healthcheck` sans jeton : HTTP 400. |
| Cause probable | L'application PISTE d'Anaël est une application de **production** ; PISTE sépare les applications par environnement, et le bac à sable demanderait une application créée en sandbox, abonnée à JUDILIBRE. Arrêt après deux essais raisonnés, comme prévu. Sans effet sur le projet, qui n'a besoin que de la production. |

**Production** (`https://api.piste.gouv.fr/cassation/judilibre/v1.0`, jeton `https://oauth.piste.gouv.fr/api/oauth/token`) : **accessible**, authentification retenue `KeyId`.

| Test | Résultat |
|---|---|
| T1 `KeyId`, `/healthcheck` | HTTP 200, `{"status":"disponible"}`. |
| T2 OAuth `client_credentials` | Jeton HTTP 200 (`token_type`, `expires_in` 3 600, `scope` `openid resource.READ`) ; `/healthcheck` avec le jeton : HTTP 200. |
| T3 `/taxonomy?id=chamber&context_value=cc` | HTTP 200 ; 12 valeurs : `pl` (Assemblée plénière), `mi` (Chambre mixte), `civ1`, `civ2`, `civ3`, `comm` (Chambre commerciale financière et économique), `soc`, `cr` (Chambre criminelle), `creun` (Chambres réunies), `ordo` (Première présidence, ordonnance), `allciv` (Toutes les chambres civiles), `other`. |
| T4 `/search?query=99-13.701` | HTTP 200, `total` 1, `relaxed` false : `jurisdiction` cc, `chamber` pl, `decision_date` 2000-11-17, `number` et `numbers` 99-13.701, `publication` b, `type` arret, `solution` cassation (id `60793b359ba5988459c3c363`). **Référence Perruche confirmée.** `/decision` sur cet id (HTTP 200) : `ecli` vide, `source` dila, `update_date` 2000-11-17. |
| T5 `/search?query=99-99.999` | HTTP 200, `total` 0, `relaxed` true (l'API a assoupli la requête et ne trouve toujours rien) : aucun résultat dont `number` ou `numbers` égale 99-99.999. **Numéro inventé absent.** La vérification d'absence reste une égalité exacte sur le numéro normalisé : une requête assouplie peut renvoyer des résultats approchés. |
| T6 `/stats` | HTTP 200 pour `cc`, `ca`, `tj` et sans paramètre (chiffres en « Couverture »). |
| T7 `/scan` | HTTP 200. Cour de cassation, 2019 : `total` 3 768 sur `update_date` (filtre par défaut, lu dans `searchQuery`), 13 521 avec `date_type=creation` (filtre sur `decision_date`). Lots 1 et 2 de 1 000 sans recouvrement : le plafond de 1 000 au total ne s'applique pas avec compte. Curseur posé au rang ~12 900 (décisions d'avant le 2019-01-20, `date_type=creation`) : 10 résultats et un `next_batch`, donc pas de plafond à 10 000 non plus. `batch_size=1001` : HTTP 400, « must be an integer between 1 and 1000 ». Tri `_score`, `decision_date`, `_id` décroissants. `ecli` rempli pour 1 000 décisions sur 1 000 du premier lot de 2019 ; chaque décision porte aussi `text`, `zones`, `visa`, `rapprochements`, `timeline`. **Plafond réel : 1 000 par lot, aucun plafond total observé.** |
| T8 quotas et CGU | Quotas : en-tête `x-rate-limit` (section « Quotas ») ; aucun endpoint de quotas dans l'API. Version des CGU : **non exposée par l'API**. Le PDF public hébergé par PISTE (`CGU_open_data_V8.pdf`, `Last-Modified` 2026-11-04, sha256 `73f99f81…a713554`) porte « Version du 6 janvier 2022 » ; `CGU_open_data_V9.pdf` et `V10` : HTTP 404. **À relever par Anaël** dans PISTE : « Consulter les quotas » et la version des CGU Judilibre acceptée. |

## 2. Licence de réutilisation des données Judilibre

**Verdict partiel : feu vert avec réserve.**

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
2. Attribution dans `NOTICE` et les notes de release, prête à copier : « Vraies références : base Open Data Judilibre de la Cour de cassation, Licence Ouverte 2.0 (https://www.etalab.gouv.fr/licence-ouverte-open-licence), extraction du AAAA-MM-JJ [si le jeu vient du miroir : « par le miroir Hugging Face antoinejeannot/jurisprudence, version v2025.03.20, dernière mise à jour le 2025-03-20 »] ; données Conseil d'État : base Open Data du Conseil d'État (opendata.justice-administrative.fr) et JADE (DILA), Licence Ouverte 2.0. Fausses références : générées par des SLM, ne correspondent à aucune décision. »
3. Chaque ligne porte sa classe et sa source (`judilibre`, `ce-opendata`, `jade`, `slm:<tag>`) ; aucune fausse référence n'est attribuée à une base publique.
4. Les vraies références ne sont pas modifiées (pas de fausse référence fabriquée par retouche d'une vraie : elles viennent toutes des SLM).
5. Version des CGU relevée à l'ouverture du compte PISTE (T8) ; si elle a changé, relire les § V, VI et XIII avant de publier. **État au 2026-11-06 : non remplie au sens strict.** L'API n'expose pas la version acceptée ; le PDF public de PISTE porte toujours la version du 6 janvier 2022 (T8). Remplie dès qu'Anaël confirme que son compte affiche cette version. **État au 2026-11-07 : remplie.** Anaël a confirmé dans son compte PISTE l'acceptation en production de `CGU_open_data_V8.pdf` (version du 6 janvier 2022), la version relue ici ; `r_republish = true` écrit dans `config/publish.toml`. Quotas de l'interface PISTE non relevés (non bloquant : lecture par `x-rate-limit`).

Le miroir Hugging Face, qui republie depuis 2024 le texte intégral de plus d'un million de décisions sous `etalab-2.0`, montre que cette lecture de la licence est courante ; ce n'est pas une preuve de conformité.

## 3. Source équivalente pour le Conseil d'État

**Verdict partiel : feu vert avec réserve.**

| Source | Accès | Couverture | Format | Licence |
|---|---|---|---|---|
| Open data de la justice administrative, `opendata.justice-administrative.fr` | Libre, sans compte ni API : moteur de recherche et archives zip par juridiction, année et mois | Conseil d'État depuis le 30 septembre 2021 (en ligne le lendemain, du mardi au samedi) ; CAA depuis le 31 mars 2022 ; TA depuis le 30 juin 2022 | XML. Champs : `Numero_Dossier`, `Date_Lecture`, `Numero_ECLI`, `Formation_Jugement`, `Code_Juridiction` (`CE`), `Nom_Juridiction`, `Code_Publication` (A Lebon, B tables, C, D, Z), `Type_Decision`, `Date_Mise_Jour`, `Texte_Integral`… | Licence Ouverte 2.0 et CGU du 18 janvier 2022 |
| JADE (DILA), `echanges.dila.gouv.fr/OPENDATA/` | Libre (HTTPS ou FTPS) | Conseil d'État : décisions publiées au Lebon depuis 1965 ; CAA depuis 1989 ; Tribunal des conflits | XML | Licence Ouverte |
| ArianeWeb (`conseil-etat.fr`) | Moteur de recherche web, sans API ni téléchargement en masse | Plus de 270 000 décisions du CE et des CAA, dont celles d'avant le 30 septembre 2021 | Pages web | Conditions non relues |

Les CGU du Conseil d'État reprennent celles de la Cour de cassation : Licence Ouverte 2.0 (§ II.C et XIII) ; mention de la source et de la date de dernière mise à jour, précisée comme « uniquement celle à laquelle le réutilisateur aura chargé la décision » ; numéro, juridiction, formation, siège et date conservés avec chaque décision (§ V) ; interdiction du profilage des magistrats et greffiers (CJA art. L. 10, mêmes peines du code pénal, § VI) ; occultation « socle » des noms (§ IX). Les conditions de `r_republish = true` de la section 2 valent à l'identique.

Réserves : pas d'API, donc vérification d'absence sur un index local construit depuis les archives mensuelles (et JADE pour l'historique) ; les décisions du CE non publiées au Lebon et antérieures au 30 septembre 2021 ne sont dans aucune base téléchargeable, donc une référence de cette période n'est vérifiable que si elle est au Lebon (sinon : « non vérifiable », exclue). Format d'une référence : `CE, 10 juillet 2020, n° 428409`, ECLI de forme `ECLI:FR:CECHR:2020:428409.20200710`. Le CE ne passe pas par PISTE pour ces sources ; l'API Légifrance (sur PISTE) couvre aussi JADE, mais n'est pas nécessaire.

## 4. Collecte d'hallucinations via `slm-quality-bench`

**Verdict partiel : feu vert avec réserve** — faisable sur le papier, rien n'existe encore. Réserves : le rendement (point 3 ci-dessous) est estimé, non mesuré ; la collecte dépend d'Ollama et du GPU de la tour d'Anaël ; aucune story de `stories.yaml` ne porte le code de collecte (Report, R9). Les ~300 hallucinations ne sont acquises qu'après un lot pilote (par exemple 10 requêtes × 3 modèles) qui mesure le rendement réel.

### Ce que le dépôt contient

Relevé en lecture seule sur `f6e77e5` (2026-11-05) :

- **Aucune fausse référence juridique.** Sur les 14 campagnes de `data/quality_bench/campaigns/` (243 Mo de `generation.jsonl`), zéro occurrence de « Cour de cassation », « Conseil d'État », « Cass. », « ECLI » ; les 24 « pourvoi » et 21 motifs `NN-NN.NNN` sont des mots de listes et des coordonnées géométriques.
- Les sept usages du banc (raisonnement, consignes, outils, extraction, RAG, abstention, rédaction) n'ont aucune question de jurisprudence. Les jeux privés ne contiennent aucune question de jurisprudence ni référence de décision.
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

- Dépend de la collecte (section 4) : story ou script de collecte, puis Ollama sur la tour, à demander à Anaël. Le compte PISTE est ouvert et répond (T1-T8).
- La classification ne demande pas de base pour les incohérentes, mais la **vérification des cohérentes** en demande une : Judilibre (API de production par `KeyId`, ou miroir HF jusqu'au 2025-03-19 en repli) et l'open data administratif.
- Grille d'incohérence fixée avant de voir les données (format, calendrier, chronologie pourvoi-décision, chambre ou formation existante, cohérence de l'ECLI, « autre »), puis rapprochée des 15 types de Nuss pour mesurer leur recouvrement.
- Intervalle : sur n = 300, l'intervalle de Wilson à 95 % fait environ ± 5 points autour de 30 %. Une part estimée entre 25 et 35 % ne tranche pas la porte sans règle fixée d'avance (Report, R4).
- Dédupliquer par référence normalisée ; garder le modèle d'origine pour vérifier qu'aucune famille ne domine.

## Conséquences pour 1-13 (jeu R)

- Vraies références : Judilibre par `/scan` (lots de 1 000, `date_type=creation` pour tirer sur la date de décision, projection des seuls champs de métadonnées avant toute écriture sur disque, puisque `text` et `zones` arrivent avec chaque décision), miroir HF en repli ; Conseil d'État par l'open data administratif et JADE. Tirage stratifié pour que juridiction, chambre et période des vraies suivent celles des fausses : sinon la date ou la juridiction trahit la classe, même après le normaliseur commun.
- Vérification d'absence (CAP-11) : égalité exacte sur le numéro normalisé, puis date et chambre, jamais le seul total d'une recherche plein texte (T5, où l'API assouplit la requête : `relaxed` true), et seulement dans la fenêtre de couverture. L'ECLI ne sert pas de clé : il manque sur des décisions anciennes (Perruche, T4).
- Quotas : rester sous ~10 requêtes par seconde et lire `x-rate-limit` ; le quota journalier déduit (1 000 000) dépasse de loin les besoins de R.
- Volume : ~300 à quelques centaines de fausses références. Une courbe C jusqu'à N = 8 192 (CAP-7) est impossible sur R sans une collecte bien plus large (Report, R3).
- Publication : R ne se régénère pas par graine (il dépend d'un instantané Judilibre et d'une collecte figée). Avec `r_republish = true`, le jeu R (métadonnées seules) va en asset de release avec son manifeste et sa date d'extraction, pour que tout tiers puisse réévaluer (Success signal).
- Normaliseur : liste blanche de champs ; refuser `text`, `zones`, `text_highlight` et les noms de parties.

## Incertitudes

- Authentification, URL du jeton de production et plafond de `/scan` : établis par T1-T8 (2026-11-06). Quotas : lecture déduite de l'en-tête `x-rate-limit`, non documentée, à confirmer dans « Consulter les quotas ». Plafond total de `/scan` : non observé jusqu'au rang ~12 900, non testé au-delà.
- Bac à sable : non testé au-delà de l'authentification (application de production seule) ; son comportement n'est pas connu.
- Version des CGU Judilibre : celle lue date du 6 janvier 2022 (PDF « V8 » hébergé par PISTE, toujours servi le 2026-11-06) ; la version affichée dans le compte d'Anaël n'est pas relevée. Les CGU de PISTE (AIFE) n'ont pas été lues.
- Textes du COJ, du CJA et du CRPA cités d'après les CGU, pas relus sur Légifrance dans leur version consolidée au 2026-11-05.
- Conditions de réutilisation d'ArianeWeb non relues (il n'est pas proposé comme source de données).
- Couverture de Judilibre : totaux et bornes mesurés par `/stats` (T6) ; répartition par chambre et par année non mesurée ; date minimale aberrante des cours d'appel (« 0201-02-24 »).
- Licences des sorties des SLM : non relues modèle par modèle.
- Rendement de la collecte (taux de refus, références par réponse, part de références existantes) : estimation, non mesurée ; à mesurer par le lot pilote (section 4).
- URL du jeton OAuth en bac à sable : relevée chez des clients tiers ; elle répond (`invalid_client` pour l'application de production), sans plus.

## Report

Corrections de spec proposées, sans modification des fichiers de spec :

- **R1 — `jeux-de-donnees.md`, section R.** Préciser : sources Conseil d'État (`opendata.justice-administrative.fr` et JADE), miroir HF `antoinejeannot/jurisprudence` en repli figé ; champs gardés (métadonnées seules, ni texte ni nom) ; fenêtre de couverture et classe « non vérifiable » exclue ; tirage stratifié des vraies sur la distribution des fausses ; extraction par `/scan` avec `date_type=creation` et clé de vérification sur le numéro normalisé, la date et la chambre (ECLI parfois absent, T4).
- **R2 — AD-18.** L'exclusion de `data/` « que les graines suffisent à régénérer » ne vaut pas pour R. Ajouter le jeu R (métadonnées, étiquettes, sources, manifeste daté) aux assets de release quand `r_republish = true`, et l'attribution de la section 2 dans `NOTICE`. Valeur à écrire dans `config/publish.toml` : `r_republish = true`, seulement après qu'Anaël a confirmé la version des CGU Judilibre acceptée dans son compte PISTE (condition 5 de la section 2, non remplie au 2026-11-06 malgré T8 joué).
- **R3 — CAP-7 sur R (`SPEC.md`, success de CAP-7 ; `methodes-et-lots.md`, ligne du témoin C).** Une courbe C jusqu'à N = 8 192 suppose des milliers de fausses références réelles. Proposer : sur R, C jusqu'au N disponible, ou entraînement sur S et évaluation sur R (robustesse hors distribution, déjà une mesure de CAP-12), ou une collecte élargie décidée en 1-12.
- **R4 — Porte des 30 % (`methodes-et-lots.md`).** Fixer avant 1-12 : unité (référence normalisée dédupliquée), règle de décision (estimation ponctuelle, ou borne de l'intervalle de Wilson), traitement des « non vérifiables ».
- **R5 — Contrainte « pas d'Ollama ni de GPU » (`SPEC.md`, contraintes).** Préciser que la collecte d'hallucinations tourne hors du projet (dans `slm-quality-bench` ou un script unique sur la tour) et que le projet ne lit qu'un fichier figé avec son sha256. Le volet `stories.yaml` est en R9.
- **R6 — Secrets.** Ajouter `JUDILIBRE_KEY_ID` à la convention de configuration du spine (mode retenu par T1-T2) ; `PISTE_CLIENT_ID` et `PISTE_CLIENT_SECRET` seulement pour le repli OAuth. La clé PISTE n'a pas de préfixe repérable : `nnww publish` devrait aussi refuser une archive contenant la valeur de toute variable de secret connue.
- **R7 — CAP-11 (`SPEC.md`, success de CAP-11).** « Vérifiée absente de Judilibre » ne couvre pas les références du Conseil d'État : écrire « vérifiée absente de Judilibre ou des bases de la justice administrative, dans leur fenêtre de couverture ».
- **R8 — `docs/SOURCES.md`, § 6.** Ajouter la source Conseil d'État, le miroir HF et la licence (Licence Ouverte 2.0 et CGU), et retirer la ligne « À vérifier pendant le cadrage » une fois ce constat fusionné.
- **R9 — `stories.yaml`, entrée 1-12.** 1-12 dépend d'une collecte que rien ne porte encore. Ajouter une story de collecte placée avant 1-12 (commande `collect` dans `slm-quality-bench`, ou script unique sur la tour), ou l'inclure dans la description de 1-12. Ajouter à `invoke_dev_with` de 1-12 : collecte préalable avec lot pilote qui mesure le rendement ; Ollama et GPU de la tour à demander à Anaël par notification, comme le compte PISTE pour 1-3 ; sortie figée avec son sha256.

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
- API Judilibre de production et bac à sable de PISTE, appels T1-T8 du 2026-11-06 (codes, champs de métadonnées et en-tête `x-rate-limit` des réponses) ; PDF des CGU relu le même jour (pdftotext, page de titre).
- Dépôt voisin `slm-quality-bench`, lu localement sur le commit `f6e77e5` : `README.md`, `slm_quality_bench/questions/schema.py`, `slm_quality_bench/models.yaml`, `slm_quality_bench/ollama/client.py`, `slm_quality_bench/campaigns/`, `data/quality_bench/campaigns/*/generation.jsonl`, `data/quality_bench/private/`.

## Revue

### Passe 1 (2026-11-05, SHA revu 39ef82d)

- Important, medium, second avis 1 : `r_republish = true` recommandé sans condition alors que la condition 5 (CGU relevées en T8) n'est pas remplie. Corrigé (recommandation conditionnelle, `true` écrit après T8 et avant toute publication de R).
- Important, medium, second avis 2 : fraîcheur du miroir HF (« exigée » en section 1, « recommandée » en section 2) et attribution à Judilibre seul si R vient du miroir. Corrigé (section 1 harmonisée, mention du miroir et de sa date dans l'attribution).
- Important, medium, second avis 3 : verdict hors vocabulaire de CAP-1 et prévision « attendu ». Corrigé (feu vert avec réserve pour les points 2 à 4, point 1 sans verdict jusqu'à T1-T8).
- Important, medium, second avis 4 : collecte jugée faisable sur un rendement estimé, dépendance Ollama, aucune story. Corrigé (réserves explicites, lot pilote de mesure, R9).
- Important, medium, second avis 5 : dépendance de 1-12 à la collecte et à Ollama. Corrigé (Report R9 sur `stories.yaml`, sans modifier le fichier).
- Nit, low, second avis 6 : secret OAuth en argument de `curl`, jeton vide envoyé si T2 échoue, URL sandbox non confirmée. Corrigé (secrets par l'entrée standard, `sed -n …p` et arrêt si jeton vide, URL marquée non confirmée ; vérifié contre un serveur local).
- Nit, low, second avis 7 : R3, R5, R7 sans fichier cible. Corrigé.
- Nit, low, second avis 8 : CJA L. 10 et COJ L. 111-13 non relus sur Légifrance. Rejeté : déjà déclaré (section 2 et Incertitudes) ; pas d'outil web dans cette revue, reste non vérifié.
- Nit, low, second avis 9 : contenu des jeux privés de `slm-quality-bench`. Corrigé (phrase réduite à l'absence de question de jurisprudence ; aucun autre contenu recopié).

### Passe 2 (2026-11-05, SHA revu 46d35fa)

- Nit, low, reviewer : R2 donnait `r_republish = true` sans la condition T8 posée en tête. Corrigé (R2 renvoie à T8).
- Aucun secret ni contenu privé de `slm-quality-bench` trouvé ; verdicts conformes au vocabulaire de CAP-1 ; aucun Important.

### T1-T8 joués (2026-11-06)

- Bac à sable : T1 HTTP 400 (`KeyId` non reconnu, jeton attendu), T2 `invalid_client` en 400 puis 401 (application de production seule) ; T3 à T7 non joués, arrêt après deux essais raisonnés.
- Production : T1 et T2 HTTP 200, `KeyId` retenu ; T3 12 chambres ; T4 Perruche confirmée (cc, pl, 2000-11-17, 99-13.701, ECLI vide) ; T5 numéro inventé absent par égalité de champ ; T6 cc 569 921, ca 649 831, tj 771 922 ; T7 1 000 par lot, aucun plafond total jusqu'au rang ~12 900, filtre par défaut sur `update_date` ; T8 quotas lus dans `x-rate-limit` (1 000 000 par jour et ~20 par seconde, déduits), version des CGU non exposée par l'API.
- Point 1 : sans verdict → **feu vert avec réserve**. Verdict d'ensemble : feu vert avec réserve, plus provisoire. Condition 5 de `r_republish` : non remplie au sens strict, en attente d'une confirmation d'Anaël ; `config/publish.toml` inchangé (décision séparée).
- Restent à Anaël : la version des CGU Judilibre et les quotas affichés dans son compte PISTE ; créer une application de bac à sable seulement si un besoin apparaît.
- Aucune valeur d'identifiant, aucun jeton ni en-tête envoyé dans le constat ; réponses lourdes de `/scan` supprimées après lecture des métadonnées.

### Passe 3 (2026-11-06, SHA revu bc1c541)

- Important, high, second avis 1 : R2 faisait écrire `r_republish = true` « après T8 » alors que T8 est joué et la condition 5 non remplie. Corrigé (`true` seulement après confirmation par Anaël de la version des CGU acceptée dans son compte).
- Important, medium, second avis 2 : « les deux modes comptent sur le même quota » affirmé sans mesure (`x-rate-limit` relevé en `KeyId` seulement). Corrigé (requalifié en hypothèse en section 1 et dans « Quotas »).
- Important, medium, second avis 3 : « la preuve publique concorde » présentait le PDF V8 comme une preuve. Corrigé (indice public ; `Last-Modified` 2026-11-04 interprété : fichier republié sans changement de version, ne dit rien du compte).
- Nit, low, second avis 4 : 17 appels décomptés contre 18 appels de production ; 12 000 contre ~12 900 rangs. Corrigé (écart d'un appel déclaré non expliqué ; ~12 900 partout).
- Nit, low, second avis 5 : consigne T8 restée à l'impératif. Corrigé (au passé, relevés d'interface laissés à Anaël).
- Nit, low, second avis 6 : mot-clé d'en-tête d'autorisation cité dans le constat. Rejeté sur le fond : `nnww publish` n'existe pas encore dans `src/` ; le seul filtre (`journal/writer.py`, `SECRET_PATTERNS`) masque les journaux, pas `docs/`, et son motif `bearer` exige un jeton de 8 caractères ou plus (`Bearer %s` ne le déclenche pas). Mention reformulée sans le motif.
- Verdicts : point 1 et ensemble en « feu vert avec réserve », cohérents avec CAP-1 ; aucun secret (recherche de chaînes longues : URL seulement).

### Passe 4 (2026-11-06, SHA revu bff83f9)

- Aucun Important. Les correctifs de la passe 3 tiennent : R2 et la condition 5 concordent avec le verdict d'ensemble et la section sur `r_republish` ; l'hypothèse « même quota » n'apparaît plus comme un fait (section 1, « Quotas ») ; le PDF V8 est un indice ; ~12 900 rangs et 18 appels / 17 décomptés cohérents dans le tableau, T7, les hypothèses et le bilan.
- Nit, low, reviewer : la ligne de la passe 3 sur le filtre de secrets citait encore le mot-clé d'autorisation. Corrigé (reformulé). Le script d'exemple de la section T1-T2 garde `Bearer %s` en gabarit, sans valeur : non secret, laissé.
- Aucun secret (recherche de chaînes longues : URL seulement).
