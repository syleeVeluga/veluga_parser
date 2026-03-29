"""
Gemini Flash VL adapter — produces the same v2 result dict schema as parse_pdf().

Renders each PDF page to a base64-encoded PNG via pypdfium2 and submits it to
Google Gemini Flash vision API with a structured prompt. The returned Markdown
per page is parsed into elements using a lightweight converter.

Optional dependency: google-generativeai>=0.8.0
Requires GEMINI_API_KEY to be configured via /api/settings/api-keys or .env.
"""
import base64
import io
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_MD_FENCE_RE = re.compile(r"^```.*?```", re.DOTALL | re.MULTILINE)
_TABLE_ROW_RE = re.compile(r"^\|.+\|")
_TABLE_SEP_RE = re.compile(r"^\|[-| :]+\|")


def _render_pages_base64(file_path: Path) -> list[tuple[str, int, int]]:
    """Render all PDF pages to base64 PNG strings using pypdfium2.

    Returns list of (b64_str, width_px, height_px).
    """
    try:
        import pypdfium2 as pdfium
    except ImportError as e:
        raise RuntimeError(
            "pypdfium2 is required for Gemini page rendering. "
            "It should be installed as a docling dependency.\nError: " + str(e)
        ) from e

    pdf = pdfium.PdfDocument(str(file_path))
    results = []
    for page_idx in range(len(pdf)):
        page = pdf[page_idx]
        bitmap = page.render(scale=2.0)
        pil_img = bitmap.to_pil()
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        results.append((b64, pil_img.width, pil_img.height))
    pdf.close()
    return results


def _markdown_to_elements(markdown: str, page_no: int, start_counter: int) -> list[dict]:
    """Convert Gemini-returned Markdown text to v2 element dicts."""
    from src.backend.services.parser import _detect_language

    elements: list[dict] = []
    counter = start_counter
    lines = markdown.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Fenced code block
        if stripped.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            content = "\n".join(code_lines).strip()
            if content:
                elements.append({
                    "element_id": f"elem_{counter:04d}",
                    "type": "code",
                    "content": content,
                    "page_number": page_no,
                    "reading_order": counter,
                })
                counter += 1
            i += 1
            continue

        # ATX headings
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            elem_type = "title" if level == 1 else "section_header"
            lang = _detect_language(text)
            elem: dict = {
                "element_id": f"elem_{counter:04d}",
                "type": elem_type,
                "content": text,
                "page_number": page_no,
                "reading_order": counter,
                "hierarchy_level": level - 1,
            }
            if lang:
                elem["language"] = lang
            elements.append(elem)
            counter += 1
            i += 1
            continue

        # Markdown table (collect consecutive rows)
        if _TABLE_ROW_RE.match(stripped):
            table_lines = []
            while i < len(lines) and _TABLE_ROW_RE.match(lines[i].strip()):
                if not _TABLE_SEP_RE.match(lines[i].strip()):
                    table_lines.append(lines[i])
                i += 1
            md_table = "\n".join(table_lines).strip()
            if md_table:
                elements.append({
                    "element_id": f"elem_{counter:04d}",
                    "type": "table",
                    "content": md_table,
                    "markdown_table": md_table,
                    "page_number": page_no,
                    "reading_order": counter,
                })
                counter += 1
            continue

        # Non-empty paragraph
        if stripped:
            # Check for list item
            list_match = re.match(r"^[-*+]\s+(.+)$|^(\d+)\.\s+(.+)$", stripped)
            if list_match:
                text = list_match.group(1) or list_match.group(3)
                elem_type = "list_item"
            else:
                text = stripped
                elem_type = "text"

            lang = _detect_language(text)
            elem = {
                "element_id": f"elem_{counter:04d}",
                "type": elem_type,
                "content": text,
                "page_number": page_no,
                "reading_order": counter,
            }
            if lang:
                elem["language"] = lang
            elements.append(elem)
            counter += 1

        i += 1

    return elements


_GEMINI_PROMPT = (
    "Extract all text from this PDF page as clean Markdown. "
    "Preserve document structure: use # for page titles, ## for section headers, "
    "### for sub-headers, | for tables, ``` for code blocks, and - for bullet lists. "
    "Output only the Markdown, no preamble or explanation."
)


def parse_pdf_gemini(file_path: Path, image_dir: Path) -> dict:
    """
    Parse a PDF using Google Gemini Flash Vision API.
    Returns a v2 schema result dict.

    Each page is rendered to PNG and submitted sequentially to avoid rate limits.
    """
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise RuntimeError(
            "google-generativeai is not installed. Install it with:\n"
            "  pip install google-generativeai>=0.8.0\n"
            "Error: " + str(e)
        ) from e

    import src.backend.config as config
    api_key = config.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Set it via the Settings page or POST /api/settings/api-keys."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    image_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Gemini conversion for: {file_path}")
    page_data = _render_pages_base64(file_path)
    total_pages = len(page_data)

    elements: list[dict] = []
    all_languages: set[str] = set()
    page_markdowns: dict[str, str] = {}
    doc_title: str | None = None
    elem_counter = 0

    for page_idx, (b64_str, _w, _h) in enumerate(page_data):
        page_no = page_idx + 1
        logger.info(f"Gemini processing page {page_no}/{total_pages}")

        try:
            image_part = {"mime_type": "image/png", "data": b64_str}
            response = model.generate_content([_GEMINI_PROMPT, image_part])
            markdown = response.text or ""
        except Exception as exc:
            logger.warning(f"Gemini API failed on page {page_no}: {exc}")
            markdown = ""

        page_markdowns[str(page_no)] = markdown

        page_elements = _markdown_to_elements(markdown, page_no, elem_counter)
        for elem in page_elements:
            if elem.get("language"):
                all_languages.add(elem["language"])
            if doc_title is None and elem["type"] == "title":
                doc_title = elem["content"]
        elements.extend(page_elements)
        elem_counter += len(page_elements)

        # Rate limiting: 0.5s between pages to avoid 429
        if page_idx < total_pages - 1:
            time.sleep(0.5)

    languages = sorted(all_languages) if all_languages else ["en"]

    pages_data = [
        {
            "page_number": p,
            "elements": [e for e in elements if e["page_number"] == p],
        }
        for p in range(1, total_pages + 1)
    ]

    has_tables = any(e["type"] == "table" for e in elements)
    has_code = any(e["type"] == "code" for e in elements)

    return {
        "schema_version": "2.0",
        "metadata": {
            "total_pages": total_pages,
            "languages": languages,
            "has_tables": has_tables,
            "has_images": False,
            "has_equations": False,
            "has_code": has_code,
            "title": doc_title,
            "authors": [],
            "page_dimensions": [],
        },
        "toc": [
            {
                "level": e.get("hierarchy_level", 0),
                "text": e["content"],
                "page_number": e["page_number"],
                "element_id": e["element_id"],
            }
            for e in elements
            if e["type"] in ("title", "section_header")
        ],
        "elements": elements,
        "pages": pages_data,
        "chunks": {},
        "page_markdowns": page_markdowns,
    }
