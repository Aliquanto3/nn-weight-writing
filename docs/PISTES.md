# Pistes envisagées

Idées notées le 2026-11-05, avant tout cadrage. Ce document sert de matière à l'atelier `bmad-forge-idea` : rien n'est encore décidé.

## Question de recherche

Quand un LLM écrit directement tous les poids d'un réseau, sans gradient, sur quelles tâches cela vaut-il mieux qu'entraîner ce réseau ? Et jusqu'à quelle taille de modèle la méthode tient-elle ?

Hypothèse de travail : la méthode marche quand la tâche se réduit à des **règles que le LLM connaît déjà** (cohérence de dates, de formats, de numérotation). Elle cale sur les tâches **perceptives**, où le savoir n'est pas formulable en règles, et sur les réseaux trop grands pour être raisonnés neurone par neurone.

## Place parmi les autres projets

| | Ce qu'on modifie | Point de départ | Mode d'action | Dépôt |
|---|---|---|---|---|
| Steering | Les activations, à l'inférence | SLM pré-entraîné | Ajout d'un vecteur, réversible | [mood-steering-slm](https://github.com/Aliquanto3/mood-steering-slm) |
| Édition | Quelques tenseurs | SLM pré-entraîné | Le LLM découvre une direction et la retire | [slm-weight-editing](https://github.com/Aliquanto3/slm-weight-editing) |
| **Écriture** | Tous les poids | Rien | Le LLM traduit un savoir qu'il a déjà en poids | ce dépôt |
| Entraînement | Tous les poids | Initialisation aléatoire | Descente de gradient sur données annotées | ce dépôt (témoin) |

Différence de nature avec l'édition : en édition, le LLM *découvre* quelque chose dans un modèle qu'il ne connaît pas. En écriture, il *compile* ce qu'il sait.

## Méthodes à comparer sur chaque tâche

| Code | Méthode | Ce qu'elle teste |
|---|---|---|
| **A** | Le LLM écrit les poids (protocole Lauritzen et Nuss : description de la tâche, quelques exemples non annotés, aucun gradient) | La méthode étudiée |
| **B** | Le LLM écrit des règles en Python (regex, contrôle de dates), sans réseau | **Témoin décisif** : si B vaut A, le réseau n'est qu'un format de sortie exotique pour un programme à règles |
| **C** | Entraînement standard, en courbe sur N = 64, 256, 1 024, 8 192 exemples et plus | L'efficacité en données, et le point où l'entraînement rattrape A (convergence annoncée par Lauritzen) |
| **D** | Le LLM génère des données annotées, puis on entraîne dessus | Une autre façon de distiller le savoir du LLM, plus classique |
| **E** | Le LLM écrit une initialisation, puis on l'affine par gradient (KBANN revisité) | Le meilleur des deux, s'il existe |
| **F** (option) | C avec des entrées préparées (année, mois, jour extraits) | Vérifie si l'écart A − C vient de la représentation des entrées plutôt que de la méthode |

À chaque méthode, ses mesures :
- exactitude sur un jeu réservé, jamais lu par l'agent ;
- robustesse hors distribution : nouveaux types d'erreurs, autre juridiction, autre format ;
- coût : tokens, euros, minutes, énergie estimée ;
- lisibilité : quelle part des neurones correspond à une règle qu'on peut nommer ;
- variance : plusieurs tentatives par méthode et par modèle (Haiku, Sonnet, Opus, Fable).

## Tâches, par difficulté croissante

1. **Jouets à règles connues** : parité, comparaison de nombres, petit automate. On connaît la solution exacte, ce qui sert à valider le harnais.
2. **Tabulaire à règles** : un jeu public dont la règle de décision est connue ou presque.
3. **Références juridiques françaises** : reproduction de l'expérience de Nuss, puis version durcie (voir plus bas).
4. **Tâche perceptive** : chiffres manuscrits ou une petite classification de textes sans règle évidente. C'est là que la méthode devrait montrer ses limites.
5. **Taille croissante** : même tâche avec 10⁴, 10⁵, 10⁶, 10⁷ paramètres, pour voir où l'écriture cesse d'être faisable ou rentable.

## Durcir l'expérience juridique

- **Casser la circularité** : de vraies références tirées de Judilibre ; de fausses références tirées de vraies hallucinations de SLM (via slm-quality-bench), et pas d'un générateur qui suit les 15 types d'erreurs connus du détecteur.
- **Types d'erreurs tenus à l'écart** : certains types n'apparaissent qu'à l'évaluation, pour mesurer la généralisation.
- **Existence contre cohérence** : la méthode ne peut vérifier que la cohérence. Quantifier la part des fausses références *cohérentes* (bon format, dates plausibles, mais décision inexistante) qu'aucun réseau sans base de données ne détectera.

## Remonter vers les modèles de langage

On ne peut pas écrire à la main le savoir linguistique d'un SLM : la piste « from scratch » s'arrête bien avant. Les pistes qui peuvent passer à l'échelle sont hybrides :

- **Greffe d'un circuit écrit** : le LLM écrit une tête d'attention ou un bloc MLP qui applique une règle (par exemple « la date du pourvoi précède celle de la décision »), puis on le greffe dans un SLM existant (Granite 4.0 350M, Qwen3.5-0.8B). On rejoint alors slm-weight-editing, dont on peut réutiliser le harnais et le protocole (budget de passes, jeux réservés, diff vérifiable).
- **Petit transformer écrit, à la Tracr** : le LLM écrit un transformer de quelques couches sur une tâche algorithmique (tri, comptage, parenthèses). On compare au compilateur Tracr et à un entraînement.
- **Tête de classification écrite au-dessus d'un encodeur gelé** : le LLM écrit seulement la dernière couche, à partir des activations d'un petit encodeur. Le savoir linguistique vient de l'encodeur, les règles du LLM.

## Protocole (à reprendre de slm-weight-editing)

- L'agent qui écrit les poids n'exécute le réseau qu'à travers le harnais, qui compte et journalise chaque passe, dans un budget fixé avant la séance.
- Aucun gradient, aucune perte calculée par l'agent pour la méthode A.
- Les jeux d'évaluation restent hors de portée de l'agent ; l'évaluation tourne après le gel des poids, par une commande à part.
- Chaque réseau écrit est publié avec le journal de sa séance et l'empreinte sha256 de ses poids.

## Contraintes pratiques

- Réseaux de 10⁴ à 10⁶ paramètres : tout tourne sur CPU, aussi sur le portable pro. Pas besoin d'Ollama ni de GPU avant la greffe dans un SLM.
- Le coût vient des séances d'écriture (longues réflexions sur Opus ou Fable). Fixer un budget dès le cadrage, par exemple 3 tentatives par tâche et par modèle.
- Questions à trancher : PyTorch ou NumPy seul pour les petits réseaux ; écriture par l'agent dans Claude Code ou par l'API dans un harnais scripté (plus reproductible, coût mesuré plus précisément).

## Questions ouvertes pour l'atelier

1. Le livrable principal est-il un **banc comparatif** (méthodes × tâches × tailles) ou une **reproduction critique** de l'expérience juridique ?
2. Faut-il viser la publication d'un billet ou d'un rapport, comme pour slm-weight-editing ?
3. Jusqu'où aller vers les SLM dans ce dépôt, et à partir de quand la greffe de circuits relève-t-elle de slm-weight-editing ?
4. Quel budget total en tokens accepter pour les séances d'écriture ?
