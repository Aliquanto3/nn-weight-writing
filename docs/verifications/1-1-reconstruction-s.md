# Constat 1-1 : reconstruction de S d'après Nuss

Story 1-1 (CAP-1, point « S d'après Nuss » de `jeux-de-donnees.md`). Recherche documentaire du 2026-11-05.

## Verdict : conforme avec écarts

Équivalent CAP-1 proposé : **feu vert avec réserve**. La décision revient à Anaël (CAP-1).

Ce que `jeux-de-donnees.md` dit de S correspond à ce qu'on peut vérifier : les trois juridictions, les trois exemples d'erreurs et les repères chiffrés (environ 97 000 paramètres, 40 exemples non annotés, 97,7 % contre 82,8 %, 4 000 et 8 192 références). Le post original n'est pas lisible sans compte LinkedIn, et aucune trace publique ne donne la liste des 15 types : **3 types sont attestés (dont un, le « 30 février », par `docs/SOURCES.md` seulement), 12 sont reconstruits**. S reste donc une reconstruction de l'esprit du jeu de Nuss, pas une copie, et ses scores ne se comparent à ceux de Nuss qu'en ordre de grandeur ; le chiffre de référence lui-même diverge selon les republications (97,7 % contre 82,8 %, ou 97,8 % contre 94,6 %, voir plus bas). Réserves à porter au rapport du lot 1 : liste des types, format, proportions et chiffre de référence non vérifiables. Ce constat ne propose pas de blocage, parce que la question du lot 1 (un LLM écrit-il de bons poids sur une tâche de cohérence de références) ne dépend pas d'une copie exacte du jeu de Nuss ; s'il retient un blocage, Anaël le consigne comme décision (CAP-1).

## Accès à la source

- **Post de Jorick Nuss** (LinkedIn, vers le 2026-11-04) : pas accessible. Son URL n'a pas été trouvée. Le profil `fr.linkedin.com/in/jorick-nuss-7725251a1` et les profils qui republient le post renvoient HTTP 999 (blocage des robots par LinkedIn). On le connaît seulement par les extraits que la recherche web donne de republications (Jérôme Ramette, Luc Legay, Simon Biffe, Alain Issarni) et par le relevé de `docs/SOURCES.md`. Le présent constat ne cite aucun contenu du post au-delà de ces extraits.
- **Fil de Jacob Lauritzen** (X, 2026-11-03) : la page renvoie HTTP 402. Le texte du message principal apparaît dans les résultats de recherche : « Got fable to hand-write weights of a 100k param model to recognize real versus fake legal citations. Basically one-shotted a full NN that's better than training it ». Une réponse ajoute que les deux approches convergent quand on entraîne plus longtemps. Le fil ne décrit aucun type d'erreur et porte sur des citations dont le droit n'est pas précisé, probablement pas français.
- **Code, données ou générateur** : rien trouvé, ni chez Nuss ni chez Lauritzen (recherches GitHub et web).
- **Ce que les traces publiques confirment** : la reproduction, par Nuss, de l'expérience de Lauritzen sur le droit français (Cour de cassation, Conseil d'État, cours d'appel) avec Claude Sonnet 5.5 ; environ 97 000 paramètres, la description de la tâche, 40 exemples non annotés et aucune descente de gradient ; 97,7 % sur 4 000 références jamais vues contre 82,8 % pour un entraînement sur 8 192 exemples annotés ; « 15 types d'erreurs » avec, parmi les exemples, un pourvoi formé après la décision et une chambre inexistante ; une règle lisible fondée sur l'écart entre l'année du pourvoi et celle de la décision ; et la réserve de l'auteur : données synthétiques, filtre de cohérence et non d'existence.

## Les 15 types

Rappel des formats (connaissance générale, à figer en 1-9) :

- Cour de cassation : chambre (1re, 2e ou 3e civile, commerciale, sociale, criminelle, chambre mixte, assemblée plénière), date, n° de pourvoi `AA-NN.NNN`, où `AA` est l'année d'enregistrement du pourvoi ;
- Conseil d'État : formation (chambre ou chambres réunies, Section, Assemblée), date, n° de requête à 6 chiffres ;
- cour d'appel : ville du siège, chambre ou pôle, date, n° RG `AA/NNNNN`.

| # | Type | Statut | Source ou justification |
|---|---|---|---|
| 1 | Pourvoi formé après la décision (année `AA` du n° de pourvoi postérieure à l'année de la décision) | **attesté** | Exemple cité par Nuss (SOURCES.md, republications Ramette et Legay). Le bloc de neurones qu'il décrit, sur l'écart entre l'année du pourvoi et celle de la décision, en est la règle. |
| 2 | Date calendaire impossible (30 février, 31 avril, 31 juin…) | **attesté**, second rang (exemple « 30 février ») | Exemple cité par Nuss d'après `docs/SOURCES.md`, relevé du post fait par Anaël (source primaire de second rang). Aucune source consultée accessible ne le confirme : les extraits de republications accessibles ne le reprennent pas mot pour mot. L'extension aux autres dates impossibles est de notre fait. |
| 3 | Chambre inexistante à la Cour de cassation (« 4e chambre civile », « 2e chambre commerciale ») | **attesté** | Exemple cité par Nuss (SOURCES.md, republications Ramette et Legay). Les exemples entre parenthèses sont les nôtres. |
| 4 | Cour d'appel inexistante (siège sans cour d'appel : « CA Lille », « CA Marseille », « CA Strasbourg ») | reconstruit | Erreur fréquente des LLM : ils confondent tribunal judiciaire et cour d'appel (Douai, Aix-en-Provence, Colmar). C'est l'analogue de 3 au niveau de la juridiction. |
| 5 | Formation incompatible avec la juridiction (« CE, 1re chambre civile », « CA Paris, assemblée plénière ») | reconstruit | Mélange des vocabulaires des deux ordres de juridiction, voisin de 3. À distinguer de 3 dans le générateur : formation qui existe ailleurs, et non formation qui n'existe nulle part. |
| 6 | Décision datée dans le futur (après la date de constitution du corpus) | reconstruit | Incohérence de date la plus simple après 2, et détectable sans base. |
| 7 | Décision antérieure à la création de la formation citée | reconstruit | Incohérence entre date et formation. Les dates de création (chambres de la Cour de cassation, chambres du CE après la réforme de 2016) sont à vérifier sur source officielle en 1-9 avant d'être codées. |
| 8 | Écart d'années invraisemblable entre pourvoi et décision (pourvoi enregistré bien trop tôt, par exemple 10 ans avant) | reconstruit | Prolonge la règle attestée en 1 : l'écart a une borne basse (0) et une borne haute (quelques années). Nuss parle d'un « écart », mais rien ne dit qu'il en fait un type distinct. |
| 9 | N° RG de cour d'appel postérieur à l'arrêt (`AA/NNNNN` avec `AA` > année de l'arrêt) | reconstruit | Analogue de 1 pour les cours d'appel. Nuss couvre les cours d'appel, mais on ne sait pas s'il a transposé ce type. |
| 10 | Numéro mal formé pour sa juridiction (pourvoi sans le motif `AA-NN.NNN`, RG sans barre, nombre de chiffres faux) | reconstruit | Erreur de forme typique d'une référence inventée. Risque : elle tient au style de surface, à doser pour ne pas rendre S trivial. |
| 11 | Numéro au format d'une autre juridiction (RG pour la Cour de cassation, pourvoi pour le CE) | reconstruit | Croisement des formats des trois juridictions retenues par Nuss. |
| 12 | Décision rendue un dimanche ou un jour férié | reconstruit | Incohérence calendaire plus fine que 2, qui demande un calcul de jour de la semaine (intéressante pour un réseau). |
| 13 | Nature de la décision incompatible avec la juridiction (« cassation » prononcée par une cour d'appel) | reconstruit | N'existe que si le format de S porte la solution. On ne sait pas si les références de Nuss la portent. |
| 14 | Recueil de publication incompatible (« Lebon » pour la Cour de cassation, « Bull. crim. » pour une chambre civile) | reconstruit | N'existe que si le format de S porte la publication. Même incertitude que 13. |
| 15 | ECLI incohérent avec la référence (année ou juridiction différente) | reconstruit | N'existe que si le format de S porte un ECLI. Même incertitude que 13. |

Bilan : 3 attestés (1 et 3 par les republications et `SOURCES.md`, 2 par `SOURCES.md` seul), 12 reconstruits. Les types 13 à 15 dépendent de champs dont on ne sait pas s'ils figurent chez Nuss. Si 1-9 retient un format sans solution, sans publication ou sans ECLI, il faut les remplacer par des types reconstruits sur les champs gardés (par exemple, pour le CE, un numéro de requête incompatible avec l'année, puisque les numéros sont croissants dans le temps).

## Écarts connus avec l'original

- **Liste des types** : 12 sur 15 sont les nôtres. La part de chaque type dans les fausses références est inconnue.
- **Taille** : seuls sont connus les 4 000 références d'évaluation, les 8 192 exemples annotés de l'entraînement témoin et les 40 exemples non annotés donnés au LLM. On ne connaît ni la taille totale du jeu, ni la façon dont les 40 exemples ont été tirés.
- **Proportions** : on ne connaît ni la part de vraies et de fausses références (en équilibre ou non), ni la répartition entre les trois juridictions. Si le jeu n'est pas équilibré, 97,7 % se lit autrement.
- **Format des références** : inconnu. On ne sait pas si la forme est abrégée (« Cass. civ. 1re ») ou développée, ni si la référence contient la solution, la publication ou l'ECLI, ni si plusieurs styles d'écriture sont mélangés.
- **Vraies références** : on ne sait pas si elles sont tirées de décisions réelles ou générées. Nuss dit seulement « données synthétiques ». Si les vraies sont réelles et les fausses générées, le style peut trahir la classe, et c'est ce risque que R corrige avec son normaliseur commun.
- **Juridictions** : les trois sont attestées. Les cours d'appel couvertes, les formations du CE et les chambres de la Cour de cassation retenues sont inconnues.
- **Métrique** : « 97,7 % de précision » veut probablement dire exactitude (*accuracy*), mais le post ne le dit pas, d'après ce qu'on en voit. Il faut mesurer les deux.
- **Chiffre divergent** : une republication (Alain Issarni) donnerait 97,8 % contre 94,6 % pour le même réseau entraîné sur 8 192 exemples, au lieu de 97,7 % contre 82,8 %. Il peut s'agir d'une version modifiée du post, d'un autre point de la courbe ou d'une erreur de recopie. Sans accès au post, on ne peut pas trancher. Le rapport du lot 1 doit le signaler.
- **Ce que le post ne dit pas** (d'après les traces accessibles) : l'architecture du réseau ; la description exacte de la tâche donnée au LLM ; si le LLM connaissait la liste des 15 types (sans doute, puisque le même auteur a conçu le générateur, ce qui est la circularité déjà relevée dans `SOURCES.md`) ; le nombre de tentatives ; le réglage de l'entraînement témoin (durée, optimiseur, encodage des entrées) ; l'existence d'un témoin à règles.

## Conséquences pour la story 1-9

1. **Générateur de S** : coder les 15 types du tableau, chacun avec son identifiant `#` et son statut (attesté ou reconstruit) dans les métadonnées du générateur, pour que le rapport puisse séparer les scores par statut. Figer d'abord le format des références : si la solution, la publication ou l'ECLI n'y figurent pas, remplacer les types 13 à 15 comme indiqué plus haut.
2. **Vérifier les faits juridiques avant de les coder** : liste des 36 cours d'appel, chambres et dates de création, formations du CE, formats de numéros. Le générateur ne doit pas fabriquer de « vraies » références fausses par erreur de connaissance.
3. **S-réservé (10 connus, 5 tenus à l'écart)** : les 3 types attestés restent dans les 10 connus, puisqu'ils sont publics et qu'une description de tâche inspirée de Nuss les citerait. Proposition, à confirmer quand 1-9 aura figé le format, pour les 5 tenus à l'écart : **4, 7, 9, 11, 12**. Ils portent sur la juridiction, la formation, la date et le numéro, présents dans toute référence des trois formats rappelés plus haut. Ils ne sont pas tous indépendants des règles connues, et c'est voulu : 9 teste le transfert de la règle 1 aux cours d'appel, 12 un calcul que les types connus n'enseignent pas. Les 10 connus comprennent 13 à 15 tant qu'ils ne sont pas remplacés (point 1). Il faut écarter des 5 tout type qui dépend d'un champ optionnel (13 à 15). Le test de 1-9 vérifie que la description de tâche de S-réservé ne nomme aucun des 5 types et n'en emploie pas le vocabulaire (« dimanche », « férié », « RG », « création »…).
4. **Proportions** : à fixer et à journaliser, faute de repère chez Nuss. Proposition : vraies et fausses à parts égales, types uniformes parmi les fausses, juridictions à parts égales. On rapporte l'exactitude et la précision.
5. **Tailles** : reprendre 4 000 références d'évaluation, 8 192 exemples annotés pour C et 40 exemples non annotés pour le paquet de l'agent, afin que les chiffres se comparent à ceux de Nuss.

## Report

Corrections proposées, non appliquées, à faire par une story ou une PR à part :

- **`jeux-de-donnees.md`, section S** : ajouter que la liste des 15 types est reconstruite, 3 attestés et 12 de notre fait, avec un renvoi à `docs/verifications/1-1-reconstruction-s.md`. Ajouter que format, proportions et métrique de Nuss sont inconnus et fixés par 1-9.
- **`jeux-de-donnees.md`, table « À vérifier au cadrage »** : marquer le point « S d'après Nuss » comme traité, avec le renvoi au constat et la décision d'Anaël (feu vert avec réserve proposé), une fois prise.
- **`docs/SOURCES.md`** : ajouter que l'URL du post n'est pas connue et que le post n'est pas lisible sans compte. Signaler le chiffre divergent (97,8 % contre 94,6 %) d'une republication. Le titre de Nuss varie selon la source (« CTO et cofondateur » sur Crunchbase, « Lead AI Engineer » sur son profil LinkedIn) : le noter ou citer la source retenue.
- **Pour Anaël** : s'il a accès au post avec son compte LinkedIn, en relever le texte exact, la date et l'URL. Le constat pourrait alors passer des types reconstruits à attestés et trancher le chiffre divergent.

## Sources consultées (2026-11-05)

| Source | URL | Résultat |
|---|---|---|
| `docs/SOURCES.md`, `jeux-de-donnees.md`, `SPEC.md` (CAP-1, CAP-9) | dépôt | Lus |
| Profil LinkedIn de Jorick Nuss | <https://fr.linkedin.com/in/jorick-nuss-7725251a1> | HTTP 999, illisible. L'extrait de recherche donne « Lead AI Engineer @ Haiku » |
| Republication, Jérôme Ramette | <https://www.linkedin.com/in/jramette/> | Extrait de recherche seulement : protocole, chiffres 97,7 / 82,8, exemples « pourvoi formé après la décision », « chambre inexistante », réserve sur les données synthétiques |
| Republication, Luc Legay | <https://www.linkedin.com/in/legay/> | HTTP 999. Extrait de recherche : mêmes chiffres et exemples, règle sur l'année du pourvoi et celle de la décision |
| Republication, Simon Biffe | <https://www.linkedin.com/in/simon-biffe-b93a58225/> | Extrait de recherche : filtre de cohérence, pas d'existence |
| Republication, Alain Issarni | <https://www.linkedin.com/in/alain-issarni/> | Extrait de recherche : 97,8 % contre 94,6 % (divergent, non vérifié) |
| Fil de Jacob Lauritzen | <https://x.com/jacsebl/status/2117606206764175543> | HTTP 402. Texte du message principal et d'une réponse par l'extrait de recherche |
| Reprise de Matt Stockton | <https://x.com/mstockton/status/2117695754278142357> | Extrait de recherche : contexte seulement |
| Fiche Crunchbase de Haiku | <https://www.crunchbase.com/organization/haiku-5135> | Extrait de recherche : Nuss, CTO et cofondateur |
| Recherches web (Nuss, Lauritzen, « 15 types d'erreurs », code GitHub) | — | Aucun code, aucune donnée, aucune liste des 15 types |

## Revue

### Passe 1 (2026-11-05, SHA revu abd8cb9)

Constats du second avis (Haiku), tranchés un par un :

- Nit, low (proposé high), second avis 1 : « 30 février » attesté par `SOURCES.md` seul. Corrigé : statut « attesté, second rang », SOURCES.md nommé source primaire de second rang, bilan détaillé. Pas une invention, d'où la sévérité abaissée.
- Important, medium, second avis 2 : verdict présenté comme acquis et « sans en faire un blocage » préjugeant la décision d'Anaël. Corrigé : verdict proposé, réserves nommées (types, format, proportions, chiffre divergent), motif de l'absence de blocage, décision renvoyée à Anaël. « Feu vert avec réserve » maintenu : S est une reconstruction déclarée.
- Rejeté, medium, second avis 3 : 4, 7, 9, 11 et 12 reposent sur juridiction, formation, date et numéro, présents dans les trois formats rappelés ; seuls 13 à 15 dépendent de champs optionnels. Précisé : proposition conditionnelle au format de 1-9.
- Rejeté, medium, second avis 4 : le remplacement de 13 à 15 si le format ne les porte pas est déjà prévu (bilan, point 1). Renvoi ajouté au point 3.
- Nit, low, second avis 5 : contradiction réelle entre « indépendants des règles connues » et 9 qui transpose 1. Corrigé : dépendance assumée.
- Nit, low, second avis 6 : la phrase était juste (Nuss reproduit Lauritzen) mais ambiguë. Corrigé : « par Nuss ».
- Rejeté, low, second avis 7 : la justification du type 1 est l'exemple cité par Nuss ; la phrase sur le bloc de neurones est un complément, pas la preuve.

### Passe 2 (2026-11-05, SHA revu b7ee4eb)

Relecture du correctif de la passe 1 (`abd8cb9..b7ee4eb`) : verdict proposé, réserves, 30 février de second rang et point 3 de 1-9 justes et cohérents avec le reste du constat (chiffre divergent, bilan, écarts).

- Nit, low, reviewer : correctif incomplet, la correction proposée pour `jeux-de-donnees.md` marquait encore le point comme traité « feu vert avec réserve », sans attendre la décision d'Anaël. Corrigé : marquage subordonné à cette décision.
