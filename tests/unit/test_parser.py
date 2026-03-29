"""
Unit tests for parser service — uses mocked docling to avoid heavy dependency.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _make_prov(page_no: int = 1):
    prov = MagicMock()
    prov.page_no = page_no
    bbox = MagicMock()
    bbox.l, bbox.t, bbox.r, bbox.b = 0.0, 0.0, 100.0, 20.0
    prov.bbox = bbox
    return prov


def _make_label(name: str):
    label = MagicMock()
    label.name = name
    return label


def _make_mock_text_item(text: str, page_no: int = 1, label_name: str = "TEXT"):
    item = MagicMock()
    item.text = text
    item.label = _make_label(label_name)
    item.prov = [_make_prov(page_no)]
    return item


def _make_mock_section_header(text: str, level: int = 1, page_no: int = 1):
    item = MagicMock()
    item.text = text
    item.label = _make_label("SECTION_HEADER")
    item.level = level
    item.prov = [_make_prov(page_no)]
    return item


def _make_mock_title_item(text: str, page_no: int = 1):
    item = MagicMock()
    item.text = text
    item.label = _make_label("TITLE")
    item.level = 0
    item.prov = [_make_prov(page_no)]
    return item


def _make_mock_table_item(rows: list, page_no: int = 1):
    item = MagicMock()
    item.text = None
    item.label = _make_label("TABLE")
    df = MagicMock()
    df.values.tolist.return_value = rows
    item.export_to_dataframe.return_value = df
    item.export_to_markdown.return_value = "| col1 | col2 |\n|------|------|\n| a | b |"
    item.prov = [_make_prov(page_no)]
    return item


def _make_mock_picture_item(page_no: int = 1):
    item = MagicMock()
    item.text = None
    item.label = _make_label("PICTURE")
    item.prov = [_make_prov(page_no)]
    item.get_image.return_value = None
    return item


def _make_mock_caption_item(text: str, page_no: int = 1):
    item = MagicMock()
    item.text = text
    item.label = _make_label("CAPTION")
    item.prov = [_make_prov(page_no)]
    return item


# ---------------------------------------------------------------------------
# Language detection tests
# ---------------------------------------------------------------------------

class TestLanguageDetection:
    def test_detect_korean(self):
        from src.backend.services.parser import _detect_language
        assert _detect_language("안녕하세요 이것은 한국어 텍스트입니다") == "ko"

    def test_detect_english(self):
        from src.backend.services.parser import _detect_language
        assert _detect_language("Hello this is an English text document") == "en"

    def test_detect_chinese(self):
        from src.backend.services.parser import _detect_language
        assert _detect_language("这是中文文本内容测试") == "zh"

    def test_detect_japanese(self):
        from src.backend.services.parser import _detect_language
        assert _detect_language("これは日本語のテキストです") == "ja"

    def test_empty_text_returns_none(self):
        from src.backend.services.parser import _detect_language
        assert _detect_language("") is None
        assert _detect_language("   ") is None


# ---------------------------------------------------------------------------
# Internal helper unit tests (no docling needed)
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_make_element_id(self):
        from src.backend.services.parser import _make_element_id
        assert _make_element_id(0) == "elem_0000"
        assert _make_element_id(42) == "elem_0042"
        assert _make_element_id(9999) == "elem_9999"

    def test_label_to_type_known_labels(self):
        from src.backend.services.parser import _label_to_type
        for label_name, expected in [
            ("TITLE", "title"),
            ("SECTION_HEADER", "section_header"),
            ("TEXT", "text"),
            ("CAPTION", "caption"),
            ("FOOTNOTE", "footnote"),
            ("FORMULA", "formula"),
            ("PAGE_HEADER", "page_header"),
            ("PAGE_FOOTER", "page_footer"),
            ("CODE", "code"),
            ("REFERENCE", "reference"),
            ("LIST", "list"),
            ("LIST_ITEM", "list_item"),
        ]:
            item = MagicMock()
            item.label = _make_label(label_name)
            assert _label_to_type(item) == expected, f"Failed for {label_name}"

    def test_label_to_type_unknown_falls_back_to_text(self):
        from src.backend.services.parser import _label_to_type
        item = MagicMock()
        item.label = _make_label("UNKNOWN_LABEL")
        assert _label_to_type(item) == "text"

    def test_label_to_type_no_label(self):
        from src.backend.services.parser import _label_to_type
        item = MagicMock(spec=[])  # no attributes
        assert _label_to_type(item) == "text"

    def test_get_hierarchy_level_returns_int(self):
        from src.backend.services.parser import _get_hierarchy_level
        item = MagicMock()
        item.level = 2
        assert _get_hierarchy_level(item) == 2

    def test_get_hierarchy_level_defaults_to_1_on_error(self):
        from src.backend.services.parser import _get_hierarchy_level
        item = MagicMock()
        item.level = None
        assert _get_hierarchy_level(item) == 1

    def test_build_section_context_empty_stack(self):
        from src.backend.services.parser import _build_section_context
        assert _build_section_context([]) == (None, None)

    def test_build_section_context_returns_top(self):
        from src.backend.services.parser import _build_section_context
        stack = [
            {"element_id": "elem_0001", "content": "Introduction", "hierarchy_level": 1},
            {"element_id": "elem_0005", "content": "Background", "hierarchy_level": 2},
        ]
        parent_id, parent_section = _build_section_context(stack)
        assert parent_id == "elem_0005"
        assert parent_section == "Background"

    def test_link_captions_connects_to_preceding_table(self):
        from src.backend.services.parser import _link_captions
        elements = [
            {"element_id": "elem_0001", "type": "table", "page_number": 1, "content": "t"},
            {"element_id": "elem_0002", "type": "caption", "page_number": 1, "content": "Table 1"},
        ]
        _link_captions(elements)
        assert elements[1].get("refers_to_id") == "elem_0001"
        assert elements[0].get("caption_id") == "elem_0002"

    def test_link_captions_connects_to_preceding_image(self):
        from src.backend.services.parser import _link_captions
        elements = [
            {"element_id": "elem_0001", "type": "image", "page_number": 2, "content": ""},
            {"element_id": "elem_0002", "type": "caption", "page_number": 2, "content": "Fig 1"},
        ]
        _link_captions(elements)
        assert elements[1].get("refers_to_id") == "elem_0001"

    def test_link_captions_does_not_cross_pages(self):
        from src.backend.services.parser import _link_captions
        elements = [
            {"element_id": "elem_0001", "type": "table", "page_number": 1, "content": "t"},
            {"element_id": "elem_0002", "type": "caption", "page_number": 2, "content": "caption"},
        ]
        _link_captions(elements)
        assert "refers_to_id" not in elements[1]


# ---------------------------------------------------------------------------
# Full parse_pdf integration tests (mocked docling)
# ---------------------------------------------------------------------------

def _run_parse_pdf_with_mocks(tmp_path, items_and_levels, extra_doc_attrs=None):
    """
    Helper: run parse_pdf with a list of (item, level) pairs, all mocked.
    Wires mocks through sys.modules so parse_pdf's local imports resolve correctly.
    Returns the result dict.
    """
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")
    image_dir = tmp_path / "images"

    # Class stubs for isinstance checks inside parse_pdf
    TableItemClass = type("TableItem", (), {})
    PictureItemClass = type("PictureItem", (), {})

    # Tag items whose label maps to table/image
    for item, _ in items_and_levels:
        label_name = getattr(getattr(item, "label", None), "name", "")
        if label_name == "TABLE":
            item.__class__ = TableItemClass
        elif label_name == "PICTURE":
            item.__class__ = PictureItemClass

    # Build mock document that yields our items
    mock_doc = MagicMock()
    mock_doc.iterate_items.return_value = items_and_levels
    mock_doc.pages = {}
    if extra_doc_attrs:
        for k, v in extra_doc_attrs.items():
            setattr(mock_doc, k, v)

    mock_conv = MagicMock()
    mock_conv.document = mock_doc

    mock_converter = MagicMock()
    mock_converter.convert.return_value = mock_conv

    # Wire DocumentConverter so parse_pdf's local `from docling... import` resolves
    mock_dc_module = MagicMock()
    mock_dc_module.DocumentConverter.return_value = mock_converter

    # Wire TableItem / PictureItem into the document module mock
    mock_doc_module = MagicMock()
    mock_doc_module.TableItem = TableItemClass
    mock_doc_module.PictureItem = PictureItemClass

    with patch.dict("sys.modules", {
        "docling": MagicMock(),
        "docling.document_converter": mock_dc_module,
        "docling.datamodel": MagicMock(),
        "docling.datamodel.base_models": MagicMock(),
        "docling.datamodel.pipeline_options": MagicMock(),
        "docling.datamodel.document": mock_doc_module,
        "docling.backend": MagicMock(),
        "docling.backend.pypdfium2_backend": MagicMock(),
    }):
        import importlib
        import src.backend.services.parser as parser_module
        importlib.reload(parser_module)
        return parser_module.parse_pdf(pdf_path, image_dir)


class TestParsePdf:
    def test_parse_pdf_returns_v2_schema(self, tmp_path):
        items = [
            (_make_mock_text_item("Hello World"), 0),
            (_make_mock_text_item("안녕하세요"), 0),
            (_make_mock_table_item([["A", "B"], ["1", "2"]], page_no=2), 0),
        ]
        result = _run_parse_pdf_with_mocks(tmp_path, items)

        # v1 compat fields present
        assert "pages" in result
        assert "metadata" in result
        assert isinstance(result["pages"], list)
        meta = result["metadata"]
        assert "total_pages" in meta
        assert "languages" in meta
        assert "has_tables" in meta
        assert "has_images" in meta

        # v2 new fields present
        assert result.get("schema_version") == "2.0"
        assert "elements" in result
        assert "toc" in result
        assert "chunks" in result
        assert isinstance(result["elements"], list)
        assert result["chunks"] == {}

        # v2 metadata fields
        assert "has_equations" in meta
        assert "has_code" in meta
        assert "title" in meta
        assert "page_dimensions" in meta

    def test_parse_pdf_element_ids_unique_and_sequential(self, tmp_path):
        items = [
            (_make_mock_text_item("A"), 0),
            (_make_mock_text_item("B"), 0),
            (_make_mock_text_item("C"), 0),
        ]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        ids = [e["element_id"] for e in result["elements"]]
        assert len(ids) == len(set(ids)), "element_ids must be unique"
        assert ids == ["elem_0000", "elem_0001", "elem_0002"]

    def test_parse_pdf_elements_have_required_fields(self, tmp_path):
        items = [(_make_mock_text_item("Test text"), 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        elem = result["elements"][0]
        assert "element_id" in elem
        assert "type" in elem
        assert "content" in elem
        assert "page_number" in elem
        assert "reading_order" in elem

    def test_section_header_sets_hierarchy_level(self, tmp_path):
        header = _make_mock_section_header("Results", level=2, page_no=1)
        items = [(header, 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        elem = result["elements"][0]
        assert elem["type"] == "section_header"
        assert elem["hierarchy_level"] == 2

    def test_title_sets_hierarchy_level_zero(self, tmp_path):
        title = _make_mock_title_item("My Paper", page_no=1)
        items = [(title, 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        elem = result["elements"][0]
        assert elem["type"] == "title"
        assert elem["hierarchy_level"] == 0

    def test_toc_built_from_section_headers(self, tmp_path):
        items = [
            (_make_mock_section_header("Introduction", level=1), 0),
            (_make_mock_text_item("Some intro text"), 0),
            (_make_mock_section_header("Methods", level=1), 0),
        ]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        assert len(result["toc"]) == 2
        assert result["toc"][0]["text"] == "Introduction"
        assert result["toc"][1]["text"] == "Methods"

    def test_toc_includes_title(self, tmp_path):
        items = [(_make_mock_title_item("Deep Learning Survey"), 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        assert len(result["toc"]) == 1
        assert result["toc"][0]["text"] == "Deep Learning Survey"

    def test_metadata_title_from_first_title_element(self, tmp_path):
        items = [(_make_mock_title_item("The Title"), 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        assert result["metadata"]["title"] == "The Title"

    def test_parent_section_set_on_body_element_after_header(self, tmp_path):
        items = [
            (_make_mock_section_header("Introduction", level=1), 0),
            (_make_mock_text_item("Body text here"), 0),
        ]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        body_elem = result["elements"][1]
        assert body_elem["type"] == "text"
        assert body_elem.get("parent_section") == "Introduction"

    def test_caption_linked_to_preceding_table(self, tmp_path):
        table_item = _make_mock_table_item([["A", "B"]], page_no=1)
        caption_item = _make_mock_caption_item("Table 1: Results", page_no=1)
        items = [(table_item, 0), (caption_item, 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        table_elem = result["elements"][0]
        caption_elem = result["elements"][1]
        assert caption_elem.get("refers_to_id") == table_elem["element_id"]
        assert table_elem.get("caption_id") == caption_elem["element_id"]

    def test_page_header_footer_type_mapping(self, tmp_path):
        header = _make_mock_text_item("Page Header", label_name="PAGE_HEADER")
        footer = _make_mock_text_item("Page Footer", label_name="PAGE_FOOTER")
        items = [(header, 0), (footer, 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        types = [e["type"] for e in result["elements"]]
        assert "page_header" in types
        assert "page_footer" in types

    def test_backward_compat_pages_array_present(self, tmp_path):
        items = [(_make_mock_text_item("Text on page 1", page_no=1), 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        assert "pages" in result
        assert isinstance(result["pages"], list)
        assert result["pages"][0]["page_number"] == 1
        assert len(result["pages"][0]["elements"]) == 1

    def test_has_tables_set_when_table_present(self, tmp_path):
        items = [(_make_mock_table_item([["A"]], page_no=1), 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        assert result["metadata"]["has_tables"] is True

    def test_has_equations_set_for_formula_elements(self, tmp_path):
        formula = _make_mock_text_item("E=mc^2", label_name="FORMULA")
        items = [(formula, 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        assert result["metadata"]["has_equations"] is True

    def test_has_code_set_for_code_elements(self, tmp_path):
        code = _make_mock_text_item("print('hello')", label_name="CODE")
        items = [(code, 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        assert result["metadata"]["has_code"] is True

    def test_chunks_is_empty_dict(self, tmp_path):
        items = [(_make_mock_text_item("text"), 0)]
        result = _run_parse_pdf_with_mocks(tmp_path, items)
        assert result["chunks"] == {}

    def test_parse_pdf_missing_docling_raises_runtime_error(self, tmp_path):
        from src.backend.services.parser import parse_pdf
        import builtins

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")
        image_dir = tmp_path / "images"

        original_import = builtins.__import__

        def import_error(name, *args, **kwargs):
            if name.startswith("docling"):
                raise ImportError("No module named 'docling'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=import_error):
            with pytest.raises(RuntimeError, match="docling is not installed"):
                parse_pdf(pdf_path, image_dir)
