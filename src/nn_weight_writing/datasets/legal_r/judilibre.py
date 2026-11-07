"""Client de l'API Judilibre (story 1-12, D5) : transport injectable, cache de métadonnées.

Seul accès réseau du paquet. En-tête `KeyId` seulement ; la clé n'apparaît ni dans `repr`, ni
dans une exception, ni dans le cache. Moins de 10 requêtes par seconde, `x-rate-limit` lu à
chaque réponse. Le cache ne garde que les champs de `KEPT_FIELDS` (aucun texte).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

BASE_URL = "https://api.piste.gouv.fr/cassation/judilibre/v1.0"
KEY_ENV = "JUDILIBRE_KEY_ID"
KEPT_FIELDS = (
    "id",
    "jurisdiction",
    "chamber",
    "formation",
    "location",
    "number",
    "numbers",
    "ecli",
    "decision_date",
    "type",
    "publication",
    "update_date",
)
PAGE_FIELDS = ("total", "relaxed", "batch", "page", "next_batch", "next_page")
MIN_INTERVAL = 0.12
RETRY_DELAYS = (2, 4, 8)
SHORT_WINDOW_MAX = 60  # secondes : au-delà, compteur journalier
DAILY_FLOOR = 1000
SHORT_FLOOR = 2

Fetch = Callable[[str, Mapping[str, str]], tuple[int, Mapping[str, str], bytes]]


class JudilibreError(RuntimeError):
    """Erreur du client ; `suspicious` : HTTP 423 (arrêt immédiat, à signaler) ; `quota` :
    compteur journalier sous 1 000 (arrêt). `fatal` : l'une ou l'autre, jamais un `api_error`."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        suspicious: bool = False,
        quota: bool = False,
    ):
        super().__init__(message)
        self.status = status
        self.suspicious = suspicious
        self.quota = quota

    @property
    def fatal(self) -> bool:
        return self.suspicious or self.quota


def key_from_env() -> str:
    """Lit `JUDILIBRE_KEY_ID` ; `JudilibreError` (sans valeur) si elle est absente."""
    value = os.environ.get(KEY_ENV, "").strip()
    if not value:
        raise JudilibreError(f"{KEY_ENV} absente de l'environnement")
    return value


def project_decision(meta: Mapping) -> dict:
    """Liste blanche des métadonnées d'une décision : aucun texte, résumé ni surlignage."""
    return {k: meta[k] for k in KEPT_FIELDS if k in meta}


@dataclass
class RateLimitState:
    """Dernier `x-rate-limit` lu : compteurs `{"window", "type", "remaining"}`."""

    raw: str | None = None
    counters: list[dict] = field(default_factory=list)

    def update(self, header: str | None) -> None:
        if not header:
            return
        try:
            counters = json.loads(header)
        except json.JSONDecodeError:
            return
        if isinstance(counters, dict):
            counters = [counters]
        self.raw = header
        self.counters = [c for c in counters if isinstance(c, dict)]

    def short_low(self) -> bool:
        return any(
            c.get("window", 0) <= SHORT_WINDOW_MAX and c.get("remaining", 99) <= SHORT_FLOOR
            for c in self.counters
        )

    def daily_low(self) -> bool:
        return any(
            c.get("window", 0) > SHORT_WINDOW_MAX and c.get("remaining", DAILY_FLOOR) < DAILY_FLOOR
            for c in self.counters
        )


def _urllib_fetch(url: str, headers: Mapping[str, str]) -> tuple[int, Mapping[str, str], bytes]:
    request = urllib.request.Request(url, headers=dict(headers))
    try:
        with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - https fixe
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers or {}), error.read() or b""


def canonical_request(path: str, params: Mapping[str, object]) -> str:
    """Chemin et paramètres triés, sans la clé : base de la clé de cache."""
    items = sorted((str(k), str(v)) for k, v in params.items())
    return path + ("?" + urllib.parse.urlencode(items) if items else "")


def cache_key(path: str, params: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_request(path, params).encode("utf-8")).hexdigest()


class JudilibreClient:
    def __init__(
        self,
        key: str,
        *,
        fetch: Fetch | None = None,
        cache_dir: Path | None = None,
        refresh: bool = False,
        base_url: str = BASE_URL,
        min_interval: float = MIN_INTERVAL,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        log: Callable[[str], None] | None = None,
    ) -> None:
        self.__key = key
        self._fetch = fetch or _urllib_fetch
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.refresh = refresh
        self.base_url = base_url
        self.min_interval = min_interval
        self._sleep = sleep
        self._clock = clock
        self._last: float | None = None
        self._log = log or (lambda _msg: None)
        self.rate = RateLimitState()
        self.requests = 0  # requêtes réseau envoyées
        self.cache_hits = 0

    def __repr__(self) -> str:
        return f"JudilibreClient(base_url={self.base_url!r}, cache_dir={self.cache_dir!r})"

    # -- transport ---------------------------------------------------------------------

    def _wait(self) -> None:
        now = self._clock()
        if self._last is not None and now - self._last < self.min_interval:
            self._sleep(self.min_interval - (now - self._last))
        self._last = self._clock()

    def _send(self, url: str) -> tuple[int, Mapping[str, str], bytes]:
        headers = {"KeyId": self.__key, "accept": "application/json"}
        try:
            return self._fetch(url, headers)
        except Exception as error:  # réseau : message sans clé ni en-tête
            return -1, {}, type(error).__name__.encode("utf-8")

    def _request(self, path: str, params: Mapping[str, object]) -> tuple[int, dict, dict]:
        url = self.base_url + canonical_request(path, params)
        attempt = 0
        while True:
            self._wait()
            status, headers, body = self._send(url)
            self.requests += 1
            lowered = {str(k).lower(): v for k, v in headers.items()}
            self.rate.update(lowered.get("x-rate-limit"))
            if status == 423:
                raise JudilibreError(
                    f"HTTP 423 (activité suspecte) sur {path} : arrêt immédiat, à signaler",
                    status=423,
                    suspicious=True,
                )
            if status == 429 or status == -1 or status >= 500:
                if attempt < len(RETRY_DELAYS):
                    self._log(
                        f"HTTP {status} sur {path}, nouvel essai dans {RETRY_DELAYS[attempt]} s"
                    )
                    self._sleep(RETRY_DELAYS[attempt])
                    attempt += 1
                    continue
                raise JudilibreError(
                    f"HTTP {status} sur {path} après {attempt} essais", status=status
                )
            if status != 200:
                raise JudilibreError(f"HTTP {status} sur {path}", status=status)
            if self.rate.daily_low():
                raise JudilibreError(
                    "quota journalier sous 1 000 requêtes : arrêt", status=status, quota=True
                )
            if self.rate.short_low():
                self._sleep(1.0)
            try:
                data = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise JudilibreError(f"réponse illisible sur {path}", status=status) from error
            return status, lowered, data

    # -- cache -------------------------------------------------------------------------

    def _cache_path(self, path: str, params: Mapping[str, object]) -> Path | None:
        if self.cache_dir is None:
            return None
        return self.cache_dir / f"{cache_key(path, params)}.json"

    def get(self, path: str, params: Mapping[str, object]) -> dict:
        """Page projetée : `request`, `fetched_at`, `status`, `x_rate_limit`, `page`, `results`."""
        target = self._cache_path(path, params)
        if target is not None and target.exists() and not self.refresh:
            self.cache_hits += 1
            return json.loads(target.read_text(encoding="utf-8"))
        if target is not None and target.exists() and self.refresh:
            self._log(f"rafraîchi : {canonical_request(path, params)}")
        status, headers, data = self._request(path, params)
        entry = {
            "request": canonical_request(path, params),
            "cache_key": cache_key(path, params),
            "fetched_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": status,
            "x_rate_limit": headers.get("x-rate-limit"),
            "page": {k: data[k] for k in PAGE_FIELDS if isinstance(data, dict) and k in data},
        }
        if path in {"/scan", "/search"}:
            entry["results"] = [project_decision(r) for r in data.get("results") or []]
        elif path == "/stats":
            entry["results"] = _stats_whitelist(data.get("results") or {})
        elif path == "/taxonomy":
            entry["results"] = {str(k): str(v) for k, v in (data.get("result") or {}).items()}
        else:
            entry["results"] = None
        if target is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")
        return entry

    # -- points d'accès -----------------------------------------------------------------

    def scan(self, params: Mapping[str, object]) -> list[dict]:
        """Tous les lots d'un `/scan`, en suivant `next_batch` jusqu'à `null`."""
        out: list[dict] = []
        current: Mapping[str, object] = dict(params)
        seen = set()
        while True:
            entry = self.get("/scan", current)
            out.extend(entry["results"])
            nxt = entry["page"].get("next_batch")
            if not nxt:
                return out
            parsed = dict(urllib.parse.parse_qsl(nxt, keep_blank_values=True))
            marker = canonical_request("/scan", parsed)
            if marker in seen:
                raise JudilibreError("next_batch en boucle")
            seen.add(marker)
            current = parsed

    def scan_day(self, jurisdiction: str, day: str, location: str | None = None) -> list[dict]:
        params: dict[str, object] = {
            "jurisdiction": jurisdiction,
            "date_start": day,
            "date_end": day,
            "date_type": "creation",
            "abridged": "true",
            "batch_size": 1000,
        }
        if location:
            params["location"] = location
        return self.scan(params)

    def search_number(self, number: str, jurisdiction: str, *, max_pages: int = 5) -> list[dict]:
        """Diagnostic `/search` (T4, T5) : résultats projetés ; le `total` n'est jamais lu."""
        out: list[dict] = []
        for page in range(max_pages):
            params = {
                "query": number,
                "jurisdiction": jurisdiction,
                "page_size": 50,
                "page": page,
            }
            entry = self.get("/search", params)
            out.extend(entry["results"])
            if not entry["page"].get("next_page"):
                break
        return out

    def stats(self, jurisdiction: str, keys: str | None = None) -> dict:
        params = {"jurisdiction": jurisdiction}
        if keys:
            params["keys"] = keys
        return self.get("/stats", params)["results"]

    def taxonomy(self, taxonomy_id: str, context_value: str) -> dict:
        return self.get("/taxonomy", {"id": taxonomy_id, "context_value": context_value})["results"]


def _stats_whitelist(results: Mapping) -> dict:
    keys = ("min_decision_date", "max_decision_date", "total_decisions")
    out = {k: results[k] for k in keys if k in results}
    if "aggregated_data" in results:
        out["aggregated_data"] = [
            {"key": dict(item.get("key") or {}), "decisions_count": item.get("decisions_count")}
            for item in results["aggregated_data"]
        ]
    return out
