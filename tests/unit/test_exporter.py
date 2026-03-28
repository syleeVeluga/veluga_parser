"""
Unit tests for exporter service.
"""
import json
from pathlib import Path

import pytest


SAMPLE_RESULT = {
    "pages": [
        {
            "page_number": 1,
            "elements": [
                {"type": "text", "content": "안녕하세요", "language": "ko"},
                {"type": "text", "content": "Hello World", "language": "en"},
                {
                    "type": "table",
                    "rows": [["Name", "Value"], ["Alpha", "1"], ["Beta", "2"]],
                    "content": "| Name | Value |\n|---|---|\n| Alpha | 1 |",
                },
                {"type": "image", "path": "/uploads/test/images/img0.png", "content": ""},
            ],
        },
        {
            "page_number": 2,
            "elements": [
                {"type": "text", "content": "Page two text", "language": "en"},
            ],
        },
    ],
    "metadata": {
        "total_pages": 2,
        "languages": ["ko", "en"],
        "has_tables": True,
        "has_images": True,
    },
}


class TestToJson:
    def test_creates_valid_json_file(self, tmp_path):
        from src.backend.services.exporter import to_json
        out = tmp_path / "result.json"
        result = to_json(SAMPLE_RESULT, out)
        assert result == out
        assert out.exists()
        parsed = json.loads(out.read_text(encoding="utf-8"))
        assert parsed["metadata"]["total_pages"] == 2
        assert "pages" in parsed

    def test_preserves_unicode(self, tmp_path):
        from src.backend.services.exporter import to_json
        out = tmp_path / "result.json"
        to_json(SAMPLE_RESULT, out)
        content = out.read_text(encoding="utf-8")
        assert "안녕하세요" in content

    def test_creates_parent_dirs(self, tmp_path):
        from src.backend.services.exporter import to_json
        out = tmp_path / "deep" / "nested" / "result.json"
        to_json(SAMPLE_RESULT, out)
        assert out.exists()


class TestTableToGfm:
    def test_single_row_is_header_only(self):
        from src.backend.services.exporter import _table_rows_to_gfm
        result = _table_rows_to_gfm([["A", "B"]])
        assert "| A | B |" in result
        assert "---" in result  # separator row contains dashes (GFM style)

    def test_two_rows_header_and_data(self):
        from src.backend.services.exporter import _table_rows_to_gfm
        result = _table_rows_to_gfm([["Name", "Value"], ["Alpha", "1"]])
        lines = result.split("\n")
        assert lines[0] == "| Name | Value |"
        assert "---" in lines[1]
        assert "Alpha" in lines[2]

    def test_empty_rows_returns_empty(self):
        from src.backend.services.exporter import _table_rows_to_gfm
        assert _table_rows_to_gfm([]) == ""


class TestToMarkdown:
    def test_creates_markdown_file(self, tmp_path):
        from src.backend.services.exporter import to_markdown
        out = tmp_path / "result.md"
        result = to_markdown(SAMPLE_RESULT, out)
        assert result == out
        assert out.exists()

    def test_contains_gfm_table(self, tmp_path):
        from src.backend.services.exporter import to_markdown
        out = tmp_path / "result.md"
        to_markdown(SAMPLE_RESULT, out)
        content = out.read_text(encoding="utf-8")
        assert "| Name | Value |" in content
        assert "| Alpha | 1 |" in content
        assert "|" in content

    def test_contains_korean_text(self, tmp_path):
        from src.backend.services.exporter import to_markdown
        out = tmp_path / "result.md"
        to_markdown(SAMPLE_RESULT, out)
        content = out.read_text(encoding="utf-8")
        assert "안녕하세요" in content

    def test_contains_image_reference(self, tmp_path):
        from src.backend.services.exporter import to_markdown
        out = tmp_path / "result.md"
        to_markdown(SAMPLE_RESULT, out)
        content = out.read_text(encoding="utf-8")
        assert "![Image]" in content

    def test_contains_page_headers(self, tmp_path):
        from src.backend.services.exporter import to_markdown
        out = tmp_path / "result.md"
        to_markdown(SAMPLE_RESULT, out)
        content = out.read_text(encoding="utf-8")
        assert "## Page 1" in content
        assert "## Page 2" in content


class TestToText:
    def test_creates_text_file(self, tmp_path):
        from src.backend.services.exporter import to_text
        out = tmp_path / "result.txt"
        result = to_text(SAMPLE_RESULT, out)
        assert result == out
        assert out.exists()

    def test_contains_all_text_content(self, tmp_path):
        from src.backend.services.exporter import to_text
        out = tmp_path / "result.txt"
        to_text(SAMPLE_RESULT, out)
        content = out.read_text(encoding="utf-8")
        assert "안녕하세요" in content
        assert "Hello World" in content
        assert "Page two text" in content

    def test_contains_page_markers(self, tmp_path):
        from src.backend.services.exporter import to_text
        out = tmp_path / "result.txt"
        to_text(SAMPLE_RESULT, out)
        content = out.read_text(encoding="utf-8")
        assert "=== Page 1 ===" in content
        assert "=== Page 2 ===" in content

    def test_table_rows_tab_separated(self, tmp_path):
        from src.backend.services.exporter import to_text
        out = tmp_path / "result.txt"
        to_text(SAMPLE_RESULT, out)
        content = out.read_text(encoding="utf-8")
        assert "Name\tValue" in content


class TestGenerateAllExports:
    def test_generates_all_three_files(self, tmp_path):
        from src.backend.services.exporter import generate_all_exports
        job_dir = tmp_path / "job123"
        paths = generate_all_exports(SAMPLE_RESULT, job_dir)
        assert "json_path" in paths
        assert "markdown_path" in paths
        assert "text_path" in paths
        assert Path(paths["json_path"]).exists()
        assert Path(paths["markdown_path"]).exists()
        assert Path(paths["text_path"]).exists()
