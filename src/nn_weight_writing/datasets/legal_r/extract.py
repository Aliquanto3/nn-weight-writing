"""Extracteur de références dans un texte brut (story 1-12, D3), à base de motifs, sans modèle.

Une référence s'ouvre à une ancre (juridiction, ECLI, ou numéro sans juridiction devant lui) et
va jusqu'à l'ancre suivante, la fin de phrase ou 200 caractères. Seul `raw` porte du texte cité ;
les autres champs ne gardent que des segments reconnus (formation, siège) ou des entiers.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

MAX_SPAN = 200
MIN_NUMBER_DIGITS = 5
_MONTHS = {
    "janvier": 1,
    "janv": 1,
    "jan": 1,
    "fevrier": 2,
    "fevr": 2,
    "fev": 2,
    "mars": 3,
    "avril": 4,
    "avr": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "juil": 7,
    "aout": 8,
    "septembre": 9,
    "sept": 9,
    "octobre": 10,
    "oct": 10,
    "novembre": 11,
    "nov": 11,
    "decembre": 12,
    "dec": 12,
}
_ACCENTS = str.maketrans("éèêëàâäîïôöûüùçÉÈÊÀÂÎÔÛÇ", "eeeeaaaiioouuucEEEAAIOUC")
_MONTH_FORMS = [*_MONTHS, "février", "févr", "fév", "août", "décembre", "déc"]
_MONTH_RE = "|".join(sorted(_MONTH_FORMS, key=len, reverse=True))
_UP = r"[A-ZÀ-ÖØ-Þ]"
_NAME = rf"{_UP}[\w'’-]*(?:[ -](?:en|de|la|sur|lès|les|du)[ -]{_UP}[\w-]*|[ -]{_UP}[\w-]*)*"

# Ancres de juridiction (D3, 1). L'ordre compte : la plus longue d'abord à même position.
_OTHER = (
    r"tribunal\w*(?:\s+(?:judiciaire|administratif|de\s+grande\s+instance|d'instance|de\s+"
    r"commerce|correctionnel|des\s+conflits))?|\bTA\b|\bCAA\b|cour\s+administrative\s+d'appel|"
    r"Conseil\s+constitutionnel|Cons\.\s*const\.|\bCEDH\b|Cour\s+europ[ée]enne|\bCJUE\b|\bCJCE\b|"
    r"Cour\s+de\s+justice|\bTGI\b|\bTJ\b|conseil\s+de\s+prud'?hommes|cour\s+d'assises"
)
_ANCHORS = [
    ("other", re.compile(_OTHER, re.IGNORECASE)),
    ("cc", re.compile(r"Cour\s+de\s+cassation|\bCass\b\.?", re.IGNORECASE)),
    ("ce", re.compile(r"(?i:Conseil\s+d'[ée]tat)|\bCE\b(?!\))|\bC\.\s?E\.")),
    (
        "ca",
        re.compile(
            rf"[Cc]our\s+d'appel\s+(?:de\s+|d'\s*|du\s+|des\s+)(?P<seat>{_NAME})|"
            rf"\bCA\s+(?:de\s+|d'\s*)?(?P<seat2>{_NAME})"
        ),
    ),
]
# Juridictions nommées sans ancre (revue du tour de correction) : elles ferment la référence
# ouverte et coupent l'héritage de juridiction, sans ouvrir de référence. Les chambres d'une cour
# d'appel (`_CA_CHAMBERS`) ne coupent pas une référence de cour d'appel.
_CA_CHAMBERS = re.compile(
    r"chambres?\s+de\s+l'instruction|chambres?\s+des\s+appels\s+correctionnels", re.IGNORECASE
)
_CUTS = re.compile(
    r"(?i:juges?\s+(?:aux\s+affaires\s+familiales|de\s+l'ex[ée]cution|des\s+enfants|"
    r"d'instruction|des\s+libert[ée]s|de\s+l'application\s+des\s+peines|des\s+tutelles|"
    r"de\s+paix|de\s+proximit[ée]|des\s+contentieux\s+de\s+la\s+protection|commissaire)|"
    r"juridictions?\s+de\s+proximit[ée]|cour\s+nationale\s+du\s+droit\s+d'asile|"
    r"conseils?\s+(?:de\s+discipline|de\s+l'ordre|r[ée]gional|"
    r"sup[ée]rieur\s+de\s+la\s+magistrature)|cours?\s+d'appel\b)|"
    rf"\b[Cc]ours?\s+(?:de\s+|d'\s*){_UP}|\b(?:JAF|JEX|JLD|CNDA|CA)\b"
)
# Une juridiction nommée ne coupe qu'en tête de citation (début de ligne, après une ponctuation),
# pas dans le récit (« la Cour de cassation juge que la cour d'appel a violé la loi (arrêt du … »).
_CUT_HEAD = re.compile(r"(?:^|[,;:(\-])\s*(?:(?:le|la|les|l'|du|au|un|une)\s*)?$", re.I | re.M)
# Ancres secondaires : n'ouvrent une référence que hors de toute référence ouverte.
_CHAMBER_ANCHOR = re.compile(r"(?<![\w.])(?:Civ\.|Crim\.|Ass\.\s*plén\.|Ch\.\s*mixte)")
_ECLI = re.compile(r"\bECLI:[A-Za-z]{2}:[A-Za-z0-9]+:\d{4}:[A-Za-z0-9.]+[A-Za-z0-9]", re.IGNORECASE)

_DATE_TEXT = re.compile(
    rf"\b(?P<d>\d{{1,2}}|1er|premier)\s*(?:er)?\s+(?P<m>{_MONTH_RE})\.?\s+(?P<y>\d{{4}})\b",
    re.IGNORECASE,
)
# Une date numérique prise dans une suite de chiffres n'en est pas une (« 15-14.12.2014-01000 »).
_DATE_NUM = re.compile(
    r"(?<!\d[-./])\b(?P<d>\d{1,2})[/.](?P<m>\d{1,2})[/.](?P<y>\d{4})\b(?![-./]\d)"
)
_DATE_ISO = re.compile(r"(?<!\d[-./])\b(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})\b(?![-./]\d)")

_MARKER = re.compile(
    r"(?:\bn[°º]s?|\bnos?\b\.?|\bnum[ée]ros?\b|\bpourvois?\b|\breq\.|\brequ[êe]tes?\b)"
    r"[^\d\n]{0,25}?(?=\d)",
    re.IGNORECASE,
)
_TOKEN = re.compile(r"\d+(?:(?:\s*[-./]\s*|\s)\d+)*")
_BARE = re.compile(r"(?<![\d./-])(?:\d{2}-\d{2}\.\d{3}|\d{2}/\d{5})(?![\d./-]?\d)")
# Numéro nu du CE (citation à la Lebon, E3) : seulement entre séparateurs de citation, après une
# virgule, un point-virgule ou une parenthèse et avant une ponctuation ou la fin, jamais un
# montant ou un effectif (« portant sur 250000 euros »).
_BARE_CE = re.compile(r"(?:(?<=[,;(])|(?<=[,;(]\s))\d{6}(?=\s*(?:[,;.)\]](?!\d)|$))", re.MULTILINE)
# Numéros et dates d'un texte normatif (loi, décret…) : masqués avant l'extraction.
_LAW = re.compile(
    r"\b(?:loi|décret|decret|arrêté|arrete|directive|règlement|reglement|circulaire|"
    r"ordonnance(?=\s+n[°º]\s*\d{2,4}-\d))s?\b"
    r"(?:\s+(?:organique|constitutionnelle|délégué|d'exécution|\((?:CEE|CE|UE)\)))*"
    r"(?:\s*(?:n[°º]\s*)?\d[\d\-/]*(?:/(?:CEE|CE|UE))?)?"
    r"(?:\s+du\s+(?:\d{1,2}|1er)\s*(?:er)?\s+\w+\.?\s+\d{4})?",
    re.IGNORECASE,
)

# Formations (segments reconnus seulement, D3 2).
_ORD = r"(?:\b\d{1,2}(?!\d)\s*(?:re|ère|ere|er|e|ème|eme|nd|nde)?(?![a-zà-ÿ])|\bpremi[èe]re|\bdeuxi[èe]me|seconde|troisi[èe]me|quatri[èe]me|cinqui[èe]me|sixi[èe]me|septi[èe]me|huiti[èe]me|neuvi[èe]me|dixi[èe]me|onzi[èe]me|douzi[èe]me)"  # noqa: E501
# Rang qui suit un nom de chambre : jamais le jour d'une date (« soc. 12 mars »).
_ORD_AFTER = rf"(?:{_ORD})(?!\s*(?:er\s+)?(?:{_MONTH_RE})\b)(?![./-]\d)"
_FORMATIONS = re.compile(
    "|".join(
        [
            rf"{_ORD}\s*(?:et|/)\s*{_ORD}\s*(?:chambres?|ch\.|sous-sections?|sous-sect\.|ss-sect\.|SSR)(?:\s+r[ée]unies)?",  # noqa: E501
            rf"{_ORD}\s*(?:chambre|ch\.)\s+(?:civile|commerciale|sociale|criminelle)",
            rf"{_ORD}\s+civ\.?",
            r"chambre\s+civile(?:\s*,?\s*" + _ORD_AFTER + r")?",
            r"\bciv(?:\.|ile\b)(?:\s*,?\s*" + _ORD_AFTER + r")?",
            r"chambre\s+commerciale(?:\s*,?\s*financi[èe]re\s+et\s+[ée]conomique)?(?:\s+"
            + _ORD_AFTER
            + r")?",  # noqa: E501
            r"chambre\s+sociale(?:\s+" + _ORD_AFTER + r")?",
            r"chambre\s+criminelle(?:\s+" + _ORD_AFTER + r")?",
            r"\b(?:comm?|soc|crim|fisc)\.(?:\s*" + _ORD_AFTER + r"\b)?",
            r"chambre\s+mixte|\bch\.\s*mix(?:te|\.)",
            r"assembl[ée]e\s+pl[ée]ni[èe]re|\bass\.\s*pl[ée]n\.?|\bAP\b|\bpl[ée]n\.",
            r"chambre\s+fiscale|chambre\s+des\s+requ[êe]tes|chambres\s+r[ée]unies|\bch\.\s*r[ée]un\.",
            r"assembl[ée]e\s+du\s+contentieux|\bAss\.|\bAssembl[ée]e\b",
            r"(?<!sous-)\bsection\s+du\s+contentieux|(?<!sous-)\b[Ss]ect\.|(?<![-\w])Section\b",
            rf"{_ORD}\s*(?:chambres?|ch\.|sous-sections?|sous-sect\.|ss-sect\.|SSR|SSJS)",
            rf"(?:chambre|sous-section)\s+{_ORD_AFTER}\b",
            # Jamais le seul mot « référé », du texte libre (« la recevabilité du référé »).
            r"juge\s+des\s+r[ée]f[ée]r[ée]s|ordonnance\s+de\s+r[ée]f[ée]r[ée]\b|\bord\.\s*r[ée]f\.",
        ]
    ),
    re.IGNORECASE,
)
_ABBREVIATIONS = {
    "cass",
    "civ",
    "crim",
    "fisc",
    "soc",
    "com",
    "comm",
    "plén",
    "plen",
    "ass",
    "sect",
    "req",
    "ch",
    "réun",
    "reun",
    "mix",
    "ord",
    "réf",
    "ref",
    "n",
    "no",
    "art",
    "al",
    "bull",
    "jur",
    "c",
    "e",
    "ca",
    "ce",
    "janv",
    "févr",
    "fevr",
    "fév",
    "avr",
    "juil",
    "sept",
    "oct",
    "nov",
    "déc",
    "dec",
    "ss",
    "sous-sect",
    "ss-sect",
    "const",
    "cons",
    "min",
    "préc",
    "op",
    "cit",
    "ibid",
    "v",
    "cf",
    "p",
    "pp",
    "éd",
    "ed",
}


@dataclass(frozen=True)
class ExtractedRef:
    """Une référence extraite. Seul `raw` porte du texte cité, jamais publié (D8)."""

    jurisdiction: str | None
    formation_text: str | None
    seat_text: str | None
    day: int | None
    month: int | None
    year: int | None
    number_text: str | None
    ecli: str | None
    raw: str
    start: int
    end: int


# Tirets typographiques (P2) et lettres en exposant (« 2ᵉ », « 1ʳᵉ », « nᵒ ») : un caractère pour
# un caractère, pour que `start` et `end` restent les offsets du texte d'origine.
_DASHES = "‐‑‒–—−"


def _superscript_letters() -> dict[str, str]:
    """Lettres modificatrices dont la décomposition NFKD est une seule lettre (ᵉ, ʳ, ˢ, ᵗ…)."""
    codes = [*range(0x02B0, 0x02E5), *range(0x1D2C, 0x1D6B), *range(0x1D9B, 0x1DC0)]
    out = {}
    for code in [*codes, 0x2071, 0x207F, *range(0x2090, 0x209D)]:
        ch = chr(code)
        folded = unicodedata.normalize("NFKD", ch)
        if folded != ch and len(folded) == 1 and folded.isalpha():
            out[ch] = folded
    return out


_SAME_LENGTH = str.maketrans({**dict.fromkeys(_DASHES, "-"), **_superscript_letters()})


def _clean(text: str) -> str:
    """Espaces insécables, apostrophes, tirets, exposants et mise en forme : même longueur."""
    out = text.translate(_SAME_LENGTH)
    for ch in "    ":
        out = out.replace(ch, " ")
    out = out.replace("’", "'").replace("ʼ", "'")
    for ch in "*`_#|>":
        out = out.replace(ch, " ")
    return out


def _mask(text: str, pattern: re.Pattern) -> str:
    return pattern.sub(lambda m: " " * len(m.group(0)), text)


def _sentence_ends(text: str) -> list[int]:
    """Positions de fin de phrase : ligne vide, ou `.!?` suivi d'une majuscule hors abréviation."""
    ends = [m.start() for m in re.finditer(r"\n\s*\n", text)]
    for m in re.finditer(r"[.!?](?=\s+[A-ZÀ-Þ(])", text):
        if text[m.start()] == ".":
            word = re.search(r"([\wÀ-ÿ-]+)$", text[max(0, m.start() - 20) : m.start()])
            if word and (word.group(1).lower() in _ABBREVIATIONS or len(word.group(1)) == 1):
                continue
        ends.append(m.start() + 1)
    return sorted(ends)


def _ecli_jurisdiction(ecli: str) -> str | None:
    parts = ecli.upper().split(":")
    if len(parts) < 3 or parts[1] != "FR":
        return "other"
    code = parts[2]
    if code == "CCASS":
        return "cc"
    if code.startswith("CE"):
        return "ce"
    if code.startswith("CA") and not code.startswith("CAA"):
        return "ca"
    return "other"


@dataclass
class _Token:
    kind: str  # "date", "number", "ecli", "formation"
    start: int
    end: int
    value: object


def _date_value(match: re.Match) -> tuple[int, int, int]:
    d = match["d"].lower()
    day = 1 if d in {"1er", "premier"} else int(d)
    month_text = match["m"].lower().translate(_ACCENTS)
    month = _MONTHS[month_text] if month_text in _MONTHS else int(month_text)
    return day, month, int(match["y"])


def _numbers(text: str, segments_ce: list[tuple[int, int]]) -> list[_Token]:
    tokens: list[_Token] = []
    taken: list[tuple[int, int]] = []
    for marker in _MARKER.finditer(text):
        token = _TOKEN.match(text, marker.end())
        if not token or any(a <= token.start() < b for a, b in taken):
            continue
        value = token.group(0)
        rest = text[token.end() :]
        # Un jour suivi d'un mois n'appartient pas au numéro (« n° 428409 - 10 juillet 2020 »).
        groups = re.split(r"(\s*[-./]\s*|\s)", value)
        if len(groups) >= 3 and re.match(rf"\s*(?:er\s+)?(?:{_MONTH_RE})\b", rest, re.I):
            value = "".join(groups[:-2])
        trailing_date = re.search(r"\s\d{1,2}[/.]\d{1,2}[/.]\d{4}$", value)
        if trailing_date:
            value = value[: trailing_date.start()]
        value = value.strip()
        if sum(c.isdigit() for c in value) < MIN_NUMBER_DIGITS:
            continue
        start = token.start()
        tokens.append(_Token("number", start, start + len(value), value))
        taken.append((start, start + len(value)))
    for pattern, ce_only in ((_BARE, False), (_BARE_CE, True)):
        for match in pattern.finditer(text):
            if any(a <= match.start() < b for a, b in taken):
                continue
            if ce_only and not any(a <= match.start() < b for a, b in segments_ce):
                continue
            tokens.append(_Token("number", match.start(), match.end(), match.group(0)))
            taken.append((match.start(), match.end()))
    return tokens


def _dates(text: str, numbers: list[_Token]) -> list[_Token]:
    """Dates, cherchées après les numéros : une date prise dans un numéro est écartée."""
    tokens: list[_Token] = []
    for pattern in (_DATE_TEXT, _DATE_NUM, _DATE_ISO):
        for match in pattern.finditer(text):
            if any(t.start <= match.start() < t.end for t in tokens):
                continue
            if any(n.start < match.end() and match.start() < n.end for n in numbers):
                continue
            tokens.append(_Token("date", match.start(), match.end(), _date_value(match)))
    return tokens


def _anchors(text: str) -> list[tuple[int, int, str, str | None]]:
    """Ancres primaires : (début, fin, juridiction, siège)."""
    found: list[tuple[int, int, str, str | None]] = []
    for jurisdiction, pattern in _ANCHORS:
        for match in pattern.finditer(text):
            if any(a <= match.start() < b for a, b, _, _ in found):
                continue
            seat = None
            if jurisdiction == "ca":
                seat = match.group("seat") or match.group("seat2")
            found.append((match.start(), match.end(), jurisdiction, seat))
    found.sort()
    return found


def _formation_prefix(text: str, start: int, floor: int) -> int:
    """Début d'une formation écrite juste avant « de la Cour de cassation » ou « du Conseil »."""
    window = text[max(floor, start - 80) : start]
    if not re.search(r"(?:de\s+la|du|de\s+l')\s*$", window, re.IGNORECASE):
        return start
    best = start
    offset = max(floor, start - 80)
    for match in _FORMATIONS.finditer(window):
        best = min(best, offset + match.start())
        break
    return best


# Liaison entre une date ou un numéro écrits avant une ancre et ce qui suit (tour de correction) :
# ponctuation (pas le point-virgule, qui sépare deux citations), quelques mots de liaison et un
# marqueur de numéro, sans chiffre ni point final.
_CONNECTIVE = re.compile(
    r"[\s,:()\-]*(?:(?:(?:arr[êe]ts?|d[ée]cisions?|rendue?s?|prononc[ée]e?s?|par|du|de|des|la|"
    r"le|les|en|date|dans)\b|l')[\s,:()\-]*)*"
    r"(?:(?:\bn[°º]s?|\bnos?\b\.?|\bnum[ée]ros?\b|\bpourvois?\b|\breq\.|\brequ[êe]tes?\b)"
    r"[^\d\n]{0,25})?",
    re.IGNORECASE,
)
MAX_CONNECTIVE = 40


def _connects(gap: str) -> bool:
    return (
        len(gap) <= MAX_CONNECTIVE
        and not re.search(r"\n\s*\n", gap)
        and _CONNECTIVE.fullmatch(gap) is not None
    )


def _same_value(a: object, b: object) -> bool:
    """Même champ : numéros égaux aux espaces près, ou même date."""
    if isinstance(a, str) and isinstance(b, str):
        return _compact(a) == _compact(b)
    return a == b


def _attached_fields(text: str, tokens: list[_Token], a_end: int, end: int) -> dict[str, object]:
    """Date et numéro liés à l'ancre qui la suivent (« Cour d'appel de Paris, n° Y ») : de proche
    en proche, formations mises à part, tant que l'écart est une simple liaison (`_connects`)."""
    fields: dict[str, object] = {}
    cur = a_end
    for tok in sorted((t for t in tokens if a_end <= t.start < end), key=lambda t: t.start):
        if not _connects(_FORMATIONS.sub(" ", text[cur : tok.start])):
            break
        if tok.kind in fields and not _same_value(fields[tok.kind], tok.value):
            break
        fields.setdefault(tok.kind, tok.value)
        cur = tok.end
    return fields


def _second_reference(tokens: list[_Token], start: int, end: int) -> int:
    """Début de la deuxième référence de `[start, end)` : premier champ répété (date ou numéro
    d'une autre valeur), ou `end`. Ce qui suit peut revenir à l'ancre suivante."""
    fields: dict[str, object] = {}
    for tok in sorted((t for t in tokens if start <= t.start < end), key=lambda t: t.start):
        if tok.kind in fields and not _same_value(fields[tok.kind], tok.value):
            return tok.start
        fields.setdefault(tok.kind, tok.value)
    return end


def _token_prefix(
    text: str, start: int, floor: int, tokens: list[_Token], present: dict[str, object]
) -> int:
    """Début d'une date et d'un numéro écrits juste avant l'ancre (« Arrêt du 12 mars 2015, Cour
    de cassation », « Date : … (Arrêt n° … du Conseil d'État) ») ; au plus un de chaque, et
    seulement un champ que la référence n'a pas après l'ancre (`present`), ou qu'elle rappelle.
    Si la chaîne liée bute sur un champ déjà pris (« n° X du 4 mai 2011, Cour d'appel de Paris,
    n° Y »), elle forme une autre référence : rien n'est rattaché."""
    used: set[str] = set()
    cur = start
    while True:
        before = [t for t in tokens if floor <= t.start and t.end <= cur]
        if not before:
            return cur
        tok = max(before, key=lambda t: t.end)
        if not _connects(text[tok.end : cur]):
            return cur
        if tok.kind in used or (
            tok.kind in present and not _same_value(present[tok.kind], tok.value)
        ):
            return start
        used.add(tok.kind)
        cur = tok.start


def _is_header(text: str, a_start: int, a_end: int) -> tuple[bool, int]:
    """Ancre d'en-tête : sa ligne finit par « : », est un titre (`#`) ou est en gras seule."""
    line_start = text.rfind("\n", 0, a_start) + 1
    line_end = text.find("\n", a_end)
    line_end = len(text) if line_end < 0 else line_end
    line = text[line_start:line_end].strip()
    bare = line.strip("*_ ")
    header = (
        bare.endswith(":")
        or line.startswith("#")
        or (line.startswith("**") and line.endswith("**") and "**" not in line[2:-2])
    )
    return header, line_end


def _inherit(
    text: str, segments: list[dict], ends: list[int], cuts: list[tuple[int, bool]]
) -> None:
    """Juridiction héritée par une référence ouverte sans juridiction (numéro ou date nus).

    Elle prend la juridiction de la dernière ancre qui la précède, sans autre ancre entre les
    deux, dans l'un de deux cas bornés :
    - en-tête : la ligne de l'ancre finit par « : » ou est un titre, et la référence commence
      au plus `MAX_SPAN` caractères après la fin de cette ligne (bloc « Arrêt n° / Date ») ;
    - même phrase : aucune fin de phrase entre l'ancre et la référence, à moins de
      2 × `MAX_SPAN` caractères de l'ancre (phrase longue coupée par la borne de D3).
    Une référence qui hérite ne transmet rien : pas d'héritage en chaîne. Une juridiction
    nommée entre les deux, même sans ancre (`_CUTS` : juge aux affaires familiales, chambre de
    l'instruction, cour de Riom…), l'interrompt.
    """
    anchored = [s for s in segments if s["j"] is not None]
    for seg in segments:
        if seg["j"] is not None:
            continue
        previous = [s for s in anchored if s["anchor"][1] <= seg["start"]]
        if not previous:
            continue
        source = max(previous, key=lambda s: s["anchor"][0])
        a_start, a_end = source["anchor"]
        if any(
            a_end <= c < seg["start"] and not (chamber and source["j"] == "ca")
            for c, chamber in cuts
        ):
            continue
        header, line_end = _is_header(text, a_start, a_end)
        in_header = header and 0 <= seg["start"] - line_end <= MAX_SPAN
        same_sentence = seg["start"] - a_end <= 2 * MAX_SPAN and not any(
            a_end < e <= seg["start"] for e in ends
        )
        if in_header or same_sentence:
            seg["j"], seg["seat"] = source["j"], source["seat"]


def _compact(number: str) -> str:
    return re.sub(r"\s", "", number)


def extract_references(text: str) -> list[ExtractedRef]:
    if not text:
        return []
    clean = _mask(_clean(text), _LAW)
    ends = _sentence_ends(clean)
    anchors = _anchors(clean)
    primary_starts = [a[0] for a in anchors]
    # Numéros d'abord (marqueur ou motif nu), puis les dates hors des numéros.
    pre_numbers = _numbers(clean, [])
    pre_tokens = [*pre_numbers, *_dates(clean, pre_numbers)]
    covered = [(a[0], a[1]) for a in anchors]
    cuts = sorted(
        (m.start(), pattern is _CA_CHAMBERS)
        for pattern in (_CUTS, _CA_CHAMBERS)
        for m in pattern.finditer(clean)
        if _CUT_HEAD.search(clean, max(0, m.start() - 20), m.start())
        and not any(a < m.end() and m.start() < b for a, b in covered)
    )

    def segment_end(start: int, jurisdiction: str | None = None) -> int:
        limit = start + MAX_SPAN
        nxt = [p for p in primary_starts if p > start]
        nxt += [p for p, chamber in cuts if p > start and not (chamber and jurisdiction == "ca")]
        if nxt:
            limit = min(limit, min(nxt))
        after = [e for e in ends if e > start]
        if after:
            limit = min(limit, after[0])
        return min(limit, len(clean))

    segments: list[dict] = []
    floor = steal = 0
    for a_start, a_end, jurisdiction, seat in anchors:
        start = a_start
        if jurisdiction in {"cc", "ce"}:
            start = _formation_prefix(clean, a_start, floor)
        end = segment_end(a_start, jurisdiction)
        # Date ou numéro écrits avant l'ancre : hors de la référence précédente, ou dans ce qui
        # y ouvrirait une deuxième référence (« …, n° X, et l'arrêt du 4 mai 2011, Conseil
        # d'État, n° Y »).
        # Une juridiction nommée sans ancre, dans la même phrase juste avant, garde ce qui la suit.
        named = any(
            steal <= c < start and start - c <= MAX_SPAN and not any(c < e <= start for e in ends)
            for c, _ in cuts
        )
        prefixed = _token_prefix(
            clean,
            start,
            start if named else steal,
            pre_tokens,
            _attached_fields(clean, pre_tokens, a_end, end),
        )
        if segments and prefixed < segments[-1]["end"]:
            segments[-1]["end"] = prefixed
        segments.append(
            {
                "start": prefixed,
                # Avant l'ancre, seule une formation entre, sauf date ou numéro rattachés.
                "body": prefixed if prefixed < start else a_end,
                "end": end,
                "j": jurisdiction,
                "seat": seat,
                "anchor": (a_start, a_end),
            }
        )
        floor = segments[-1]["end"]
        steal = max(a_end, _second_reference(pre_tokens, segments[-1]["body"], floor))

    def containing(pos: int) -> dict | None:
        return next((s for s in segments if s["start"] <= pos < s["end"]), None)

    # Une référence secondaire s'arrête au début de la référence primaire suivante, date ou
    # numéro rattachés compris : un jeton n'est jamais lu dans deux références.
    primary_begins = sorted(s["start"] for s in segments)

    def secondary_end(pos: int, jurisdiction: str | None) -> int:
        nxt = [p for p in primary_begins if p > pos]
        end = segment_end(pos, jurisdiction)
        return min(end, nxt[0]) if nxt else end

    # Ancres secondaires : chambre abrégée, ECLI, numéro sans juridiction.
    secondary: list[tuple[int, str | None, _Token | None]] = []
    for match in _CHAMBER_ANCHOR.finditer(clean):
        secondary.append((match.start(), "cc", None))
    ecli_tokens = [
        _Token("ecli", m.start(), m.end(), m.group(0).upper()) for m in _ECLI.finditer(clean)
    ]
    for tok in ecli_tokens:
        secondary.append((tok.start, _ecli_jurisdiction(tok.value) or "other", None))
    ce_spans = [(s["start"], s["end"]) for s in segments if s["j"] == "ce"]
    for tok in _numbers(clean, ce_spans):
        secondary.append((tok.start, None, tok))
    date_tokens = _dates(clean, pre_numbers)
    for pos, jurisdiction, tok in sorted(secondary, key=lambda x: x[0]):
        if containing(pos) is not None:
            continue
        start = pos
        if tok is not None:
            # Une date écrite juste avant le numéro lui appartient : la référence qui la
            # contient s'étend jusqu'au numéro, sinon la nouvelle référence part de la date.
            before = [d for d in date_tokens if d.end <= pos and _connects(clean[d.end : pos])]
            if before:
                date = max(before, key=lambda d: d.end)
                holder = containing(date.start)
                if holder is not None:
                    holder["end"] = max(holder["end"], tok.end)
                    continue
                start = date.start
        segments.append(
            {
                "start": start,
                "body": start,
                "end": max(secondary_end(pos, jurisdiction), tok.end if tok else pos),
                "j": jurisdiction,
                "seat": None,
                "anchor": (pos, pos),
            }
        )
    segments.sort(key=lambda s: s["start"])
    _inherit(text, segments, ends, cuts)
    ce_spans = [(s["start"], s["end"]) for s in segments if s["j"] == "ce"]
    number_tokens = _numbers(clean, ce_spans)
    date_tokens = _dates(clean, number_tokens)
    formation_tokens = [
        _Token("formation", m.start(), m.end(), m.group(0).strip())
        for m in _FORMATIONS.finditer(clean)
    ]
    out: list[ExtractedRef] = []
    for seg in segments:
        for ref in _parse_segment(
            text, seg, number_tokens, date_tokens, ecli_tokens, formation_tokens
        ):
            # Le rappel seul d'un numéro déjà cité n'ouvre pas de nouvelle référence.
            last = out[-1] if out else None
            if (
                last is not None
                and ref.number_text
                and ref.day is None
                and ref.ecli is None
                and last.number_text
                and _compact(last.number_text) == _compact(ref.number_text)
                and ref.jurisdiction in {None, last.jurisdiction}
                and ref.formation_text in {None, last.formation_text}
                and ref.seat_text in {None, last.seat_text}
            ):
                continue
            out.append(ref)
    return out


def _parse_segment(text, seg, numbers, dates, eclis, formations) -> list[ExtractedRef]:
    start, end, jurisdiction = seg["start"], seg["end"], seg["j"]
    tokens = [
        t
        for t in (*numbers, *dates, *eclis, *formations)
        if start <= t.start < end and not (seg["body"] > t.start and t.kind != "formation")
    ]
    tokens.sort(key=lambda t: (t.start, t.kind))
    # Un jeton inclus dans un autre (date dans un ECLI, formation dans une date) est écarté.
    kept: list[_Token] = []
    for tok in tokens:
        if any(k.start <= tok.start and tok.end <= k.end and k is not tok for k in kept):
            continue
        if tok.kind == "formation" and any(
            t.kind != "formation" and t.start <= tok.start < t.end for t in tokens
        ):
            continue
        kept.append(tok)
    refs: list[dict] = []
    current: dict = {"start": start}

    def close(at: int) -> None:
        current["end"] = at
        refs.append(dict(current))

    for tok in kept:
        slot = {"date": "date", "number": "number", "ecli": "ecli", "formation": "formation"}[
            tok.kind
        ]
        if (
            slot == "number"
            and "number" in current
            and _compact(current["number"]) == _compact(tok.value)
        ):
            current["last"] = tok.end  # rappel du même numéro : même référence
            continue
        if slot in current:
            # Une formation de plus n'ouvre une référence que si la courante a date ou numéro.
            if slot == "formation" and "date" not in current and "number" not in current:
                continue
            close(tok.start)
            current.clear()
            current["start"] = tok.start
        current[slot] = tok.value
        current["last"] = tok.end
    close(current.get("last", end))
    out = []
    for ref in refs:
        if not any(k in ref for k in ("date", "number", "ecli")):
            continue
        j = jurisdiction
        if j is None and "ecli" in ref:
            j = _ecli_jurisdiction(ref["ecli"])
        day, month, year = ref.get("date", (None, None, None))
        r_start, r_end = ref["start"], max(ref.get("end", end), ref["start"])
        out.append(
            ExtractedRef(
                jurisdiction=j,
                formation_text=ref.get("formation"),
                seat_text=seg["seat"] if j == "ca" else None,
                day=day,
                month=month,
                year=year,
                number_text=ref.get("number"),
                ecli=ref.get("ecli"),
                raw=text[r_start:r_end],
                start=r_start,
                end=r_end,
            )
        )
    return out
