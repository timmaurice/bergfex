"""Tests for the phrases bergfex prints in place of a reading.

Despite living under a key called "values", this map is not a translation: each
language lists the wording bergfex uses for "no report" and maps it onto Home
Assistant's ``unknown``, which is what the card greys out. Left unmapped, the
phrase reaches the card as if it were a snow condition.

Fourteen of the eighteen languages listed a phrase bergfex does not serve. The
entries were re-read off live pages on 2026-09-12 by taking the German page of
the same resort and field as the reference.
"""

import pytest

from custom_components.bergfex.const import KEYWORDS, SUPPORTED_LANGUAGES
from custom_components.bergfex.parser import _translate_value

# What each language's pages actually printed where the German one said
# "keine Meldung". "at" is absent: _translate_value returns early for it.
LIVE_PHRASES = {
    "en": "no information",
    "fr": "pas de nouvelle",
    "it": "nessuna comunicazione",
    "es": "no hay información",
    "nl": "geen melding",
    "se": "inget meddelande",
    "no": "ingen melding",
    "dk": "ingen besked",
    "fi": "ei ilmoitusta",
    "hu": "nincs üzenet",
    "cz": "žádné hlášení",
    "sk": "žiadne hlásenie",
    "pl": "brak komunikatu",
    "hr": "nema poruke",
    "si": "brez sporočila",
    "ru": "нет сообщений",
    "ro": "fără comunicare",
}


@pytest.mark.parametrize("lang,phrase", sorted(LIVE_PHRASES.items()))
def test_the_live_no_report_phrase_becomes_unknown(lang, phrase):
    assert _translate_value(phrase, lang) == "unknown"


def test_every_language_but_german_is_covered():
    """A language added without a phrase would print bergfex's wording verbatim."""
    uncovered = [
        lang
        for lang in SUPPORTED_LANGUAGES
        if lang != "at" and not KEYWORDS[lang].get("values")
    ]

    assert not uncovered


def test_a_longer_phrase_is_not_eaten_by_a_shorter_one():
    """English serves both "no info" and "no information".

    Replacing the shorter first leaves "unknownrmation" behind, so the map is
    applied longest first rather than in whatever order const.py happens to
    list it.
    """
    assert _translate_value("no information", "en") == "unknown"
    assert _translate_value("no info", "en") == "unknown"


def test_a_real_reading_is_left_alone():
    assert _translate_value("nincs üzenet ma", "hu") == "unknown ma"
    assert _translate_value("régi hó", "hu") == "régi hó"


def test_german_is_returned_untouched():
    assert _translate_value("keine Meldung", "at") == "keine Meldung"
