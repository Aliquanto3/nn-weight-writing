---
story: "1-8"
title: Séances sur le jouet et calibrage du budget de passes (partie Sonnet)
status: review
branch: exp/1-8-jouet-sonnet
---

# Story 1-8 (partie Sonnet) : séances sur le jouet

## Objet

Séances A-programme, A-littéral et B de `sonnet-5.5` (pilote Claude Code, abonnement) sur les trois tâches jouet, 1 tentative par case, lot 1, effort `medium` inchangé. Recalibrage du budget de passes croisant MiMo et Sonnet. Relevés complets : `docs/experiences/1-8-jouet-sonnet.md`.

## Livrables

- `docs/experiences/1-8-jouet-sonnet.md` (tableau des 9 cases, défauts, preuve de l'événement `init`, étanchéité, recalibrage).
- `budget/ledger.csv` écrit par le harnais.
- Correctifs `bf4c086` et `ef9f6cb` : `session/claude_code.py` (contrôle de la configuration dédiée) et `tests/test_claude_code.py`.

## Décisions

- D1 Mêmes graines et jeux qu'en MiMo (graine 0, `--n 256 --n-heldout 400`), exactitude par `scripts/exactitude_reserve.py`.
- D2 `plugins/` n'est admis que sans plugin installé (cache des places de marché, `installed_plugins.json` à table vide) ; `settings.json` : seules les clés `$schema` et `theme` sont admises (sans effet sur le contexte ni les outils).
- D3 `skills/synced`, `plugins/store`, `plugins/synced` (copies du compte claude.ai recréées par Claude Code) admis : non chargés, `skills` vide dans l'événement `init` avec `--disable-slash-commands`, contrôlé à chaque séance. Le dossier d'Anaël n'est pas modifié.
- D4 `protocol.toml` et prompt système inchangés ; recommandation de budget consignée sans modifier le protocole : `pass_budget = 20` conservé.

## Résultats

9 séances gelées sur 9, 400/400 sur le réservé, 0 à 3 passes sur 20, 0 $ facturé, 0,421884 $ équivalent API (journal ; environ le double selon `result.total_cost_usd` de Claude Code), aucun drapeau d'audit, aucune limite d'usage. Une séance refusée avant lancement par le défaut 2, rejouée. Événement `init` : aucun plugin tiers, skill, commande ni outil hors serveur du harnais (agents : seuls les intégrés).

## Reports

- Coût équivalent du pilote Claude Code sous-estimé d'environ moitié (jetons de sortie partiels dans les événements `assistant`, cache écrit en tranche d'une heure non pris en compte par `pricing.toml`) : lire `result.usage`, trancher le tarif de cache (story du harnais).
- Contrôle des `agents` de `init` dans `init_problems` ; éventuellement `syncClaudeAiSkills: false` dans le `settings.json` dédié.
- Décision de `pass_budget` avant 1-9 ; effort `medium` des modèles Claude à confirmer par Anaël ; commande d'exactitude : 1-14.
