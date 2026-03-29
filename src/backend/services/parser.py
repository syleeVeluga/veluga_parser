"""
Parser service wrapping docling DocumentConverter for multi-lingual PDF parsing.
Supports Korean, English, Japanese, and Chinese via EasyOCR pipeline.
Produces v2 schema with rich element types for Advanced RAG chunking.
"""
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Mapping from DocItemLabel.name to element type string
LABEL_TYPE_MAP: dict[str, str] = {
    "TITLE": "title",
    "SECTION_HEADER": "section_header",
    "TEXT": "text",
    "TABLE": "table",
    "PICTURE": "image",
    "FIGURE": "figure",
    "LIST": "list",
    "LIST_ITEM": "list_item",
    "CAPTION": "caption",
    "FOOTNOTE": "footnote",
    "FORMULA": "formula",
    "PAGE_HEADER": "page_header",
    "PAGE_FOOTER": "page_footer",
    "CODE": "code",
    "REFERENCE": "reference",
}

# Element types that represent visual/structured content (link-target for captions)
_LINKABLE_TYPES = {"table", "image", "figure"}


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


def _make_element_id(counter: int) -> str:
    """Return a zero-padded element identifier."""
    return f"elem_{counter:04d}"


def _extract_prov(item: Any) -> tuple[int, list[float]]:
    """Extract page number and bounding box from item provenance."""
    page_no = 1
    bbox: list[float] = []
    if not (hasattr(item, "prov") and item.prov):
        return page_no, bbox
    try:
        prov = item.prov[0] if isinstance(item.prov, list) else item.prov
        page_no = int(getattr(prov, "page_no", 1))
        if hasattr(prov, "bbox") and prov.bbox:
            b = prov.bbox
            bbox = [
                float(getattr(b, "l", 0)),
                float(getattr(b, "t", 0)),
                float(getattr(b, "r", 0)),
                float(getattr(b, "b", 0)),
            ]
    except Exception:
        pass
    return page_no, bbox


def _label_to_type(item: Any) -> str:
    """Map a docling item's label to an element type string."""
    label = getattr(item, "label", None)
    if label is None:
        return "text"
    label_name = label.name if hasattr(label, "name") else str(label)
    return LABEL_TYPE_MAP.get(label_name, "text")


def _get_hierarchy_level(item: Any) -> int:
    """Get hierarchy level from a section header item (1-based)."""
    try:
        raw = item.level
        return int(raw) if raw is not None else 1
    except Exception:
        return 1


def _build_section_context(stack: list[dict]) -> tuple[str | None, str | None]:
    """Return (parent_id, parent_section) from the current section stack."""
    if not stack:
        return None, None
    top = stack[-1]
    return top.get("element_id"), top.get("content", "")


def _link_captions(elements: list[dict]) -> None:
    """
    Second pass: link caption elements to their nearest preceding
    table/image/figure on the same page.
    """
    for i, elem in enumerate(elements):
        if elem["type"] != "caption":
            continue
        for j in range(i - 1, -1, -1):
            prev = elements[j]
            if prev["page_number"] != elem["page_number"]:
                break
            if prev["type"] in _LINKABLE_TYPES:
                elem["refers_to_id"] = prev["element_id"]
                prev["caption_id"] = elem["element_id"]
                break


def _get_page_dimensions(doc: Any) -> list[dict]:
    """Extract page dimensions from the docling document."""
    dimensions: list[dict] = []
    try:
        pages = getattr(doc, "pages", None)
        if pages is None:
            return dimensions
        for page_no, page in pages.items():
            size = getattr(page, "size", None)
            if size:
                dimensions.append({
                    "page_number": int(page_no),
                    "width": float(getattr(size, "width", 0)),
                    "height": float(getattr(size, "height", 0)),
                })
    except Exception:
        pass
    return sorted(dimensions, key=lambda d: d["page_number"])


def parse_pdf(file_path: Path, image_dir: Path) -> dict:
    """
    Parse a PDF file using docling and return a structured v2 result dict.

    The result includes all Docling element types with rich metadata suitable
    for Advanced RAG chunking (hierarchical, semantic, hybrid strategies).

    Returns:
        schema_version: "2.0" result with 'elements', 'toc', 'pages', 'chunks', 'metadata'.
    """
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
        from docling.datamodel.document import TableItem, PictureItem
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

    elements: list[dict] = []
    all_languages: set[str] = set()
    has_tables = False
    has_images = False
    has_equations = False
    has_code = False
    toc: list[dict] = []
    section_stack: list[dict] = []
    doc_title: str | None = None
    img_counter: dict[int, int] = {}

    for reading_order, (item, _level) in enumerate(doc.iterate_items()):
        page_no, bbox = _extract_prov(item)
        element_id = _make_element_id(reading_order)

        # Determine type: isinstance takes priority for Table/Picture
        if isinstance(item, TableItem):
            elem_type = "table"
        elif isinstance(item, PictureItem):
            elem_type = "image"
        else:
            elem_type = _label_to_type(item)

        elem: dict = {
            "element_id": element_id,
            "type": elem_type,
            "content": "",
            "page_number": page_no,
            "reading_order": reading_order,
        }
        if bbox:
            elem["bbox"] = bbox

        # Label string for transparency
        label = getattr(item, "label", None)
        if label is not None:
            elem["label"] = label.name if hasattr(label, "name") else str(label)

        # Section hierarchy tracking
        if elem_type in ("title", "section_header"):
            hier_level = _get_hierarchy_level(item) if elem_type == "section_header" else 0
            # Pop stack entries at same or shallower depth
            while section_stack and section_stack[-1].get("hierarchy_level", 0) >= hier_level:
                section_stack.pop()
            elem["hierarchy_level"] = hier_level

        # Parent context from stack
        parent_id, parent_section = _build_section_context(section_stack)
        if parent_id:
            elem["parent_id"] = parent_id
        if parent_section:
            elem["parent_section"] = parent_section

        # --- Type-specific content extraction ---
        if isinstance(item, TableItem):
            has_tables = True
            try:
                df = item.export_to_dataframe()
                rows = df.values.tolist()
                elem["rows"] = rows
                elem["num_rows"] = len(rows)
                elem["num_cols"] = len(rows[0]) if rows else 0
            except Exception:
                elem["rows"] = []
                elem["num_rows"] = 0
                elem["num_cols"] = 0
            try:
                md = item.export_to_markdown()
                elem["content"] = md
                elem["markdown_table"] = md
            except Exception:
                elem["content"] = ""

        elif isinstance(item, PictureItem):
            has_images = True
            idx = img_counter.get(page_no, 0)
            img_counter[page_no] = idx + 1
            img_filename = f"page{page_no}_img{idx}.png"
            img_path = image_dir / img_filename
            elem["path"] = str(img_path)
            try:
                img = item.get_image(doc)
                if img:
                    img.save(str(img_path))
            except Exception as ex:
                logger.warning(f"Could not save image: {ex}")

        else:
            # All text-based elements
            text = getattr(item, "text", "") or ""
            elem["content"] = text
            lang = _detect_language(text)
            if lang:
                elem["language"] = lang
                all_languages.add(lang)

            if elem_type == "formula":
                has_equations = True
                elem["content_latex"] = ""  # LaTeX extraction requires VLM — left empty
            elif elem_type == "code":
                has_code = True

        # TOC collection + stack push for headers
        if elem_type in ("title", "section_header"):
            hier_level = elem.get("hierarchy_level", 1)
            if elem_type == "title" and doc_title is None:
                doc_title = elem["content"]
            toc.append({
                "level": hier_level,
                "text": elem["content"],
                "page_number": page_no,
                "element_id": element_id,
            })
            section_stack.append({
                "element_id": element_id,
                "content": elem["content"],
                "hierarchy_level": hier_level,
            })

        elements.append(elem)

    # Second pass: link captions to preceding tables/images
    _link_captions(elements)

    # Derive pages array from elements (backward compatibility)
    page_map: dict[int, list[dict]] = {}
    for elem in elements:
        p = elem["page_number"]
        page_map.setdefault(p, []).append(elem)

    total_pages = max(page_map.keys(), default=1)
    pages_data = [
        {"page_number": p, "elements": page_map.get(p, [])}
        for p in range(1, total_pages + 1)
    ]

    languages = sorted(all_languages) if all_languages else ["en"]

    # Generate per-page Markdown using Docling's native export
    page_markdowns: dict[str, str] = {}
    try:
        from docling_core.types.doc.base import ImageRefMode
        image_mode = ImageRefMode.EMBEDDED
    except ImportError:
        image_mode = None

    for p in range(1, total_pages + 1):
        try:
            kwargs: dict[str, Any] = {"page_no": p}
            if image_mode is not None:
                kwargs["image_mode"] = image_mode
            md = doc.export_to_markdown(**kwargs)
            page_markdowns[str(p)] = md
        except Exception as ex:
            logger.warning(f"Docling export_to_markdown failed for page {p}: {ex}")
            page_markdowns[str(p)] = ""

    return {
        "schema_version": "2.0",
        "metadata": {
            "total_pages": total_pages,
            "languages": languages,
            "has_tables": has_tables,
            "has_images": has_images,
            "has_equations": has_equations,
            "has_code": has_code,
            "title": doc_title,
            "authors": [],
            "page_dimensions": _get_page_dimensions(doc),
        },
        "toc": toc,
        "elements": elements,
        "pages": pages_data,
        "chunks": {},
        "page_markdowns": page_markdowns,
    }
