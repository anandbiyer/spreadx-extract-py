"""PDF page rasterizer — converts pages to PNG images.

Uses PyMuPDF's built-in pixmap rendering, replacing the
pdfjs-dist + @napi-rs/canvas combo from the TypeScript version.

Ported from: financial-spreadx/lib/pdf/page-rasterizer.ts
"""

from __future__ import annotations

import fitz  # PyMuPDF


def rasterize_page(
    pdf_bytes: bytes, page_number: int, scale: float = 2.0
) -> bytes:
    """Rasterize a single PDF page to a PNG buffer.

    Args:
        pdf_bytes:   The full PDF file as bytes.
        page_number: 1-based page number.
        scale:       Render scale (2.0 = 2x default resolution).

    Returns:
        PNG image bytes (~150-300 KB per page at 2x scale).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[page_number - 1]  # fitz uses 0-based index
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")
    finally:
        doc.close()


def rasterize_pages(
    pdf_bytes: bytes, page_numbers: list[int], scale: float = 2.0
) -> dict[int, bytes]:
    """Rasterize multiple PDF pages to PNG buffers.

    Args:
        pdf_bytes:    The full PDF file as bytes.
        page_numbers: List of 1-based page numbers.
        scale:        Render scale.

    Returns:
        Dict mapping page number to PNG bytes.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result: dict[int, bytes] = {}
    try:
        for page_num in page_numbers:
            page = doc[page_num - 1]
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            result[page_num] = pix.tobytes("png")
    finally:
        doc.close()
    return result
