"""Known answer tests for the string comparators."""

import pytest

from linkage.strings import jaro, jaro_winkler, soundex

# Standard worked examples from the Jaro-Winkler literature, reported to three
# decimals: (left, right, Jaro, Jaro-Winkler). MARTHA is also checked by hand below.
PUBLISHED = [
    ("MARTHA", "MARHTA", 0.944, 0.961),
    ("DWAYNE", "DUANE", 0.822, 0.840),
    ("DIXON", "DICKSONX", 0.767, 0.813),
]


@pytest.mark.parametrize(("left", "right", "jaro_value", "winkler_value"), PUBLISHED)
def test_published_jaro_winkler_values(left, right, jaro_value, winkler_value):
    assert jaro(left, right) == pytest.approx(jaro_value, abs=5e-4)
    assert jaro_winkler(left, right) == pytest.approx(winkler_value, abs=5e-4)


def test_martha_by_hand():
    # 6 common characters, one transposed pair (TH vs HT): (1 + 1 + 5/6) / 3.
    assert jaro("MARTHA", "MARHTA") == pytest.approx((1 + 1 + 5 / 6) / 3)
    # Shared prefix MAR (3 letters): J + 3 * 0.1 * (1 - J).
    expected = jaro("MARTHA", "MARHTA") * 0.7 + 0.3
    assert jaro_winkler("MARTHA", "MARHTA") == pytest.approx(expected)


def test_edge_cases():
    assert jaro("", "") == 0.0
    assert jaro("abc", "") == 0.0
    assert jaro("same", "same") == 1.0
    assert jaro("abc", "xyz") == 0.0
    assert jaro("martha", "marhta") == jaro("marhta", "martha")


def test_no_prefix_boost_below_threshold():
    # Jaro of 'cbe' and 'caaa' is below 0.7, so no Winkler boost despite shared 'c'.
    assert jaro_winkler("cbe", "caaa") == jaro("cbe", "caaa")


# Examples from the US National Archives Soundex coding guide.
@pytest.mark.parametrize(("name", "code"), [
    ("Robert", "R163"), ("Rupert", "R163"), ("Rubin", "R150"), ("Ashcraft", "A261"),
    ("Tymczak", "T522"), ("Pfister", "P236"), ("Honeyman", "H555"), ("Lee", "L000"),
])
def test_soundex_national_archives_examples(name, code):
    assert soundex(name) == code


def test_soundex_empty():
    assert soundex("") == ""
