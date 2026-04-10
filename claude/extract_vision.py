"""S5 — Vision Extractor (OCR path).

Extracts financial rows from rasterized (scanned) PDF pages
using Claude Vision.

Ported from: financial-spreadx/lib/claude/extract-vision.ts
"""

from __future__ import annotations

import base64
import json
import re

import anthropic

from config import CLAUDE_MODEL, VISION_EXTRACT_MAX_TOKENS


_VISION_PROMPT_TEMPLATE = """This is page {page_number} of a financial statement ({statement_type_display}, template: {template_type}).
Extract all financial line items as structured rows.

IMPORTANT layout guidance:
- This page may use a DUAL-COLUMN layout (e.g., assets on the left and liabilities
  on the right, or operating activities on the left and investing/financing on the right).
  Extract ALL items from EVERY column — do not stop after the first column.
- If the page has a WIDE TABLE with many columns, read each column header carefully
  and map values to the correct year/period.
- Read the ENTIRE page from top to bottom, left to right.
- Include items from supplemental disclosures or footnote sections if they contain
  financial data with numeric values.

Return JSON matching this schema exactly:
{{
  "rows": [
    {{
      "raw_label": "string (verbatim label from the image)",
      "raw_values": {{ "2024": 1234.56, "2023": null }},
      "section_path": ["string"],
      "indentation_level": 0,
      "is_subtotal": false,
      "note_ref": null
    }}
  ]
}}
Rules:
- raw_label must be the exact text from the image
- Negative values use negative numbers, not parentheses
- Values in parentheses like (1,234) should be -1234
- Return only JSON, no markdown or commentary
- If the page does not contain financial statement data, return {{"rows": []}}"""


def extract_statement_from_image(
    image_buffer: bytes,
    statement_type: str,
    template_type: str,
    page_number: int,
) -> list[dict]:
    """Extract financial rows from a rasterized PDF page image.

    Args:
        image_buffer:   PNG image bytes of the rasterized page.
        statement_type: income_statement | balance_sheet | cash_flow | equity_statement.
        template_type:  T1-T8 template classification.
        page_number:    Page number for context.

    Returns:
        List of dicts with keys: raw_label, raw_values, section_path,
        indentation_level, is_subtotal, note_ref.
    """
    b64 = base64.b64encode(image_buffer).decode("ascii")

    prompt = _VISION_PROMPT_TEMPLATE.format(
        page_number=page_number,
        statement_type_display=statement_type.replace("_", " "),
        template_type=template_type,
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=VISION_EXTRACT_MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = ""
    for block in response.content:
        if block.type == "text":
            raw = block.text
            break
    if not raw:
        raw = '{"rows": []}'

    clean = re.sub(r"```json|```", "", raw).strip()

    try:
        parsed = json.loads(clean)
        rows = parsed.get("rows", [])
        return [r for r in rows if r.get("raw_label", "").strip()]
    except (json.JSONDecodeError, AttributeError):
        return []
