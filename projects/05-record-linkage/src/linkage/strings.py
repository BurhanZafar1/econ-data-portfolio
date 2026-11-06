"""String comparators used in record linkage, written out from their definitions.

Jaro (1989) and Winkler (1990) define the comparator used by the US Census
Bureau for name matching. Soundex is the phonetic code used by the US
National Archives for census indexing.
"""

from __future__ import annotations

from functools import lru_cache

WINKLER_PREFIX_SCALE = 0.1
WINKLER_MAX_PREFIX = 4
WINKLER_BOOST_THRESHOLD = 0.7
SOUNDEX_CODES = {
    **dict.fromkeys("bfpv", "1"),
    **dict.fromkeys("cgjkqsxz", "2"),
    **dict.fromkeys("dt", "3"),
    "l": "4",
    **dict.fromkeys("mn", "5"),
    "r": "6",
}


@lru_cache(maxsize=1_000_000)
def jaro(left: str, right: str) -> float:
    """Jaro similarity in [0, 1]: shared characters, penalised for transpositions.

    Half the transposition count is taken in whole numbers, as in the Census
    Bureau's strcmp95 code that accompanies Winkler (1990).
    """
    if left == right:
        return 1.0 if left else 0.0
    len_left, len_right = len(left), len(right)
    if len_left == 0 or len_right == 0:
        return 0.0
    window = max(max(len_left, len_right) // 2 - 1, 0)
    left_hit = [False] * len_left
    right_hit = [False] * len_right
    common = 0
    for i, char in enumerate(left):
        start, stop = max(0, i - window), min(i + window + 1, len_right)
        for j in range(start, stop):
            if not right_hit[j] and right[j] == char:
                left_hit[i] = right_hit[j] = True
                common += 1
                break
    if common == 0:
        return 0.0
    left_common = [c for c, hit in zip(left, left_hit) if hit]
    right_common = [c for c, hit in zip(right, right_hit) if hit]
    transpositions = sum(a != b for a, b in zip(left_common, right_common)) // 2
    return (common / len_left + common / len_right + (common - transpositions) / common) / 3


def jaro_winkler(left: str, right: str) -> float:
    """Jaro similarity boosted for a shared prefix of up to four characters.

    The boost applies only when the Jaro score already exceeds 0.7.
    """
    base = jaro(left, right)
    if base <= WINKLER_BOOST_THRESHOLD:
        return base
    prefix = 0
    for a, b in zip(left[:WINKLER_MAX_PREFIX], right[:WINKLER_MAX_PREFIX]):
        if a != b:
            break
        prefix += 1
    return base + prefix * WINKLER_PREFIX_SCALE * (1 - base)


def soundex(word: str) -> str:
    """American Soundex code (letter plus three digits), National Archives rules.

    Letters h and w do not separate two letters with the same code; vowels do.
    """
    letters = [c for c in word.lower() if c.isalpha()]
    if not letters:
        return ""
    digits: list[str] = []
    previous = SOUNDEX_CODES.get(letters[0], "")
    for char in letters[1:]:
        code = SOUNDEX_CODES.get(char, "")
        if code and code != previous:
            digits.append(code)
        if char not in "hw":
            previous = code
    return (letters[0].upper() + "".join(digits) + "000")[:4]
