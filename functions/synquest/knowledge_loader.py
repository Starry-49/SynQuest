"""Reusable knowledge-source loading for SynQuest.

Supports structured JSON plus lightweight text extraction from:
- .json
- .md
- .txt
- .html / .htm
- .docx
"""

from __future__ import annotations

import json
import re
import zipfile
from html import unescape
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SUPPORTED_SUFFIXES = {".json", ".md", ".txt", ".html", ".htm", ".docx"}
WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower())
    return slug.strip("-") or "entry"


def _read_plain_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_html_text(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    stripped = re.sub(r"<[^>]+>", " ", unescape(html))
    return re.sub(r"\n{3,}", "\n\n", stripped)


def _read_docx_text(path: Path) -> str:
    paragraphs: list[str] = []
    with zipfile.ZipFile(path) as archive:
        with archive.open("word/document.xml") as document:
            root = ElementTree.parse(document).getroot()

    for paragraph in root.findall(".//w:p", WORD_NAMESPACE):
        texts = [node.text for node in paragraph.findall(".//w:t", WORD_NAMESPACE) if node.text]
        joined = "".join(texts).strip()
        if joined:
            paragraphs.append(joined)
    return "\n".join(paragraphs)


def read_knowledge_text(path: str | Path) -> str:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported knowledge source: {suffix}")
    if suffix == ".json":
        return json.dumps(json.loads(source.read_text(encoding="utf-8")), ensure_ascii=False, indent=2)
    if suffix in {".md", ".txt"}:
        return _read_plain_text(source)
    if suffix in {".html", ".htm"}:
        return _read_html_text(source)
    if suffix == ".docx":
        return _read_docx_text(source)
    raise ValueError(f"Unsupported knowledge source: {suffix}")


def _facts_from_lines(title: str, lines: list[str]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for line in lines:
        cleaned = line.strip(" -\t")
        if not cleaned:
            continue
        facts.append(
            {
                "question": f"关于“{title}”，下列哪项描述是正确的？",
                "answer": cleaned.strip("。 "),
                "explanation": cleaned,
                "distractors": [],
            }
        )
    return facts


def _normalize_unstructured_text(text: str, source_name: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current_title = source_name
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines, current_title
        if not current_lines:
            return
        entries.append(
            {
                "id": slugify(current_title),
                "module": "Imported Source",
                "title": current_title,
                "summary": current_lines[0][:120],
                "keywords": [],
                "distractors": [],
                "facts": _facts_from_lines(current_title, current_lines),
            }
        )
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            flush()
            current_title = line.lstrip("# ").strip() or source_name
            continue
        current_lines.append(line)

    flush()
    if entries:
        return entries

    compact_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if compact_lines:
        return [
            {
                "id": slugify(source_name),
                "module": "Imported Source",
                "title": source_name,
                "summary": compact_lines[0][:120],
                "keywords": [],
                "distractors": [],
                "facts": _facts_from_lines(source_name, compact_lines),
            }
        ]
    return []


def load_knowledge_entries(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".json":
        raw = json.loads(source.read_text(encoding="utf-8"))
        entries = raw["entries"] if isinstance(raw, dict) and "entries" in raw else raw
        if not isinstance(entries, list):
            raise ValueError("JSON knowledge base must be a list or contain an `entries` list.")
        return entries

    text = read_knowledge_text(source)
    return _normalize_unstructured_text(text, source.stem.replace("_", " ").replace("-", " "))


def inspect_knowledge_source(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    text = read_knowledge_text(source)
    entries = load_knowledge_entries(source)
    facts = sum(len(entry.get("facts", [])) for entry in entries)
    return {
        "path": str(source),
        "suffix": source.suffix.lower(),
        "characters": len(text),
        "entries": len(entries),
        "facts": facts,
        "titleSamples": [entry.get("title", "Untitled") for entry in entries[:5]],
    }
