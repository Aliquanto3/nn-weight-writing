"""Codes de refus des outils de séance et motifs de fin de séance (Consistency Conventions)."""

from __future__ import annotations

from enum import StrEnum


class RefusalCode(StrEnum):
    """Code renvoyé par un outil (`{"refused": code, "detail": ...}`) et journalisé (`refusal`)."""

    # Filtre statique du bac à sable (AD-5, AD-19).
    SYNTAX_ERROR = "syntax_error"
    FORBIDDEN_IMPORT = "forbidden_import"
    FORBIDDEN_NAME = "forbidden_name"
    FORBIDDEN_ATTRIBUTE = "forbidden_attribute"
    FORBIDDEN_STATEMENT = "forbidden_statement"
    ATTRIBUTE_STORE = "attribute_store"
    FITTING_FUNCTION = "fitting_function"
    LITERALS_TOO_LARGE = "literals_too_large"
    CODE_TOO_COMPLEX = "code_too_complex"
    # Catalogue et arguments (AD-15).
    UNKNOWN_TOOL = "unknown_tool"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    INVALID_ARGUMENTS = "invalid_arguments"
    # Budget de passes (AD-6).
    PASS_BUDGET_EXHAUSTED = "pass_budget_exhausted"
    MUTATION_AFTER_BUDGET = "mutation_after_budget"
    # Réseau et production (AD-3).
    INVALID_MANIFEST = "invalid_manifest"
    ENCODER_MISMATCH = "encoder_mismatch"
    NO_NETWORK_DECLARED = "no_network_declared"
    NETWORK_HAS_WEIGHTS = "network_has_weights"
    INVALID_WEIGHTS = "invalid_weights"
    SIZE_OUT_OF_RANGE = "size_out_of_range"
    # Gel (AD-8).
    NO_PRODUCTION = "no_production"
    WEIGHTS_INCOMPLETE = "weights_incomplete"
    INVALID_BLOCKS = "invalid_blocks"
    TYPE_NOT_IN_VOCABULARY = "type_not_in_vocabulary"
    FREEZE_ATTEMPTS_EXHAUSTED = "freeze_attempts_exhausted"
    # Séance close (gel ou fin).
    SESSION_CLOSED = "session_closed"


class EndReason(StrEnum):
    """Motif de l'événement `end` (AD-6, AD-7), distinct des codes de refus."""

    FROZEN = "frozen"
    PASS_BUDGET = "pass_budget"
    TURN_LIMIT = "turn_limit"
    MONEY_BUDGET = "money_budget"
    ERROR = "error"
