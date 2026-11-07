"""Client Judilibre de la pré-étude R (story 1-12, D5, AC5 et AC12). Aucun accès réseau."""

from __future__ import annotations

import json

import pytest
from legal_r_support import EMPTY_SCAN, KEY, FakeClock, FakeTransport, make_client, ok

from nn_weight_writing.datasets.legal_r.judilibre import (
    JudilibreClient,
    JudilibreError,
    RateLimitState,
    cache_key,
    canonical_request,
    key_from_env,
    project_decision,
)

PERRUCHE_DAY = {"jurisdiction": "cc", "date_start": "2000-11-17"}


def _all_written(directory) -> str:
    return "".join(p.read_text(encoding="utf-8") for p in sorted(directory.rglob("*.json")))


def test_key_never_exposed(tmp_path, monkeypatch):
    clock = FakeClock()
    transport = FakeTransport(
        [
            ("/scan", PERRUCHE_DAY, [ok("scan_cc_2000-11-17.json")]),
            ("/healthcheck", {}, [(423, {}, b"")]),
        ],
        clock,
    )
    client = make_client(transport, clock, tmp_path)
    client.scan_day("cc", "2000-11-17")
    assert KEY not in repr(client)
    assert transport.calls[0][1]["KeyId"] == KEY
    assert KEY not in transport.calls[0][0]
    with pytest.raises(JudilibreError) as raised:
        client.get("/healthcheck", {})
    assert KEY not in str(raised.value) and KEY not in repr(raised.value)
    assert KEY not in _all_written(tmp_path)

    def boom(url, headers):
        raise OSError(f"échec avec {headers['KeyId']}")

    failing = JudilibreClient(KEY, fetch=boom, sleep=lambda s: None)
    with pytest.raises(JudilibreError) as raised:
        failing.get("/healthcheck", {})
    assert KEY not in str(raised.value)
    monkeypatch.delenv("JUDILIBRE_KEY_ID", raising=False)
    with pytest.raises(JudilibreError, match="absente"):
        key_from_env()
    monkeypatch.setenv("JUDILIBRE_KEY_ID", KEY)
    assert key_from_env() == KEY


def test_rate_limit_interval():
    clock = FakeClock()
    transport = FakeTransport([("/healthcheck", {}, [ok({"status": "disponible"})])], clock)
    client = make_client(transport, clock)
    for _ in range(30):
        client.get("/healthcheck", {})
    times = [t for _, _, t in transport.calls]
    assert len(times) == 30
    assert min(b - a for a, b in zip(times, times[1:], strict=False)) >= 0.12 - 1e-9
    assert client.requests == 30


def test_rate_limit_header_pause_and_stop():
    clock = FakeClock()
    low_short = '[{"window":62204,"type":"throttle","remaining":999000},{"window":0,"remaining":2}]'
    low_daily = '[{"window":62204,"type":"throttle","remaining":999},{"window":0,"remaining":19}]'
    transport = FakeTransport(
        [
            (
                "/healthcheck",
                {},
                [ok({"status": "ok"}, low_short), ok({"status": "ok"}, low_daily)],
            ),
        ],
        clock,
    )
    client = make_client(transport, clock)
    client.get("/healthcheck", {})
    assert 1.0 in clock.sleeps
    assert client.rate.raw == low_short
    with pytest.raises(JudilibreError, match="quota journalier"):
        client.get("/healthcheck", {})
    state = RateLimitState()
    state.update("pas du json")
    assert state.counters == [] and not state.short_low() and not state.daily_low()


def test_429_retry_423_stop():
    clock = FakeClock()
    transport = FakeTransport(
        [
            ("/healthcheck", {"n": "1"}, [(429, {}, b""), ok({"status": "ok"})]),
            ("/healthcheck", {"n": "2"}, [(429, {}, b"")]),
            ("/healthcheck", {"n": "3"}, [(423, {}, b"")]),
        ],
        clock,
    )
    client = make_client(transport, clock)
    assert client.get("/healthcheck", {"n": 1})["status"] == 200
    assert [s for s in clock.sleeps if s >= 1] == [2]
    clock.sleeps.clear()
    with pytest.raises(JudilibreError, match="HTTP 429") as raised:
        client.get("/healthcheck", {"n": 2})
    assert raised.value.status == 429 and not raised.value.suspicious
    assert [s for s in clock.sleeps if s >= 1] == [2, 4, 8]
    before = len(transport.calls)
    with pytest.raises(JudilibreError, match="423") as raised:
        client.get("/healthcheck", {"n": 3})
    assert raised.value.suspicious and len(transport.calls) == before + 1


def test_cache_whitelist_and_reuse(tmp_path):
    clock = FakeClock()
    transport = FakeTransport([("/scan", PERRUCHE_DAY, [ok("scan_cc_2000-11-17.json")])], clock)
    client = make_client(transport, clock, tmp_path)
    first = client.scan_day("cc", "2000-11-17")
    again = make_client(transport, clock, tmp_path).scan_day("cc", "2000-11-17")
    assert first == again and len(transport.calls) == 1
    written = _all_written(tmp_path)
    for secret in ("TEXTE-INTEGRAL-SECRET", "SURLIGNAGE-SECRET", "résumé", "Dès lors", "zones"):
        assert secret not in written
    (entry_path,) = tmp_path.glob("*.json")
    entry = json.loads(entry_path.read_text(encoding="utf-8"))
    params = {
        "jurisdiction": "cc",
        "date_start": "2000-11-17",
        "date_end": "2000-11-17",
        "date_type": "creation",
        "abridged": "true",
        "batch_size": 1000,
    }
    assert entry_path.stem == cache_key("/scan", params) == entry["cache_key"]
    assert entry["request"] == canonical_request("/scan", params)
    assert entry["request"].startswith("/scan?abridged=true&batch_size=1000&date_end=")
    assert set(entry) == {
        "request",
        "cache_key",
        "fetched_at",
        "status",
        "x_rate_limit",
        "page",
        "results",
    }
    assert entry["page"] == {"total": 2, "next_batch": None}
    assert {k for r in entry["results"] for k in r} <= {
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
    }
    assert project_decision({"id": "x", "text": "t", "zones": {}, "summary": "s"}) == {"id": "x"}
    refreshed = make_client(transport, clock, tmp_path)
    refreshed.refresh = True
    refreshed.scan_day("cc", "2000-11-17")
    assert len(transport.calls) == 2


def test_scan_follows_next_batch(tmp_path):
    clock = FakeClock()
    day = {"jurisdiction": "cc", "date_start": "2019-03-14"}
    transport = FakeTransport(
        [
            (
                "/scan",
                {**day, "searchAfter": "0&1552521600000&5fca7615c561ac6356f0388a"},
                [ok("scan_cc_2019-03-14_lot2.json")],
            ),
            ("/scan", day, [ok("scan_cc_2019-03-14_lot1.json")]),
            ("/scan", {"jurisdiction": "cc"}, [ok(EMPTY_SCAN)]),
        ],
        clock,
    )
    client = make_client(transport, clock, tmp_path)
    results = client.scan_day("cc", "2019-03-14")
    assert [r["id"] for r in results] == [
        "5fca7615c561ac6356f0388b",
        "5fca7615c561ac6356f0388a",
        "fixture-cc-2019-3",
    ]
    assert len(transport.calls) == 2
    assert client.scan_day("cc", "2019-03-15") == []
