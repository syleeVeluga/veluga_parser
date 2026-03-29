"""
Chunker service — produces hierarchical, semantic, and hybrid chunks from a v2 parse result.
No external dependencies; token estimation uses a simple word-count heuristic.
"""

# Element types included in body chunks (page headers/footers excluded)
_BODY_TYPES = {
    "title", "section_header", "text", "list", "list_item",
    "caption", "footnote", "formula", "code", "reference", "table", "image", "figure",
}
_EXCLUDED = {"page_header", "page_footer"}
# Elements that must never be split across chunks
_ATOMIC = {"table", "image", "figure", "formula"}
_HEADER_TYPES = {"title", "section_header"}

_DEFAULT_MAX_TOKENS = 512


def _estimate_tokens(text: str) -> int:
    """Approximate token count using word count * 1.3 (no tokenizer required)."""
    return max(1, round(len(text.split()) * 1.3))


def _make_chunk_id(strategy: str, idx: int) -> str:
    prefix = {"hierarchical": "hc", "semantic": "sc", "hybrid": "hyb"}.get(strategy, strategy[:2])
    return f"{prefix}_{idx:04d}"


def _chunk_metadata(elements: list[dict], content: str) -> dict:
    pages = sorted({e["page_number"] for e in elements}) if elements else [1]
    langs: set[str] = set()
    for e in elements:
        if e.get("language"):
            langs.add(e["language"])
    return {
        "start_page": pages[0],
        "end_page": pages[-1],
        "has_table": any(e["type"] == "table" for e in elements),
        "has_image": any(e["type"] in ("image", "figure") for e in elements),
        "languages": sorted(langs),
    }


def _get_section_path(elem: dict, all_elements: list[dict]) -> list[str]:
    """Build section breadcrumb for an element using parent_section and element content."""
    path: list[str] = []
    parent_section = elem.get("parent_section")
    if parent_section:
        path.append(parent_section)
    if elem["type"] in _HEADER_TYPES and elem.get("content"):
        path.append(elem["content"])
    return path


def _chunk_hierarchical(elements: list[dict]) -> list[dict]:
    """
    One chunk per logical section. Each section_header/title starts a new chunk.
    Body elements are collected until the next header of same-or-higher level.
    """
    body = [e for e in elements if e["type"] not in _EXCLUDED]
    chunks: list[dict] = []
    current_elems: list[dict] = []
    current_content_parts: list[str] = []
    current_section_path: list[str] = []
    chunk_idx = 0

    def _emit():
        nonlocal chunk_idx
        if not current_elems:
            return
        content = "\n\n".join(p for p in current_content_parts if p.strip())
        chunk = {
            "chunk_id": _make_chunk_id("hierarchical", chunk_idx),
            "strategy": "hierarchical",
            "content": content,
            "token_estimate": _estimate_tokens(content),
            "element_ids": [e["element_id"] for e in current_elems],
            "page_numbers": sorted({e["page_number"] for e in current_elems}),
            "section_path": list(current_section_path),
            "metadata": _chunk_metadata(current_elems, content),
        }
        chunks.append(chunk)
        chunk_idx += 1

    for elem in body:
        etype = elem["type"]
        if etype in _HEADER_TYPES:
            _emit()
            current_elems = [elem]
            current_content_parts = [elem.get("content", "")]
            # Build section path: inherit parent, then this header
            path = []
            if elem.get("parent_section"):
                path.append(elem["parent_section"])
            if elem.get("content"):
                path.append(elem["content"])
            current_section_path = path
        else:
            if not current_elems:
                # Body before any header — start implicit chunk
                current_section_path = []
            current_elems.append(elem)
            current_content_parts.append(elem.get("content", ""))

    _emit()
    return chunks


def _chunk_semantic(elements: list[dict]) -> list[dict]:
    """
    Atomic chunks for tables/figures/formulas; prose grouped into running chunks per section.
    """
    body = [e for e in elements if e["type"] not in _EXCLUDED]
    chunks: list[dict] = []
    chunk_idx = 0
    prose_elems: list[dict] = []
    prose_parts: list[str] = []
    prose_section_path: list[str] = []

    def _emit_prose():
        nonlocal chunk_idx
        if not prose_elems:
            return
        content = "\n\n".join(p for p in prose_parts if p.strip())
        chunks.append({
            "chunk_id": _make_chunk_id("semantic", chunk_idx),
            "strategy": "semantic",
            "content": content,
            "token_estimate": _estimate_tokens(content),
            "element_ids": [e["element_id"] for e in prose_elems],
            "page_numbers": sorted({e["page_number"] for e in prose_elems}),
            "section_path": list(prose_section_path),
            "metadata": _chunk_metadata(prose_elems, content),
        })
        chunk_idx += 1
        prose_elems.clear()
        prose_parts.clear()

    for elem in body:
        etype = elem["type"]
        content = elem.get("content", "")

        if etype in _HEADER_TYPES:
            # Section boundary: flush prose, update path
            _emit_prose()
            path = []
            if elem.get("parent_section"):
                path.append(elem["parent_section"])
            if content:
                path.append(content)
            prose_section_path = path
            # Include header in the next prose chunk
            prose_elems.append(elem)
            prose_parts.append(content)

        elif etype in _ATOMIC:
            # Emit pending prose, then emit atomic chunk
            _emit_prose()
            # Collect caption if immediately following
            atomic_elems = [elem]
            atomic_parts = [content]
            # Caption will be handled when encountered as next elem (linked via refers_to_id)
            atomic_content = "\n\n".join(p for p in atomic_parts if p.strip())
            section_path: list[str] = []
            if elem.get("parent_section"):
                section_path.append(elem["parent_section"])
            chunks.append({
                "chunk_id": _make_chunk_id("semantic", chunk_idx),
                "strategy": "semantic",
                "content": atomic_content,
                "token_estimate": _estimate_tokens(atomic_content),
                "element_ids": [e["element_id"] for e in atomic_elems],
                "page_numbers": sorted({e["page_number"] for e in atomic_elems}),
                "section_path": section_path,
                "metadata": _chunk_metadata(atomic_elems, atomic_content),
            })
            chunk_idx += 1

        else:
            prose_elems.append(elem)
            prose_parts.append(content)

    _emit_prose()
    return chunks


def _chunk_hybrid(elements: list[dict], max_tokens: int = _DEFAULT_MAX_TOKENS) -> list[dict]:
    """
    Hierarchical chunking first, then split oversized chunks at paragraph boundaries.
    Atomic elements (table, image, figure, formula) are never split mid-element.
    """
    base_chunks = _chunk_hierarchical(elements)
    result: list[dict] = []
    chunk_idx = 0

    # Build element lookup for splitting
    elem_by_id = {e["element_id"]: e for e in elements}

    for base in base_chunks:
        if base["token_estimate"] <= max_tokens:
            # Rename chunk_id to hybrid prefix
            base_chunk = dict(base)
            base_chunk["chunk_id"] = _make_chunk_id("hybrid", chunk_idx)
            base_chunk["strategy"] = "hybrid"
            result.append(base_chunk)
            chunk_idx += 1
            continue

        # Split at paragraph (text element) boundaries, keeping atomics intact
        elem_ids = base["element_ids"]
        elems_in_chunk = [elem_by_id[eid] for eid in elem_ids if eid in elem_by_id]
        section_path = base["section_path"]

        current_sub_elems: list[dict] = []
        current_sub_parts: list[str] = []
        current_tokens = 0

        def _emit_sub():
            nonlocal chunk_idx
            if not current_sub_elems:
                return
            content = "\n\n".join(p for p in current_sub_parts if p.strip())
            result.append({
                "chunk_id": _make_chunk_id("hybrid", chunk_idx),
                "strategy": "hybrid",
                "content": content,
                "token_estimate": _estimate_tokens(content),
                "element_ids": [e["element_id"] for e in current_sub_elems],
                "page_numbers": sorted({e["page_number"] for e in current_sub_elems}),
                "section_path": list(section_path),
                "metadata": _chunk_metadata(current_sub_elems, content),
            })
            chunk_idx += 1
            current_sub_elems.clear()
            current_sub_parts.clear()

        for elem in elems_in_chunk:
            etype = elem["type"]
            content = elem.get("content", "")
            tok = _estimate_tokens(content)

            if etype in _ATOMIC:
                # Never split atomics — emit pending sub, then emit atomic standalone
                _emit_sub()
                result.append({
                    "chunk_id": _make_chunk_id("hybrid", chunk_idx),
                    "strategy": "hybrid",
                    "content": content,
                    "token_estimate": tok,
                    "element_ids": [elem["element_id"]],
                    "page_numbers": [elem["page_number"]],
                    "section_path": list(section_path),
                    "metadata": _chunk_metadata([elem], content),
                })
                chunk_idx += 1
                current_tokens = 0

            elif current_tokens + tok > max_tokens and current_sub_elems:
                # Would exceed limit — flush current sub and start new one
                _emit_sub()
                current_sub_elems.append(elem)
                current_sub_parts.append(content)
                current_tokens = tok

            else:
                current_sub_elems.append(elem)
                current_sub_parts.append(content)
                current_tokens += tok

        _emit_sub()

    return result


def chunk_document(doc: dict) -> dict:
    """
    Populate doc["chunks"] with hierarchical, semantic, and hybrid chunk lists.
    Modifies the dict in-place and returns it.
    """
    elements = doc.get("elements", [])
    doc["chunks"] = {
        "hierarchical": _chunk_hierarchical(elements),
        "semantic": _chunk_semantic(elements),
        "hybrid": _chunk_hybrid(elements),
    }
    return doc
