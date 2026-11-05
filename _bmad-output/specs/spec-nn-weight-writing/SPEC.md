---
id: SPEC-nn-weight-writing
companions:
  - harnais.md
  - protocole-ecriture.md
  - methodes-et-lots.md
  - jeux-de-donnees.md
  - ../../planning-artifacts/architecture/architecture-nn-weight-writing-2026-11-05/ARCHITECTURE-SPINE.md
  - ../../../AGENTS.md
  - ../../../docs/SOURCES.md
sources:
  - ../../forge/nn-weight-writing/forged-idea.md
  - ../../../docs/PISTES.md
---

> **Contrat de référence.** Ce SPEC et les fichiers de `companions:` forment le contrat complet de ce qu'il faut construire, tester et valider. Les sources du frontmatter ne servent qu'à la traçabilité.

# nn-weight-writing — un LLM écrit tous les poids d'un réseau

## Why

Opportunité et vérification. Début novembre 2026, Lauritzen puis Nuss rapportent qu'un LLM écrit sans gradient un réseau d'environ 10⁵ paramètres qui détecte les fausses références juridiques mieux qu'un entraînement (97,7 % contre 82,8 % chez Nuss), sans code, données ni témoin à règles publiés. Le projet répond à la question : sur quelles tâches l'écriture de poids vaut-elle mieux qu'un script à règles (B) ou qu'un entraînement (C), et jusqu'à quelle taille ? Hypothèse : sur les données de Nuss, B ≥ A est presque acquis ; le réseau n'a d'intérêt que par sa différentiabilité (E) ou sur des signaux bruités. Un résultat négatif est un livrable. Public : Anaël, puis la communauté qui a vu passer le post de Nuss.

## Capabilities

Lot 1 (priorité), dans l'ordre d'exécution :

- **CAP-1** — vérifications de cadrage
  - **intent:** Anaël dispose, avant toute séance du lot 1, d'un constat écrit sur chacun des quatre points à vérifier : fidélité de S à Nuss, MiMo via OpenRouter, accès et licence de Judilibre, licences des jeux d'images.
  - **success:** Quatre constats dans `docs/verifications/`, chacun avec un verdict (feu vert, feu vert avec réserve, blocage) et sa conséquence sur la spec ; un blocage est consigné comme décision avant la suite.
- **CAP-2** — harnais de séance
  - **intent:** Un agent LLM écrit les poids d'un réseau par les seuls outils du harnais, qui compte, journalise et borne ses passes sur les exemples non annotés.
  - **success:** Tests : la passe au-delà du budget est refusée et journalisée ; une passe ne renvoie aucun score ; aucun outil n'atteint un jeu réservé, une étiquette ni un calcul de gradient ; le code de l'agent (A-programme, B) ne lit aucune donnée et chaque cas du corpus d'évasions échoue ; le journal liste chaque passe dans l'ordre.
- **CAP-3** — deux pilotes, fournisseurs et coût
  - **intent:** La même séance tourne par le pilote Claude Code (Sonnet 5.5, Fable 5.1, abonnement d'Anaël) ou par le pilote API (MiMo-V2.6-Pro via OpenRouter, API Anthropic en repli) en changeant un paramètre, avec tokens, coût facturé et coût équivalent API journalisés par séance.
  - **success:** Une séance jouet complète passe par chaque pilote ; prompt système, description, catalogue d'outils et budget de passes sont identiques quel que soit le pilote et le modèle (test) ; la première requête du pilote Claude Code ne contient que le prompt système et la description de tâche (test) ; le cumul facturé et équivalent par lot et pour le projet est lisible dans le registre ; le harnais refuse d'ouvrir une séance qui ferait dépasser le budget facturé restant.
- **CAP-4** — gel et évaluation séparée
  - **intent:** Les poids d'une séance sont gelés avec leur empreinte sha256, puis évalués sur le jeu réservé par une commande à part que l'agent n'appelle jamais.
  - **success:** Réévaluer des poids gelés redonne le même score ; l'évaluation refuse des poids dont l'empreinte diffère du journal.
- **CAP-5** — méthodes A-programme et A-littéral
  - **intent:** L'agent écrit les poids soit par un script générateur (A-programme), soit poids par poids en clair (A-littéral réduit, ~10⁴ paramètres).
  - **success:** Sur S, A-programme est mesuré vers 10⁴ et vers 10⁵ (taille de Nuss) ; chaque réseau A porte dans son journal sa taille nominale, sa taille effective (longueur du script, taille compressée des poids) et la règle déclarée de chaque bloc de neurones ; le script d'A-programme est conservé.
- **CAP-6** — témoin B
  - **intent:** Le même LLM, dans une séance de même protocole, écrit des règles en Python sans réseau, évaluées sur le même jeu réservé.
  - **success:** Score de B sur chaque jeu où A est mesuré, code de B publié.
- **CAP-7** — témoins C et F
  - **intent:** On mesure l'entraînement standard en courbe d'efficacité en données (C) et avec entrées préparées (F, champs de date extraits).
  - **success:** Pour chaque jeu, une courbe C sur une architecture de référence fixe, N = 64, 256, 1 024, 8 192 et au-delà, plusieurs graines ; chaque architecture écrite en A réentraînée depuis des poids aléatoires à N = 8 192 ; un point F au moins à chaque N.
- **CAP-8** — jouet à solution connue
  - **intent:** Des tâches dont la solution exacte est connue valident le harnais de bout en bout et calibrent le budget de passes.
  - **success:** Une solution écrite à la main atteint 100 % par le harnais ; des séances A et B tournent sur Sonnet et MiMo, 1 tentative par case ; le budget de passes recalibré est consigné puis figé.
- **CAP-9** — jeux S et S-réservé
  - **intent:** On reproduit les données de Nuss (15 types d'erreurs) et une variante où 5 types ne sont vus qu'à l'évaluation.
  - **success:** Générateur reproductible par graine ; les 15 types documentés avec leur écart à Nuss ; le jeu d'évaluation de S-réservé contient les 5 types tenus à l'écart, que la description de tâche et son vocabulaire de types ne mentionnent pas.
- **CAP-10** — pré-étude R
  - **intent:** On mesure, sur ~300 hallucinations de SLM, la part de fausses références incohérentes, seules détectables sans base de données.
  - **success:** Part chiffrée avec intervalle, classement publié, décision « comparatif » ou « mesure de plafond » consignée selon la porte des 30 %.
- **CAP-11** — jeu R
  - **intent:** On compare les méthodes sur de vraies références (Judilibre) contre de vraies hallucinations de SLM, sans circularité avec les 15 types.
  - **success:** Chaque fausse référence est vérifiée absente de Judilibre ; un test montre que vraies et fausses passent par le même normaliseur.
- **CAP-12** — mesures par case
  - **intent:** Chaque case (tâche × méthode × modèle) est décrite par l'exactitude réservée, la robustesse hors distribution, le coût, la lisibilité et la variance entre tentatives.
  - **success:** Un tableau agrégé est régénéré par commande depuis les journaux, sans saisie manuelle, coût facturé et coût équivalent API en colonnes séparées ; la lisibilité y est mesurée par ablation des blocs déclarés (`methodes-et-lots.md`).
- **CAP-13** — rapport et publication du lot 1
  - **intent:** Le lot 1 est publié comme reproduction critique de Nuss, résultat négatif compris.
  - **success:** `docs/rapport-lot1.md`, release v0.1.0 avec notes ; protocole et code de B dans le dépôt, poids et journaux en assets de la release, sha256 cités dans le rapport ; drapeaux d'audit de l'interdit statistique publiés par séance, chaque séance signalée jugée avant conclusion ; brouillon de billet LinkedIn en réponse à Nuss remis à Anaël.

Lots suivants :

- **CAP-14** — lot 2, où le réseau compte
  - **intent:** On mesure A, B, C et E sur des tâches perceptives et sur une échelle de tailles, jusqu'au critère de limite.
  - **success:** Scores sur formes synthétiques, chiffres 8×8, MNIST, Fashion-MNIST ; courbe exactitude-taille de 10⁴ à 10⁷ sur MNIST avec le signal d'arrêt atteint nommé ; release v0.2.0.
- **CAP-15** — lot 3 conditionnel
  - **intent:** Un petit transformer écrit par le LLM sur 1 ou 2 tâches algorithmiques est comparé à Tracr et à un entraînement, si les trois conditions de déclenchement de `methodes-et-lots.md` sont réunies après le lot 2.
  - **success:** Exactitude des trois sur la même tâche et le même jeu réservé.

## Constraints

- Tous les poids sont écrits à partir de rien ; aucun modèle pré-entraîné, gelé ou modifié (`slm-weight-editing`).
- Protocole d'écriture de `protocole-ecriture.md`, non contournable une fois les séances lancées.
- Décisions d'architecture AD-1 à AD-19 du spine (`ARCHITECTURE-SPINE.md`) : toute story s'y conforme et les cite par leur identifiant.
- Budget : 200 $ facturés pour tout le projet (lot 1 : 100, lot 2 : 75, lot 3 : 25), séances d'écriture seulement, tous pilotes. Les séances par abonnement sont facturées 0 $ ; leur coût équivalent API est journalisé et publié, sans s'imputer (AD-11). Dépassement = décision explicite d'Anaël.
- Pilote Claude Code : binaire non modifié, identifiants de l'abonnement jamais passés par une autre application, usage individuel ordinaire (`harnais.md`, AD-14).
- Portes et règles de choix de `methodes-et-lots.md` (coût sur le facturé, R à 30 %, modèle du lot 2, critère de limite).
- Tout tourne sur CPU, portable pro compris : pas d'Ollama ni de GPU.
- Tout est publié, mais aucun poids ni jeu de données dans un commit (`AGENTS.md`) : poids et journaux vont en assets de release.
- Le harnais n'expose aucun gradient : NumPy dans les outils de séance, PyTorch réservé à C et E (AD-1, AD-13).

## Non-goals

- Un détecteur de références juridiques prêt à l'emploi : un réseau sans base vérifie la cohérence, pas l'existence.
- Méthode D (le LLM génère des données annotées puis on entraîne) : distillation classique, +25 % de séances.
- Tâche tabulaire : doublon du juridique.
- Tête écrite sur un encodeur gelé : dimensions opaques sans statistiques, contraire au protocole.
- Greffe d'un circuit écrit dans un SLM : relève de `slm-weight-editing`.
- Opus comme second modèle : même famille que Sonnet ; MiMo teste « propre à Claude ? » pour ~10 fois moins cher.
- Un bac à sable étanche à une évasion malveillante : il bloque les raccourcis d'un agent honnête, l'audit publié couvre le reste (AD-5, AD-19).
- Publication du billet par un agent : Anaël publie.

## Success signal

`docs/rapport-lot1.md` et la release v0.1.0 répondent, chiffres et journaux publiés, à la question « sur S, A fait-il mieux que B et que C à données égales ? » pour Sonnet et MiMo, 3 tentatives par case sur les jeux juridiques (2 si la porte de coût joue sur des séances facturées), dans 100 $ facturés, avec un verdict sur R (comparatif ou plafond). Tout tiers peut réévaluer chaque réseau publié par sa commande d'évaluation et retrouver le score et l'empreinte du rapport.

## Assumptions

- Sonnet 5.5 et Fable 5.1 sont accessibles par l'abonnement d'Anaël dans Claude Code ; sinon repli sur l'API Anthropic, facturé. Une coupure par limite d'usage termine la séance en erreur ; elle est rejouée, jamais reprise.
- A-programme, A-littéral et B s'imputent sur le budget pour leur seul coût facturé ; C, E et F sont des entraînements locaux hors budget.
- La tentative unique de Fable sur S couvre A-programme, A-littéral et B.
- Jouet = parité, comparaison de nombres, petit automate (PISTES).
- Les mesures de PISTES (robustesse, lisibilité, énergie estimée) restent : la forge ne les a pas écartées.
