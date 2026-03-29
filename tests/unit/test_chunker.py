"""
Unit tests for the chunker service.
No docling or external dependencies required.
"""
import pytest
from src.backend.services.chunker import (
    _estimate_tokens,
    _make_chunk_id,
    _chunk_hierarchical,
    _chunk_semantic,
    _chunk_hybrid,
    chunk_document,
)


# ---------------------------------------------------------------------------
# Element factory helpers
# ---------------------------------------------------------------------------

def _elem(etype: str, content: str, page: int = 1, eid: str = None, level: int = None,
          parent_section: str = None) -> dict:
    e: dict = {
        "element_id": eid or f"elem_{etype[:3]}",
        "type": etype,
        "content": content,
        "page_number": page,
        "reading_order": 0,
    }
    if level is not None:
        e["hierarchy_level"] = level
    if parent_section is not None:
        e["parent_section"] = parent_section
    return e


def _section(text: str, level: int = 1, page: int = 1, eid: str = "elem_sh") -> dict:
    return _elem("section_header", text, page=page, eid=eid, level=level)


def _title(text: str, page: int = 1) -> dict:
    e = _elem("title", text, page=page, eid="elem_title", level=0)
    return e


def _text(content: str, page: int = 1, eid: str = "elem_txt") -> dict:
    return _elem("text", content, page=page, eid=eid)


def _table(content: str = "| A | B |", page: int = 1, eid: str = "elem_tbl") -> dict:
    e = _elem("table", content, page=page, eid=eid)
    e["rows"] = [["A", "B"]]
    return e


def _image(page: int = 1, eid: str = "elem_img") -> dict:
    return _elem("image", "", page=page, eid=eid)


def _formula(content: str = "E=mc^2", page: int = 1, eid: str = "elem_frm") -> dict:
    return _elem("formula", content, page=page, eid=eid)


def _page_header(content: str = "Header", page: int = 1) -> dict:
    return _elem("page_header", content, page=page, eid="elem_ph")


def _page_footer(content: str = "Footer", page: int = 1) -> dict:
    return _elem("page_footer", content, page=page, eid="elem_pf")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_estimate_tokens_positive(self):
        assert _estimate_tokens("Hello world") > 0

    def test_estimate_tokens_empty(self):
        assert _estimate_tokens("") >= 1

    def test_estimate_tokens_proportional(self):
        short = _estimate_tokens("hi")
        long = _estimate_tokens("hi " * 100)
        assert long > short

    def test_make_chunk_id_hierarchical(self):
        assert _make_chunk_id("hierarchical", 3) == "hc_0003"

    def test_make_chunk_id_semantic(self):
        assert _make_chunk_id("semantic", 0) == "sc_0000"

    def test_make_chunk_id_hybrid(self):
        assert _make_chunk_id("hybrid", 10) == "hyb_0010"


# ---------------------------------------------------------------------------
# Hierarchical chunker
# ---------------------------------------------------------------------------

class TestChunkHierarchical:
    def test_one_chunk_per_section(self):
        elems = [
            _section("Intro", eid="e1"),
            _text("Some intro text.", eid="e2"),
            _section("Methods", eid="e3"),
            _text("Methods text.", eid="e4"),
        ]
        chunks = _chunk_hierarchical(elems)
        assert len(chunks) == 2
        assert "Intro" in chunks[0]["content"]
        assert "Methods" in chunks[1]["content"]

    def test_chunk_ids_unique(self):
        elems = [_section("A", eid="e1"), _section("B", eid="e2"), _section("C", eid="e3")]
        chunks = _chunk_hierarchical(elems)
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))

    def test_section_path_set_on_chunk(self):
        elems = [_section("Introduction", eid="e1"), _text("body", eid="e2")]
        chunks = _chunk_hierarchical(elems)
        assert chunks[0]["section_path"] == ["Introduction"]

    def test_element_ids_in_chunk(self):
        elems = [_section("Sec", eid="e1"), _text("Body", eid="e2")]
        chunks = _chunk_hierarchical(elems)
        assert "e1" in chunks[0]["element_ids"]
        assert "e2" in chunks[0]["element_ids"]

    def test_page_numbers_collected(self):
        elems = [
            _section("S", page=1, eid="e1"),
            _text("T", page=2, eid="e2"),
        ]
        chunks = _chunk_hierarchical(elems)
        assert 1 in chunks[0]["page_numbers"]
        assert 2 in chunks[0]["page_numbers"]

    def test_page_headers_excluded(self):
        elems = [
            _page_header(),
            _section("Sec", eid="e1"),
            _page_footer(),
        ]
        chunks = _chunk_hierarchical(elems)
        all_ids = [eid for c in chunks for eid in c["element_ids"]]
        assert "elem_ph" not in all_ids
        assert "elem_pf" not in all_ids

    def test_body_before_header_gets_own_chunk(self):
        elems = [_text("Preamble text", eid="e1"), _section("Intro", eid="e2")]
        chunks = _chunk_hierarchical(elems)
        assert len(chunks) == 2
        assert "e1" in chunks[0]["element_ids"]

    def test_token_estimate_present_and_positive(self):
        elems = [_section("Sec", eid="e1"), _text("Content", eid="e2")]
        chunks = _chunk_hierarchical(elems)
        for c in chunks:
            assert c["token_estimate"] >= 1


# ---------------------------------------------------------------------------
# Semantic chunker
# ---------------------------------------------------------------------------

class TestChunkSemantic:
    def test_table_becomes_standalone_chunk(self):
        elems = [
            _section("Sec", eid="e0"),
            _text("Prose before table", eid="e1"),
            _table(eid="e2"),
            _text("Prose after table", eid="e3"),
        ]
        chunks = _chunk_semantic(elems)
        table_chunks = [c for c in chunks if "e2" in c["element_ids"]]
        assert len(table_chunks) == 1
        # Table chunk should only contain the table element
        assert table_chunks[0]["element_ids"] == ["e2"]

    def test_image_becomes_standalone_chunk(self):
        elems = [_image(eid="img1"), _text("caption text", eid="e2")]
        chunks = _chunk_semantic(elems)
        img_chunks = [c for c in chunks if "img1" in c["element_ids"]]
        assert len(img_chunks) == 1

    def test_formula_becomes_standalone_chunk(self):
        elems = [_section("Math", eid="e0"), _formula(eid="f1"), _text("Discussion", eid="e1")]
        chunks = _chunk_semantic(elems)
        formula_chunks = [c for c in chunks if "f1" in c["element_ids"]]
        assert len(formula_chunks) == 1

    def test_prose_grouped_within_section(self):
        elems = [
            _section("Sec", eid="e0"),
            _text("Para 1", eid="e1"),
            _text("Para 2", eid="e2"),
        ]
        chunks = _chunk_semantic(elems)
        prose_chunks = [c for c in chunks if "e1" in c["element_ids"]]
        assert len(prose_chunks) == 1
        assert "e2" in prose_chunks[0]["element_ids"]

    def test_page_headers_excluded(self):
        elems = [_page_header(), _text("Content", eid="e1"), _page_footer()]
        chunks = _chunk_semantic(elems)
        all_ids = [eid for c in chunks for eid in c["element_ids"]]
        assert "elem_ph" not in all_ids
        assert "elem_pf" not in all_ids


# ---------------------------------------------------------------------------
# Hybrid chunker
# ---------------------------------------------------------------------------

class TestChunkHybrid:
    def test_small_chunk_not_split(self):
        elems = [
            _section("Intro", eid="e0"),
            _text("Short text.", eid="e1"),
        ]
        chunks = _chunk_hybrid(elems, max_tokens=512)
        assert len(chunks) == 1

    def test_oversized_chunk_is_split(self):
        # Create content that exceeds max_tokens=10
        long_text = " ".join(["word"] * 50)
        elems = [
            _section("BigSection", eid="e0"),
            _text(long_text, page=1, eid="e1"),
            _text(long_text, page=1, eid="e2"),
            _text(long_text, page=1, eid="e3"),
        ]
        chunks = _chunk_hybrid(elems, max_tokens=10)
        assert len(chunks) > 1

    def test_hybrid_never_splits_table(self):
        """A table element must not be split across chunks even if it's large."""
        big_table = _table(content=" ".join(["cell"] * 200), eid="t1")
        elems = [_section("S", eid="e0"), big_table]
        chunks = _chunk_hybrid(elems, max_tokens=5)
        # Table must appear exactly once and as a whole
        table_chunks = [c for c in chunks if "t1" in c["element_ids"]]
        assert len(table_chunks) == 1
        # No other chunk contains t1
        assert all(c["element_ids"] == ["t1"] or "t1" not in c["element_ids"] for c in chunks)

    def test_hybrid_chunk_ids_unique(self):
        elems = [
            _section("A", eid="e1"),
            _text("text1", eid="e2"),
            _section("B", eid="e3"),
            _text("text2", eid="e4"),
        ]
        chunks = _chunk_hybrid(elems)
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))

    def test_hybrid_strategy_field(self):
        elems = [_section("S", eid="e1"), _text("body", eid="e2")]
        chunks = _chunk_hybrid(elems)
        for c in chunks:
            assert c["strategy"] == "hybrid"

    def test_page_headers_excluded_from_hybrid(self):
        elems = [_page_header(), _section("Sec", eid="e1"), _page_footer()]
        chunks = _chunk_hybrid(elems)
        all_ids = [eid for c in chunks for eid in c["element_ids"]]
        assert "elem_ph" not in all_ids
        assert "elem_pf" not in all_ids


# ---------------------------------------------------------------------------
# chunk_document integration
# ---------------------------------------------------------------------------

class TestChunkDocument:
    def test_chunk_document_populates_chunks(self):
        doc = {
            "elements": [
                _section("Introduction", eid="e1"),
                _text("Intro body", eid="e2"),
            ],
            "chunks": {},
        }
        result = chunk_document(doc)
        assert "hierarchical" in result["chunks"]
        assert "semantic" in result["chunks"]
        assert "hybrid" in result["chunks"]

    def test_chunk_document_returns_same_dict(self):
        doc = {"elements": [_text("hello", eid="e1")], "chunks": {}}
        result = chunk_document(doc)
        assert result is doc

    def test_chunk_ids_unique_across_strategies(self):
        doc = {
            "elements": [
                _section("S1", eid="e1"),
                _text("text", eid="e2"),
                _section("S2", eid="e3"),
            ],
            "chunks": {},
        }
        chunk_document(doc)
        all_ids = []
        for strategy_chunks in doc["chunks"].values():
            all_ids.extend(c["chunk_id"] for c in strategy_chunks)
        # Each strategy has its own prefix, so IDs are globally unique
        assert len(all_ids) == len(set(all_ids))

    def test_empty_document_produces_empty_chunks(self):
        doc = {"elements": [], "chunks": {}}
        chunk_document(doc)
        assert doc["chunks"]["hierarchical"] == []
        assert doc["chunks"]["semantic"] == []
        assert doc["chunks"]["hybrid"] == []

    def test_only_page_headers_produces_empty_chunks(self):
        doc = {
            "elements": [_page_header(), _page_footer()],
            "chunks": {},
        }
        chunk_document(doc)
        assert doc["chunks"]["hierarchical"] == []
        assert doc["chunks"]["semantic"] == []
        assert doc["chunks"]["hybrid"] == []
