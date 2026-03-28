"""
Unit tests for parser service — uses mocked docling to avoid heavy dependency.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_text_item(text: str, page_no: int = 1):
    item = MagicMock()
    item.text = text
    prov = MagicMock()
    prov.page_no = page_no
    bbox = MagicMock()
    bbox.l, bbox.t, bbox.r, bbox.b = 0.0, 0.0, 100.0, 20.0
    prov.bbox = bbox
    item.prov = [prov]
    return item


def _make_mock_table_item(rows: list, page_no: int = 1):
    item = MagicMock()
    item.text = None
    df = MagicMock()
    df.values.tolist.return_value = rows
    item.export_to_dataframe.return_value = df
    item.export_to_markdown.return_value = "| col1 | col2 |\n|------|------|\n| a | b |"
    prov = MagicMock()
    prov.page_no = page_no
    bbox = MagicMock()
    bbox.l, bbox.t, bbox.r, bbox.b = 0.0, 50.0, 100.0, 100.0
    prov.bbox = bbox
    item.prov = [prov]
    return item


class TestLanguageDetection:
    def test_detect_korean(self):
        from src.backend.services.parser import _detect_language
        korean_text = "안녕하세요 이것은 한국어 텍스트입니다"
        assert _detect_language(korean_text) == "ko"

    def test_detect_english(self):
        from src.backend.services.parser import _detect_language
        english_text = "Hello this is an English text document"
        assert _detect_language(english_text) == "en"

    def test_detect_chinese(self):
        from src.backend.services.parser import _detect_language
        chinese_text = "这是中文文本内容测试"
        assert _detect_language(chinese_text) == "zh"

    def test_detect_japanese(self):
        from src.backend.services.parser import _detect_language
        japanese_text = "これは日本語のテキストです"
        assert _detect_language(japanese_text) == "ja"

    def test_empty_text_returns_none(self):
        from src.backend.services.parser import _detect_language
        assert _detect_language("") is None
        assert _detect_language("   ") is None


class TestParsePdf:
    def test_parse_pdf_returns_correct_schema(self, tmp_path):
        """parse_pdf returns the expected internal schema dict."""
        from src.backend.services.parser import parse_pdf

        # Create a minimal fake PDF file (bytes just need to exist for the mock)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake content")
        image_dir = tmp_path / "images"

        mock_text_item = _make_mock_text_item("Hello World", page_no=1)
        mock_korean_text = _make_mock_text_item("안녕하세요", page_no=1)
        mock_table = _make_mock_table_item([["A", "B"], ["1", "2"]], page_no=2)

        mock_doc = MagicMock()
        mock_doc.iterate_items.return_value = [
            (mock_text_item, 0),
            (mock_korean_text, 0),
            (mock_table, 0),
        ]

        mock_conv_result = MagicMock()
        mock_conv_result.document = mock_doc

        mock_converter_instance = MagicMock()
        mock_converter_instance.convert.return_value = mock_conv_result

        with patch.dict("sys.modules", {
            "docling": MagicMock(),
            "docling.document_converter": MagicMock(),
            "docling.datamodel": MagicMock(),
            "docling.datamodel.base_models": MagicMock(),
            "docling.datamodel.pipeline_options": MagicMock(),
            "docling.datamodel.document": MagicMock(),
            "docling.backend": MagicMock(),
            "docling.backend.pypdfium2_backend": MagicMock(),
        }):
            import docling.datamodel.document as doc_module
            from unittest.mock import MagicMock as MM

            TextItemClass = MM()
            TableItemClass = MM()
            PictureItemClass = MM()

            # Make isinstance checks work
            mock_text_item.__class__ = type("TextItem", (), {})
            mock_korean_text.__class__ = type("TextItem", (), {})
            mock_table.__class__ = type("TableItem", (), {})

            doc_module.TextItem = mock_text_item.__class__
            doc_module.TableItem = mock_table.__class__
            doc_module.PictureItem = type("PictureItem", (), {})

            import importlib
            import src.backend.services.parser as parser_module
            importlib.reload(parser_module)

            with patch("src.backend.services.parser.DocumentConverter", return_value=mock_converter_instance, create=True):
                with patch("src.backend.services.parser.PdfFormatOption", create=True):
                    with patch("src.backend.services.parser.InputFormat", create=True):
                        with patch("src.backend.services.parser.PdfPipelineOptions", create=True):
                            with patch("src.backend.services.parser.PyPdfiumDocumentBackend", create=True):
                                result = parser_module.parse_pdf(pdf_path, image_dir)

        assert "pages" in result
        assert "metadata" in result
        assert isinstance(result["pages"], list)
        meta = result["metadata"]
        assert "total_pages" in meta
        assert "languages" in meta
        assert "has_tables" in meta
        assert "has_images" in meta

    def test_parse_pdf_missing_docling_raises_runtime_error(self, tmp_path):
        """parse_pdf raises RuntimeError when docling is not installed."""
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
