"""Shared configuration constants for the extraction pipeline."""

# Claude AI model used for all API calls
CLAUDE_MODEL = "claude-sonnet-4-6"

# Page classification thresholds (from page-classifier.ts)
DIGITAL_WORD_THRESHOLD = 80
DIGITAL_ASCII_THRESHOLD = 0.90
HYBRID_WORD_THRESHOLD = 20

# Page filter continuation window
CONTINUATION_MAX_WINDOW = 8

# Text windows
PAGE_TEXT_WINDOW = 2000         # Chars scanned for statement-type signals
MAX_PAGE_TEXT_FOR_EXTRACT = 6000  # Truncate single-page text sent to Claude
MAX_CONCAT_TEXT_FOR_EXTRACT = 12000  # Truncate multi-page concatenated text
MAX_NOTE_TEXT = 4000            # Truncate note text sent to Claude

# Extraction max tokens
TEXT_EXTRACT_MAX_TOKENS = 8192     # Claude output ceiling for text extraction
VISION_EXTRACT_MAX_TOKENS = 8192   # Claude output ceiling for vision extraction

# Rasterization
DEFAULT_DPI_SCALE = 2.0
SCANNED_DPI_SCALE = 1.5        # Lower DPI for classification (speed)
