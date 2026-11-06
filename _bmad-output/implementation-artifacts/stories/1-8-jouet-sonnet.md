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
- Correctifs `aed4996` et `49ce9c0` (`bf4c086`, `ef9f6cb` avant rebase) : `session/claude_code.py` (contrôle de la configuration dédiée) et `tests/test_claude_code.py`.

## Décisions

- D1 Mêmes graines et jeux qu'en MiMo (graine 0, `--n 256 --n-heldout 400`), exactitude par `scripts/exactitude_reserve.py`.
- D2 `plugins/` n'est admis que sans plugin installé (cache des places de marché, `installed_plugins.json` à table vide) ; `settings.json` : seules les clés `$schema` et `theme` sont admises (sans effet sur le contexte ni les outils).
- D3 `skills/synced`, `plugins/store`, `plugins/synced` (copies du compte claude.ai recréées par Claude Code) admis : non chargés, `skills` vide dans l'événement `init` avec `--disable-slash-commands`, contrôlé à chaque séance. Le dossier d'Anaël n'est pas modifié.
- D4 `protocol.toml` et prompt système inchangés ; recommandation de budget consignée sans modifier le protocole : `pass_budget = 20` conservé.

## Résultats

9 séances gelées sur 9, 400/400 sur le réservé, 0 à 3 passes sur 20, 0 $ facturé, 0,421884 $ équivalent API au journal, 0,828 $ équivalent réel estimé (`result.total_cost_usd` de Claude Code, une séance estimée × 2,08), aucun drapeau d'audit, aucune limite d'usage. Une séance refusée avant lancement par le défaut 2, rejouée. Événement `init` : aucun plugin tiers, skill, commande ni outil hors serveur du harnais (agents : seuls les intégrés).

## Reports

- Coût équivalent et contrôle des `agents` : corrigés en revue (`5adf75b`). Reste : tarif `cache_write_1h` de Fable 5.1 (20,00 $) à confirmer sur la page de prix ; première séance réelle après correctif à vérifier (réconciliation présente, `end.totals.cost_equiv_usd` égal à `total_cost_usd` au micro-dollar près). Éventuellement `syncClaudeAiSkills: false` dans le `settings.json` dédié.
- Décision de `pass_budget` avant 1-9 ; effort `medium` des modèles Claude à confirmer par Anaël ; commande d'exactitude : 1-14.

## Revue

### Passe 1 (2026-11-06, SHA revu 172ae8a)

Base : `origin/main` 925c602, à jour. Correctifs : `5adf75b` (Fix), compte rendu (Docs).

- Important, medium, second avis 2 et 4 : écriture du cache d'une heure tarifée au taux de 5 min, équivalents biaisés bas. Corrigé : `cache_write_1h` dans `Price` et `pricing.toml` (Sonnet 4,00 $ relevé ; Fable 20,00 $ à confirmer), `Usage.cache_write_1h`, champ optionnel `cache_write_1h_tokens` du `model_call` (lecteur rétrocompatible, `OPTIONAL_FIELDS`).
- Important, medium, second avis 3 : sortie partielle des événements `assistant`. Prouvé par le compte rendu (84 contre 2138 jetons). Corrigé : journal gardé ouvert après le gel pour ce pilote (`close_on_freeze`), `model_call` de réconciliation sur `result.usage` avec `total_cost_usd` ; test sur flux simulé (`test_session_cost_reconciled_with_result_usage_and_1h_cache`) et refus d'outil après gel testé.
- Important, medium, second avis 1 : « doubler » présenté comme majorant. Corrigé : tableau des équivalents réels des 9 séances, 0,828 $ (parité A-programme estimée × 2,08, marquée).
- Nit, low, second avis 5 : `skills` fichier → `NotADirectoryError`. Corrigé et testé.
- Nit, low, second avis 6 : `installed_plugins.json` non UTF-8 levait. Corrigé et testé. `"plugins": null` : rejeté (aucun plugin déclaré, admis à bon droit).
- Nit, low, second avis 7 : `agents` non contrôlé. Corrigé : seuls les cinq agents intégrés observés admis, testé.
- Nit, low, second avis 8 : cas `plugins` au niveau séance. Rejeté : `config_dir_problems` est l'unique entrée et le cas séance `skills` couvre le chemin de refus avant lancement.
- Nit, low, second avis 9 : lignes de registre dans le commit Fix. Noté, historique non réécrit en revue (correctif et données séparables plus tard si voulu).
- Nit, low, second avis 10 : « ligne error » et SHA d'avant rebase. Corrigé dans le compte rendu et la spec.
- Nit, low, revue : une séance tuée (délai, contamination) n'a pas de `result` et garde un équivalent partiel. Reporté, noté au compte rendu.
- Complexité : 0 constat (réconciliation en O(messages), une fois par séance).

### Passe 2 (2026-11-06, SHA revu 434d9cc)

Base : rebasée sur `origin/main` 050cc3a, sans conflit. Relu : correctifs de la passe 1 (`5c287ce` Fix, `434d9cc` Docs).

- Gel du pilote Claude Code (`close_on_freeze = False`) : tenu. Après le gel, `_call` refuse sans journaliser ni compter de passe (production et empreintes figées), `_outcome` rend `frozen` avant délai ou contamination, `run.py` clôt en `frozen` avec la cause sur exception, pilote API inchangé (défaut `True`), ligne `closed` du registre écrite dans le `finally`.
- Nit, low, revue : délai et exception après le gel non testés. Corrigé : `test_timeout_after_freeze_keeps_frozen`, `test_error_after_freeze_keeps_frozen_and_is_raised` (option `hang_after_turns` du faux `claude`).
- Réconciliation : tenue. Écart par clé borné à 0 (écart négatif ignoré, pas de double comptage, sommes des maxima par message), `total_cost_usd` seulement dans `exchange`, coût recalculé à nos tarifs ; oracle du test calculé à la main (4406 µ$), totaux et registre cohérents.
- `cache_write_1h` : tenu. Sonnet 4,00 $, Fable 20,00 $ marqué à confirmer ; pilote API et OpenRouter sans `cache_write_1h` (tarif de 5 min) ; les 10 journaux de `runs/` relus sans erreur par `read_records`.
- Nit, low, revue : `totals` de l'`end` sans `cache_write_1h_tokens` (le coût l'intègre, la part n'est lisible qu'en sommant les `model_call`). Rejeté pour cette story : pas de consommateur.
- Pre-existing, low, revue : un `usage` à valeur non entière (`int("n/a")`) lève dans le pilote, avant comme après le gel ; la séance reste consignée.
- `init_problems` : cinq agents intégrés seuls admis, tout autre nom (ou nom absent) refusé. Compte rendu : 0,828 $ contre 0,4219 $, × 2,08 recalculé (0,051617 × 2,08 = 0,1074), marqué estimé.
- Complexité : 0 constat.
