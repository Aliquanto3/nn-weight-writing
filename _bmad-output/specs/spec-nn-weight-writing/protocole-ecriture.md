# Protocole d'écriture

S'applique aux séances A-programme, A-littéral et B, quel que soit le pilote (Claude Code ou API). Il est figé avant la première séance mesurée ; toute modification ensuite invalide les séances déjà faites et se consigne comme décision.

## Autorisé

- Regarder les exemples non annotés du paquet de séance et le vocabulaire fermé des types d'erreur visibles (AD-2).
- Y exécuter le réseau ou les règles par le harnais, dans le budget de passes ; une passe renvoie les sorties, jamais un score.

## Budget de passes

- 20 passes par séance, identiques pour A et B et à toutes les tailles (sans quoi le signal (a) du critère de limite ne veut rien dire).
- Seule l'exécution sur les exemples est une passe, décomptée avant exécution, même si la production est invalide ; soumettre un script ou des règles n'en est pas une (AD-6).
- Après la dernière passe, seul le gel reste permis.
- Recalibré une seule fois après le jouet, décision consignée, puis figé pour toutes les séances mesurées.

## Interdit

- Tout gradient, toute perte calculée par l'agent (méthodes A).
- Toute statistique qui produit des poids : moyenne, k-means, ACP, ou équivalent.
- Toute annotation des exemples par l'agent.
- Tout accès à un jeu réservé : il reste dans `heldout/` ou hors du dépôt ; l'évaluation tourne après le gel, par une commande à part.
- Tout accès aux données depuis le code de l'agent (script d'A-programme, règles B) : il s'exécute isolé (`harnais.md`).

## Contrôle de l'interdit statistique

L'agent voit les exemples et peut les recopier dans son code : le harnais ne peut pas tout empêcher (AD-19).

- **Refusé à la soumission** : fonctions d'ajustement (`lstsq`, `svd`, `pinv`, `eig`, `eigh`, `solve`, `inv`, `polyfit`, `cov`, `corrcoef`) ; littéraux au-delà de 8 Ko de chaînes ou 512 nombres.
- **Signalé sans refus** : recouvrement de fragments d'au moins 12 caractères entre littéraux et exemples ; boucles sur des tableaux de la taille du jeu d'exemples.
- **Jugé avant conclusion** : le rapport publie les drapeaux par séance ; une séance signalée est relue et jugée, et la décision est consignée avant d'en tirer une conclusion.

## Deux définitions de A

- **A-littéral** : chaque poids écrit en clair ; réseau réduit (~10⁴ paramètres) pour tenir dans une séance.
- **A-programme** : un script générateur produit les poids ; script journalisé et publié.
- Les deux sont comparées vers 10⁴ paramètres ; sur S, A-programme est aussi mesuré vers 10⁵ (taille de Nuss). Sur S-réservé et R : A-programme vers 10⁵, A-littéral vers 10⁴.
- Au gel, l'agent déclare la règle que chaque bloc de neurones applique, et les types visés, pris dans le vocabulaire visible (base de la mesure de lisibilité).
- Deux tailles mesurées : nominale (nombre de paramètres) et effective (longueur du script, taille compressée des poids).

## Critère de limite (montée en taille)

On s'arrête au premier des trois signaux :

1. (a) plus de réseau valide dans le budget de passes ;
2. (b) A plafonne alors que C monte encore, à données égales ;
3. (c) A passe sous B.

Prédiction consignée avant mesure : (b) vers 10⁵ paramètres.

## Publication

Chaque réseau écrit est publié avec le journal de sa séance, l'empreinte sha256 de ses poids et ses drapeaux d'audit ; le code de B est publié. Le protocole lui-même est publié avec le rapport.
