"""Grille d'incohérence de R (story 1-12, D4), fixée avant les données.

Domaines : `U` (logique ou calendaire, toute date), `F` (fait de `facts.toml` vérifié sur la
fenêtre de S : seulement si la décision est datée dans [2001-01-02, date de génération]) et
`M` (règle mesurée sur la base réelle, toute date). Les règles désactivées par la mesure de
spécificité (`r_facts.disabled_rules`) ne jouent pas pour leur juridiction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from nn_weight_writing.datasets.legal_r.normalize import NormalizedRef
from nn_weight_writing.datasets.legal_r.r_facts import RFacts
from nn_weight_writing.datasets.legal_rules import (
    MAX_DAY,
    is_leap,
    number_jurisdictions,
    number_year,
    violations,
)
from nn_weight_writing.tasks.legal.facts import Facts, load_facts

GRID_VERSION = 1
F_START = date(2001, 1, 2)
ECLI_STRUCTURE = re.compile(r"^ECLI:FR:[A-Z0-9]{1,7}:\d{4}:[A-Z0-9.]{1,25}$")


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    nuss: str | None
    domain: str  # "U", "F" ou "M"
    basis: str


RULES: tuple[Rule, ...] = (
    Rule("R-C1", "calendrier", "t02", "U", "logique : jour au-delà du maximum du mois"),
    Rule("R-C2", "calendrier", "t15", "U", "logique : 29 février d'une année non bissextile"),
    Rule("R-C3", "calendrier", "t06", "U", "logique : date postérieure à la génération"),
    Rule("R-C4", "calendrier", "t12", "F", "holidays.sample : dimanche, fête légale fixe"),
    Rule("R-H1", "chronologie", "t01", "F", "cassation.number : pourvoi après la décision"),
    Rule("R-H2", "chronologie", "t08", "F", "empirique : écart d'au moins 10 ans (max 6)"),
    Rule("R-H3", "chronologie", "t09", "F", "cours_appel.number : appel après l'arrêt"),
    Rule("R-H4", "chronologie", "t13", "F", "empirique : écart d'au moins 10 ans (max 8)"),
    Rule("R-F1", "format", "t10", "F", "*.number.pattern : aucun des trois motifs"),
    Rule("R-F2", "format", "t11", "F", "*.number.pattern : motif d'une autre juridiction"),
    Rule("R-O1", "formation", "t03", "F", "cassation : chambre inexistante"),
    Rule("R-O2", "formation", "t05", "F", "cassation, conseil_etat : formation de l'autre ordre"),
    Rule("R-O3", "formation", "t04", "F", "cours_appel : siège absent des 36"),
    Rule("R-O4", "formation", "t07", "F", "conseil_etat : renommage de 2016"),
    Rule("R-O5", "formation", None, "F", "conseil_etat.numbered_max : rang hors de [1, 10]"),
    Rule("R-E1", "ECLI", None, "U", "norme ECLI (JO C 127 du 29 avril 2011) : structure"),
    Rule("R-E2", "ECLI", None, "M", "mesure : code d'une autre juridiction"),
    Rule("R-E3", "ECLI", None, "U", "norme ECLI : année de l'ECLI = année de la décision"),
    Rule("R-E4", "ECLI", None, "M", "mesure : ordinal du CE = {numéro}.{AAAAMMJJ}"),
    Rule("R-E5", "ECLI", None, "M", "mesure : préfixe de chambre de l'ordinal"),
    Rule("R-A1", "autre", "t14", "F", "cassation.number : série incompatible avec la chambre"),
)
BY_RULE = {rule.id: rule for rule in RULES}
NUSS_TO_RULE = {rule.nuss: rule.id for rule in RULES if rule.nuss}
ECLI_RULES = frozenset(r.id for r in RULES if r.category == "ECLI")
_NUMBERED = re.compile(
    r"((?:\d+(?:re|e), )*\d+(?:re|e)(?: et \d+(?:re|e))?) (ch|sous-sect)\.( réunies)?"
)
_CC_FORM = re.compile(r"^(?:civ|com|soc|crim)\.(?: \d+(?:re|e))?$|^ch\. |^ass\. plén\.$")


def nuss_types(rules: frozenset[str]) -> tuple[str, ...]:
    return tuple(sorted(BY_RULE[r].nuss for r in rules if BY_RULE[r].nuss))


def _triplet(ref: NormalizedRef) -> tuple[int, int, int]:
    return (ref.year, ref.month, ref.day)


def _valid(ref: NormalizedRef) -> date | None:
    try:
        return date(ref.year, ref.month, ref.day)
    except TypeError, ValueError:
        return None


def ce_numbered(formation: str | None) -> tuple[str, tuple[int, ...]] | None:
    """(`ch` ou `sous-sect`, rangs) d'une formation numérotée du CE, réunies comprises."""
    if not formation:
        return None
    match = _NUMBERED.fullmatch(formation)
    if not match:
        return None
    ranks = tuple(int(x) for x in re.findall(r"\d+", match[1]))
    if (len(ranks) > 1) != bool(match[3]):
        return None
    return match[2], ranks


def is_ce_form(formation: str | None, facts: Facts) -> bool:
    return formation in {facts.ce_assembly, facts.ce_section, "juge des référés"} or bool(
        ce_numbered(formation)
    )


def is_cc_form(formation: str | None, facts: Facts) -> bool:
    if not formation:
        return False
    return (
        formation in facts.chambers
        or formation in facts.nonexistent
        or bool(_CC_FORM.match(formation))
    )


def _formation_free(ref: NormalizedRef, facts: Facts) -> set[str]:
    """Règles de S qui ne dépendent pas de la formation (référence sans formation)."""
    found: set[str] = set()
    if ref.number is None:
        return found
    kinds = number_jurisdictions(ref.number, facts)
    if not kinds:
        found.add("R-F1")
    elif ref.jurisdiction in {"cc", "ce", "ca"} and ref.jurisdiction not in kinds:
        found.add("R-F2")
    if ref.jurisdiction == "cc" and "cc" in kinds:
        appeal = number_year(ref.number, ref.year)
        if appeal > ref.year:
            found.add("R-H1")
        if ref.year - appeal >= facts.cc_old_gap[0]:
            found.add("R-H2")
    if ref.jurisdiction == "ca" and "ca" in kinds:
        appeal = number_year(ref.number, ref.year)
        if appeal > ref.year:
            found.add("R-H3")
        if ref.year - appeal >= facts.ca_old_gap[0]:
            found.add("R-H4")
    return found


def _calendar(ref: NormalizedRef) -> set[str]:
    found: set[str] = set()
    if not 1 <= ref.month <= 12 or ref.day < 1 or ref.day > MAX_DAY.get(ref.month, 31):
        found.add("R-C1")
    if ref.month == 2 and ref.day == 29 and not is_leap(ref.year):
        found.add("R-C2")
    return found


def _collegial_ce(formation: str | None, facts: Facts) -> bool:
    return formation in {facts.ce_assembly, facts.ce_section} or bool(ce_numbered(formation))


def _holiday(ref: NormalizedRef, facts: Facts) -> bool:
    day = _valid(ref)
    if day is None:
        return False
    return day.weekday() == 6 or (day.month, day.day) in facts.holiday_fixed


def _ecli_rules(ref: NormalizedRef, r_facts: RFacts) -> set[str]:
    found: set[str] = set()
    if not ref.ecli:
        return found
    if not ECLI_STRUCTURE.fullmatch(ref.ecli):
        found.add("R-E1")
        return found
    _, _, code, year, ordinal = ref.ecli.split(":")
    if ref.year is not None and int(year) != ref.year:
        found.add("R-E3")
    owners = {j for j, codes in r_facts.ecli_codes.items() if code in codes}
    if owners and ref.jurisdiction in {"cc", "ce", "ca"} and ref.jurisdiction not in owners:
        found.add("R-E2")
    if ref.jurisdiction == "ce" and ref.number and ref.has_date():
        expected = f"{ref.number}.{ref.year:04d}{ref.month:02d}{ref.day:02d}"
        if ordinal != expected:
            found.add("R-E4")
    if ref.jurisdiction == "cc" and ref.formation in r_facts.cc_prefixes:
        prefix = ordinal[:2]
        known = set().union(*r_facts.cc_prefixes.values())
        if prefix in known and prefix not in r_facts.cc_prefixes[ref.formation]:
            found.add("R-E5")
    return found


def incoherences(
    ref: NormalizedRef,
    *,
    generation_date: date,
    facts: Facts | None = None,
    r_facts: RFacts,
) -> frozenset[str]:
    """Règles de D4 violées par `ref`, filtrées par domaine et par les règles désactivées."""
    facts = facts or load_facts()
    found: set[str] = set()
    dated = ref.has_date()
    gen = (generation_date.year, generation_date.month, generation_date.day)
    if dated:
        found |= _calendar(ref)
        if _triplet(ref) > gen:
            found.add("R-C3")
        reference = ref.to_reference()
        if reference is not None:
            for t in violations(reference, facts) - {"t06", "t12", "x_formation"}:
                found.add(NUSS_TO_RULE[t])
        else:
            found |= _formation_free(ref, facts)
        if ref.jurisdiction == "cc" and _holiday(ref, facts):
            found.add("R-C4")
        if (
            ref.jurisdiction == "ce"
            and _collegial_ce(ref.formation, facts)
            and _holiday(ref, facts)
        ):
            found.add("R-C4")
    if ref.jurisdiction == "cc" and is_ce_form(ref.formation, facts):
        found.discard("R-O1")
        found.add("R-O2")
    if ref.jurisdiction == "ce" and is_cc_form(ref.formation, facts):
        found.add("R-O2")
    numbered = ce_numbered(ref.formation) if ref.jurisdiction == "ce" else None
    if numbered:
        kind, ranks = numbered
        if any(not 1 <= k <= facts.ce_numbered_max for k in ranks):
            found.add("R-O5")
        if dated and len(ranks) >= 2:
            first_chamber = date.fromordinal(facts.subsection_until.toordinal() + 1)
            last_subsection = date.fromordinal(facts.chamber_from.toordinal() - 1)
            t = _triplet(ref)
            if kind == "ch" and t < (first_chamber.year, first_chamber.month, first_chamber.day):
                found.add("R-O4")
            if kind == "sous-sect" and t > (
                last_subsection.year,
                last_subsection.month,
                last_subsection.day,
            ):
                found.add("R-O4")
    found |= _ecli_rules(ref, r_facts)
    in_f = dated and (F_START.year, F_START.month, F_START.day) <= _triplet(ref) <= gen
    kept = {r for r in found if BY_RULE[r].domain != "F" or in_f}
    return frozenset(kept - r_facts.disabled(ref.jurisdiction))
