"""Publication des artefacts d'un lot (AD-18, R2 et R6 du constat 1-3, story 1-14).

`checks` porte les contrôles et leurs codes de refus, `archive` l'assemblage déterministe.
Dépendances : `journal` et `evaluation.schema` (constantes seules). La configuration
(`config.load_publish`) est lue par `cli`, qui passe `r_republish` et `r_tasks`.
"""
