"""Normaliseur commun (AD-16, story 1-12 D3 et P2).

Les champs extraits d'une réponse de SLM, les métadonnées Judilibre et celles de l'open data du
Conseil d'État passent tous par `normalize`. Liste blanche de champs : aucun texte libre n'entre.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, fields

from nn_weight_writing.datasets.legal_r.r_facts import fold, load_seat_tables
from nn_weight_writing.tasks.legal.facts import load_facts
from nn_weight_writing.tasks.legal.reference import Reference

NORMALIZER_ID = "legal_r.normalize@2"  # @2 : tour de correction de la phase B (E15)
ALLOWED_FIELDS = frozenset(
    {
        "jurisdiction",
        "formation_text",
        "seat_text",
        "day",
        "month",
        "year",
        "number_text",
        "ecli",
        "source",
        "source_id",
        "decision_type",
        "publication",
        "update_date",
    }
)
FORBIDDEN_FIELDS = frozenset(
    {
        "text",
        "zones",
        "text_highlight",
        "highlights",
        "summary",
        "themes",
        "titlesAndSummaries",
        "visa",
        "rapprochements",
        "timeline",
        "files",
        "Texte_Integral",
    }
)
JURISDICTIONS = ("cc", "ce", "ca", "other")
DASHES = "‐‑‒–—−"
_SPACES = re.compile(r"\s+")
_CC_VARIANT = re.compile(r"(\d{2})[-.]?(\d{2})\.?(\d{3})")
_PENAL = re.compile(r"correctionnel|penal|instruction|criminel", re.IGNORECASE)


@dataclass(frozen=True)
class RefFields:
    """Champs d'entrée du normaliseur : liste blanche (`ALLOWED_FIELDS`) seulement."""

    jurisdiction: str | None = None
    formation_text: str | None = None
    seat_text: str | None = None
    day: int | None = None
    month: int | None = None
    year: int | None = None
    number_text: str | None = None
    ecli: str | None = None
    source: str | None = None
    source_id: str | None = None
    decision_type: str | None = None
    publication: str | None = None
    update_date: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping) -> RefFields:
        """Garde les clés de `ALLOWED_FIELDS`, ignore `FORBIDDEN_FIELDS`, refuse le reste."""
        unknown = set(data) - ALLOWED_FIELDS - FORBIDDEN_FIELDS
        if unknown:
            raise ValueError(f"champs hors liste blanche : {sorted(unknown)}")
        return cls(**{k: data[k] for k in data if k in ALLOWED_FIELDS})


assert {f.name for f in fields(RefFields)} == ALLOWED_FIELDS


@dataclass(frozen=True)
class NormalizedRef:
    jurisdiction: str | None
    formation: str | None
    day: int | None
    month: int | None
    year: int | None
    number: str | None
    ecli: str | None
    source: str | None = None
    source_id: str | None = None
    penal: bool = False  # cour d'appel, formation pénale citée (hors fenêtre, D5)

    def key(self) -> tuple:
        return (self.jurisdiction, self.number, (self.year, self.month, self.day))

    def has_date(self) -> bool:
        return None not in (self.day, self.month, self.year)

    def is_complete(self) -> bool:
        return self.jurisdiction in {"cc", "ce", "ca"} and bool(self.number) and self.has_date()

    def to_reference(self) -> Reference | None:
        if not self.is_complete() or self.formation is None:
            return None
        if not 1 <= self.month <= 12 or self.day < 1:
            return None
        return Reference(
            self.jurisdiction, self.formation, self.day, self.month, self.year, self.number
        )


# --- Numéro (P2) ---------------------------------------------------------------------------


def normalize_number(text: str | None, jurisdiction: str | None) -> str | None:
    """Tirets typographiques -> `-`, espaces retirés ; variantes `cc` canonisées (P2)."""
    if text is None:
        return None
    for dash in DASHES:
        text = text.replace(dash, "-")
    text = _SPACES.sub("", text)
    if not text:
        return None
    if jurisdiction == "cc":
        match = _CC_VARIANT.fullmatch(text)
        if match:
            return f"{match[1]}-{match[2]}.{match[3]}"
    return text


# --- Formations ----------------------------------------------------------------------------

_ORDINAL_WORDS = {
    "premiere": 1,
    "premier": 1,
    "deuxieme": 2,
    "seconde": 2,
    "second": 2,
    "troisieme": 3,
    "quatrieme": 4,
    "cinquieme": 5,
    "sixieme": 6,
    "septieme": 7,
    "huitieme": 8,
    "neuvieme": 9,
    "dixieme": 10,
    "onzieme": 11,
    "douzieme": 12,
}
_RANK = re.compile(
    r"\b(?:(\d{1,2})\s*(?:re|ere|er|e|eme|nd|nde|°)?|(" + "|".join(_ORDINAL_WORDS) + r"))\b"
)
_CC_KINDS = (
    ("civ", re.compile(r"\bciv\b|\bcivile?s?\b")),
    ("com", re.compile(r"\bcomm?\b|\bcommerciale\b")),
    ("soc", re.compile(r"\bsoc\b|\bsociale\b")),
    ("crim", re.compile(r"\bcrim\b|\bcriminelle\b")),
    ("mixte", re.compile(r"\bmixte\b|\bmix\b")),
    ("plen", re.compile(r"\bplen\b|\bpleniere\b|\bap\b")),
    ("fiscale", re.compile(r"\bfiscale\b|\bfisc\b")),  # « Cass. fisc. »
)
_UNPARSED_CC = re.compile(r"\brequetes\b|\breunies\b|\breun\b")
_CC_FORMS = {"civ": "civ.", "com": "com.", "soc": "soc.", "crim": "crim."}
_CE_NUMBERED_KIND = re.compile(
    r"\b(?:sous\s*sect(?:ion)?s?|ss\s*sect(?:ion)?s?|ssr|ssjs)\b|\b(ch(?:ambre)?s?|chr|chs)\b"
)


def _fold_formation(text: str) -> str:
    return fold(text.replace(".", " ").replace(",", " ").replace("(", " ").replace(")", " "))


def _ranks(folded: str) -> list[int]:
    out = []
    for match in _RANK.finditer(folded):
        if match[1]:
            out.append(int(match[1]))
        else:
            out.append(_ORDINAL_WORDS[match[2]])
    return out


def _rank_text(k: int) -> str:
    return f"{k}{'re' if k == 1 else 'e'}"


def _cc_kind(folded: str) -> str | None:
    for kind, pattern in _CC_KINDS:
        if pattern.search(folded):
            return kind
    return None


def _ce_form(folded: str) -> str | None:
    """Forme du Conseil d'État si le texte en désigne une sans ambiguïté, sinon None."""
    # Jamais du seul mot « référé » : juge ou bureau des référés, ordonnance de référé.
    if re.search(
        r"\bjuge\w* des referes\b|\bdes referes\b|\bordonnance\w* de refere\b|\bord\w* ref\w*\b",
        folded,
    ):
        return "juge des référés"
    if re.search(r"\bass(?:emblee)?\b", folded):
        return "Ass."
    kind_match = _CE_NUMBERED_KIND.search(folded)
    ranks = _ranks(folded)
    if kind_match and ranks:
        kind = "ch." if kind_match[1] else "sous-sect."
        if len(ranks) >= 2:
            texts = [_rank_text(k) for k in sorted(set(ranks))]
            if len(texts) == 1:
                return f"{texts[0]} {kind}"
            head = ", ".join(texts[:-1])
            return f"{head} et {texts[-1]} {kind} réunies"
        return f"{_rank_text(ranks[0])} {kind}"
    if re.search(r"(?<!sous )\bsect(?:ion)?\b", folded) and not re.search(r"\bsous", folded):
        return "Sect."
    return None


def canonical_cc_chamber(text: str | None) -> str | None:
    """Forme de D1 d'une chambre citée pour la Cour de cassation (voir D3) ; None si illisible."""
    if not text:
        return None
    facts = load_facts()
    code = text.strip()
    by_code = {v: k for k, v in facts.chambers.items()}
    if code in by_code:
        return by_code[code]
    if code in {"creun", "ordo", "allciv", "other"}:
        return None
    if text.strip() in facts.chambers or text.strip() in facts.nonexistent:
        return text.strip()
    folded = _fold_formation(text)
    kind = _cc_kind(folded)
    if kind is None:
        return _ce_form(folded)
    if kind == "civ" and _UNPARSED_CC.search(folded):
        return None
    ranks = _ranks(folded)
    if kind == "mixte":
        return "ch. mixte"
    if kind == "plen":
        return "ass. plén."
    if kind == "fiscale":
        return "ch. fiscale"
    if kind == "civ":
        return f"civ. {_rank_text(ranks[0])}" if ranks else None
    head = _CC_FORMS[kind]
    return f"{head} {_rank_text(ranks[0])}" if ranks else head


def canonical_ce_formation(text: str | None) -> str | None:
    """Forme d'une formation citée pour le Conseil d'État (D3) ; chambre de cassation -> D1."""
    if not text:
        return None
    facts = load_facts()
    stripped = text.strip()
    if stripped in facts.chambers or stripped in facts.nonexistent:
        return stripped
    folded = _fold_formation(text)
    kind = _cc_kind(folded)
    if kind is not None:
        return canonical_cc_chamber(text)
    return _ce_form(folded)


def canonical_seat(text: str | None) -> str | None:
    """Siège de cour d'appel : 36 sièges, alias et codes Judilibre ; sinon nom en forme de titre."""
    if not text:
        return None
    aliases, codes = load_seat_tables()
    stripped = text.strip()
    if stripped in codes:
        return codes[stripped]
    folded = fold(stripped)
    for seat in load_facts().all_seats:
        if fold(seat) == folded:
            return seat
    if folded in aliases:
        return aliases[folded]
    return stripped.title()


# --- Normalisation -------------------------------------------------------------------------


def normalize(fields: RefFields) -> NormalizedRef:
    if not isinstance(fields, RefFields):
        raise TypeError("normalize attend un RefFields (liste blanche)")
    jurisdiction = fields.jurisdiction if fields.jurisdiction in JURISDICTIONS else None
    penal = False
    if jurisdiction == "cc":
        formation = canonical_cc_chamber(fields.formation_text)
    elif jurisdiction == "ce":
        formation = canonical_ce_formation(fields.formation_text)
    elif jurisdiction == "ca":
        formation = canonical_seat(fields.seat_text)
        penal = bool(fields.formation_text and _PENAL.search(fold(fields.formation_text)))
    else:
        formation = None
    ecli = fields.ecli.strip().upper() if fields.ecli and fields.ecli.strip() else None
    return NormalizedRef(
        jurisdiction=jurisdiction,
        formation=formation,
        day=fields.day,
        month=fields.month,
        year=fields.year,
        number=normalize_number(fields.number_text, jurisdiction),
        ecli=ecli,
        source=fields.source,
        source_id=fields.source_id,
        penal=penal,
    )


# --- Projections ---------------------------------------------------------------------------


def _iso_date(text: str | None) -> tuple[int | None, int | None, int | None]:
    if not text or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text[:10]):
        return None, None, None
    year, month, day = text[:10].split("-")
    return int(day), int(month), int(year)


def fields_from_extracted(ref) -> RefFields:
    """`ExtractedRef` -> `RefFields` (source `slm`) ; `raw` n'est jamais copié."""
    return RefFields(
        jurisdiction=ref.jurisdiction,
        formation_text=ref.formation_text,
        seat_text=ref.seat_text,
        day=ref.day,
        month=ref.month,
        year=ref.year,
        number_text=ref.number_text,
        ecli=ref.ecli,
        source="slm",
    )


def fields_from_judilibre(meta: Mapping) -> RefFields:
    """Décision Judilibre (projetée ou non) -> `RefFields` ; premier de `numbers` si présent."""
    day, month, year = _iso_date(meta.get("decision_date"))
    numbers = meta.get("numbers") or []
    number = numbers[0] if numbers else meta.get("number")
    publication = meta.get("publication")
    if isinstance(publication, list):
        publication = ",".join(publication)
    jurisdiction = meta.get("jurisdiction")
    return RefFields(
        jurisdiction=jurisdiction,
        formation_text=meta.get("chamber"),
        seat_text=meta.get("location") if jurisdiction == "ca" else None,
        day=day,
        month=month,
        year=year,
        number_text=number,
        ecli=meta.get("ecli") or None,
        source="judilibre",
        source_id=meta.get("id"),
        decision_type=meta.get("type"),
        publication=publication,
        update_date=meta.get("update_date"),
    )


def fields_from_ce_opendata(record: Mapping) -> RefFields:
    """Enregistrement de l'open data du Conseil d'État (index ou XML) -> `RefFields`."""
    day, month, year = _iso_date(record.get("Date_Lecture"))
    return RefFields(
        jurisdiction="ce",
        formation_text=record.get("Formation_Jugement"),
        day=day,
        month=month,
        year=year,
        number_text=record.get("Numero_Dossier"),
        ecli=record.get("Numero_ECLI") or None,
        source="ce-opendata",
        source_id=record.get("Numero_Dossier"),
        decision_type=record.get("Type_Decision"),
        publication=record.get("Code_Publication"),
        update_date=record.get("Date_Mise_Jour"),
    )
