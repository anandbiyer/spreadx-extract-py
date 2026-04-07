"""Unit tests for Claude extraction modules with mocked API calls.

No ANTHROPIC_API_KEY needed — all Claude calls are mocked.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from claude.extract import extract_statement
from claude.extract_vision import extract_statement_from_image
from claude.extract_notes import extract_note


def _mock_response(text: str):
    """Build a mock Anthropic response with a single text block."""
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(content=[block])


# ── extract_statement tests ──


@patch("claude.extract.anthropic.Anthropic")
def test_extract_statement_parses_rows(mock_cls):
    """Valid 3-row JSON -> returns 3 dicts with correct fields."""
    mock_cls.return_value.messages.create.return_value = _mock_response(
        '{"rows": ['
        '{"raw_label": "Revenue", "year_values": [{"year": "2024", "value": 100}], '
        '"section_path": ["Revenue"], "indentation_level": 0, "is_subtotal": false, "note_ref": null},'
        '{"raw_label": "Cost of Sales", "year_values": [{"year": "2024", "value": -50}], '
        '"section_path": ["Expenses"], "indentation_level": 1, "is_subtotal": false, "note_ref": "Note 5"},'
        '{"raw_label": "Net Income", "year_values": [{"year": "2024", "value": 50}], '
        '"section_path": [], "indentation_level": 0, "is_subtotal": true, "note_ref": null}'
        "]}"
    )

    rows = extract_statement("some text", "income_statement", "T1")
    assert len(rows) == 3
    assert rows[0]["raw_label"] == "Revenue"
    assert rows[0]["raw_values"]["2024"] == 100
    assert rows[1]["note_ref"] == "Note 5"
    assert rows[2]["is_subtotal"] is True


@patch("claude.extract.anthropic.Anthropic")
def test_extract_statement_year_conversion(mock_cls):
    """Fiscal year '2018-19' in year_values -> raw_values key '2019'."""
    mock_cls.return_value.messages.create.return_value = _mock_response(
        '{"rows": [{"raw_label": "Total", "year_values": [{"year": "2018-19", "value": 999}], '
        '"section_path": [], "indentation_level": 0, "is_subtotal": true, "note_ref": null}]}'
    )

    rows = extract_statement("text", "income_statement", "T3")
    assert "2019" in rows[0]["raw_values"]
    assert rows[0]["raw_values"]["2019"] == 999


# ── extract_statement_from_image tests ──


@patch("claude.extract_vision.anthropic.Anthropic")
def test_extract_vision_strips_fences(mock_cls):
    """Response wrapped in ```json ... ``` -> parses correctly."""
    mock_cls.return_value.messages.create.return_value = _mock_response(
        '```json\n{"rows": [{"raw_label": "Assets", "raw_values": {"2024": 500}, '
        '"section_path": [], "indentation_level": 0, "is_subtotal": false, "note_ref": null}]}\n```'
    )

    rows = extract_statement_from_image(b"\x89PNG fake", "balance_sheet", "T8", 1)
    assert len(rows) == 1
    assert rows[0]["raw_label"] == "Assets"


@patch("claude.extract_vision.anthropic.Anthropic")
def test_extract_vision_fallback_empty(mock_cls):
    """Invalid JSON from Claude -> returns empty list."""
    mock_cls.return_value.messages.create.return_value = _mock_response(
        "I cannot extract data from this image."
    )

    rows = extract_statement_from_image(b"\x89PNG fake", "balance_sheet", "T8", 1)
    assert rows == []


# ── extract_note tests ──


@patch("claude.extract_notes.anthropic.Anthropic")
def test_extract_note_fallback(mock_cls):
    """Unparseable Claude response -> returns fallback NoteExtraction."""
    mock_cls.return_value.messages.create.side_effect = Exception("API error")

    result = extract_note("Note 5: Loans and Advances\nSome detail...", 5, "T3")
    assert result.note_number == 5
    assert result.note_title == "Note 5: Loans and Advances"
    assert result.sub_tables == []
    assert len(result.summary) > 0
