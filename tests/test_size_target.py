"""Taille cible des séances A (1-10a) : fenêtre d'une demi-décade, refus, prompt, journal."""

from __future__ import annotations

import pytest
from conftest import ENCODER, journal_records

from nn_weight_writing.session import prompt
from nn_weight_writing.session.refusals import RefusalCode
from nn_weight_writing.session.tools import check_size_target, size_label, size_window


def manifest(hidden: int) -> dict:
    """2 -> hidden -> 1 : 4 * hidden + 1 paramètres."""
    return {
        "encoder": ENCODER,
        "layers": [
            {"type": "dense", "in": 2, "out": hidden, "activation": "relu"},
            {"type": "dense", "in": hidden, "out": 1, "activation": "identity"},
        ],
    }


def test_windows_are_half_decades_and_contiguous():
    assert size_window(10_000) == (3162, 31623)
    assert size_window(100_000) == (31623, 316228)
    assert (size_label(10_000), size_label(100_000)) == ("1e4", "1e5")


@pytest.mark.parametrize(
    ("method", "size", "message"),
    [
        ("B", 10_000, "la taille cible est interdite pour la méthode B"),
        ("A-program", None, "la taille cible est obligatoire pour la méthode A-program"),
        ("A-literal", None, "la taille cible est obligatoire pour la méthode A-literal"),
        ("A-program", 5000, "taille cible 5000 refusée ; admises : 10000, 100000"),
        ("A-literal", 1_000_000, "taille cible 1000000 refusée ; admises : 10000, 100000"),
    ],
)
def test_opening_refuses_invalid_size_target(method, size, message):
    with pytest.raises(ValueError) as error:
        check_size_target(method, size)
    assert str(error.value) == message


def test_service_refuses_to_open_with_wrong_size_target(make_service):
    with pytest.raises(ValueError, match="interdite pour la méthode B"):
        make_service("B", size_target=10_000)
    with pytest.raises(ValueError, match="taille cible 5000 refusée"):
        make_service("A-program", size_target=5000)


def test_prompt_states_the_window():
    text = prompt.system_prompt("A-program", 20, 10_000)
    assert (
        "Taille visée : environ 10⁴ paramètres ; declare_network refuse un réseau "
        "hors de [3 162 ; 31 623].\n"
    ) in text
    assert "hors de [31 623 ; 316 228]" in prompt.system_prompt("A-literal", 20, 100_000)
    assert "Taille visée" not in prompt.system_prompt("B", 20)
    with pytest.raises(ValueError):
        prompt.system_prompt("A-program", 20)


def test_declare_network_refused_outside_window_without_pass(make_service):
    service = make_service("A-program", size_target=10_000)
    for hidden, declared in ((10, 41), (8000, 32001)):
        result = service.call("declare_network", {"manifest": manifest(hidden)})
        assert result["refused"] == RefusalCode.SIZE_OUT_OF_RANGE
        assert result["detail"] == f"{declared} paramètres déclarés ; fenêtre admise [3162 ; 31623]"
    assert service.passes_used == 0 and service.manifest is None
    refusals = [r for r in journal_records(service) if r["type"] == "refusal"]
    assert [r["code"] for r in refusals] == ["size_out_of_range"] * 2


def test_declare_network_accepted_inside_window(make_service):
    service = make_service("A-literal", size_target=10_000)
    assert service.call("declare_network", {"manifest": manifest(1000)}) == {
        "declared": True,
        "params": 4001,
    }
    other = make_service("A-literal", size_target=100_000)
    assert other.call("declare_network", {"manifest": manifest(1000)})["refused"] == (
        RefusalCode.SIZE_OUT_OF_RANGE
    )


def test_open_event_records_size_target(make_service):
    assert journal_records(make_service("A-program", size_target=100_000))[0]["size_target"] == (
        100_000
    )
    assert journal_records(make_service("B"))[0]["size_target"] is None
