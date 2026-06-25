"""Unit tests for ``make_sentence`` — the human-readable rendering of a saved search
that goes into alert/validation emails. Pure string formatting, no infrastructure.
"""

import json

import pytest

from tipi_tasks.sentence import make_sentence

pytestmark = pytest.mark.unit


def sentence_for(search_dict):
    return make_sentence(json.dumps(search_dict))


def test_topic_only():
    assert sentence_for({"topic": "Medio ambiente"}) == " sobre Medio ambiente."


def test_nonempty_subtopics_replaces_topic():
    result = sentence_for({"topic": "Medio ambiente", "subtopics": ["Clima"]})
    assert result == " sobre Clima."
    assert "Medio ambiente" not in result


def test_empty_subtopics_keeps_topic():
    result = sentence_for({"topic": "Medio ambiente", "subtopics": []})
    assert result == " sobre Medio ambiente."


def test_knowledgebase_and_ignoretagless_are_skipped():
    result = sentence_for(
        {"topic": "Medio ambiente", "knowledgebase": "politicas", "ignoretagless": True}
    )
    assert result == " sobre Medio ambiente."


def test_startdate_is_reformatted():
    assert sentence_for({"startdate": "2024-01-15"}) == " desde 15/01/2024."


def test_deputy_name_is_reordered():
    assert sentence_for({"deputy": "Perez, Juan"}) == " firmadas por Juan Perez."


def test_text_field_is_quoted():
    assert sentence_for({"text": "clima"}) == ' que contengan "clima".'


def test_multiple_fields_no_trailing_comma():
    result = sentence_for({"topic": "Medio ambiente", "author": "PSOE"})
    assert result == " sobre Medio ambiente, de PSOE."
    assert not result.rstrip(".").endswith(",")


def test_list_value_joins_last_item_with_y():
    # A multi-value field should read "A, B y C" (Spanish list conjunction), not "A, B, C".
    result = sentence_for({"tags": ["Clima", "Agua", "Empleo"]})
    assert "relacionadas con Clima, Agua y Empleo" in result
