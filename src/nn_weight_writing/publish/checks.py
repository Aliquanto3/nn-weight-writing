"""Contrôles de publication (AD-18, R2 et R6 du constat 1-3, décisions Q1-Q5, Q10, Q11).

Chaque contrôle rend des `Violation` (chemin, code, détail). Aucun détail ne contient la valeur
d'un secret ni un `raw` réservé : seulement le nom de la variable, ou la tâche, le jeu et l'`id`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath


class PublishRefusalCode(StrEnum):
    KEY_PATTERN = "key_pattern"
    SECRET_VALUE = "secret_value"
    RESERVED_EXAMPLE = "reserved_example"
    NO_HELDOUT = "no_heldout"
    R_WITHOUT_REPUBLISH = "r_without_republish"
    R_FORBIDDEN_FIELD = "r_forbidden_field"
    R_SOURCE_MISMATCH = "r_source_mismatch"
    R_ATTRIBUTION_MISSING = "r_attribution_missing"
    OUTPUT_EXISTS = "output_exists"
    # Décision Q10 : noms de parties et longueur des `raw`.
    R_PARTY_NAME = "r_party_name"
    R_RAW_TOO_LONG = "r_raw_too_long"
    # Décision Q11 : `interne/`, `collecte/`, `cache/` et collecte brute de 1-12a.
    FORBIDDEN_PATH = "forbidden_path"


@dataclass(frozen=True)
class Violation:
    path: str
    code: PublishRefusalCode
    detail: str

    def __str__(self) -> str:
        return f"refus {self.code} : {self.path} : {self.detail}"


# --- motifs de clés et valeurs de secrets (R6, Q5) ----------------------------------------------

KEY_PATTERNS = (b"sk-ant-", b"sk-or-", b"Bearer ")
SECRET_ENV_VARS = (
    "JUDILIBRE_KEY_ID",
    "PISTE_CLIENT_ID",
    "PISTE_CLIENT_SECRET",
    "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY",
)
SECRET_EXTRA_VARS = ("CLAUDE_CODE_OAUTH_TOKEN",)
SECRET_SUFFIXES = ("_KEY", "_SECRET", "_TOKEN")
SECRET_MIN_CHARS = 8


def is_secret_name(name: str) -> bool:
    upper = name.upper()
    return upper in SECRET_ENV_VARS or upper in SECRET_EXTRA_VARS or upper.endswith(SECRET_SUFFIXES)


def read_env_file(path: Path) -> dict[str, str]:
    """`KEY=VALUE` par ligne (préfixe `export ` admis, guillemets retirés, `#` en tête ignoré)."""
    values: dict[str, str] = {}
    for line in Path(path).read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.removeprefix("export ").split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name.strip()] = value
    return values


@dataclass(frozen=True)
class Secrets:
    """Valeurs à chercher : (nom de la première variable qui la porte, formes en octets)."""

    values: tuple[tuple[str, tuple[bytes, ...]], ...] = ()

    @property
    def count(self) -> int:
        return len(self.values)


def _forms(value: str) -> tuple[bytes, ...]:
    forms = {
        value.encode("utf-8"),
        json.dumps(value)[1:-1].encode("utf-8"),
        json.dumps(value, ensure_ascii=False)[1:-1].encode("utf-8"),
    }
    return tuple(sorted(forms))


def collect_secrets(environ: Mapping[str, str], env_files: Iterable[Path] = ()) -> Secrets:
    """Variables de secret de l'environnement et des fichiers `.env` (Q5) ; valeurs de moins de
    8 caractères ignorées ; une valeur portée par plusieurs variables compte une fois."""
    sources: list[tuple[str, str]] = sorted(environ.items())
    for path in env_files:
        sources += sorted(read_env_file(path).items())
    by_value: dict[str, str] = {}
    for name, value in sources:
        if is_secret_name(name) and isinstance(value, str) and len(value) >= SECRET_MIN_CHARS:
            by_value.setdefault(value, name.upper())
    return Secrets(tuple((name, _forms(value)) for value, name in sorted(by_value.items())))


def check_secrets(path: str, data: bytes, secrets: Secrets) -> list[Violation]:
    found = [
        Violation(path, PublishRefusalCode.KEY_PATTERN, f"motif de clé {p.decode()!r}")
        for p in KEY_PATTERNS
        if p in data
    ]
    names = sorted({name for name, forms in secrets.values if any(f in data for f in forms)})
    found += [
        Violation(path, PublishRefusalCode.SECRET_VALUE, f"valeur de la variable {name}")
        for name in names
    ]
    return found


# --- chemins refusés (Q11) ----------------------------------------------------------------------

FORBIDDEN_DIRS = frozenset({"interne", "collecte", "cache"})
RAW_COLLECTION_FILES = frozenset({"collecte.jsonl", "pilote.jsonl"})


def check_path(path: str) -> list[Violation]:
    """Refuse `interne/`, `collecte/`, `cache/` (contrat de 1-12) et la collecte brute de 1-12a
    (`data/r/collecte/`, `collecte.jsonl`, `pilote.jsonl`), non publiée au lot 1. Le classement
    de 1-12 (`data/r/pre_etude/classement.jsonl`, `resume.json`) reste contrôlable."""
    parts = PurePosixPath(path.replace("\\", "/")).parts
    dirs = [p.lower() for p in parts[:-1]]
    reasons = sorted({p for p in dirs if p in FORBIDDEN_DIRS})
    if parts and parts[-1].lower() in RAW_COLLECTION_FILES:
        reasons.append(parts[-1])
    return [
        Violation(path, PublishRefusalCode.FORBIDDEN_PATH, f"chemin non publié ({reason})")
        for reason in reasons
    ]


# --- recherche normalisée du réservé (AD-19, Q4) ------------------------------------------------

RESERVED_MIN_CHARS = 12
TEXT_SUFFIXES = frozenset({".jsonl", ".json", ".md", ".py", ".txt", ".toml", ".csv"})
_ESCAPE = re.compile(r"\\(u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|x[0-9a-fA-F]{2}|[nrtbf\"'\\/])")
_SIMPLE = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f"}
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """NFC, casse repliée, blancs réduits à une espace."""
    return _SPACES.sub(" ", unicodedata.normalize("NFC", text).casefold())


def _unescape_one(match: re.Match) -> str:
    token = match.group(1)
    if token[0] in "uUx":
        code = int(token[1:], 16)
        return chr(code) if code <= 0x10FFFF else match.group(0)
    return _SIMPLE.get(token, token)


def unescape(text: str) -> str:
    """Décode une couche d'échappements JSON et Python (`\\n`, `\\"`, `\\'`, `\\uXXXX`…)."""
    return _ESCAPE.sub(_unescape_one, text)


def _strings(value: object, depth: int = 0) -> Iterator[str]:
    """Chaînes d'un document JSON, clés comprises ; une chaîne qui est elle-même du JSON est
    décodée à son tour (double encodage), sur 4 niveaux au plus."""
    if isinstance(value, str):
        yield value
        stripped = value.strip()
        if depth < 4 and stripped[:1] in ("{", "[", '"'):
            try:
                inner = json.loads(stripped)
            except ValueError:
                return
            yield from _strings(inner, depth + 1)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item, depth)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item, depth)


def json_documents(path: str, text: str) -> list | None:
    """Documents d'un `.json` (un seul) ou d'un `.jsonl` (un par ligne) ; None si illisible."""
    suffix = PurePosixPath(path).suffix
    try:
        if suffix == ".json":
            return [json.loads(text)]
        if suffix == ".jsonl":
            return [json.loads(line) for line in text.splitlines() if line.strip()]
    except ValueError:
        return None
    return None


def text_pieces(text: str, documents: list | None) -> list[str]:
    """Texte à fouiller : chaînes JSON décodées (ou le texte brut), puis jusqu'à trois couches
    d'échappements décodées."""
    base = [s for doc in documents for s in _strings(doc)] if documents is not None else [text]
    pieces: list[str] = []
    for piece in base:
        pieces.append(piece)
        for _ in range(3):
            if "\\" not in piece:
                break
            decoded = unescape(piece)
            if decoded == piece:
                break
            pieces.append(decoded)
            piece = decoded
    return pieces


@dataclass
class Reserved:
    """`raw` des jeux réservés, normalisés, indexés par leurs `key_len` premiers caractères."""

    index: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    key_len: int = RESERVED_MIN_CHARS
    count: int = 0
    skipped: int = 0
    datasets: list[str] = field(default_factory=list)


def load_reserved(heldout_root: Path) -> Reserved | None:
    """Lit `heldout/*/*/examples.jsonl` ; None si le dossier est absent ou sans jeu."""
    files = sorted(Path(heldout_root).glob("*/*/examples.jsonl"))
    if not files:
        return None
    reserved = Reserved()
    entries: dict[str, str] = {}
    for path in files:
        task, dataset = path.parent.parent.name, path.parent.name
        reserved.datasets.append(f"{task}/{dataset}")
        for line in path.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            raw = row.get("raw")
            raw = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
            if len(raw) < RESERVED_MIN_CHARS:
                reserved.skipped += 1
                continue
            entries.setdefault(normalize(raw).strip(), f"{task}/{dataset}/{row.get('id')}")
    entries = {raw: ref for raw, ref in entries.items() if raw}
    if entries:
        reserved.key_len = min(RESERVED_MIN_CHARS, *(len(raw) for raw in entries))
    for raw, ref in sorted(entries.items()):
        reserved.index.setdefault(raw[: reserved.key_len], []).append((raw, ref))
    reserved.count = len(entries)
    return reserved


def find_reserved(pieces: list[str], reserved: Reserved) -> list[str]:
    """Références (`tâche/jeu/id`) des `raw` réservés présents en entier dans les pièces."""
    if not reserved.index:
        return []
    corpus = "\x00".join(normalize(p) for p in pieces if len(p) >= reserved.key_len)
    width = reserved.key_len
    get = reserved.index.get
    hits: set[str] = set()
    for start in range(len(corpus) - width + 1):
        bucket = get(corpus[start : start + width])
        if bucket:
            hits.update(ref for raw, ref in bucket if corpus.startswith(raw, start))
    return sorted(hits)


# --- contenu de R (section 2 du constat 1-3, Q2, Q10) -------------------------------------------

R_FORBIDDEN_FIELDS = frozenset({"text", "zones", "text_highlight"})
R_RAW_MAX_CHARS = 160
PARTY_PATTERNS = (
    (re.compile(r"(?:^|\s)c/\s"), "c/"),
    (re.compile(r"\bcontre\b", re.IGNORECASE), "contre"),
    (re.compile(r"\bM\.\s"), "M."),
    (re.compile(r"\bMmes?\b"), "Mme"),
    (re.compile(r"\bsoci[ée]t[ée]\b", re.IGNORECASE), "société"),
)


def _walk(value: object) -> Iterator[dict]:
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def check_content(path: str, documents: list, *, strict: bool) -> list[Violation]:
    """Champs interdits à toute profondeur ; noms de parties et longueur de chaque `raw`.

    Hors de l'archive de R (`strict=False`), `text` est admis dans un bloc de message
    (`{"type": "text", "text": ...}`) : c'est la forme des échanges journalisés, pas un texte de
    décision. Dans l'archive de R, il ne l'est jamais.
    """
    found: set[tuple[PublishRefusalCode, str]] = set()
    for line, document in enumerate(documents, start=1):
        where = f"ligne {line}" if len(documents) > 1 else "document"
        for node in _walk(document):
            for key in R_FORBIDDEN_FIELDS & set(node):
                if key == "text" and not strict and node.get("type") == "text":
                    continue
                found.add((PublishRefusalCode.R_FORBIDDEN_FIELD, f"clé {key} ({where})"))
            raw = node.get("raw")
            if not isinstance(raw, str):
                continue
            ident = node.get("id", where)
            if len(raw) > R_RAW_MAX_CHARS:
                detail = f"raw de {len(raw)} caractères (> {R_RAW_MAX_CHARS}), id {ident}"
                found.add((PublishRefusalCode.R_RAW_TOO_LONG, detail))
            for pattern, label in PARTY_PATTERNS:
                if pattern.search(raw):
                    detail = f"motif de nom de partie « {label} » dans raw, id {ident}"
                    found.add((PublishRefusalCode.R_PARTY_NAME, detail))
    return [Violation(path, code, detail) for code, detail in sorted(found)]


PUBLIC_SOURCES = frozenset({"judilibre", "ce-opendata", "jade"})
_SLM_SOURCE = re.compile(r"slm:\S+")


def check_sources(path: str, data: bytes | None, example_ids: list[str] | None) -> list[Violation]:
    """Condition 3 : une classe et une source par ligne, aucune fausse attribuée à une base."""

    def bad(detail: str) -> Violation:
        return Violation(path, PublishRefusalCode.R_SOURCE_MISMATCH, detail)

    if data is None:
        return [bad("sources.jsonl absent")]
    found: list[Violation] = []
    ids: list[str] = []
    for line, text in enumerate(data.decode("utf-8", "replace").splitlines(), start=1):
        if not text.strip():
            continue
        try:
            row = json.loads(text)
        except ValueError:
            found.append(bad(f"ligne {line} illisible"))
            continue
        ident, cls, source = row.get("id"), row.get("class"), row.get("source")
        ids.append(ident)
        if cls not in ("real", "fake"):
            found.append(bad(f"id {ident} : classe {cls!r} hors real, fake"))
        public = source in PUBLIC_SOURCES
        slm = isinstance(source, str) and _SLM_SOURCE.fullmatch(source) is not None
        if not public and not slm:
            found.append(bad(f"id {ident} : source {source!r} inconnue"))
        elif cls == "real" and slm:
            found.append(bad(f"id {ident} : vraie attribuée à un SLM"))
        elif cls == "fake" and public:
            found.append(bad(f"id {ident} : fausse attribuée à une base publique ({source})"))
    if example_ids is not None and sorted(ids) != sorted(example_ids):
        missing = len(set(example_ids) - set(ids))
        extra = len(set(ids) - set(example_ids))
        found.append(bad(f"id différents d'examples.jsonl ({missing} absents, {extra} en trop)"))
    return found


NOTICE_PHRASE = "base Open Data Judilibre de la Cour de cassation"
LICENCE_URL = "https://www.etalab.gouv.fr/licence-ouverte-open-licence"
R_DATE_KEY = "extraction_date"
_EXTRACTION = re.compile(r"extraction du (\d{4}-\d{2}-\d{2})")


def extraction_date(dataset_json: object) -> str | None:
    """`extraction_date` de `dataset.json`, en premier niveau ou sous `composition`."""
    if not isinstance(dataset_json, dict):
        return None
    composition = dataset_json.get("composition")
    value = dataset_json.get(R_DATE_KEY)
    if value is None and isinstance(composition, dict):
        value = composition.get(R_DATE_KEY)
    return value if isinstance(value, str) else None


def check_notice(
    notice_path: str, notice: str | None, dates: list[tuple[str, str | None]]
) -> list[Violation]:
    """Condition 2 et Q10 : phrase d'attribution, URL de la licence, date d'extraction de chaque
    jeu de R reprise dans `NOTICE`."""

    def missing(path: str, detail: str) -> Violation:
        return Violation(path, PublishRefusalCode.R_ATTRIBUTION_MISSING, detail)

    if notice is None:
        return [missing(notice_path, "fichier absent")]
    found = []
    if NOTICE_PHRASE not in notice:
        found.append(missing(notice_path, f"« {NOTICE_PHRASE} » absent"))
    if LICENCE_URL not in notice:
        found.append(missing(notice_path, f"URL de la licence ({LICENCE_URL}) absente"))
    noticed = set(_EXTRACTION.findall(notice))
    if not noticed:
        found.append(missing(notice_path, "« extraction du AAAA-MM-JJ » absent"))
    for dataset, date in dates:
        if date is None:
            found.append(missing(dataset, f"dataset.json sans {R_DATE_KEY}"))
        elif noticed and date not in noticed:
            found.append(missing(notice_path, f"date d'extraction {date} de {dataset} absente"))
    return found


# --- contrôle d'un membre ou d'un fichier -------------------------------------------------------


@dataclass(frozen=True)
class Rules:
    secrets: Secrets
    reserved: Reserved | None
    r_tasks: frozenset[str]
    r_republish: bool


def check_member(
    path: str, data: bytes, rules: Rules, *, reserved: bool = True, strict: bool = False
) -> list[Violation]:
    """Chemin, motifs de clé, secrets, réservé (si `reserved`) et contenu de R d'un membre."""
    found = check_path(path) + check_secrets(path, data, rules.secrets)
    if PurePosixPath(path).suffix.lower() not in TEXT_SUFFIXES:
        return found
    text = data.decode("utf-8", "replace")
    documents = json_documents(path, text)
    if reserved and rules.reserved is not None:
        for ref in find_reserved(text_pieces(text, documents), rules.reserved):
            found.append(Violation(path, PublishRefusalCode.RESERVED_EXAMPLE, f"exemple {ref}"))
    if documents is not None:
        found += check_content(path, documents, strict=strict)
    return found


def mentions_r_task(text: str, r_tasks: frozenset[str]) -> list[str]:
    return sorted(t for t in r_tasks if re.search(rf"\b{re.escape(t)}\b", text))


def check_paths(paths: Iterable[Path], rules: Rules, base: Path) -> tuple[list[Violation], int]:
    """`nnww publish --check` (Q3) : mêmes contrôles sur des fichiers à publier hors archive.

    Un dossier est parcouru en entier. Sans `r_republish`, un fichier qui nomme une tâche de R
    est refusé. Rend les violations et le nombre de fichiers contrôlés.
    """
    files: list[Path] = []
    for path in paths:
        path = Path(path)
        if path.is_dir():
            files += sorted(p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"{path} : introuvable")
    found: list[Violation] = []
    if rules.reserved is None:
        found.append(Violation("heldout/", PublishRefusalCode.NO_HELDOUT, "aucun jeu réservé"))
    for path in files:
        label = _label(path, base)
        data = path.read_bytes()
        found += check_member(label, data, rules)
        if not rules.r_republish:
            for task in mentions_r_task(data.decode("utf-8", "replace"), rules.r_tasks):
                detail = f"nomme la tâche de R {task} sans r_republish = true"
                found.append(Violation(label, PublishRefusalCode.R_WITHOUT_REPUBLISH, detail))
        if path.name == "sources.jsonl":
            examples = path.parent / "examples.jsonl"
            ids = _ids(examples.read_bytes()) if examples.is_file() else None
            found += check_sources(label, data, ids)
    return found, len(files)


def _ids(data: bytes) -> list[str]:
    lines = data.decode("utf-8", "replace").splitlines()
    return [json.loads(line).get("id") for line in lines if line.strip()]


def _label(path: Path, base: Path) -> str:
    for anchor in (base, Path.cwd()):
        try:
            return path.resolve().relative_to(Path(anchor).resolve()).as_posix()
        except ValueError:
            continue
    return path.resolve().as_posix()
