# nn-weight-writing

Faire écrire par un LLM tous les poids d'un réseau de neurones, sans entraînement, puis comparer le résultat aux règles écrites en code, à l'entraînement standard, à l'édition de poids et au steering.

> **État : spécification.** Aucun code pour l'instant. Sources dans [`docs/SOURCES.md`](docs/SOURCES.md), pistes envisagées dans [`docs/PISTES.md`](docs/PISTES.md) ; le cadrage BMAD suivra dans `_bmad-output/planning-artifacts/`.

## Idée

Début novembre 2026, Jacob Lauritzen (Legora) a fait écrire par Fable les poids d'un réseau d'environ 100 k paramètres qui distingue vraies et fausses citations juridiques ([fil sur X](https://x.com/jacsebl/status/2117606206764175543)). Jorick Nuss a reproduit l'expérience sur le droit français avec Claude Sonnet 5.5 : 97,7 % de précision pour les poids écrits, contre 82,8 % pour le même réseau entraîné sur 8 192 exemples annotés. Ces chiffres sont ceux qu'il rapporte ; ni code ni données n'ont été publiés.

Ce dépôt veut vérifier ce résultat avec les témoins qui manquent, puis voir jusqu'où la méthode tient :

- **témoin à règles** : le même LLM écrit des règles en Python ; si elles valent le réseau, celui-ci n'apporte rien ;
- **courbe d'entraînement** : à partir de combien d'exemples annotés l'entraînement rattrape-t-il les poids écrits ?
- **données moins circulaires** : vraies références tirées de l'open data, fausses références tirées de vraies hallucinations de SLM ;
- **montée en taille et en difficulté** : des tâches à règles aux tâches perceptives, de 10⁴ à 10⁷ paramètres, puis la greffe d'un circuit écrit dans un petit modèle de langage.

## Ce que ce n'est pas

Un détecteur de références juridiques prêt à l'emploi. Un réseau sans base de données vérifie la cohérence d'une référence, pas son existence.

## Projets liés

- [slm-weight-editing](https://github.com/Aliquanto3/slm-weight-editing) : un LLM édite quelques poids d'un SLM déjà entraîné pour corriger un défaut.
- [mood-steering-slm](https://github.com/Aliquanto3/mood-steering-slm) : un vecteur ajouté aux activations à l'inférence, sans toucher aux poids.
- [slm-quality-bench](https://github.com/Aliquanto3/slm-quality-bench) : banc d'évaluation en français des SLM, source possible de vraies hallucinations.

## Licence

[Apache 2.0](LICENSE).
