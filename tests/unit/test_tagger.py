"""Unit tests for the core tagging algorithm (``extract_tags_from_text``).

This is the crown-jewel pure-logic path: it decodes a base64-pickled list of tag
descriptors and counts regex matches per ``.``-split line. The tag blob is built here
exactly the way qhld-engine feeds it in production (see
``qhld-data`` ``repositories/tags.py:compile_tag``): each descriptor carries a
case-insensitive **compiled** ``regex`` object under ``compiletag``, and the whole list
is ``pickle``d then base64-encoded.
"""

import codecs
import pickle

import regex
import pytest

from tipi_tasks import config
from tipi_tasks.tagger import extract_tags_from_text

pytestmark = pytest.mark.unit


def make_tag(topic, subtopic, tag, pattern, knowledgebase="politicas", public=True):
    """A single tag descriptor shaped like qhld-data's ``compile_tag`` output."""
    return {
        "topic": topic,
        "subtopic": subtopic,
        "tag": tag,
        "knowledgebase": knowledgebase,
        "public": public,
        "compiletag": regex.compile("(?i)" + pattern),
    }


def encode_tags(tags):
    """base64(pickle(tags)) — the exact transport qhld-engine uses for the task arg."""
    return codecs.encode(pickle.dumps(tags), "base64").decode()


def test_single_match_success_shape():
    blob = encode_tags([make_tag("Medio ambiente", "Clima", "Clima", "clima")])

    result = extract_tags_from_text("Hablamos mucho sobre el clima hoy", blob)

    assert result["status"] == "SUCCESS"
    assert result["result"]["topics"] == ["Medio ambiente"]
    tags = result["result"]["tags"]
    assert len(tags) == 1
    found = tags[0]
    assert found["tag"] == "Clima"
    assert found["times"] == 1
    # metadata is preserved, but the compiled regex is stripped from the output.
    assert found["knowledgebase"] == "politicas"
    assert found["public"] is True
    assert "compiletag" not in found


def test_counts_multiple_occurrences_in_a_line():
    blob = encode_tags([make_tag("Medio ambiente", "Clima", "Clima", "clima")])

    result = extract_tags_from_text("clima clima y mas clima", blob)

    assert result["result"]["tags"][0]["times"] == 3


def test_merges_same_tag_across_lines():
    """``__append_tag_to_founds`` sums counts for the same topic/subtopic/tag found on
    separate ``.``-split lines into a single entry."""
    blob = encode_tags([make_tag("Medio ambiente", "Clima", "Clima", "clima")])

    result = extract_tags_from_text("El clima importa. Hablamos del clima otra vez", blob)

    tags = result["result"]["tags"]
    assert len(tags) == 1
    assert tags[0]["times"] == 2


def test_topics_deduped_sorted_and_tags_sorted():
    blob = encode_tags([
        make_tag("Medio ambiente", "Clima", "Clima", "clima"),
        make_tag("Medio ambiente", "Agua", "Agua", "agua"),
        make_tag("Economia", "Empleo", "Empleo", "empleo"),
    ])

    result = extract_tags_from_text("clima, agua y empleo importan", blob)

    # topics: unique + sorted.
    assert result["result"]["topics"] == ["Economia", "Medio ambiente"]
    # tags: sorted by (topic, subtopic, tag).
    ordered = [(t["topic"], t["subtopic"], t["tag"]) for t in result["result"]["tags"]]
    assert ordered == [
        ("Economia", "Empleo", "Empleo"),
        ("Medio ambiente", "Agua", "Agua"),
        ("Medio ambiente", "Clima", "Clima"),
    ]


def test_excerpt_passthrough_when_short():
    blob = encode_tags([make_tag("Medio ambiente", "Clima", "Clima", "clima")])
    text = "Texto corto sobre el clima"

    result = extract_tags_from_text(text, blob)

    assert result["excerpt"] == text


def test_excerpt_truncated_when_long():
    blob = encode_tags([make_tag("Medio ambiente", "Clima", "Clima", "clima")])
    size = config.SCANNED_TEXT_EXCERPT_SIZE
    text = "clima " + "x" * (size + 100)

    result = extract_tags_from_text(text, blob)

    expected = text[: size - 3] + " [...]"
    assert result["excerpt"] == expected
    assert result["excerpt"].endswith(" [...]")


def test_skips_all_digit_text():
    """When the whole text is digits, every line is skipped — no tags, even if the
    pattern would otherwise match."""
    blob = encode_tags([make_tag("Numeros", "N", "N", "123")])

    result = extract_tags_from_text("123456", blob)

    assert result["result"]["tags"] == []
    assert result["result"]["topics"] == []


def test_skips_too_short_lines():
    blob = encode_tags([make_tag("Letras", "X", "X", "x")])

    result = extract_tags_from_text("x", blob)

    assert result["result"]["tags"] == []
