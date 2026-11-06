"""Les 15 types d'incohérence de S (D2) et leur description montrée à l'agent (D7)."""

from __future__ import annotations

from dataclasses import dataclass

ALL = ("cc", "ce", "ca")


@dataclass(frozen=True)
class ErrorType:
    id: str
    name: str
    status: str  # attested | reconstructed
    nuss: str  # attested | attested_secondary | reconstructed
    jurisdictions: tuple[str, ...]
    description: str


def _t(id_, name, status, nuss, jurisdictions, description) -> ErrorType:
    return ErrorType(id_, name, status, nuss, tuple(jurisdictions), description)


TYPES: tuple[ErrorType, ...] = (
    _t(
        "t01",
        "appeal_after_decision",
        "attested",
        "attested",
        ("cc",),
        "Pourvoi postérieur à la décision : l'année AA du numéro de pourvoi est postérieure "
        "à l'année de la décision.",
    ),
    _t(
        "t02",
        "impossible_date",
        "attested",
        "attested_secondary",
        ALL,
        "Date impossible : jour qui n'existe pas dans ce mois (30 ou 31 février, 31 avril, "
        "31 juin, 31 septembre, 31 novembre).",
    ),
    _t(
        "t03",
        "unknown_cassation_chamber",
        "attested",
        "attested",
        ("cc",),
        "Chambre inexistante de la Cour de cassation : rang ou nom de chambre qui n'existe pas "
        "(« civ. 4e », « com. 2e », « ch. fiscale »).",
    ),
    _t(
        "t04",
        "unknown_appeal_court",
        "reconstructed",
        "reconstructed",
        ("ca",),
        "Cour d'appel inexistante : la ville citée est le siège d'un tribunal judiciaire sans "
        "cour d'appel (par exemple « CA Lille »).",
    ),
    _t(
        "t05",
        "other_order_formation",
        "reconstructed",
        "reconstructed",
        ("cc", "ce"),
        "Formation de l'autre ordre : formation du Conseil d'État citée pour la Cour de "
        "cassation (« Cass. Sect. », « Cass. 3e ch. »), ou chambre de la Cour de cassation "
        "citée pour le Conseil d'État (« CE, soc. »).",
    ),
    _t(
        "t06",
        "future_date",
        "reconstructed",
        "reconstructed",
        ALL,
        "Décision future : date postérieure au 1er novembre 2026, date d'arrêt du corpus.",
    ),
    _t(
        "t07",
        "formation_not_at_date",
        "reconstructed",
        "reconstructed",
        ("ce",),
        "Formation du Conseil d'État qui n'existe pas à la date de la décision : « chambre » "
        "numérotée avant le 21 avril 2016 (on disait alors sous-section), ou « sous-section » "
        "après le 31 décembre 2016.",
    ),
    _t(
        "t08",
        "appeal_too_old",
        "reconstructed",
        "reconstructed",
        ("cc",),
        "Pourvoi trop ancien : le pourvoi (année AA du numéro) est enregistré dix ans ou plus "
        "avant l'année de la décision.",
    ),
    _t(
        "t09",
        "court_appeal_after_judgment",
        "reconstructed",
        "reconstructed",
        ("ca",),
        "Appel postérieur à l'arrêt : l'année AA du numéro de cour d'appel est postérieure à "
        "l'année de l'arrêt.",
    ),
    _t(
        "t10",
        "malformed_number",
        "reconstructed",
        "reconstructed",
        ALL,
        "Numéro mal formé : tiret, point ou barre manquant ou remplacé, ou nombre de chiffres "
        "faux.",
    ),
    _t(
        "t11",
        "foreign_number_format",
        "reconstructed",
        "reconstructed",
        ALL,
        "Numéro au format d'une autre juridiction : par exemple six chiffres à la Cour de "
        "cassation, ou AA-NN.NNN dans une cour d'appel.",
    ),
    _t(
        "t12",
        "non_working_day",
        "reconstructed",
        "reconstructed",
        ALL,
        "Décision rendue un dimanche ou un jour férié (fêtes légales de l'article L. 3133-1 "
        "du code du travail).",
    ),
    _t(
        "t13",
        "court_appeal_too_old",
        "reconstructed",
        "reconstructed",
        ("ca",),
        "Appel trop ancien : l'appel (année AA du numéro de cour d'appel) est enregistré dix "
        "ans ou plus avant l'arrêt.",
    ),
    _t(
        "t14",
        "series_chamber_mismatch",
        "reconstructed",
        "reconstructed",
        ("cc",),
        "Série du numéro de pourvoi incompatible avec la chambre : la chambre criminelle "
        "numérote ses pourvois à partir de 80.000 (partie NN.NNN), les chambres civiles, "
        "commerciale et sociale en dessous ; sans objet pour la chambre mixte et "
        "l'assemblée plénière.",
    ),
    _t(
        "t15",
        "feb29_non_leap",
        "reconstructed",
        "reconstructed",
        ALL,
        "Date du 29 février d'une année non bissextile.",
    ),
)

BY_ID: dict[str, ErrorType] = {t.id: t for t in TYPES}

# Types tenus à l'écart de S-réservé : vus seulement à l'évaluation.
HELD_OUT: tuple[str, ...] = ("t04", "t07", "t09", "t11", "t12")
KNOWN: tuple[str, ...] = tuple(t.id for t in TYPES if t.id not in HELD_OUT)
