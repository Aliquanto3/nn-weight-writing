# Sources

Sources à l'origine du projet et travaux voisins, classés par proximité avec la méthode étudiée : un LLM écrit tous les poids d'un réseau de neurones, sans entraînement. Relevé du 2026-11-05.

## 1. Point de départ : poids écrits par un LLM (novembre 2026)

| Source | Ce qu'elle rapporte | Statut |
|---|---|---|
| Jacob Lauritzen (CTO de Legora), fil sur X du 2026-11-03 : <https://x.com/jacsebl/status/2117606206764175543> | Fable écrit à la main les poids d'un modèle d'environ 100 k paramètres qui distingue les vraies citations juridiques des fausses. Selon lui, le réseau est obtenu presque du premier coup et fait mieux que l'entraînement. Il ajoute que **les deux approches convergent quand on entraîne plus longtemps**. | Fil seulement : ni code, ni données, ni protocole détaillé trouvés (recherche web du 2026-11-05). |
| Jorick Nuss (CTO et cofondateur de Haiku, LegalTech), post LinkedIn du ~2026-11-04 | Reproduction sur le **droit français** (Cour de cassation, Conseil d'État, cours d'appel) avec **Claude Sonnet 5.5**. 15 types d'erreurs typiques d'une référence inventée par un LLM (pourvoi formé après la décision, 30 février, chambre inexistante…). Réseau d'environ 97 000 paramètres, conçu à partir de la description de la tâche et de 40 exemples non annotés, sans descente de gradient. Après 6 min de réflexion : **97,7 %** de précision sur 4 000 références jamais vues, contre **82,8 %** pour le même réseau entraîné sur 8 192 exemples annotés. Des blocs de neurones correspondent à des règles lisibles, comme l'écart entre l'année du pourvoi et celle de la décision. | L'auteur le dit lui-même : données synthétiques, le réseau contrôle la cohérence d'une référence, pas son existence. Pas de lien vers le code. |

Points à vérifier avant d'y croire (détail dans [`PISTES.md`](PISTES.md)) : il manque un témoin à règles écrites en Python ; les données sont peut-être circulaires (le générateur de fausses références et le détecteur partent des mêmes 15 types d'erreurs) ; la ligne de base entraînée a pu être désavantagée (arithmétique sur des dates apprise à partir de caractères bruts) ; l'avantage disparaît quand on entraîne plus longtemps.

## 2. Programmer des réseaux sans gradient : la lignée « compilation »

- **KBANN**, G. Towell et J. Shavlik, « Knowledge-Based Artificial Neural Networks », *Artificial Intelligence* 70, 1994. Traduit un jeu de règles propositionnelles en poids initiaux, puis affine par rétropropagation. C'est l'ancêtre direct de la méthode « poids écrits puis affinés ».
- **RASP**, G. Weiss, Y. Goldberg et E. Yahav, « Thinking Like Transformers », ICML 2021, [arXiv:2106.06981](https://arxiv.org/abs/2106.06981). Un langage de programmes dont chaque opération correspond à un mécanisme de transformer.
- **Tracr**, D. Lindner et al., « Tracr: Compiled Transformers as a Laboratory for Interpretability », 2023, [arXiv:2301.05062](https://arxiv.org/abs/2301.05062). Compile un programme RASP en poids de transformer, sans entraînement.
- **Learning Transformer Programs**, D. Friedman, A. Wettig et D. Chen, NeurIPS 2023, [arXiv:2306.01128](https://arxiv.org/abs/2306.01128). Le chemin inverse : entraîner un transformer contraint pour qu'il se relise comme un programme.

La nouveauté de novembre 2026 tient au compilateur : ce n'est plus un outil déterministe qui part d'un programme formel, c'est le LLM lui-même, à partir d'une description en langue naturelle.

## 3. Éditer un modèle déjà entraîné (dépôts voisins)

- **Weight-space programming**, MIT CSAIL, novembre 2026 : un LLM de pointe trouve dans Qwen3.5-0.8B la direction qui fait boucler le raisonnement, puis la retire de 0,016 % des poids. [Billet](https://rikiyat.github.io/blog/weight-space-programming/), [modèle](https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming). C'est la base de [slm-weight-editing](https://github.com/Aliquanto3/slm-weight-editing).
- **ROME**, K. Meng et al., « Locating and Editing Factual Associations in GPT », 2022, [arXiv:2202.05262](https://arxiv.org/abs/2202.05262), et **MEMIT**, « Mass-Editing Memory in a Transformer », 2022, [arXiv:2210.07229](https://arxiv.org/abs/2210.07229) : éditions de faits en forme close dans les couches MLP.

## 4. Agir sur les activations, sans toucher aux poids (dépôt voisin)

- **ActAdd**, A. Turner et al., « Steering Language Models With Activation Engineering », 2023, [arXiv:2308.10248](https://arxiv.org/abs/2308.10248).
- **Representation Engineering**, A. Zou et al., 2023, [arXiv:2310.01405](https://arxiv.org/abs/2310.01405).
- Ces deux travaux fondent [mood-steering-slm](https://github.com/Aliquanto3/mood-steering-slm).

## 5. Transférer un savoir sans annotation

- **Distillation**, G. Hinton, O. Vinyals et J. Dean, « Distilling the Knowledge in a Neural Network », 2015, [arXiv:1503.02531](https://arxiv.org/abs/1503.02531). Nuss présente l'écriture de poids comme une forme de distillation : le savoir vient de ce que le LLM sait déjà, pas des données. La différence est qu'il n'y a ici ni modèle enseignant interrogé exemple par exemple, ni gradient.

## 6. Données pour le cas juridique français

- **Judilibre** : open data des décisions de la Cour de cassation (et des cours d'appel), accessible par API sur le portail [PISTE](https://piste.gouv.fr). Il fournit de vraies références.
- **Fausses références réelles** : les hallucinations de SLM relevées par [slm-quality-bench](https://github.com/Aliquanto3/slm-quality-bench), à collecter. Elles donneraient une distribution d'erreurs qui ne vient pas du même LLM que le détecteur.

À vérifier pendant le cadrage : les conditions d'accès à Judilibre et sa licence de réutilisation, et une source équivalente pour le Conseil d'État.
