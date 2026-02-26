"""Text simplifier — reduce reading complexity toward a target grade level.

TextSimplifier uses the Flesch-Kincaid Grade Level formula to estimate the
current readability of a passage and applies heuristic transformations to
reduce complexity when it exceeds the target.

Flesch-Kincaid Grade Level formula
-----------------------------------
    FKGL = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59

Target grade levels map approximately to:
    Grade 5  ~ elementary reading
    Grade 8  ~ middle-school / general public
    Grade 12 ~ high-school / professional

Simplification strategies applied iteratively
----------------------------------------------
1. Split very long sentences at semicolons, colons, and conjunctions.
2. Replace common complex words with simpler synonyms.
3. Remove parenthetical asides that increase sentence length.
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Syllable estimation
# ---------------------------------------------------------------------------

_VOWEL_RUN: re.Pattern[str] = re.compile(r"[aeiouy]+", re.IGNORECASE)
_SILENT_E: re.Pattern[str] = re.compile(r"[^aeiouy]e$", re.IGNORECASE)
_SPLIT_SUFFIXES: re.Pattern[str] = re.compile(
    r"(?i)(tion|sion|cious|tious|ious|ious|eous)$"
)


def _count_syllables(word: str) -> int:
    """Estimate syllable count for a single word using heuristics."""
    word = word.lower().strip(".,!?;:\"'()")
    if not word:
        return 0
    # Count vowel runs as syllables.
    count = len(_VOWEL_RUN.findall(word))
    # Subtract silent trailing 'e' (but not 'le', 'me', 'he' etc.).
    if len(word) > 2 and _SILENT_E.search(word):
        count -= 1
    return max(count, 1)


def _count_syllables_in_text(text: str) -> int:
    words = re.findall(r"[a-zA-Z]+", text)
    return sum(_count_syllables(w) for w in words)


def _count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _count_sentences(text: str) -> int:
    sentences = re.split(r"[.!?]+", text)
    return max(len([s for s in sentences if s.strip()]), 1)


def flesch_kincaid_grade(text: str) -> float:
    """Compute the Flesch-Kincaid Grade Level for the given text.

    Parameters
    ----------
    text:
        Plain text (no HTML). Should contain at least one complete sentence.

    Returns
    -------
    float
        Estimated grade level. Values < 0 are clamped to 0.
    """
    word_count = _count_words(text)
    sentence_count = _count_sentences(text)
    syllable_count = _count_syllables_in_text(text)

    if word_count == 0:
        return 0.0

    asl = word_count / sentence_count  # average sentence length
    asw = syllable_count / word_count  # average syllables per word
    grade = 0.39 * asl + 11.8 * asw - 15.59
    return round(max(grade, 0.0), 2)


# ---------------------------------------------------------------------------
# Synonym map for common complex -> simple replacements
# ---------------------------------------------------------------------------

_SYNONYM_MAP: dict[str, str] = {
    "utilize": "use",
    "utilise": "use",
    "facilitate": "help",
    "demonstrate": "show",
    "ascertain": "find out",
    "endeavour": "try",
    "endeavor": "try",
    "commence": "start",
    "terminate": "end",
    "initiate": "start",
    "subsequently": "then",
    "approximately": "about",
    "sufficient": "enough",
    "additional": "more",
    "obtain": "get",
    "require": "need",
    "implement": "do",
    "leverage": "use",
    "methodology": "method",
    "functionality": "feature",
    "parameters": "settings",
    "configuration": "setup",
    "comprehend": "understand",
    "indicate": "show",
    "prioritise": "focus on",
    "prioritize": "focus on",
    "concerning": "about",
    "regarding": "about",
    "pertaining to": "about",
    "in order to": "to",
    "due to the fact that": "because",
    "at this point in time": "now",
    "in the event that": "if",
    "for the purpose of": "to",
    "notwithstanding": "despite",
    "nevertheless": "but",
    "furthermore": "also",
    "however": "but",
    "therefore": "so",
    "consequently": "so",
    "henceforth": "from now on",
}

# Build a compiled pattern for all synonyms (longest first to avoid partial replacements).
_sorted_complex_words = sorted(_SYNONYM_MAP.keys(), key=len, reverse=True)
_SYNONYM_PATTERN: re.Pattern[str] = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in _sorted_complex_words) + r")\b",
    re.IGNORECASE,
)


def _replace_synonyms(text: str) -> str:
    """Replace complex words with simpler alternatives."""

    def _replacer(match: re.Match[str]) -> str:  # type: ignore[type-arg]
        word = match.group(0)
        replacement = _SYNONYM_MAP.get(word.lower(), word)
        # Preserve leading capitalisation.
        if word[0].isupper():
            return replacement.capitalize()
        return replacement

    return _SYNONYM_PATTERN.sub(_replacer, text)


# ---------------------------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------------------------

_PARENTHETICAL: re.Pattern[str] = re.compile(r"\([^)]{10,}\)")
_LONG_SENTENCE_SPLIT: re.Pattern[str] = re.compile(
    r"(?<=[a-z]),?\s+(however|but|although|whereas|while|yet|and|or)\s+",
    re.IGNORECASE,
)


def _split_long_sentences(text: str, max_words: int = 25) -> str:
    """Break sentences that exceed max_words at conjunction boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result: list[str] = []
    for sentence in sentences:
        words_in_sentence = len(sentence.split())
        if words_in_sentence > max_words:
            # Try splitting at a conjunction.
            split_text = _LONG_SENTENCE_SPLIT.sub(". ", sentence, count=1)
            result.append(split_text)
        else:
            result.append(sentence)
    return " ".join(result)


def _remove_parentheticals(text: str) -> str:
    """Remove parenthetical asides that add length without core meaning."""
    return _PARENTHETICAL.sub("", text)


# ---------------------------------------------------------------------------
# Simplifier
# ---------------------------------------------------------------------------

_MAX_ITERATIONS: int = 5


class TextSimplifier:
    """Reduce text to a target Flesch-Kincaid grade level.

    Applies heuristic transformations iteratively until the target grade is
    reached or the maximum number of passes is exhausted. The output is always
    plain text (no HTML tags added).

    Example
    -------
    >>> simplifier = TextSimplifier()
    >>> grade = simplifier.grade_level("Utilize the provided configuration parameters.")
    >>> simplified = simplifier.simplify("Utilize the provided configuration parameters.", 8)
    >>> "use" in simplified.lower()
    True
    """

    def grade_level(self, text: str) -> float:
        """Return the Flesch-Kincaid Grade Level for the given text.

        Parameters
        ----------
        text:
            Plain text to assess.

        Returns
        -------
        float
            Estimated grade level (clamped to >= 0).
        """
        return flesch_kincaid_grade(text)

    def simplify(self, text: str, target_grade_level: float) -> str:
        """Simplify text toward the target Flesch-Kincaid grade level.

        Applies synonym replacement, parenthetical removal, and sentence
        splitting until the computed grade is at or below the target, or the
        maximum number of iterations is reached.

        Parameters
        ----------
        text:
            The input text to simplify. Should be plain text (no HTML).
        target_grade_level:
            The maximum desired Flesch-Kincaid Grade Level (e.g. 8.0 for
            general public readability).

        Returns
        -------
        str
            The simplified text. May be unchanged if already at or below target.

        Raises
        ------
        ValueError
            If ``target_grade_level`` is negative.
        """
        if target_grade_level < 0:
            raise ValueError(
                f"target_grade_level must be >= 0; got {target_grade_level!r}."
            )

        current = text
        for _ in range(_MAX_ITERATIONS):
            if flesch_kincaid_grade(current) <= target_grade_level:
                break
            current = _replace_synonyms(current)
            current = _remove_parentheticals(current)
            current = _split_long_sentences(current)

        # Normalise whitespace introduced by removals.
        current = re.sub(r" {2,}", " ", current).strip()
        return current

    def readability_summary(self, text: str) -> dict[str, float]:
        """Return a summary of readability metrics for the given text.

        Parameters
        ----------
        text:
            Plain text to analyse.

        Returns
        -------
        dict[str, float]
            Keys: ``grade_level``, ``word_count``, ``sentence_count``,
            ``avg_sentence_length``, ``avg_syllables_per_word``.
        """
        word_count = _count_words(text)
        sentence_count = _count_sentences(text)
        syllable_count = _count_syllables_in_text(text)

        avg_sentence_length = word_count / sentence_count if sentence_count else 0.0
        avg_syllables = syllable_count / word_count if word_count else 0.0

        return {
            "grade_level": flesch_kincaid_grade(text),
            "word_count": float(word_count),
            "sentence_count": float(sentence_count),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "avg_syllables_per_word": round(avg_syllables, 2),
        }
