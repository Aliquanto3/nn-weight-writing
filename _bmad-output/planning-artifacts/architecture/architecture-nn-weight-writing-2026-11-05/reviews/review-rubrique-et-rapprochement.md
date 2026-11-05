# Revue du spine : grille et rapprochement avec la spec

Verdict : le spine est solide sur la frontière de confiance, le bac à sable, le port fournisseur et le coût, mais il laisse sans décision la chaîne de la lisibilité (types d'erreur, blocs, format des jeux, `eval.json`), perd plusieurs champs de journal exigés par `harnais.md` et ne porte aucune règle de publication ni la porte de coût ; à corriger avant de lancer 1-5.

Les gabarits `{i}`, `{task}`… sont ignorés (voulus).

## Critical

### C1. La chaîne « lisibilité par ablation » est contradictoire et sans format (AD-2, AD-8, AD-9, AD-12)
- AD-2 exige que le paquet ne contienne « aucun type d'erreur », alors que AD-8 oblige chaque bloc à porter « les identifiants des types d'erreur visés ». L'agent ne connaît donc pas le vocabulaire des types qu'on lui demande de citer. Pour S-réservé, `jeux-de-donnees.md` dit que l'agent « connaît 10 types » : AD-2 ne dit pas comment (description ? exemples ?) ni que les exemples du paquet ne sont tirés que des 10 types visibles.
- Aucun format n'est fixé pour : le bloc déclaré dans `manifest.json` (indices d'unités, règle, types) ; ce que « éteindre un bloc » veut dire (poids entrants, sortants, activation) ; les fichiers de jeux (champs `raw`, `label`, `error_type`, `source`) dans `data/` et `heldout/` ; le contenu de `eval.json` (exactitude globale et par type, robustesse, ablation par bloc, score de lisibilité).
- Quatre stories (1-5 évaluation, 1-9 générateurs, 1-11 témoins, 1-14 tableau) fabriqueront chacune leur format.
- Correctif : ajouter un AD « Schémas des artefacts de données » (jeu : JSONL `id, raw, label, error_type` plus un manifeste de jeu avec générateur, version, graine, sha256 ; bloc : `{units:[int], rule:str, targets:[type_id]}` ; ablation : mise à zéro des poids sortants du bloc ; `eval.json` : champs nommés). Fixer le vocabulaire des `type_id` : donné à l'agent dans la description pour les types visibles, jamais pour les 5 réservés. Corriger AD-2 (« aucune étiquette par exemple ; liste des types visibles admise dans la description »).

## High

### H1. AD-7 : champs du journal exigés par `harnais.md` absents (AD-7, AD-8)
- Absents ou non rattachés à un type d'événement : tokens d'entrée, de sortie et de cache et coût par appel (seul `Usage` d'AD-10 en parle, la charge de `model_call` n'est pas définie) ; **durée** (séance et appels ; la spec compte les « minutes » dans le coût et l'énergie estimée en dépend) ; contenu de chaque échange (messages, arguments et résultats d'outils) ; **taille nominale et taille effective** (longueur du script, taille compressée des poids) pour A ; règle déclarée par bloc dans `freeze` ; coût cumulé de la séance ; `valid` du réseau au gel.
- Correctif : définir la charge de chaque `type` (`model_call` : `usage`, `cost_usd`, `duration_ms`, `provider_cost`, messages ; `freeze` : `sha256`, `nominal_params`, `effective_script_bytes`, `effective_compressed_bytes`, `blocks`, `valid` ; `end` : `duration_s`, `cost_usd`). Fixer le compresseur (zlib niveau 9) pour que la taille effective soit unique.

### H2. Fin de séance et signal (a) du critère de limite : contradiction interne (AD-6, AD-7, Structural Seed)
- AD-6 dit qu'au-delà du budget la passe est « refusée, journalisée et non exécutée » (la séance continue). Le Structural Seed et le motif `pass_budget` font finir la boucle « aux passes épuisées ». On ne sait pas si l'agent peut geler après la 20e passe. Or le signal (a), « plus de réseau valide dans le budget », doit se lire dans le journal.
- Correctif : trancher dans AD-6 (après épuisement, seuls `freeze` et la fin restent permis ; `end.reason = pass_budget` si aucun gel valide) et exiger `freeze.valid` et `end.frozen: bool`. Écrire aussi la valeur 20 dans `protocol.toml`.

### H3. D'où vient `manifest.json` pour A-programme ? (AD-3, AD-5, AD-8)
- AD-5 fait renvoyer à `build()` un `dict[str, ndarray]` et l'amorçage ne sérialise que des `.npz`. AD-3 affirme qu'A-programme produit « le même couple ». Rien ne dit qui écrit couches, activations et blocs. Les stories 1-5 et 1-10 divergeront.
- Correctif : `build()` renvoie `{"manifest": dict, "weights": dict}`, ou le manifeste est un argument de l'outil de gel ; l'écrire dans AD-3 et AD-5.

### H4. Portée du sha256 ambiguë (AD-8, AD-9)
- AD-8 hache les octets de `weights.npz` (ou `rules.py`), AD-9 « recalcule le sha256 de `frozen/` ». Un `manifest.json` modifié (activations) change le score sans changer l'empreinte, alors que la spec veut que tout tiers retrouve score et empreinte. L'écriture `.npz` doit aussi être déterministe (horodatages zip).
- Correctif : empreinte = sha256 d'un condensé canonique de `manifest.json` + `weights.npz` (+ `script.py`), chaque fichier listé dans l'événement `freeze` ; écriture `.npz` déterministe.

### H5. Porte de coût et tentatives par case sans support (AD-11, AD-6, `config/`)
- Si la séance médiane Sonnet sur S dépasse 2 $, on passe de 3 à 2 tentatives. Le spine n'a ni la table des tentatives par modèle et tâche (3 / 2 / 1 ; Fable 1 sur S seulement), ni le calcul de la médiane, ni le lieu de consignation de la décision. Idem pour les autres portes (30 % de R, modèle du lot 2, recalibrage des passes) : aucun ancrage dans `config/`.
- Correctif : `[attempts]` et `[gates]` dans `config/protocol.toml` ; `nnww ledger --median --task S --model sonnet` ; `nnww session` refuse une tentative au-delà du nombre autorisé ; `open` copie le hash de `protocol.toml`.

### H6. Surface des outils de l'agent non décidée (AD-6, AD-5, AD-10)
- Le spine ne nomme que `run_on_examples` et `freeze`. Noms, schémas et sémantiques de la lecture du paquet, de la soumission A-littéral, de l'exécution du script et de la soumission des règles B ne sont pas fixés, ni ce que compte une passe (tous les exemples du paquet ou un sous-ensemble). Point dur : A-littéral à ~10⁴ poids en clair dépasse probablement la sortie maximale d'un appel ; il faut un envoi incrémental, sinon la troncature produit des échecs différents selon le modèle.
- Correctif : un AD « Catalogue d'outils » (liste fermée, schémas JSON, `write_layer(i, W, b)` incrémental, passe = tous les exemples du paquet, `max_tokens` dans `models.toml`).

### H7. Règles de publication absentes (AD-12, AD-7, CLI)
- `harnais.md` et 1-14 exigent : aucune clé d'API dans ce qui est publié, journaux de R publiés seulement si la licence Judilibre le permet (constat 1-3). Le spine n'a qu'un test de préfixes de clé sur le journal ; rien sur `bundle/` et `eval.json` de R (références Judilibre aussi), ni sur l'archive `runs-lot<N>.tar.gz`. Aucune sous-commande ne construit l'archive, `SHA256SUMS` ni la release (`gh release upload` n'est que dans un schéma). Un `eval.json` détaillé par exemple publierait en outre les étiquettes du jeu réservé.
- Correctif : `nnww publish <lot>` qui (1) scanne tous les fichiers de l'archive pour les préfixes de clé, (2) exclut les données de R sauf drapeau `license_ok` dans `protocol.toml`, (3) refuse toute étiquette par exemple du jeu réservé, (4) écrit `SHA256SUMS`.

### H8. Protocole d'entraînement des témoins non fixé (AD-13, AD-3, AD-12)
- CAP-7 exige architecture de référence fixe, N = 64, 256, 1 024, 8 192 et au-delà, plusieurs graines, réentraînement de chaque architecture A à N = 8 192, point F à chaque N ; E part de A. Le spine ne fixe ni optimiseur, époques, critère d'arrêt, validation, architecture de référence par tâche, ni le contenu de `result.json`. Si 1-11 et 2-2 choisissent différemment, A − C et E − C deviennent incomparables. Et AD-7 dit que le tableau CAP-12 vient « des journaux et des `eval.json`, sans autre entrée », ce qui exclut `result.json` (contradiction avec CAP-7).
- Correctif : un AD « Protocole des témoins » (hyperparamètres uniques dans `config/train.toml`, ensembles N et graines, schéma de `result.json`) ; AD-7 : « journaux, `eval.json` et `result.json` ».

## Medium

- **M1. Séance en erreur et concurrence du registre (AD-11).** Le registre n'est écrit qu'à la clôture : une séance tuée perd son coût ; deux séances parallèles voient chacune « dépensé + max_session_usd ≤ plafond » sans compter l'autre. Correctif : ligne de réservation à l'ouverture, ligne finale dans un `finally` ; une tentative en erreur compte pour son coût et son numéro.
- **M2. Paramètres d'échantillonnage et prompts (AD-10, AD-7).** Température, effort de réflexion, `max_tokens`, prompt système commun, délais et nouvelles tentatives non décidés ni journalisés ; ils pèsent sur la variance entre tentatives. Correctif : dans `models.toml`, avec le hash du prompt système et des schémas d'outils copié dans `open`.
- **M3. Protocole modifié après la première séance (AD-6).** « Toute modification invalide les séances déjà faites » : rien ne l'impose. Correctif : `open.protocol_sha256` ; le tableau refuse de mêler deux valeurs dans un lot.
- **M4. Environnement purgé sous Windows (AD-5).** Un environnement vide casse l'interpréteur (`SYSTEMROOT`, graine aléatoire). Correctif : liste blanche minimale (`SYSTEMROOT`), sans clé d'API, et un test du bac à sable sous Windows.
- **M5. Délais et profils du bac à sable (AD-5, Deferred).** Délai maximal sans valeur ; profil B sans `numpy` ne servira pas B sur images (lot 2) ; exception ou valeur hors étiquettes dans `predict` : comportement non défini ; `datetime.now` non interdit, ce qui peut casser « deux évaluations identiques ». Correctif : délai dans `protocol.toml`, règle de notation des exceptions, profil images nommément différé à 2-3.
- **M6. `torch` et CLI (AD-13, AD-1).** `cli.py` dépend de `baselines` : un import de `torch` à l'import ferait charger torch par `nnww session`, contre « NumPy seul ». `uv sync` (AGENTS.md) n'installe pas le groupe `train` par défaut : tests de `baselines` à sauter ou `default-groups`. Le wheel `torch` pour Python 3.14 (vérification exigée par `harnais.md`) est présenté comme acquis. Correctif : import paresseux dans `train`, décision `default-groups`, vérification en première story.
- **M7. Paquet `budget` (côtés, AD-1, graphe).** Le tableau le classe côté évaluateur mais `session --> budget` ; AD-1 ne l'analyse pas. Correctif : le classer « commun » et l'analyser par le test AD-1.
- **M8. Identifiants de tâche et jeux multiples (AD-12).** `tasks/legal/` couvre S, S-réservé et R sans identifiant distinct ; `heldout/<task>/` n'a qu'un jeu alors que la robustesse « autre source » exige un second. Correctif : `task_id` explicites et `heldout/<task>/{primary,ood}/`.
- **M9. Exemples non annotés du paquet (AD-2).** Nombre (40 chez Nuss), tirage, graine et lien avec le pool de C non décidés. Correctif : `bundle_size` et graine dans `protocol.toml`, journalisés dans `open`.
- **M10. Normaliseur et absence de R (CAP-11).** Le test « même normaliseur » et la preuve « chaque fausse référence absente de Judilibre » n'ont aucun AD ; l'interface d'import des hallucinations de `slm-quality-bench` (lu seulement) non plus. Correctif : le normaliseur s'applique avant matérialisation (AD-4/AD-12), un fichier de vérification par jeu R, format d'entrée de l'import.
- **M11. Robustesse et énergie en Deferred.** Formules renvoyées à 1-14, mais leurs entrées (durées, tokens, second jeu) doivent être journalisées dès 1-5/1-6. Correctif : poser les entrées (H1, M8) maintenant, ne différer que la formule.
- **M12. Versionnage et release (AGENTS.md).** SemVer dans `pyproject.toml` et `__init__.py`, tag annoté, release à chaque lot : absent. Correctif : convention « Release » et `__version__` dans l'arborescence.
- **M13. Exploitation.** `runs/` est ignoré par git : poids et journaux (livrable et dépense) n'ont ni sauvegarde ni rétention avant la release ; ni reprise ni lancement de la matrice (~18 puis ~54 séances) ; clés d'Anaël (OpenRouter, PISTE) non posées. Correctif : section « Exploitation » (sauvegarde de `runs/` hors dépôt, commande de matrice séquentielle, secrets en variables d'environnement).
- **M14. CAP-8, solution écrite à la main à 100 %.** Aucun mécanisme. Correctif : le fournisseur `fake` rejoue une séance scriptée par tâche jouet, testée à 100 %.

## Low

- **L1. Versions figées (Stack, AGENTS.md).** Versions exactes dans le tableau ; AGENTS.md interdit de figer de mémoire. La note dit « relevées sur PyPI » : à confirmer, sinon ne garder que les contraintes majeures.
- **L2. Langue des noms de fichiers (Consistency).** « Noms de fichiers en anglais » contredit `docs/rapport-lot1.md` imposé par la spec ; excepter `docs/`.
- **L3. Ignorés par git (AD-12).** AGENTS.md ignore `data/`, `models/`, `heldout/` ; AD-12 ajoute `runs/` mais omet `models/`.
- **L4. Conventions de lint (AGENTS.md).** Ruff, ligne de 100 et `uv run python` non repris.
- **L5. Pré-étude R (CAP-10).** Format de classement (étiquette, auteur, méthode d'intervalle) à fixer en 1-12 : il alimente la porte des 30 % et 1-13.
- **L6. Licence du dépôt public.** Non posée alors que code et protocole sont publiés.
- **L7. Limite mémoire différée.** Acceptable au lot 1, à rouvrir avant 2-4 (10⁷ paramètres, portable de 16 Go).
- **L8. Lieu des décisions.** Recalibrage des passes, portes : « se consigne comme décision » sans dire où (dépôt ou journal du run).

## Rapprochement : tests obligatoires de 1-5 et 1-6

| Exigence | Support dans le spine |
| --- | --- |
| Passe hors budget refusée (budget 20) | AD-6 (valeur 20 absente, voir H2) |
| Passe sans score | AD-6 |
| Aucun accès à `heldout/` | AD-1, AD-2 |
| Gradient indisponible | AD-1 (statique), AD-13 |
| Script A-programme isolé, NumPy seul | AD-5 |
| Gel refusé sans règle par bloc | AD-8 (format du bloc absent, C1) |
| Évaluation refusée sur empreinte divergente | AD-9 (portée du hash, H4) |
| Journal ordonné des passes | AD-7 (`seq`) |
| 1-6 : coût, plafond, un appel réel par fournisseur | AD-10, AD-11, `@pytest.mark.live` (porte de coût : H5) |

## Contradictions avec AGENTS.md

Aucune contradiction frontale ; points limites : versions figées (L1), `models/` non ignoré (L3), versionnage et release absents (M12), langue des fichiers et lint (L2, L4).
