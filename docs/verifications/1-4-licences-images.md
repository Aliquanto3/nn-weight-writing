# Constat 1-4 : licences des jeux d'images

Date : 2026-11-05. Périmètre : MNIST, Fashion-MNIST, chiffres 8×8 de scikit-learn (`load_digits`), pour le lot 2 (CAP-1, CAP-14).

## Verdict : conforme avec réserves

- Fashion-MNIST (MIT) et les chiffres 8×8 (CC BY 4.0 selon la fiche UCI) : réutilisation conforme, avec attribution.
- MNIST : conforme sous réserve. La page officielle de LeCun n'a pas pu être consultée (connexion refusée depuis le poste, voir Incertitudes) ; la licence ne repose donc que sur des sources secondaires qui divergent (CC BY-SA 3.0 pour TensorFlow et PyMVPA, MIT pour la carte Hugging Face). Le jeu étant dérivé de données NIST, aucune source consultée ne tranche leur statut.
- Rien ne bloque les usages prévus. La solution la plus sûre pour MNIST est de ne publier aucune image MNIST dans la release (voir Conséquences).

## Table

| Jeu | Licence | Source primaire | Obligations | Usages permis pour nous |
|---|---|---|---|---|
| MNIST (60 000 + 10 000 images 28×28) | Non déclarée sur une source primaire consultée. Sources secondaires : CC BY-SA 3.0 (TensorFlow/Keras, PyMVPA, Armory) ; MIT (carte Hugging Face `ylecun/mnist`). Copyright : LeCun et Cortes (dérivé de NIST). | Page officielle `yann.lecun.com/exdb/mnist/` : non consultée (ECONNREFUSED). | Si CC BY-SA 3.0 : attribution, mention de la licence, partage à l'identique des adaptations (si on redistribue des images ou un dérivé). Si MIT : conserver l'avis de copyright. Dans tous les cas : citer LeCun, Cortes, Burges. | Téléchargement local : oui. Images envoyées à un LLM par API : oui (usage de recherche, pas une redistribution ; point non détaillé dans les sources, voir Incertitudes). Poids écrits, résultats, scores : oui avec attribution. Redistribuer des images MNIST dans la release : à éviter ; si fait, risque de partage à l'identique incompatible avec Apache-2.0 pour ces fichiers. |
| Fashion-MNIST (60 000 + 10 000 images 28×28) | MIT, « Copyright © 2017 Zalando SE » | `github.com/zalandoresearch/fashion-mnist` (fichier LICENSE, lu) | Conserver l'avis de copyright et le texte MIT dans les copies ou parties substantielles ; demande de citer l'article arXiv:1708.07747 dans les publications. | Tous nos usages, y compris redistribution d'images, sous réserve de joindre l'avis MIT. Compatible Apache-2.0. |
| Chiffres 8×8 (`load_digits`, 1 797 images, copie du jeu de test UCI) | CC BY 4.0 (fiche UCI du jeu complet, 5 620 instances) | `archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits` (lue) ; doc scikit-learn : « copy of the test set of the UCI ML hand-written digits datasets » | Attribution : citer Alpaydin et Kaynak (1998), DOI 10.24432/C50P49 ; indiquer la licence ; signaler les modifications. Pas de partage à l'identique. | Tous nos usages, y compris redistribution. Compatible avec une release Apache-2.0 (CC BY 4.0 : attribution seulement). |

Aucune des trois licences ne limite l'usage à une finalité (pas de clause « non commercial »), ni ne vise l'envoi à une API d'un fournisseur de LLM.

## Attributions prêtes à copier

À placer dans `NOTICE` ou `docs/ATTRIBUTIONS.md` du dépôt, et dans les notes de release.

Chiffres 8×8 :
```
Optical Recognition of Handwritten Digits (UCI Machine Learning Repository)
E. Alpaydin and C. Kaynak (1998). https://doi.org/10.24432/C50P49
Licence CC BY 4.0 : https://creativecommons.org/licenses/by/4.0/
Utilisé via scikit-learn (sklearn.datasets.load_digits, copie du jeu de test, 1 797 images). Nous n'avons pas modifié les données au-delà de leur mise en forme pour l'affichage.
```

Fashion-MNIST :
```
Fashion-MNIST, Copyright (c) 2017 Zalando SE, https://tech.zalando.com
Licence MIT (texte complet dans LICENSES/fashion-mnist-MIT.txt)
Han Xiao, Kashif Rasul, Roland Vollgraf. Fashion-MNIST: a Novel Image Dataset for Benchmarking Machine Learning Algorithms. arXiv:1708.07747, 2017.
```
Joindre le texte MIT complet (copyright Zalando SE) s'il y a redistribution d'images.

MNIST :
```
MNIST handwritten digit database. Yann LeCun (Courant Institute, NYU), Corinna Cortes (Google Labs, New York), Christopher J.C. Burges (Microsoft Research).
http://yann.lecun.com/exdb/mnist/ ; dérivé des bases NIST SD-1 et SD-3.
Les images de ce dépôt ne sont pas redistribuées ; téléchargées localement par l'utilisateur.
```
Si des images MNIST sont tout de même redistribuées, ajouter : « Copyright LeCun et Cortes, mis à disposition selon les sources secondaires sous CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/) » et traiter le point de partage à l'identique avant publication.

## Conséquences pour la story 2-1

1. `data/` et `heldout/` restent hors commit (déjà prévu) ; le harnais télécharge les jeux depuis leur source (scikit-learn embarque les chiffres 8×8 dans son paquet ; Fashion-MNIST et MNIST par téléchargement).
2. Ne pas placer d'image MNIST, ni d'archive de séance qui en embarque, dans la release publique sans décision explicite d'Anaël ; les archives de séance peuvent référencer les images par indice et jeu (par exemple `mnist:test:1234`) plutôt que les contenir. Pour Fashion-MNIST et les chiffres 8×8, l'embarquement est permis avec attribution.
3. Les poids écrits et les scores ne contiennent pas d'image : aucune obligation de partage à l'identique à notre connaissance ; ils citent seulement les jeux.
4. Ajouter le fichier d'attributions ci-dessus et le texte MIT de Zalando au dépôt, et les citer dans le rapport de release v0.2.0.
5. Journaliser dans chaque séance le jeu, la version et l'URL de téléchargement.
6. Envoi à un LLM par API : à signaler dans le README (les images de test partent chez Anthropic ou OpenRouter). Les politiques de rétention des fournisseurs ne font pas partie de ce constat.

## Incertitudes

- Page officielle de MNIST : trois essais (https, http, variantes d'URL) ont échoué en connexion refusée ; une copie d'archive n'est pas accessible aux outils. La licence ne vient donc que de sources secondaires divergentes. À refaire depuis un navigateur : lire la page officielle et voir si elle déclare une licence.
- Divergence CC BY-SA 3.0 (TensorFlow/Keras, PyMVPA, Armory ; le texte TensorFlow dit que LeCun et Cortes détiennent le copyright d'un dérivé de NIST) contre MIT (carte Hugging Face). Ces mentions ne sont pas des déclarations de l'auteur.
- Statut des données NIST d'origine (SD-1, SD-3) : la page NIST SD-19 consultée ne dit rien sur leur licence ; non établi.
- Chiffres 8×8 de scikit-learn : le dépôt scikit-learn est sous BSD, mais la licence des données est celle d'UCI. La doc scikit-learn ne reproduit pas la licence des données. La fiche UCI porte la CC BY 4.0 pour le jeu complet ; scikit-learn en distribue la partie test.
- Envoi d'images à une API : aucune des licences consultées ne traite de ce cas ; il est lu comme un usage de recherche non redistribué, interprétation et non constat.
- Ce document n'est pas un avis juridique.

## Report

Corrections de spec proposées (specs non modifiées) :

1. `jeux-de-donnees.md`, section Images : remplacer « Licences vérifiées au lot 1 (CAP-1) » par un renvoi à ce constat (`docs/verifications/1-4-licences-images.md`) et la mention « MNIST : licence non établie à la source, redistribution des images exclue ».
2. `jeux-de-donnees.md`, tableau « À vérifier » : préciser la ligne « Licences d'images » avec le verdict « conforme avec réserves ».
3. `harnais.md` (publication, AD-18) : ajouter à la commande de publication le refus d'une archive qui contient des images MNIST, par analogie avec le refus des artefacts de R.
4. `SPEC.md` CAP-14 ou `stories.yaml` 2-1 : ajouter un critère « fichier d'attributions présent et cité dans les notes de v0.2.0 ».
5. Décision à demander à Anaël : accepter l'exclusion des images MNIST de la release, ou faire lever l'incertitude (page officielle consultée depuis un navigateur).

## Sources (consultées le 2026-11-05)

- UCI, Optical Recognition of Handwritten Digits : https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits (primaire ; CC BY 4.0, citation, DOI)
- scikit-learn, `load_digits` : https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_digits.html ; description du jeu : https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/sklearn/datasets/descr/digits.rst
- Fashion-MNIST, dépôt : https://github.com/zalandoresearch/fashion-mnist ; licence : https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/LICENSE (primaire)
- MNIST, page officielle : http://yann.lecun.com/exdb/mnist/ (non consultée, connexion refusée)
- TensorFlow/Keras, `mnist.load_data` (secondaire, CC BY-SA 3.0) : https://www.tensorflow.org/api_docs/python/tf/keras/datasets/mnist/load_data
- PyMVPA, MNIST (secondaire, CC BY-SA 3.0) : http://www.pymvpa.org/datadb/mnist.html
- Armory, licences de jeux (secondaire) : https://armory.readthedocs.io/en/latest/dataset_licensing/
- Hugging Face, `ylecun/mnist` (secondaire, MIT) : https://huggingface.co/datasets/ylecun/mnist et https://huggingface.co/datasets/ylecun/mnist/raw/main/README.md
- TensorFlow Datasets, MNIST (citation) : https://www.tensorflow.org/datasets/catalog/mnist
- NIST SD-19 (rien sur les licences SD-1/SD-3) : https://www.nist.gov/srd/nist-special-database-19
- Wikipedia, MNIST database (aucune licence du jeu) : https://en.wikipedia.org/wiki/MNIST_database
