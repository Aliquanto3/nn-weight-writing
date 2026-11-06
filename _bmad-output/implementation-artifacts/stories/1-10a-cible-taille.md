---
story: "1-10a"
title: Taille cible des séances A
status: review
branch: feat/1-10-cible-taille
---

# Story 1-10a : taille cible des séances A

## Objet

Préparation de 1-10 : les cases demandent « A-programme vers 10⁴ » ou « vers 10⁵ » ; le harnais ne savait pas exprimer la taille visée.

## Comportement

- `size_target` (option CLI `--size-target`) : 10000 ou 100000, obligatoire pour A-program et A-literal, interdit pour B ; toute autre valeur est refusée à l'ouverture (`ValueError`, code de sortie 2 en CLI, avant toute réservation au registre).
- Fenêtre d'une demi-décade `[N/√10, N·√10]`, bornes arrondies : [3162 ; 31623] pour 10⁴, [31623 ; 316228] pour 10⁵.
- Le prompt système ajoute pour A la ligne « Taille visée : environ 10⁴ paramètres ; declare_network refuse un réseau hors de [3 162 ; 31 623]. » ; il reste indépendant du modèle et du pilote (identité à (tâche, méthode, taille cible)).
- `declare_network` refuse un manifeste hors fenêtre : code `size_out_of_range`, message avec le nombre déclaré et la fenêtre, aucune passe consommée, refus journalisé.
- `size_target` figure dans l'événement `open` (`null` pour B) et dans l'identifiant de séance (`legal_s-A-program-1e4-<modèle>-t1-<horodatage>`).
- Budget de passes (20) et `config/protocol.toml` inchangés.

## Tests

`tests/test_size_target.py`, `tests/test_cli_session.py`, `tests/test_tools.py`, `tests/test_api_driver.py` (identité du prompt par taille ; séance jouet aux poids complétés par des unités inertes jusqu'à la fenêtre). La fixture `make_service` ouvre les séances A à 10⁴ puis lève la fenêtre quand aucune taille n'est demandée (réseaux jouets).
