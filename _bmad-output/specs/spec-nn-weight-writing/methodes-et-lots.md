# Méthodes et lots

## Méthodes

| Code | Méthode | Ce qu'elle teste | Lots |
|---|---|---|---|
| A-programme | Le LLM écrit un script qui génère les poids | La méthode étudiée, forme compacte | 1, 2, 3 |
| A-littéral | Le LLM écrit chaque poids en clair (~10⁴ paramètres) | La méthode étudiée, forme stricte | 1 |
| B | Le LLM écrit des règles Python, sans réseau | Témoin décisif : si B ≥ A, le réseau n'est qu'un format de sortie | 1, 2 |
| C | Entraînement standard : courbe N = 64, 256, 1 024, 8 192 et plus sur une architecture de référence fixe par tâche ; chaque architecture écrite en A réentraînée depuis des poids aléatoires à N = 8 192 | Efficacité en données ; point où C rattrape A ; l'écart vient-il des poids ou de la forme du réseau ? | 1, 2, 3 |
| E | A sert d'initialisation, puis affinage par gradient (KBANN) | Seul intérêt propre au réseau : la différentiabilité | 2 |
| F | C avec entrées préparées (année, mois, jour extraits) | L'écart A − C vient-il de la représentation des entrées ? | 1 |

Mesures de chaque case : exactitude sur le jeu réservé, robustesse hors distribution (types tenus à l'écart, autre source), coût (tokens, dollars facturés et équivalent API, minutes, énergie estimée), lisibilité, variance entre tentatives. Le coût équivalent API compare les modèles quel que soit le pilote ; le facturé dit ce que le projet a payé (AD-11).

**Audit de l'interdit statistique** : chaque case publie les drapeaux de ses séances (AD-19) ; une séance signalée est jugée, décision consignée, avant d'entrer dans une conclusion.

**Lisibilité**, sans juge humain ni LLM : l'évaluation éteint chaque bloc de neurones déclaré au gel et mesure la baisse d'exactitude par type d'erreur ; score = part des neurones dont l'extinction touche surtout le type déclaré. Mesurable sur S et S-réservé, où les types sont étiquetés ; qualitative sur les images.

## Lot 1 — reproduction critique (100 $ facturés)

- Ordre : vérifications de cadrage, harnais, jouet, puis juridique (S, S-réservé, pré-étude R, R).
- Méthodes : A-programme, A-littéral, B, C en courbe, F.
- Modèles : Sonnet 5.5 (pilote Claude Code, abonnement) et MiMo-V2.6-Pro (pilote API, OpenRouter), 3 tentatives par case sur les jeux juridiques, 1 sur le jouet (~18 séances au lieu de 54, 20 à 35 $ reportés sur S et R ; estimation faite avant le pilote Claude Code) ; Fable 5.1 (abonnement), 1 tentative sur S.
- Le jouet calibre le budget de passes ; ses séances ne comptent pas dans les conclusions.
- **Porte de coût**, calculée sur le coût **facturé** (AD-11) des premières séances Sonnet de S (plus représentatives que le jouet) : si la séance médiane dépasse 2 $, on passe à 2 tentatives par case pour la suite. Par abonnement, Sonnet est facturé 0 $ et la porte ne joue pas (3 tentatives) ; elle ne joue qu'en repli sur l'API Anthropic.
- **Porte avant R**, après la pré-étude : si moins de 30 % des hallucinations sont incohérentes, R devient une mesure de plafond et non un comparatif.
  - Règle fixée le 2026-11-07, avant toute collecte (report R4 du constat 1-3 ; décision de l'orchestrateur, à confirmer par Anaël) :
  - unité : la référence normalisée et dédupliquée (juridiction, numéro normalisé, date) ; une référence qui existe dans la base sort du compte ;
  - hallucination incohérente : défaut détectable sans base, selon une grille fixée avant de voir les données (format, calendrier, chronologie, chambre ou formation existante, cohérence de l'ECLI, « autre ») ; hallucination cohérente : bien formée et plausible, vérifiée absente de la base dans sa fenêtre de couverture ;
  - les « non vérifiables » (cohérentes hors fenêtre de couverture) sont exclues du dénominateur, comptées et publiées à part ;
  - part p = incohérentes / (incohérentes + cohérentes absentes), intervalle de Wilson à 95 % ; p < 30 % → mesure de plafond, p ≥ 30 % → comparatif, sur l'estimation ponctuelle ; si l'intervalle contient 30 %, la décision suit p et le rapport la dit « serrée » ;
  - la taille de la collecte est fixée par le lot pilote de 1-12a, avant tout classement ; pas de collecte supplémentaire après avoir vu p.
- Livrables : `docs/rapport-lot1.md`, release v0.1.0, brouillon de billet LinkedIn en réponse à Nuss, publié par Anaël.

## Lot 2 — où le réseau compte (75 $ facturés)

- Méthodes : A, B, C, E.
- Tâches : formes synthétiques, puis chiffres 8×8 de scikit-learn et MNIST, puis Fashion-MNIST.
- Échelle de tailles de 10⁴ à 10⁷ paramètres, sur MNIST seulement, jusqu'au critère de limite (`protocole-ecriture.md`).
- **Choix du modèle** : MiMo s'il reste à moins de 3 points de Sonnet au lot 1, sinon Sonnet avec 3 tentatives par abonnement (2 seulement en repli sur l'API Anthropic facturée).
- MiMo doit voir les images : la vision est vérifiée au lot 1 (CAP-1).
- Livrables : release v0.2.0 ; billet seulement si un résultat est marquant.

## Lot 3 — conditionnel (25 $)

Petit transformer écrit sur 1 ou 2 tâches algorithmiques (tri, comptage, parenthèses), comparé à Tracr et à un entraînement.

**Déclenchement**, vérifié après le rapport du lot 2, les trois conditions réunies :

1. il reste au moins 25 $ de budget facturé ;
2. au lot 2, A a produit un réseau valide à 10⁵ paramètres ou plus (le signal (a) n'a pas joué avant) : écrire un transformer est plus dur qu'un MLP ;
3. Anaël donne son feu vert.
