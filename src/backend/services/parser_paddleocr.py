"""
PaddleOCR 3 adapter — produces the same v2 result dict schema as parse_pdf().
Uses pypdfium2 (already a docling transitive dependency) to render each PDF
page to a PIL image, then passes it to PaddleOCR for text extraction.

Optional dependency: paddleocr>=3.0.0
If not installed, raises RuntimeError with install hint at call time.
"""
import logging
import statistics
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _detect_language(text: str) -> str | None:
    """Shared language detection — mirrors parser.py heuristic."""
    from src.backend.services.parser import _detect_language as _dl
    return _dl(text)


def _make_element_id(counter: int) -> str:
    return f"elem_{counter:04d}"


def _render_pages(file_path: Path) -> list[Any]:
    """Render all PDF pages to PIL images using pypdfium2."""
    try:
        import pypdfium2 as pdfium
    except ImportError as e:
        raise RuntimeError(
            "pypdfium2 is required for PaddleOCR rendering. "
            "It should be installed as a docling dependency.\nError: " + str(e)
        ) from e

    pdf = pdfium.PdfDocument(str(file_path))
    images = []
    for page_idx in range(len(pdf)):
        page = pdf[page_idx]
        bitmap = page.render(scale=2.0)
        pil_img = bitmap.to_pil()
        images.append(pil_img)
    pdf.close()
    return images


def _ocr_page(ocr_engine: Any, pil_image: Any, page_no: int) -> list[dict]:
    """Run PaddleOCR on a single PIL image and return raw blocks."""
    import numpy as np

    img_array = np.array(pil_image)
    try:
        result = ocr_engine.ocr(img_array, cls=True)
    except Exception as exc:
        logger.warning(f"PaddleOCR failed on page {page_no}: {exc}")
        return []

    blocks: list[dict] = []
    if not result or not result[0]:
        return blocks

    for line in result[0]:
        if not line or len(line) < 2:
            continue
        bbox_points, (text, confidence) = line
        if not text or not text.strip():
            continue
        # bbox_points: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] — convert to [l,t,r,b]
        xs = [pt[0] for pt in bbox_points]
        ys = [pt[1] for pt in bbox_points]
        blocks.append({
            "text": text.strip(),
            "confidence": float(confidence),
            "bbox": [min(xs), min(ys), max(xs), max(ys)],
        })
    return blocks


def _is_title_block(block: dict, all_heights: list[float]) -> bool:
    """Heuristic: block is a title if its height is significantly above median."""
    if not all_heights:
        return False
    h = block["bbox"][3] - block["bbox"][1]
    median_h = statistics.median(all_heights)
    return h > median_h * 1.5


def parse_pdf_paddleocr(file_path: Path, image_dir: Path) -> dict:
    """
    Parse a PDF using PaddleOCR 3 and return a v2 schema result dict.

    Produces text-level elements (no semantic labelling beyond title heuristic).
    page_markdowns is plain concatenated text per page.
    """
    try:
        from paddleocr import PaddleOCR
    except ImportError as e:
        raise RuntimeError(
            "PaddleOCR is not installed. Install it with:\n"
            "  pip install paddleocr>=3.0.0\n"
            "Error: " + str(e)
        ) from e

    image_dir.mkdir(parents=True, exist_ok=True)

    # Initialize PaddleOCR — use multilingual model supporting CJK + English
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    except Exception:
        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

    logger.info(f"Starting PaddleOCR conversion for: {file_path}")
    page_images = _render_pages(file_path)
    total_pages = len(page_images)

    elements: list[dict] = []
    all_languages: set[str] = set()
    page_markdowns: dict[str, str] = {}
    doc_title: str | None = None
    elem_counter = 0

    for page_idx, pil_image in enumerate(page_images):
        page_no = page_idx + 1
        blocks = _ocr_page(ocr, pil_image, page_no)

        # Compute all block heights for title heuristic
        all_heights = [b["bbox"][3] - b["bbox"][1] for b in blocks]

        page_texts: list[str] = []

        for block in blocks:
            text = block["text"]
            lang = _detect_language(text)
            if lang:
                all_languages.add(lang)

            elem_type = "text"
            if page_no == 1 and doc_title is None and _is_title_block(block, all_heights):
                elem_type = "title"
                doc_title = text

            bbox = block["bbox"]
            elem: dict = {
                "element_id": _make_element_id(elem_counter),
                "type": elem_type,
                "content": text,
                "page_number": page_no,
                "reading_order": elem_counter,
                "bbox": bbox,
            }
            if lang:
                elem["language"] = lang

            elements.append(elem)
            page_texts.append(text)
            elem_counter += 1

        page_markdowns[str(page_no)] = "\n".join(page_texts)

    languages = sorted(all_languages) if all_languages else ["en"]

    pages_data = [
        {
            "page_number": p,
            "elements": [e for e in elements if e["page_number"] == p],
        }
        for p in range(1, total_pages + 1)
    ]

    return {
        "schema_version": "2.0",
        "metadata": {
            "total_pages": total_pages,
            "languages": languages,
            "has_tables": False,
            "has_images": False,
            "has_equations": False,
            "has_code": False,
            "title": doc_title,
            "authors": [],
            "page_dimensions": [],
        },
        "toc": [],
        "elements": elements,
        "pages": pages_data,
        "chunks": {},
        "page_markdowns": page_markdowns,
    }
