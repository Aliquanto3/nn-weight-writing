---
story: "1-5"
title: Noyau du harnais de séance
status: review
branch: feat/1-5-noyau-harnais
---

# Story 1-5 : Noyau du harnais de séance

## Objet

Service d'outils et catalogue unique, paquet de séance à vocabulaire fermé, bac à sable profils A et B avec filtre et audit de l'interdit statistique, budget de passes, journal, format de réseau, gel avec sha256 et commande d'évaluation séparée (CAP-2, CAP-4, CAP-5, CAP-6 ; AD-1 à AD-9, AD-12, AD-15, AD-16, AD-19). Story pivot, à risque sécurité : le bac à sable exécute du code écrit par un LLM.

## Livrables

- `config/protocol.toml` et `src/nn_weight_writing/config.py` (seul lecteur, empreinte `protocol_sha256`).
- `session/refusals.py` (codes de refus, motifs de fin), `session/tools.py` (catalogue, méthodes `A-program`, `A-literal`, `B`), `session/service.py` (`ToolService.call`, `record_model_call`, `end` ; `make_session_id`).
- `sandbox/filter.py` (filtre AST), `sandbox/audit.py` (drapeaux AD-19), `sandbox/runner.py` (`run`, trame à nonce), `sandbox/_bootstrap.py` (amorçage du sous-processus `python -I`).
- `network/manifest.schema.json`, `network/layers.py` (couche `dense`, activations `identity`, `relu`, `sigmoid`, `tanh`, passe NumPy), `network/io.py` (validation, `load` sans pickle, empreintes, écriture atomique).
- `journal/schema.py` (dataclasses des 8 événements), `journal/writer.py` (ajout seul, masquage des secrets), `journal/reader.py`.
- `tasks/base.py` (contrat `Codec`), `tasks/io.py` (`read_examples`, `materialize_bundle`, `read_bundle`).
- `evaluation/schema.py` (`EvalRecord`, `RunRecord`), `evaluation/verify.py` (`evaluate`), `cli.py` (`nnww evaluate <run_dir>`), script `nnww` et marqueur `live` dans `pyproject.toml`, `numpy` ajouté par `uv add`, `runs/` ignoré.
- Tests : `test_boundary`, `test_bundle`, `test_config`, `test_evaluation`, `test_network`, `test_sandbox_filter`, `test_sandbox_runner`, `test_sandbox_evasions`, `test_service`, `test_tools` (250 tests, ~7 s).

## Mécanisme d'isolement (D1, D2)

Quatre couches, toutes actives :

1. **Filtre AST** (`sandbox/filter.py`) : liste de AD-5 ; en plus, attributs `fromregex`, `dump`, `ctypes` et noms de modules sensibles (`sys`, `os`, `builtins`, `importlib`, `subprocess`, `shutil`, `socket`, `io`, `pickle`, `marshal`) refusés comme attributs ; noms en `__` refusés ; `ImportFrom` contrôlé (module, chaque composant du chemin, nom importé et alias) contre les attributs interdits et les fonctions d'ajustement ; mots-clés de `case C(attr=x)` contrôlés comme des attributs ; en B, toute affectation ou suppression d'attribut refusée (aucun état d'un exemple à l'autre).
2. **Espaces de noms restreints** (`_bootstrap.py`) : le code de l'agent ne reçoit jamais un module. `import numpy` renvoie un `SimpleNamespace` construit depuis `vars(module)` : attributs publics seulement, sans aucun module, moins les attributs interdits et les fonctions d'ajustement ; `numpy.linalg`, `numpy.random`, `numpy.fft` sont des espaces restreints du même type. Builtins réduits (pas de `type`, `object`, `getattr`, `open`…), `__import__` restreint à ces espaces. En B, espaces et builtins sont reconstruits pour chaque exemple. Test : parcours en largeur des attributs admis par le filtre depuis tous les objets exposés et des instances usuelles (profondeur 3 pour A, 4 pour B) : aucun module atteint.
3. **Sous-processus** `sys.executable -I`, répertoire temporaire vide, environnement `SYSTEMROOT` et `PATH` seuls, délai `exec_timeout_s`, hook d'audit en fermeture posé après préchargement et compilation ; sortie par `os._exit` (aucun finaliseur de l'agent après la trame).
4. **Trame à nonce** : le parent tire `secrets.token_hex(16)`, le passe par l'entrée standard ; la trame `\x1eNNWW-FRAME <nonce> <json>` est rejetée si absente, en double ou au mauvais nonce ; poids revalidés (clés `L{i}.W|b`, `float32`, forme, finitude, 2 M valeurs au plus).

## Décisions (orchestrateur, après relecture de la spec)

- D1 (high) Canal de résultat : le parent ne fait pas confiance au stdout du sous-processus. La trame porte un nonce tiré par le parent (`secrets.token_hex`), transmis hors du code de l'agent ; trame sans le bon nonce ou en double rejetée.
- D2 (high) Le code de l'agent n'atteint ni `sys`, ni `os`, ni `builtins`, ni `importlib`, ni `subprocess`, ni `ctypes` par aucun chemin d'attributs depuis les modules du profil (mécanisme ci-dessus ; test de parcours du graphe pour A et B).
- D3 (high) Le filtre contrôle aussi `ImportFrom` et ses alias contre les fonctions d'ajustement et les imports.
- D4 (high) Corpus d'évasions = AD-5 + `re.enum.sys`, `sys.modules`, `os.write` sur 1 ou 2, faux cadre de résultat sur stdout, alias d'import d'une fonction d'ajustement, `getattr` à nom construit, `__subclasses__` sans souligné direct (par `case tuple(__class__=c)` et par `vars`). Chaque cas échoue, avec son code de refus ; 19 cas rejoués filtre contourné échouent à l'exécution.
- D5 Délai 60 s par exécution. Profil B : un seul sous-processus par passe, chaque exemple réexécuté dans un espace neuf (testé).
- D6 Après la dernière passe, `declare_network`, `write_weights`, `submit_script`, `submit_rules` sont refusés (`mutation_after_budget`) ; seul `freeze` reste permis. Une passe invalide est décomptée, y compris sans production.
- D7 Gel : contrôle de validité sans passe ; au plus 3 tentatives (`max_freeze_attempts`), refus `freeze_attempts_exhausted` au-delà.
- D8 `session/refusals.py` : `RefusalCode` (tous les codes d'outil) distinct de `EndReason`.
- D9 `config/protocol.toml` : `pass_budget = 20`, `turn_limit = 200`, `exec_timeout_s = 60`, `max_freeze_attempts = 3`, `[journal] schema_version = 1`, lu par `config.py` seul.
- D10 Limites : 512 constantes numériques de l'AST (int, float, complex, hors bool) ; 8 Ko d'octets UTF-8 (voir écart 1).
- D11 Gel de A : blocs obligatoires, partition de toutes les unités cachées de toutes les couches cachées ; B sans blocs. Tailles `size_script_bytes` (0 pour A-littéral) et `size_weights_zlib`.
- D12 Événement `open` : champs pilote, fournisseur, modèle, effort, échantillonnage, remplis en test de valeurs explicites. `bundle/` matérialisé depuis `examples.jsonl` par `tasks/io.py`. Résultats en trame : listes de float32 avec forme et dtype, clés validées.

## Écarts (spine plus forte que la décision, ou précision)

1. **D10, 8 Ko** : la spine (AD-5, AD-19) parle de « 8 Ko de chaînes ». La limite porte donc sur la somme des octets UTF-8 des littéraux `str` et `bytes` de l'AST, pas sur tout le source (un code B long mais pauvre en littéraux reste admis).
2. **D8, motif de fin** : la spine (AD-6, AD-7) nomme `frozen`, pas `freeze` ; `EndReason.FROZEN = "frozen"`.
3. **D8, empreinte divergente** : l'évaluation ne peut pas importer `session/` (graphe des dépendances de la spine). Ses codes sont dans `evaluation/verify.py` (`EvalRefusalCode` : `no_freeze_record`, `missing_file`, `unexpected_file`, `fingerprint_mismatch`, `unloadable`).
4. **D7, retour du gel** : AD-8 dit que rien de la validité n'est renvoyé à l'agent. Le gel accepté renvoie `{"frozen": true}` seul ; `valid` n'est que dans l'événement `freeze`. Un gel refusé renvoie le code de refus.
5. **D11 et AD-7, tailles** : `size_effective` de AD-7 est remplacé par deux champs, `size_script_bytes` et `size_weights_zlib` (D11) ; `size_nominal` garde son sens (paramètres ; 0 pour B).
6. **Codes du filtre** : `sandbox/` ne peut pas importer `session/` ; le filtre émet des chaînes égales aux valeurs de `RefusalCode`, un test vérifie l'inclusion.
7. **Après le gel ou `end`** : le journal est clos ; un appel d'outil renvoie `session_closed` sans être journalisé.
8. **Secrets** : le journal masque, avant écriture, les motifs de clé (`sk-ant-`, `sk-or-`, `sk-…`, `Authorization`, `x-api-key`, `Bearer`) et les valeurs de `ANTHROPIC_API_KEY` et `OPENROUTER_API_KEY` ; les flottants non finis y sont écrits en texte (JSON strict).
9. **Manifeste** : validation écrite à la main, alignée sur `manifest.schema.json` par un test (pas de dépendance `jsonschema`). Sans couche cachée, la liste de blocs doit être vide.

- D13 (revue, décision de l'orchestrateur, à confirmer par Anaël, réversible avant toute séance mesurée) : la liste AD-19 des fonctions d'ajustement est étendue, par prudence, à tous les solveurs et décompositions de `numpy.linalg` de NumPy 2.5 (`tensorsolve`, `tensorinv`, `svdvals`, `eigvals`, `eigvalsh`, `qr`, `cholesky`, `matrix_rank`) et à `numpy.polynomial` et ses ajustements (`polynomial`, `chebfit`, `legfit`, `lagfit`, `hermfit`, `hermefit`). Motif : chacune permet de résoudre ou d'ajuster sur les exemples, ce que AD-19 interdit ; la liste nominale de AD-19 n'en était qu'un échantillon. Restent admises : `det`, `slogdet`, `norm`, `matrix_norm`, `vector_norm`, `cond`, `trace`, `matmul`, `dot`, `einsum`. Effet de bord accepté : ces noms sont aussi refusés comme noms de variables (comme ceux de AD-19).
- D14 (revue) : code trop long ou trop imbriqué pour l'analyseur (RecursionError, MemoryError) refusé `code_too_complex` ; `write_weights` n'admet que des `int` et `float` (ni chaîne, ni booléen, ni entier hors float64) ; log du sous-processus plafonné côté enfant à 20 000 caractères, marqueur `[log tronqué]` ; attribut `mro` refusé.

## Critères d'acceptation (tests)

- Frontière de confiance par l'AST (AD-1) : aucun import de `torch`, `jax`, `evaluation`, `baselines`, `report`, `datasets`, `publish` (relatifs compris) côté séance ; ni `labels.jsonl` ni `heldout` dans ces sources.
- Paquet sans étiquette ni type (une ligne avec `label` ou `type_id` fait refuser le fichier), vocabulaire fermé seul présent.
- Budget 20 : passes 1 à 20, la 21e refusée `pass_budget_exhausted` ; passe invalide décomptée ; aucune clé de score ; seul `freeze` après la dernière.
- Corpus d'évasions de AD-5 et D4 : chaque cas refusé ; défense en profondeur filtre contourné ; graphe d'attributs sans module.
- Imports par profil ; B réexécuté dans un espace neuf par exemple ; fonctions d'ajustement (attribut, import, alias) et littéraux au-delà de 8 Ko ou 512 nombres refusés.
- Drapeaux d'audit (fragment de 12 caractères recopié d'un exemple, boucle de la taille du jeu) journalisés sans refus ; 11 caractères ne lèvent rien.
- Gel de A refusé si les blocs manquent, ne partitionnent pas les unités cachées ou visent un type hors vocabulaire ; 3 tentatives au plus.
- Évaluation refusée sur fichier modifié, en trop, absent, `tree_sha256` divergent ou sans gel ; deux évaluations identiques au `ts` près ; le journal n'est pas modifié.
- Aucun motif de clé dans le journal.

## Reports

- **1-6** : pilotes, fournisseurs, serveur MCP, `nnww session` complet (réservation, matérialisation, boucle, plafond de tours `turn_limit`), coûts et registre ; test d'identité du catalogue entre pilotes (AD-15) ; prompt système.
- **1-7** : encodeurs et décodeurs réels des tâches (`Codec`), tâche jouet.
- **Témoins** (AD-3) : implémentation PyTorch de `dense` et des activations, et test de parité ; d'ici là le registre `network.layers` n'a que l'implémentation NumPy.
- **1-14** : mesures de `eval.json` (jeu réservé, par type, ablation des blocs), exécution de B en évaluation par `sandbox.run`.
- Audit : le recouvrement de fragments ne porte que sur les `raw` textuels ; les jeux d'images (lot 2) demanderont un audit des littéraux numériques. La détection de boucles est statique (`range(K)` ou littéral de taille K).
- Pas de limite mémoire du sous-processus (seul le délai borne une exécution) ; à poser si une séance réelle le demande.

## Revue

### Passe 1 (2026-11-05, SHA revu a062d67)

Rebasée sur `origin/main` (302199b), sans conflit ; `pyproject.toml` sans recouvrement.

- Important, medium, second avis 1 : `write_weights` levait OverflowError (`[[10**400]]`) hors de `call()` — corrigé (refus `invalid_weights`, journalisé), test paramétré.
- Important, medium, second avis 2 : RecursionError (somme de 60 000 termes) et MemoryError (100 000 unaires) de `ast.parse` remontaient par le filtre et l'audit — corrigé (refus `code_too_complex`, audit sans drapeau), tests filtre A et B et service.
- Important, medium, second avis 3 : liste AD-19 étendue (D13) — corrigé, tests paramétrés A et B, alias, `np.polynomial`.
- Important, medium, second avis 4 : log du sous-processus sans plafond — corrigé (tampon plafonné dans `_bootstrap.py`, marqueur), test.
- Nit, low, second avis 5 : coercion de `"1.0"` et `True` en 1.0 — corrigé (`_only_numbers`, itératif), test.
- Nit, low, second avis 6 : `str.mro()` — corrigé (attribut `mro` refusé), test.
- Important, medium, revue : `manifest_errors` levait TypeError sur `type` ou `activation` non hachable (liste JSON), la séance tombait — corrigé, tests.
- Nit, low, revue : un argument non sérialisable en JSON (ensemble Python) fait lever `journal.write` ; inatteignable par un pilote JSON — reporté à 1-6 (pilotes : n'envoyer que du JSON décodé).
- Nit, low, revue : `np.roots` calcule les valeurs propres d'une matrice compagnon ; ne donne pas d'ajustement sur données — admis, à revoir avec D13.
- Complexité : 0 constat (journal en ajout O(1), décompte de `write_weights` borné par 1 M paramètres).
- Report (inchangé) : pas de limite mémoire du sous-processus.
