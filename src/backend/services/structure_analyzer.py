"""
Structure analyzer — extracts font metadata from PDF via PyPdfium2 and builds
a statistical document structure profile (body font, heading tiers, page numbers).
Runs as a post-processing step after Docling parsing, before chunking.
"""
import logging
from collections import Counter, defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


def _strip_subset_prefix(name: str) -> str:
    """Remove font subset prefix like 'ABCDEF+ArialMT' → 'ArialMT'."""
    if "+" in name:
        return name.split("+", 1)[1]
    return name


def _round_size(size: float) -> float:
    """Round font size to nearest 0.5pt for stable grouping."""
    return round(size * 2) / 2


def _detect_bold(font_name: str, weight: int) -> bool:
    name_lower = font_name.lower()
    return weight >= 600 or "bold" in name_lower or "heavy" in name_lower


def _detect_italic(font_name: str) -> bool:
    name_lower = font_name.lower()
    return "italic" in name_lower or "oblique" in name_lower


def _extract_font_spans(file_path: Path) -> dict[int, list[dict]]:
    """
    Extract per-character font metadata from the PDF using PyPdfium2.
    Returns {page_number: [FontSpan, ...]} where page_number is 1-based.

    Each FontSpan: {text, font_name, font_size, font_weight, bbox, page}
    bbox is in top-left origin coordinates: [left, top, right, bottom].
    """
    import pypdfium2 as pdfium

    page_spans: dict[int, list[dict]] = {}
    try:
        pdf = pdfium.PdfDocument(str(file_path))
    except Exception as e:
        logger.warning(f"PyPdfium2 could not open PDF: {e}")
        return page_spans

    try:
        for page_idx in range(len(pdf)):
            page_no = page_idx + 1
            page = pdf[page_idx]
            page_height = page.get_height()
            textpage = page.get_textpage()

            char_count = textpage.count_chars()
            if char_count <= 0:
                page.close()
                continue

            # Group consecutive chars with same font into spans
            spans: list[dict] = []
            current_span: dict | None = None

            for ci in range(char_count):
                try:
                    char = textpage.get_text_range(ci, 1)
                    if not char or char in ("\n", "\r", "\x00"):
                        # Whitespace/newline breaks span
                        if current_span:
                            spans.append(current_span)
                            current_span = None
                        continue

                    font_size = textpage.get_fontsize(ci)
                    font_size = _round_size(font_size) if font_size > 0 else 0.0

                    # Get char bounding box (bottom-left origin from pdfium)
                    try:
                        left, bottom, right, top = textpage.get_charbox(ci)
                        # Convert to top-left origin
                        bbox_tl = [
                            float(left),
                            float(page_height - top),
                            float(right),
                            float(page_height - bottom),
                        ]
                    except Exception:
                        bbox_tl = []

                    # Font name and weight
                    font_name = ""
                    font_weight = 400
                    try:
                        font_name_raw, font_flags = textpage.get_fontname(ci)
                        font_name = _strip_subset_prefix(font_name_raw) if font_name_raw else ""
                    except Exception:
                        pass

                    # Check if this char extends the current span
                    if (
                        current_span
                        and current_span["font_name"] == font_name
                        and current_span["_font_size_raw"] == font_size
                    ):
                        current_span["text"] += char
                        # Extend bbox
                        if bbox_tl and current_span["bbox"]:
                            current_span["bbox"][2] = max(current_span["bbox"][2], bbox_tl[2])
                            current_span["bbox"][3] = max(current_span["bbox"][3], bbox_tl[3])
                            current_span["bbox"][0] = min(current_span["bbox"][0], bbox_tl[0])
                            current_span["bbox"][1] = min(current_span["bbox"][1], bbox_tl[1])
                    else:
                        if current_span:
                            spans.append(current_span)
                        is_bold = _detect_bold(font_name, font_weight)
                        is_italic = _detect_italic(font_name)
                        current_span = {
                            "text": char,
                            "font_name": font_name,
                            "font_size": font_size,
                            "_font_size_raw": font_size,
                            "font_weight": font_weight,
                            "is_bold": is_bold,
                            "is_italic": is_italic,
                            "bbox": list(bbox_tl) if bbox_tl else [],
                            "page": page_no,
                        }
                except Exception:
                    continue

            if current_span:
                spans.append(current_span)

            # Clean up internal fields
            for s in spans:
                s.pop("_font_size_raw", None)

            if spans:
                page_spans[page_no] = spans

            textpage.close()
            page.close()
    finally:
        pdf.close()

    return page_spans


def _bbox_overlap(a: list[float], b: list[float]) -> float:
    """Compute intersection area between two [l, t, r, b] bboxes."""
    if not a or not b or len(a) < 4 or len(b) < 4:
        return 0.0
    x_left = max(a[0], b[0])
    y_top = max(a[1], b[1])
    x_right = min(a[2], b[2])
    y_bottom = min(a[3], b[3])
    if x_right <= x_left or y_bottom <= y_top:
        return 0.0
    return (x_right - x_left) * (y_bottom - y_top)


def _bbox_area(bbox: list[float]) -> float:
    if not bbox or len(bbox) < 4:
        return 0.0
    w = max(0, bbox[2] - bbox[0])
    h = max(0, bbox[3] - bbox[1])
    return w * h


def _match_spans_to_elements(
    page_spans: dict[int, list[dict]],
    elements: list[dict],
) -> None:
    """
    For each element with a bbox, find overlapping font spans and set
    the element's font_info to the dominant font (most characters).
    Modifies elements in-place.
    """
    for elem in elements:
        elem_bbox = elem.get("bbox")
        page_no = elem.get("page_number", 0)
        if not elem_bbox or page_no not in page_spans:
            continue

        spans = page_spans[page_no]
        # Expand element bbox slightly for tolerance (2pt each side)
        tol = 2.0
        expanded = [
            elem_bbox[0] - tol,
            elem_bbox[1] - tol,
            elem_bbox[2] + tol,
            elem_bbox[3] + tol,
        ]

        # Collect overlapping spans weighted by character count
        font_votes: Counter = Counter()
        font_info_map: dict[tuple, dict] = {}

        for span in spans:
            if not span["bbox"]:
                continue
            overlap = _bbox_overlap(expanded, span["bbox"])
            if overlap <= 0:
                continue
            span_area = _bbox_area(span["bbox"])
            # Require at least 20% of span area overlaps with element
            if span_area > 0 and overlap / span_area < 0.2:
                continue
            key = (span["font_name"], span["font_size"])
            char_count = len(span["text"])
            font_votes[key] += char_count
            if key not in font_info_map:
                font_info_map[key] = {
                    "font_name": span["font_name"],
                    "font_size": span["font_size"],
                    "font_weight": span["font_weight"],
                    "is_bold": span["is_bold"],
                    "is_italic": span["is_italic"],
                }

        if font_votes:
            dominant_key = font_votes.most_common(1)[0][0]
            elem["font_info"] = font_info_map[dominant_key]


def _build_structure_profile(elements: list[dict]) -> dict:
    """
    Analyze font distribution across elements to build a document structure profile.
    Returns a structure_profile dict.
    """
    # Collect font stats: (font_name, font_size) → total char count, grouped by element type
    font_char_counts: Counter = Counter()
    font_info_lookup: dict[tuple, dict] = {}
    elements_with_font = [e for e in elements if e.get("font_info")]

    if not elements_with_font:
        return {
            "body_font": None,
            "heading_fonts": [],
            "page_number_font": None,
            "running_header_font": None,
            "font_size_histogram": {},
            "structure_confidence": 0.0,
            "reclassified_elements": [],
        }

    # Build font size histogram and identify body font
    size_histogram: Counter = Counter()
    body_type_chars: Counter = Counter()

    for elem in elements_with_font:
        fi = elem["font_info"]
        key = (fi["font_name"], fi["font_size"])
        content = elem.get("content", "")
        char_count = len(content) if content else 1

        size_histogram[fi["font_size"]] += char_count
        font_char_counts[key] += char_count
        if key not in font_info_lookup:
            font_info_lookup[key] = fi

        # Count chars specifically from body text elements
        if elem["type"] in ("text", "list", "list_item", "reference"):
            body_type_chars[key] += char_count

    # 1. Body font: most frequent font among text-type elements
    if body_type_chars:
        body_key = body_type_chars.most_common(1)[0][0]
    else:
        body_key = font_char_counts.most_common(1)[0][0]

    body_font_name, body_font_size = body_key
    body_font = {"name": body_font_name, "size": body_font_size}

    # 2. Heading fonts: sizes larger than body, clustered by gap detection
    larger_sizes: set[float] = set()
    for (fname, fsize), count in font_char_counts.items():
        if fsize > body_font_size + 0.5:
            larger_sizes.add(fsize)

    # Sort descending and assign levels
    sorted_sizes = sorted(larger_sizes, reverse=True)
    heading_fonts: list[dict] = []
    for level, size in enumerate(sorted_sizes, start=1):
        # Find representative font name for this size
        best_key = max(
            ((k, c) for k, c in font_char_counts.items() if k[1] == size),
            key=lambda x: x[1],
            default=None,
        )
        if best_key:
            fi = font_info_lookup[best_key[0]]
            heading_fonts.append({
                "level": level,
                "name": fi["font_name"],
                "size": size,
            })
        if level >= 5:
            break

    heading_sizes = {h["size"] for h in heading_fonts}

    # 3. Page number font: look in page_header/page_footer with short numeric content
    page_num_candidates: Counter = Counter()
    for elem in elements_with_font:
        if elem["type"] not in ("page_header", "page_footer"):
            continue
        content = (elem.get("content", "") or "").strip()
        # Typical page numbers: 1-5 chars, mostly digits or roman numerals
        if len(content) <= 5 and any(c.isdigit() for c in content):
            fi = elem["font_info"]
            page_num_candidates[(fi["font_name"], fi["font_size"])] += 1

    page_number_font = None
    if page_num_candidates:
        pn_key = page_num_candidates.most_common(1)[0][0]
        page_number_font = {"name": pn_key[0], "size": pn_key[1]}

    # 4. Running header font: repeated text in page_header/page_footer across pages
    header_texts: Counter = Counter()
    header_font_map: dict[str, dict] = {}
    for elem in elements_with_font:
        if elem["type"] not in ("page_header", "page_footer"):
            continue
        content = (elem.get("content", "") or "").strip()
        if len(content) > 5:
            header_texts[content] += 1
            if content not in header_font_map:
                header_font_map[content] = elem["font_info"]

    running_header_font = None
    if header_texts:
        most_common_header, count = header_texts.most_common(1)[0]
        if count >= 2:
            fi = header_font_map[most_common_header]
            running_header_font = {"name": fi["font_name"], "size": fi["font_size"]}

    # 5. Reclassification: text elements with heading font sizes
    reclassified: list[dict] = []
    for elem in elements_with_font:
        if elem["type"] != "text":
            continue
        fi = elem["font_info"]
        if fi["font_size"] in heading_sizes:
            matching_level = next(
                (h["level"] for h in heading_fonts if h["size"] == fi["font_size"]),
                None,
            )
            reclassified.append({
                "element_id": elem["element_id"],
                "original_type": "text",
                "suggested_type": "section_header",
                "suggested_level": matching_level,
                "font_size": fi["font_size"],
                "reason": f"font_size {fi['font_size']}pt matches heading level {matching_level}",
            })

    # 6. Confidence score
    total_with_font = len(elements_with_font)
    total_elements = len([
        e for e in elements
        if e["type"] not in ("image", "figure", "table")
    ])
    coverage = total_with_font / total_elements if total_elements > 0 else 0.0
    # Higher confidence when: good coverage + clear body font dominance + heading tiers found
    body_dominance = body_type_chars.get(body_key, 0) / max(sum(body_type_chars.values()), 1)
    has_headings = 1.0 if heading_fonts else 0.5
    confidence = min(1.0, coverage * 0.5 + body_dominance * 0.3 + has_headings * 0.2)

    # Format histogram with string keys for JSON serialization
    hist = {str(k): v for k, v in sorted(size_histogram.items())}

    return {
        "body_font": body_font,
        "heading_fonts": heading_fonts,
        "page_number_font": page_number_font,
        "running_header_font": running_header_font,
        "font_size_histogram": hist,
        "structure_confidence": round(confidence, 2),
        "reclassified_elements": reclassified,
    }


def analyze_structure(file_path: Path, parsed_result: dict) -> dict:
    """
    Enrich parsed_result with font metadata and structure profile.
    Modifies parsed_result in-place and returns it.

    Adds to each element: font_info {font_name, font_size, font_weight, is_bold, is_italic}
    Adds to metadata: structure_profile, has_structure_analysis
    """
    elements = parsed_result.get("elements", [])
    if not elements:
        parsed_result.setdefault("metadata", {})["has_structure_analysis"] = False
        return parsed_result

    logger.info(f"Extracting font metadata from: {file_path}")
    page_spans = _extract_font_spans(file_path)

    if not page_spans:
        # Likely a scanned PDF with no text objects
        logger.info("No font spans found (possibly scanned PDF). Skipping structure analysis.")
        meta = parsed_result.setdefault("metadata", {})
        meta["has_structure_analysis"] = True
        meta["structure_profile"] = {
            "body_font": None,
            "heading_fonts": [],
            "page_number_font": None,
            "running_header_font": None,
            "font_size_histogram": {},
            "structure_confidence": 0.0,
            "reclassified_elements": [],
        }
        return parsed_result

    # Phase B: match font spans to elements
    _match_spans_to_elements(page_spans, elements)

    # Phase C: build structure profile
    profile = _build_structure_profile(elements)

    meta = parsed_result.setdefault("metadata", {})
    meta["has_structure_analysis"] = True
    meta["structure_profile"] = profile

    total_spans = sum(len(s) for s in page_spans.values())
    enriched = sum(1 for e in elements if e.get("font_info"))
    logger.info(
        f"Structure analysis complete: {total_spans} font spans, "
        f"{enriched}/{len(elements)} elements enriched, "
        f"confidence={profile['structure_confidence']}"
    )

    return parsed_result
