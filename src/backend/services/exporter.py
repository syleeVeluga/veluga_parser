"""
Exporter service — converts parsed result dict to JSON, Markdown, and plain text files.
"""
import json
from pathlib import Path


def to_json(result: dict, output_path: Path) -> Path:
    """Write result dict as formatted JSON file. Returns output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return output_path


def _table_rows_to_gfm(rows: list) -> str:
    """Convert list-of-lists to GFM table markdown string."""
    if not rows:
        return ""
    lines = []
    header = [str(cell) for cell in rows[0]]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows[1:]:
        cells = [str(cell) for cell in row]
        # Pad to match header width
        while len(cells) < len(header):
            cells.append("")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def to_markdown(result: dict, output_path: Path) -> Path:
    """Convert parsed result to Markdown file with GFM tables. Returns output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    pages = result.get("pages", [])
    meta = result.get("metadata", {})

    lines.append("# Parsed Document")
    lines.append("")
    if meta.get("languages"):
        lines.append(f"**Languages:** {', '.join(meta['languages'])}")
    lines.append(f"**Pages:** {meta.get('total_pages', len(pages))}")
    lines.append("")

    for page in pages:
        page_num = page.get("page_number", "?")
        lines.append(f"---")
        lines.append(f"## Page {page_num}")
        lines.append("")
        for elem in page.get("elements", []):
            etype = elem.get("type")
            if etype == "text":
                content = elem.get("content", "").strip()
                if content:
                    lines.append(content)
                    lines.append("")
            elif etype == "table":
                rows = elem.get("rows")
                if rows:
                    lines.append(_table_rows_to_gfm(rows))
                else:
                    content = elem.get("content", "").strip()
                    if content:
                        lines.append(content)
                lines.append("")
            elif etype == "image":
                img_path = elem.get("path", "")
                lines.append(f"![Image]({img_path})")
                lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


def to_text(result: dict, output_path: Path) -> Path:
    """Extract plain text from parsed result preserving reading order. Returns output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    pages = result.get("pages", [])

    for page in pages:
        page_num = page.get("page_number", "?")
        lines.append(f"=== Page {page_num} ===")
        for elem in page.get("elements", []):
            etype = elem.get("type")
            if etype == "text":
                content = elem.get("content", "").strip()
                if content:
                    lines.append(content)
            elif etype == "table":
                rows = elem.get("rows")
                if rows:
                    for row in rows:
                        lines.append("\t".join(str(c) for c in row))
                else:
                    content = elem.get("content", "").strip()
                    if content:
                        lines.append(content)
            elif etype == "image":
                lines.append(f"[Image: {elem.get('path', '')}]")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


def to_chunks_json(result: dict, output_path: Path) -> Path:
    """Write the chunks dict to a standalone JSON file. Returns output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chunks = result.get("chunks", {})
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    return output_path


def generate_all_exports(result: dict, job_dir: Path) -> dict:
    """
    Generate all export files and return a dict with paths.

    Returns:
        {"json_path": str, "markdown_path": str, "text_path": str, "chunks_path": str}
    """
    json_path = to_json(result, job_dir / "result.json")
    md_path = to_markdown(result, job_dir / "result.md")
    txt_path = to_text(result, job_dir / "result.txt")
    chunks_path = to_chunks_json(result, job_dir / "chunks.json")
    return {
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "text_path": str(txt_path),
        "chunks_path": str(chunks_path),
    }
