"""Shared pytest fixtures — PDF file loaders for all 5 sample documents."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path so bare imports like
# ``from models.page import ...`` work without installing the package.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Load .env file so ANTHROPIC_API_KEY is available for integration tests
_env_path = _PROJECT_ROOT / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def pdf_lt_finance() -> bytes:
    """LT Finance Limited 2019 — T3 Indian AS NBFC, 8 pages, all digital."""
    return (FIXTURES_DIR / "LT_Finance_Limited_2019.pdf").read_bytes()


@pytest.fixture(scope="session")
def pdf_aspect_capital() -> bytes:
    """Aspect Capital Limited 2023 — T5 UK Companies Act, digital."""
    return (FIXTURES_DIR / "Aspect_Capital_Limited_2023.pdf").read_bytes()


@pytest.fixture(scope="session")
def pdf_sun_hung_kai() -> bytes:
    """Sun Hung Kai & Co. Limited 2024 — T8 IFRS Asia, scanned/hybrid, 3.2 MB."""
    return (FIXTURES_DIR / "Sun_Hung_Kai___Co__Limited_AR_2024.pdf").read_bytes()


@pytest.fixture(scope="session")
def pdf_cash_america() -> bytes:
    """Cash America International 2007 — T1 US GAAP, digital."""
    return (FIXTURES_DIR / "Cash_America_International_2007.pdf").read_bytes()


@pytest.fixture(scope="session")
def pdf_tfg_llp() -> bytes:
    """TFG Asset Management UK LLP 2024 — T6 UK LLP, digital."""
    return (FIXTURES_DIR / "TFG_Asset_management_UK_LLP_2024.pdf").read_bytes()
