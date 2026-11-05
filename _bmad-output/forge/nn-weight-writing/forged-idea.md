# nn-weight-writing — idée forgée (2026-11-05)

**Question** : quand un LLM écrit tous les poids d'un réseau sans gradient, sur quelles tâches cela vaut-il mieux qu'un script à règles (B) ou qu'un entraînement (C), et jusqu'à quelle taille ?

**Hypothèse de départ** : sur les données de Nuss (15 types d'erreurs explicites), B ≥ A est presque acquis. Le réseau n'a d'intérêt que par sa différentiabilité (E, affinage par gradient) ou sur des signaux bruités. Un résultat négatif est un livrable à part entière.

## Décisions

- **Périmètre** : réseaux dont l'agent écrit tous les poids à partir de rien. Tout modèle pré-entraîné, gelé ou modifié, relève de slm-weight-editing.
- **Lot 1, reproduction critique** (100 $) : jouet (validation du harnais) puis juridique.
  - Méthodes : A-programme, A-littéral réduit (~10⁴ paramètres), B, C en courbe (64 → 8 192 exemples et plus), F (entrées préparées).
  - Modèles : Sonnet 5.5 et MiMo-V2.6-Pro, 3 tentatives par case ; Fable, 1 tentative sur S.
- **Données juridiques** :
  - S : 15 types d'erreurs, reproduction de Nuss ;
  - S-réservé : 10 types connus de l'agent, 5 vus seulement à l'évaluation ;
  - R : vraies références de Judilibre, fausses tirées d'hallucinations de SLM vérifiées inexistantes, un normaliseur commun aux deux côtés.
- **Porte avant R** : pré-étude sur ~300 hallucinations. Si moins de 30 % sont incohérentes, R devient une mesure de plafond et non un comparatif.
- **Lot 2, où le réseau compte** (75 $) : méthodes A, B, C, E.
  - Images : formes synthétiques, puis chiffres 8×8 de scikit-learn et MNIST, puis Fashion-MNIST.
  - Échelle de tailles de 10⁴ à 10⁷, sur MNIST seulement.
  - Modèle : MiMo s'il reste à moins de 3 points de Sonnet au lot 1, sinon Sonnet avec 2 tentatives.
- **Lot 3, conditionnel** (25 $) : petit transformer écrit sur 1 ou 2 tâches algorithmiques, comparé à Tracr et à un entraînement.
- **Deux définitions de A, comparées vers 10⁴ paramètres** : A-littéral (chaque poids écrit en clair) et A-programme (script générateur journalisé et publié). Deux tailles mesurées : nominale, et effective (longueur du script, taille compressée des poids).
- **Critère de limite** : on s'arrête au premier des trois signaux.
  - (a) Plus de réseau valide dans le budget de passes.
  - (b) A plafonne alors que C monte encore, à données égales.
  - (c) A passe sous B.
  - Prédiction : (b) vers 10⁵.
- **Protocole sur les exemples non annotés** : l'agent peut les regarder et y exécuter le réseau par le harnais, dans le budget de passes. Interdit : toute statistique qui produit des poids (moyenne, k-means, ACP) et toute annotation des exemples par l'agent.
- **Budget** :
  - 200 $ pour tout le projet, tous fournisseurs, séances d'écriture seulement. Un dépassement demande une décision explicite d'Anaël.
  - Harnais multi-fournisseur (API Anthropic et OpenRouter), coût journalisé par séance.
  - Porte de coût après le jouet : si la séance médiane dépasse 2 $ sur Sonnet, on passe à 2 tentatives par case.
- **Publication** :
  - lot 1 : `docs/rapport-lot1.md`, release v0.1.0 et billet LinkedIn en réponse à Nuss, publié par Anaël ;
  - lot 2 : v0.2.0, avec un billet seulement si un résultat est marquant ;
  - tout est publié : protocole, journaux, sha256 des poids, code de B.

## Écarté

- **D** (le LLM génère des données annotées, puis entraînement) : distillation classique, sans rapport avec les questions posées, et 25 % de séances en plus.
- **Tâche tabulaire** : doublon du juridique.
- **Tête écrite sur un encodeur gelé** : les dimensions de l'encodeur sont opaques sans statistiques, ce qui contredit le protocole.
- **Greffe d'un circuit dans un SLM** : renvoyée à slm-weight-editing.
- **Opus comme second modèle** : même famille que Sonnet. MiMo répond à la question « est-ce propre à Claude ? » pour environ 10 fois moins cher.

## À vérifier au cadrage

- S est reconstruit d'après un post LinkedIn : la reproduction reste approximative.
- Pour MiMo via OpenRouter : appels d'outils, et vision, nécessaire pour regarder les images au lot 2. Son 97 % vient de la calibration du juge de slm-quality-bench et ne se transfère pas forcément à l'écriture de poids.
- Accès à Judilibre : compte PISTE à ouvrir par Anaël, licence de réutilisation, collecte des hallucinations via slm-quality-bench.
- Licences de MNIST, Fashion-MNIST et des chiffres de scikit-learn.
