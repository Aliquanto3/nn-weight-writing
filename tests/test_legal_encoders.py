"""Encodeurs fixes de S (story 1-9, D5, O7)."""

from __future__ import annotations

import numpy as np
import pytest

from nn_weight_writing.tasks.legal import TASK_S
from nn_weight_writing.tasks.legal.encoders import (
    ALPHABET,
    N_CHARS,
    N_FIELDS,
    N_FIELDS_V2,
    encode_chars,
    encode_fields,
    encode_fields_v2,
)

REF = "Cass. civ. 1re, 12 mars 2015, n° 13-27.123"
PERRUCHE = "Cass. ass. plén., 17 novembre 2000, n° 99-13.701"


def test_alphabet_has_50_symbols_with_the_documented_indices():
    assert len(ALPHABET) == 50
    assert (ALPHABET.index("a"), ALPHABET.index("0"), ALPHABET.index(" ")) == (0, 26, 36)
    assert (ALPHABET.index("."), ALPHABET.index(","), ALPHABET.index("-")) == (37, 38, 39)
    assert (ALPHABET.index("/"), ALPHABET.index("é"), ALPHABET.index("ç")) == (40, 41, 49)


def test_chars_layout():
    x = encode_chars(REF)
    assert x.shape == (3060,) and x.dtype == np.float32
    assert set(np.unique(x)) == {0.0, 1.0}
    assert int(x.sum()) == 33  # 14 en-tête, 2 jour, 4 mois, 4 année, 9 numéro
    assert x[:1632].sum() == 14
    assert x[51 * 32 : 51 * 35].sum() == 2
    assert x[51 * 35 : 51 * 44].sum() == 4
    assert x[51 * 44 : 51 * 48].sum() == 4
    assert x[51 * 48 :].sum() == 9
    assert x[51 * 0 + 2] == 1  # « c »
    assert x[51 * 32 + 27] == 1  # « 1 » du jour
    assert x[51 * 48 + 27] == 1  # « 1 » du numéro
    assert not x[51 * 30 : 51 * 32].any()  # fin d'en-tête vide


def test_chars_other_symbol_and_truncation():
    header = "CE, " + "x" * 36  # 40 caractères
    raw = f"{header}, 12 mars 2015, n° 381234"
    x = encode_chars(raw)
    assert x[51 * 2 + 38] == 1  # « ce, » : la virgule est le symbole 38
    assert x[:1632].sum() == 32  # au-delà de la position 31, l'en-tête est ignoré
    assert x[51 * 32 + 27] == 1 and x[51 * 33 + 28] == 1  # « 12 » commence en 32
    # un caractère hors alphabet prend le symbole 50
    y = encode_chars("Cass. ñ, 12 mars 2015, n° 1")
    assert y[51 * 6 + 50] == 1
    assert y.sum() == 7 + 2 + 4 + 4 + 1
    # « n° » est retiré avant l'encodage : le numéro commence par son premier chiffre
    assert x[51 * 48 + 27] == 0 and encode_chars("Cass. a, 1 mars 2015, n° 1")[51 * 48 + 27] == 1


def test_encoders_are_pure():
    first = encode_chars(REF)
    encode_chars(PERRUCHE)
    encode_fields(REF)
    assert np.array_equal(first, encode_chars(REF))
    assert np.array_equal(encode_fields(REF), encode_fields(REF))


@pytest.mark.parametrize(
    ("raw", "error"),
    [
        ("Cass. soc., 12 mars 2015, 13-27.123", ValueError),
        ("Cass. soc., 12 mars, n° 13-27.123", ValueError),
        ("sans virgule", ValueError),
        (None, TypeError),
        (42, TypeError),
    ],
)
def test_encoders_refuse_non_canonical(raw, error):
    with pytest.raises(error):
        encode_chars(raw)
    with pytest.raises(error):
        encode_fields(raw)


def test_fields_layout():
    x = encode_fields(PERRUCHE)
    assert x.shape == (N_FIELDS,) == (2249,) and x.dtype == np.float32
    assert x[2244] == pytest.approx(17 / 31)
    assert x[2245] == pytest.approx(11 / 12)
    assert x[2246] == pytest.approx((2000 - 1980) / 50)
    assert x[2247] == 1
    assert x[2248] == pytest.approx((1999 - 1980) / 50)
    assert x[:1632].sum() == len("cass. ass. plén.")
    assert x[1632:2244].sum() == len("99-13.701")


def test_fields_first_day_unreadable_tokens_and_bounds():
    assert encode_fields("CE, Sect., 1er mars 2015, n° 381234")[2244] == pytest.approx(1 / 31)
    odd = encode_fields("CE, Sect., xx zzz yyyy, n° 381234")
    assert tuple(odd[2244:2247]) == (0, 0, 0)
    assert odd[2247] == 0 and odd[2248] == 0  # six chiffres : pas d'AA
    # O7 : les années restent dans [0, 1], bornes comprises
    low = encode_fields("Cass. soc., 12 mars 1975, n° 52-13.701")
    high = encode_fields("Cass. soc., 12 mars 2040, n° 13-13.701")
    assert low[2246] == 0 and low[2248] == 0
    assert high[2246] == 1
    for ref in (low, high, encode_fields("Cass. soc., 12 mars 2029, n° 29-13.701")):
        assert ref[2244:].min() >= 0 and ref[2244:].max() <= 1
    assert encode_fields("Cass. soc., 12 mars 2029, n° 29-13.701")[2246] == pytest.approx(0.98)


def test_fields_v2_layout_one_hot():
    x = encode_fields_v2(PERRUCHE)
    assert x.shape == (N_FIELDS_V2,) == (2408,) and x.dtype == np.float32
    assert np.array_equal(x[:2244], encode_fields(PERRUCHE)[:2244])  # mêmes caractères qu'@1
    # jour 17, novembre, 2000, AA présent, AA 1999 : un seul 1 par groupe
    assert list(np.flatnonzero(x[2244:]) + 2244) == [2260, 2285, 2307, 2347, 2367]
    assert TASK_S.prepared_encoder_id == "legal.fields@2"
    assert np.array_equal(TASK_S.encode_prepared(PERRUCHE), x)


def test_fields_v2_unreadable_or_out_of_range_groups_are_zero():
    x = encode_fields_v2("CE, Sect., 1er mars 2015, n° 381234")
    assert list(np.flatnonzero(x[2244:]) + 2244) == [2244, 2277, 2287 + 35]  # pas d'AA
    odd = encode_fields_v2("Cass. soc., 32 zzz 2040, n° 52-13.701")  # jour, mois, année hors
    assert list(np.flatnonzero(odd[2244:]) + 2244) == [2347]  # AA 1952 hors de 1980-2039
    last = encode_fields_v2("Cass. soc., 29 février 2039, n° 39-13.701")
    assert list(np.flatnonzero(last[2244:]) + 2244) == [2272, 2276, 2346, 2347, 2407]


def test_decode_argmax_and_tie():
    assert TASK_S.decode(np.array([0.2, 0.9])) == "fake"
    assert TASK_S.decode(np.array([0.9, 0.2])) == "real"
    assert TASK_S.decode(np.array([0.5, 0.5])) == "real"
    with pytest.raises(ValueError):
        TASK_S.decode(np.array([0.1, 0.2, 0.3]))


def test_reference_architecture_size():
    assert N_CHARS * 32 + 32 + 32 * 2 + 2 == 98018
    assert N_FIELDS * 32 + 32 + 66 == 72066
