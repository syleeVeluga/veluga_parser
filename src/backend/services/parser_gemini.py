"""
Gemini Flash VL adapter — produces the same v2 result dict schema as parse_pdf().
Uses pypdfium2 to render each PDF page to a base64 PNG, then submits each page
to Google Gemini Flash vision API with a structured prompt.

Optional dependency: google-generativeai>=0.8.0
Requires GEMINI_API_KEY environment variable (set via /api/settings/api-keys).

NOTE: Full implementation added in Sprint 2.
This stub ensures import dispatch in upload.py does not crash the app at startup.
"""
from pathlib import Path


def parse_pdf_gemini(file_path: Path, image_dir: Path) -> dict:
    """
    Parse a PDF using Google Gemini Flash Vision API.
    Requires GEMINI_API_KEY to be configured via /api/settings/api-keys.
    """
    try:
        import google.generativeai  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "google-generativeai is not installed. Install it with:\n"
            "  pip install google-generativeai>=0.8.0\n"
            "Error: " + str(e)
        ) from e

    from src.backend.config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Set it via the Settings page or POST /api/settings/api-keys."
        )

    # Full implementation added in Sprint 2
    raise NotImplementedError(
        "Gemini parser full implementation is available in Sprint 2."
    )
