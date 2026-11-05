# Constat 1-4 : licences des jeux d'images

Date : 2026-11-05. Périmètre : MNIST, Fashion-MNIST, chiffres 8×8 de scikit-learn (`load_digits`), pour le lot 2 (CAP-1, CAP-14).

## Verdict : feu vert avec réserve (vocabulaire de CAP-1), décision d'Anaël requise sur MNIST avant la story 2-1

- Fashion-MNIST (MIT) et chiffres 8×8 (CC BY 4.0 selon la fiche UCI) : feu vert avec réserve. Réserve : attribution et avis de licence joints à tout ce qui est publié (release, rapport, billet).
- MNIST : licence non établie. La page officielle de LeCun n'a pas pu être consultée (connexion refusée depuis le poste, voir Incertitudes) ; la licence ne repose que sur des sources secondaires qui divergent (CC BY-SA 3.0 pour TensorFlow et PyMVPA, MIT pour la carte Hugging Face). Le jeu étant dérivé de données NIST, aucune source consultée ne tranche leur statut. L'usage local ne pose pas de problème identifié ; la publication de tout artefact qui contient ou reproduit des pixels MNIST (archives de séance, poids ou scripts qui recopient des exemples, figures) reste suspendue à la décision d'Anaël, à consigner avant la story 2-1 (voir « Décision à demander à Anaël »). Ce constat ne prend pas cette décision.

## Table

| Jeu | Licence | Source primaire | Obligations | Usages permis pour nous |
|---|---|---|---|---|
| MNIST (60 000 + 10 000 images 28×28) | Non déclarée sur une source primaire consultée. Sources secondaires : CC BY-SA 3.0 (TensorFlow/Keras, PyMVPA, Armory) ; MIT (carte Hugging Face `ylecun/mnist`). Copyright : LeCun et Cortes (dérivé de NIST). | Page officielle `yann.lecun.com/exdb/mnist/` : non consultée (ECONNREFUSED). | Si CC BY-SA 3.0 : attribution, mention de la licence, partage à l'identique des adaptations (si on redistribue des images ou un dérivé). Si MIT : conserver l'avis de copyright. Dans tous les cas : citer LeCun, Cortes, Burges. | Téléchargement local : oui. Images envoyées à un LLM par API : non traité par les sources ; lu comme une transmission à un prestataire pour un usage de recherche, sans redistribution (interprétation, voir Incertitudes). Scores et résultats chiffrés : oui avec attribution. Poids, scripts, journaux, figures qui contiennent ou reproduisent des images : suspendus à la décision d'Anaël ; si CC BY-SA 3.0 s'applique, partage à l'identique possible, incompatible avec Apache-2.0 pour ces fichiers. Poids entraînés par C et E sur MNIST : statut d'adaptation non établi (voir Incertitudes). |
| Fashion-MNIST (60 000 + 10 000 images 28×28) | MIT, « Copyright © 2017 Zalando SE » | `github.com/zalandoresearch/fashion-mnist` (fichier LICENSE, lu) | Conserver l'avis de copyright et le texte MIT dans les copies ou parties substantielles ; demande de citer l'article arXiv:1708.07747 dans les publications. | Tous nos usages, y compris redistribution d'images, sous réserve de joindre l'avis MIT. Compatible Apache-2.0. |
| Chiffres 8×8 (`load_digits`, 1 797 images, copie du jeu de test UCI) | CC BY 4.0 (fiche UCI du jeu complet, 5 620 instances) | `archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits` (lue) ; doc scikit-learn : « copy of the test set of the UCI ML hand-written digits datasets » | Attribution : citer Alpaydin et Kaynak (1998), DOI 10.24432/C50P49 ; indiquer la licence ; signaler les modifications. Pas de partage à l'identique. Les données viennent de 43 scripteurs ; seuls les programmes de prétraitement sont de NIST (doc scikit-learn, `digits.rst`), ce qui ne change pas la licence UCI. | Tous nos usages, y compris redistribution. Compatible avec une release Apache-2.0 (CC BY 4.0 : attribution seulement). |

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
2. Les archives de séance contiendront des images : AD-7 impose dans `journal.jsonl` le « contenu de l'échange » de chaque `model_call`, donc les parties image montrées à l'agent, et les sorties de passe ou les logs de script peuvent en reproduire. Rien dans la spec ni dans l'architecture n'impose aujourd'hui de les remplacer par une référence (`mnist:test:1234`) ; AD-18 n'exclut que `bundle/`, `data/` et `heldout/` et ne refuse que les motifs de clé, les artefacts de R sans `r_republish` et les `raw` réservés. Une archive `runs-lot2.tar.gz` qui couvre MNIST embarquerait donc des images MNIST. Selon la décision d'Anaël, la story 2-1 doit soit journaliser une référence au lieu des pixels MNIST, soit exclure les séances MNIST de l'archive, soit accepter leur publication sous la licence retenue. Pour Fashion-MNIST et les chiffres 8×8, l'embarquement est permis avec attribution.
3. Poids et scripts : AD-19 rappelle que l'agent voit les exemples et peut les recopier en littéraux dans son code ; en A-littéral ou A-programme, des poids-gabarits ou un script peuvent donc reproduire des images. On ne peut pas affirmer que les poids écrits ne contiennent pas d'image. Les poids entraînés par C ou affinés par E (stories 2-2, 2-4) ne reproduisent pas d'image en clair, mais leur statut d'adaptation au sens d'une licence CC BY-SA n'est pas établi. Seuls les scores et résultats chiffrés sont sûrs.
4. Rapport, billet et figures (CAP-13, CAP-14, story 2-5) : une figure qui montre des exemples MNIST, ou des poids visualisés qui en reproduisent, relève du même point que la release. Fashion-MNIST et chiffres 8×8 : attribution dans la légende ou en fin de document.
5. Ajouter le fichier d'attributions ci-dessus et le texte MIT de Zalando au dépôt, et les citer dans le rapport, le billet et les notes de v0.2.0.
6. Journaliser dans chaque séance le jeu, la version et l'URL de téléchargement.
7. Envoi à un LLM par API : à signaler dans le README (les images de test partent chez Anthropic, ou chez OpenRouter et son fournisseur amont, nommé par le constat 1-2). Les politiques de rétention des fournisseurs ne font pas partie de ce constat.

## Incertitudes

- Page officielle de MNIST : trois essais (https, http, variantes d'URL) ont échoué en connexion refusée ; une copie d'archive n'est pas accessible aux outils. La licence ne vient donc que de sources secondaires divergentes. À refaire depuis un navigateur : lire la page officielle et voir si elle déclare une licence.
- Divergence CC BY-SA 3.0 (TensorFlow/Keras, PyMVPA, Armory ; le texte TensorFlow dit que LeCun et Cortes détiennent le copyright d'un dérivé de NIST) contre MIT (carte Hugging Face). Ces mentions ne sont pas des déclarations de l'auteur.
- Statut des données NIST d'origine (SD-1, SD-3) : la page NIST SD-19 consultée ne dit rien sur leur licence ; non établi.
- Chiffres 8×8 de scikit-learn : le dépôt scikit-learn est sous BSD, mais la licence des données est celle d'UCI. La doc scikit-learn ne reproduit pas la licence des données. La fiche UCI porte la CC BY 4.0 pour le jeu complet ; scikit-learn en distribue la partie test.
- Envoi d'images à une API : aucune des licences consultées ne traite de ce cas ; il est lu comme un usage de recherche non redistribué, interprétation et non constat.
- Poids entraînés sur MNIST (C, E) : aucune source consultée ne dit si un modèle entraîné est une adaptation au sens de CC BY-SA 3.0 ; question juridique ouverte, non tranchée ici.
- Ce document n'est pas un avis juridique.

## Report

Corrections de spec proposées (specs non modifiées) :

1. `jeux-de-donnees.md`, section Images : remplacer « Licences vérifiées au lot 1 (CAP-1) » par un renvoi à ce constat (`docs/verifications/1-4-licences-images.md`) et la mention « MNIST : licence non établie à la source, redistribution des images exclue ».
2. `jeux-de-donnees.md`, tableau « À vérifier » : préciser la ligne « Licences d'images » avec le verdict « feu vert avec réserve ; MNIST, décision d'Anaël ».
3. `ARCHITECTURE-SPINE.md`, AD-18 : selon la décision d'Anaël, ajouter à `nnww publish` le refus d'une archive qui contient des pixels MNIST (journaux compris, AD-7), par analogie avec `r_republish` (par exemple `mnist_republish` dans `config/publish.toml`) ; ou, en AD-7, journaliser une référence au lieu des pixels MNIST.
4. `SPEC.md` CAP-14 ou `stories.yaml` 2-1 et 2-5 : ajouter un critère « fichier d'attributions présent et cité dans le rapport, le billet et les notes de v0.2.0 ».

## Décision à demander à Anaël (MNIST)

À consigner comme décision avant la story 2-1 ; ce constat ne la prend pas.

- **Option A, lever l'incertitude d'abord** : consulter `yann.lecun.com/exdb/mnist/` depuis un navigateur (ou une copie d'archive) et compléter ce constat. Conséquence : courte attente ; si la page déclare une licence, elle s'applique et l'option B ou C se choisit en connaissance de cause.
- **Option B, ne publier aucun pixel MNIST** : MNIST reste utilisé en local et montré au LLM ; journaux MNIST avec référence au lieu des pixels (ou séances MNIST hors archive), refus de publier les poids ou scripts MNIST qui recopient des exemples (audit AD-19), pas de figure d'exemple MNIST. Conséquence : travail en plus en 2-1 (journal, AD-18) ; la reproductibilité des séances MNIST passe par les graines et le téléchargement ; les poids C et E restent publiables si Anaël accepte l'incertitude sur leur statut, sinon ils sont exclus aussi.
- **Option C, publier sous CC BY-SA 3.0** : traiter les artefacts MNIST comme CC BY-SA 3.0 (hypothèse la plus restrictive des sources secondaires), dans un asset distinct avec sa licence, hors Apache-2.0. Conséquence : release à deux licences ; risque résiduel si la licence réelle diffère (statut NIST non établi).
- **Option D, retirer MNIST du lot 2** : remplacer MNIST par Fashion-MNIST pour l'échelle de tailles (story 2-4). Conséquence : modifie CAP-14 et 2-4 ; perte de comparabilité avec la littérature, qui mesure surtout sur MNIST.

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

## Revue

### Passe 1 (2026-11-05, SHA revu 4d3f577)

- Important, high, second avis 1 : « les poids écrits ne contiennent pas d'image » contredit AD-19 (recopie d'exemples en littéraux). Corrigé (Conséquences 3).
- Important, high, second avis 2 : poids C et E entraînés sur MNIST non examinés. Corrigé (Conséquences 3, Incertitudes, option B).
- Important, high, second avis 3 : référence par indice imposée par rien ; AD-7 journalise le contenu des échanges, donc les images. Corrigé (Conséquences 2).
- Important, medium, second avis 4 : verdict hors vocabulaire de CAP-1 et trop fort pour MNIST. Corrigé (feu vert avec réserve, décision MNIST requise avant 2-1).
- Important, medium, second avis 5 : envoi par API affirmé sans source. Corrigé (présenté comme interprétation).
- Important, medium, second avis 6 : report visait `harnais.md` au lieu de AD-18. Corrigé (Report 3).
- Important, medium, second avis 7 : rapport, billet, figures non couverts. Corrigé (Conséquences 4, Report 4).
- Nit, low, second avis 8 : prétraitement NIST des chiffres 8×8. Corrigé (table).
- Nit, low, second avis 9 : reports non appliqués. Rejeté : la story ne modifie pas les specs, ils restent en report.
- Nit, low, second avis 10 : fournisseur amont de MiMo. Corrigé a minima (renvoi au constat 1-2, qui couvre MiMo via OpenRouter).
