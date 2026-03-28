"""
Parser service wrapping docling DocumentConverter for multi-lingual PDF parsing.
Supports Korean, English, Japanese, and Chinese via EasyOCR pipeline.
"""
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _detect_language(text: str) -> str | None:
    """Heuristic language detection based on Unicode ranges."""
    if not text or not text.strip():
        return None
    korean = sum(1 for c in text if "\uAC00" <= c <= "\uD7A3" or "\u1100" <= c <= "\u11FF")
    chinese = sum(1 for c in text if "\u4E00" <= c <= "\u9FFF")
    japanese = sum(1 for c in text if "\u3040" <= c <= "\u30FF")
    total = len(text.strip())
    if total == 0:
        return None
    if korean / total > 0.1:
        return "ko"
    if japanese / total > 0.1:
        return "ja"
    if chinese / total > 0.1:
        return "zh"
    return "en"


def _element_to_dict(element: Any, element_type: str) -> dict:
    """Convert a docling element to the internal schema dict."""
    result: dict = {"type": element_type}

    # Extract text content
    if hasattr(element, "text") and element.text:
        result["content"] = element.text
        lang = _detect_language(element.text)
        if lang:
            result["language"] = lang
    elif hasattr(element, "export_to_markdown"):
        try:
            md = element.export_to_markdown()
            result["content"] = md
        except Exception:
            result["content"] = str(element)
    else:
        result["content"] = ""

    # Extract bounding box if available
    if hasattr(element, "prov") and element.prov:
        try:
            prov = element.prov[0] if isinstance(element.prov, list) else element.prov
            if hasattr(prov, "bbox") and prov.bbox:
                bbox = prov.bbox
                result["bbox"] = [
                    float(getattr(bbox, "l", 0)),
                    float(getattr(bbox, "t", 0)),
                    float(getattr(bbox, "r", 0)),
                    float(getattr(bbox, "b", 0)),
                ]
        except Exception:
            pass

    return result


def parse_pdf(file_path: Path, image_dir: Path) -> dict:
    """
    Parse a PDF file using docling and return structured result dict.

    Returns:
        {
            "pages": [{"page_number": int, "elements": [...]}],
            "metadata": {"total_pages": int, "languages": [...], "has_tables": bool, "has_images": bool}
        }
    """
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    except ImportError as e:
        raise RuntimeError(
            f"docling is not installed. Run: pip install docling\nError: {e}"
        ) from e

    image_dir.mkdir(parents=True, exist_ok=True)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend,
            )
        }
    )

    logger.info(f"Starting docling conversion for: {file_path}")
    conv_result = converter.convert(str(file_path))
    doc = conv_result.document

    pages_data: list[dict] = []
    all_languages: set[str] = set()
    has_tables = False
    has_images = False

    # Group elements by page
    page_elements: dict[int, list[dict]] = {}

    # Process text elements
    for item, level in doc.iterate_items():
        from docling.datamodel.document import TextItem, TableItem, PictureItem
        page_num = 1
        if hasattr(item, "prov") and item.prov:
            try:
                prov = item.prov[0] if isinstance(item.prov, list) else item.prov
                page_num = getattr(prov, "page_no", 1)
            except Exception:
                page_num = 1

        if page_num not in page_elements:
            page_elements[page_num] = []

        if isinstance(item, TableItem):
            has_tables = True
            elem = {"type": "table", "rows": [], "content": ""}
            try:
                df = item.export_to_dataframe()
                elem["rows"] = df.values.tolist()
                elem["content"] = item.export_to_markdown()
            except Exception:
                elem["content"] = str(item)
            if hasattr(item, "prov") and item.prov:
                try:
                    prov = item.prov[0] if isinstance(item.prov, list) else item.prov
                    if hasattr(prov, "bbox") and prov.bbox:
                        b = prov.bbox
                        elem["bbox"] = [float(getattr(b, "l", 0)), float(getattr(b, "t", 0)),
                                        float(getattr(b, "r", 0)), float(getattr(b, "b", 0))]
                except Exception:
                    pass
            page_elements[page_num].append(elem)

        elif isinstance(item, PictureItem):
            has_images = True
            img_filename = f"page{page_num}_img{len([e for e in page_elements.get(page_num, []) if e['type'] == 'image'])}.png"
            img_path = image_dir / img_filename
            elem = {"type": "image", "path": str(img_path), "content": ""}
            try:
                img = item.get_image(doc)
                if img:
                    img.save(str(img_path))
            except Exception as ex:
                logger.warning(f"Could not save image: {ex}")
            if hasattr(item, "prov") and item.prov:
                try:
                    prov = item.prov[0] if isinstance(item.prov, list) else item.prov
                    if hasattr(prov, "bbox") and prov.bbox:
                        b = prov.bbox
                        elem["bbox"] = [float(getattr(b, "l", 0)), float(getattr(b, "t", 0)),
                                        float(getattr(b, "r", 0)), float(getattr(b, "b", 0))]
                except Exception:
                    pass
            page_elements[page_num].append(elem)

        elif isinstance(item, TextItem):
            text = item.text or ""
            lang = _detect_language(text)
            if lang:
                all_languages.add(lang)
            elem: dict = {"type": "text", "content": text}
            if lang:
                elem["language"] = lang
            if hasattr(item, "prov") and item.prov:
                try:
                    prov = item.prov[0] if isinstance(item.prov, list) else item.prov
                    if hasattr(prov, "bbox") and prov.bbox:
                        b = prov.bbox
                        elem["bbox"] = [float(getattr(b, "l", 0)), float(getattr(b, "t", 0)),
                                        float(getattr(b, "r", 0)), float(getattr(b, "b", 0))]
                except Exception:
                    pass
            page_elements[page_num].append(elem)

    # Build pages list
    total_pages = max(page_elements.keys(), default=1)
    for page_num in range(1, total_pages + 1):
        pages_data.append({
            "page_number": page_num,
            "elements": page_elements.get(page_num, []),
        })

    languages = sorted(all_languages) if all_languages else ["en"]

    return {
        "pages": pages_data,
        "metadata": {
            "total_pages": total_pages,
            "languages": languages,
            "has_tables": has_tables,
            "has_images": has_images,
        },
    }
