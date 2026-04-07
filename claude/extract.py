"""S5 — Row Extractor (digital text path).

Extracts structured financial rows from page text using Claude.

Ported from: financial-spreadx/lib/claude/extract.ts
"""

from __future__ import annotations

import json
import re

import anthropic

from config import CLAUDE_MODEL, MAX_PAGE_TEXT_FOR_EXTRACT


def extract_four_digit_year(key: str) -> str:
    """Normalize a year string to a 4-digit year.

    Examples:
        "2019"          -> "2019"
        "2018-19"       -> "2019"
        "FY 2018-19"    -> "2019"
        "Year ended 2023" -> "2023"
        "no year here"  -> "no year here"

    Ported from extract.ts extractFourDigitYear() lines 83-94.
    """
    # Fiscal year format: "2018-19" -> "2019"
    fiscal_match = re.search(r"(\d{4})-(\d{2})$", key.strip())
    if fiscal_match:
        century = (int(fiscal_match.group(1)) // 100) * 100
        return str(century + int(fiscal_match.group(2)))

    # Extract last 4-digit year found in the string
    all_years = re.findall(r"\d{4}", key)
    if all_years:
        return all_years[-1]

    return key


# Prompt ported verbatim from extract.ts lines 52-68
_EXTRACT_PROMPT_TEMPLATE = """You are a financial data extraction engine. Extract ALL financial line items from this {statement_type_display} page.

Template type: {template_type}
Statement type: {statement_type}

Rules:
1. raw_label must be the EXACT text from the document — do not paraphrase or normalize
2. Extract ALL year columns present. For each row, add one year_values entry per column. Use exactly 4 digits for the year field (e.g. "2019", "2018"). For fiscal years like "2018-19" use the ending year "2019".
3. Negative values should use negative numbers, not parentheses
4. Values in parentheses like (1,234) should be converted to -1234
5. Set is_subtotal=true for total/subtotal rows (e.g., "Total Revenue", "Net Income")
6. Set note_ref to the note reference if present (e.g., "Note 12", "Note 3.1")
7. section_path should reflect the hierarchy (e.g., ["Revenue", "Interest Income"])
8. indentation_level: 0 for main items, 1 for sub-items, 2+ for deeper nesting

Return ONLY valid JSON matching this schema:
{{
  "rows": [
    {{
      "raw_label": "string",
      "year_values": [{{"year": "2024", "value": 1234.56}}, {{"year": "2023", "value": null}}],
      "section_path": ["string"],
      "indentation_level": 0,
      "is_subtotal": false,
      "note_ref": null
    }}
  ]
}}

Page text:
{page_text}"""


def extract_statement(
    page_text: str,
    statement_type: str,
    template_type: str,
) -> list[dict]:
    """Extract financial rows from a page of text via Claude.

    Args:
        page_text:      Full text content of the page(s).
        statement_type: income_statement | balance_sheet | cash_flow | equity_statement.
        template_type:  T1-T8 template classification.

    Returns:
        List of dicts with keys: raw_label, raw_values, section_path,
        indentation_level, is_subtotal, note_ref.
    """
    prompt = _EXTRACT_PROMPT_TEMPLATE.format(
        statement_type_display=statement_type.replace("_", " "),
        statement_type=statement_type,
        template_type=template_type,
        page_text=page_text[:MAX_PAGE_TEXT_FOR_EXTRACT],
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system="You are a financial data extraction engine. You MUST return ONLY valid JSON with a top-level 'rows' array. No other keys at the top level. No markdown fences. No commentary.",
        messages=[{"role": "user", "content": prompt}],
    )

    raw = ""
    for block in response.content:
        if block.type == "text":
            raw = block.text
            break

    clean = re.sub(r"```json|```", "", raw).strip()

    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        return []

    rows = parsed.get("rows", [])
    result: list[dict] = []

    for row in rows:
        raw_label = row.get("raw_label", "").strip()
        if not raw_label:
            continue

        # Convert year_values array to raw_values dict
        year_values = row.get("year_values", [])
        raw_values: dict[str, float | None] = {}
        for yv in year_values:
            year_key = extract_four_digit_year(str(yv.get("year", "")))
            raw_values[year_key] = yv.get("value")

        result.append(
            {
                "raw_label": raw_label,
                "raw_values": raw_values,
                "section_path": row.get("section_path", []),
                "indentation_level": row.get("indentation_level", 0),
                "is_subtotal": row.get("is_subtotal", False),
                "note_ref": row.get("note_ref"),
            }
        )

    return result
