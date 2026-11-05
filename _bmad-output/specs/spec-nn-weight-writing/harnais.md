# Harnais de séance : pilotes, fournisseurs et coût

Détail de CAP-2, CAP-3 et CAP-4. La mise en œuvre est fixée par le spine (`ARCHITECTURE-SPINE.md`), cité ici par ses identifiants AD.

## Pilotes et modèles

Un même service d'outils, seul écrivain du journal, sert deux pilotes de boucle (AD-14, AD-10).

| Modèle | Pilote | Facturation | Rôle | Tentatives par case |
|---|---|---|---|---|
| Sonnet 5.5 | Claude Code (`claude -p`) | Abonnement d'Anaël, 0 $ facturé | Modèle principal | 3 (2 si la porte de coût joue) ; 1 sur le jouet |
| MiMo-V2.6-Pro | API, OpenRouter | Facturé | « Propre à Claude ? », ~10 fois moins cher | 3 (2 si la porte de coût joue) ; 1 sur le jouet |
| Fable 5.1 | Claude Code (`claude -p`) | Abonnement d'Anaël, 0 $ facturé | Plafond de qualité | 1, sur S seulement |

- **Repli** : un modèle Anthropic passe par le pilote API et l'API Anthropic si l'abonnement ne le permet pas ; la séance est alors facturée.
- **Identité du protocole** : changer de modèle ou de pilote ne change ni le prompt système, ni la description de tâche, ni le catalogue d'outils, ni le budget de passes (AD-15, test).
- **Conditions de l'abonnement** : binaire Claude Code non modifié, identifiants jamais passés par une autre application, usage individuel ordinaire.
- **Contamination** : la séance Claude Code tourne avec une configuration dédiée, sans outils intégrés, plugins, mémoire ni `CLAUDE.md` ; sa première requête ne contient que le prompt système et la description de tâche (AD-14, test).
- **Limite d'usage** : une coupure termine la séance en `error`, cause journalisée ; la tentative est rejouée, jamais reprise.

## Ce que l'agent voit

Le paquet de séance seul (AD-2) :

- la description de tâche, avec le **vocabulaire fermé des types d'erreur visibles** (identifiants et descriptions) ; pour S-réservé, les 10 types connus seulement ;
- les exemples non annotés : aucun ne porte d'étiquette ni de type ;
- l'identifiant de l'encodeur, fixé par la tâche (AD-4).

## Ce que l'agent peut faire

Par le catalogue d'outils unique (AD-15) :

- déclarer l'architecture et écrire les poids (A-littéral, par tranches), soumettre un script générateur (A-programme) ou des règles (B) ;
- exécuter sa production sur les exemples non annotés, une passe décomptée à chaque appel ; la passe renvoie les sorties, jamais un score (AD-6) ;
- geler sa production, ce qui clôt la séance ; pour A, le gel exige des blocs qui partitionnent les unités cachées, chacun avec sa règle et des identifiants du vocabulaire visible (AD-8).

Tout le reste est refusé et journalisé avec un code de refus : lecture d'un jeu réservé, gradient, perte, passe au-delà du budget. L'interdit statistique est en partie refusé, en partie audité (section suivante et `protocole-ecriture.md`).

## Isolement du code de l'agent

Tout code écrit par l'agent, script d'A-programme ou règles B, passe par un bac à sable unique (AD-5) :

- sous-processus Python isolé, répertoire vide, environnement sans clé d'API, délai maximal ;
- imports limités au profil : NumPy seul pour A ; `re`, `datetime`, `math`, `unicodedata` pour B ;
- aucun accès aux fichiers ni au réseau ; seule sortie : les poids (A) ou un label par exemple (B, réexécuté dans un espace neuf pour chaque exemple) ;
- corpus d'évasions connu en test de non-régression : chaque cas doit échouer.

**Interdit statistique** (AD-19) :

- **prévention partielle** : refus des fonctions d'ajustement (`lstsq`, `svd`, `pinv`, `eig`, `eigh`, `solve`, `inv`, `polyfit`, `cov`, `corrcoef`) et des codes dont les littéraux dépassent 8 Ko de chaînes ou 512 nombres ;
- **audit a posteriori** : chaque exécution journalise, sans refus, des drapeaux : recouvrement de fragments d'au moins 12 caractères entre littéraux et exemples, boucles sur des tableaux de la taille du jeu d'exemples.

Modèle de menace : le bac à sable bloque les raccourcis d'un agent qui optimise honnêtement, pas une évasion malveillante. L'agent voit les exemples et peut les recopier en littéraux : seul l'audit publié le révèle.

## Pile technique

- Harnais et format des poids : NumPy (`manifest.json` et `weights.npz`, AD-3) ; aucun module du côté séance n'importe de bibliothèque à gradient ni de module de l'évaluateur (AD-1, test).
- C et E : PyTorch, groupe de dépendances `train`, importé seulement par les témoins (AD-13).
- Lot 3 : Tracr dépend de JAX et dm-haiku, peu maintenus ; environnement séparé probable, à vérifier en 3-1.

## Journal de séance

Un `journal.jsonl` par séance, en ajout seul, au schéma de AD-7. Il contient au minimum :

- identifiants : tâche, jeu et sha256, méthode, modèle, **pilote**, fournisseur, tentative, graine, budget de passes, empreintes du protocole et du prompt système ;
- chaque échange avec le modèle et chaque appel d'outil, dans l'ordre, passes numérotées ;
- par appel au modèle : tokens d'entrée, de sortie et de cache, `cost_equiv_usd`, `billed_usd`, coût annoncé par le fournisseur s'il existe, durée ;
- par exécution de code : sha256, résultat, **drapeaux d'audit** ;
- production gelée : sha256 de chaque fichier et de l'arbre ; pour A, tailles nominale et effective ;
- motif de fin : `frozen`, `pass_budget`, `money_budget`, `turn_limit`, `error`.

Aucune clé d'API ni aucun en-tête HTTP n'y entre (test).

## Coût et budget

Deux coûts par appel (AD-11) :

| Coût | Calcul | Usage |
|---|---|---|
| `cost_equiv_usd` | tokens × tarifs datés de `config/pricing.toml`, quel que soit le pilote | Rapport, comparaison entre modèles |
| `billed_usd` | 0 par l'abonnement ; tarif API Anthropic en repli ; calcul tarifaire OpenRouter, contrôlé par son `usage.cost` | Plafonds et porte de coût |

- Seul le facturé s'impute sur les plafonds du lot et du projet.
- Registre `budget/ledger.csv` commité, écrit par un seul module : réservation du plafond de séance à l'ouverture, clôture avec les coûts réels, même en erreur.
- Une séance s'ouvre seulement si facturé + réservations ouvertes + plafond de séance ≤ plafond ; sinon refus et demande de décision à Anaël. En cours de séance, arrêt `money_budget` au plafond de séance.
- Les entraînements locaux (C, E, F) ne consomment pas ce budget.

## Gel et évaluation

- Le gel écrit `frozen/` hors du dépôt, puis plus rien n'y écrit ; sha256 de chaque fichier et de l'arbre dans le journal (AD-8).
- L'évaluation est une commande distincte, côté évaluateur, lancée hors séance : elle vérifie les empreintes, refuse toute divergence, puis calcule les mesures de CAP-12 sur le jeu réservé, ablation des blocs déclarés comprise ; deux évaluations donnent le même résultat (AD-9).

## Publication des journaux

- Poids et journaux partent en assets de la release GitHub du lot ; Hugging Face seulement si le lot 2 dépasse quelques centaines de Mo.
- La commande de publication refuse l'archive si elle contient un motif de clé, un exemple réservé, ou un artefact de R sans autorisation de republier (licence Judilibre, constat 1-3) (AD-18).
