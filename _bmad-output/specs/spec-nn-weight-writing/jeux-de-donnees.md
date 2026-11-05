# Jeux de données

Aucun jeu ne va dans un commit. Les jeux réservés restent dans `heldout/` ou hors du dépôt, jamais lus par l'agent.

## Jouet (lot 1)

Parité, comparaison de nombres, petit automate. Solution exacte connue : sert à valider le harnais, pas à conclure.

## S — reproduction de Nuss (lot 1)

- Références de la Cour de cassation, du Conseil d'État et des cours d'appel, fausses références selon 15 types d'erreurs typiques d'une invention de LLM (exemples cités par Nuss : pourvoi formé après la décision, 30 février, chambre inexistante).
- Reconstruit d'après un post LinkedIn, sans code ni données publiés : la reproduction reste approximative, et les écarts sont documentés (CAP-1, CAP-9).
- Repères de Nuss : réseau ~97 000 paramètres, 40 exemples non annotés, 97,7 % sur 4 000 références jamais vues, contre 82,8 % pour le même réseau entraîné sur 8 192 exemples annotés.

## S-réservé (lot 1)

Mêmes données que S, mais l'agent ne connaît que 10 types d'erreurs ; les 5 autres n'apparaissent qu'à l'évaluation. Mesure la généralisation.

## R — sans circularité (lot 1)

- Vraies références : Judilibre (API du portail PISTE).
- Fausses références : hallucinations réelles de SLM, collectées via `slm-quality-bench`, chacune vérifiée inexistante.
- Un normaliseur commun aux vraies et aux fausses, pour que le format ne trahisse pas la classe.
- **Pré-étude** sur ~300 hallucinations : part des incohérentes (détectables sans base) contre les cohérentes (bon format, dates plausibles, décision inexistante), porte des 30 % (`methodes-et-lots.md`).

## Images (lot 2)

Formes synthétiques ; chiffres 8×8 de scikit-learn ; MNIST ; Fashion-MNIST. Licences vérifiées au lot 1 (CAP-1).

## À vérifier au cadrage (CAP-1)

| Point | Ce qu'il faut établir | Ressource d'Anaël |
|---|---|---|
| S d'après Nuss | Liste des 15 types et écarts connus avec l'original | — |
| MiMo via OpenRouter | Identifiant, prix, appels d'outils, vision ; son 97 % vient de la calibration du juge de `slm-quality-bench` et ne se transfère pas forcément à l'écriture de poids | Clé OpenRouter |
| Judilibre | Accès, licence de réutilisation, source équivalente pour le Conseil d'État, collecte des hallucinations via `slm-quality-bench` | Compte PISTE |
| Licences d'images | MNIST, Fashion-MNIST, chiffres de scikit-learn : réutilisation et republication des résultats | — |
