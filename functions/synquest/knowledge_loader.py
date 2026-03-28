"""Reusable knowledge-source loading and normalization for SynQuest.

Supports structured JSON plus extraction/normalization from:
- .json
- .md
- .txt
- .html / .htm
- .docx
- .pdf
- .pptx
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from collections import Counter, defaultdict
from html import unescape
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SUPPORTED_SUFFIXES = {".json", ".md", ".txt", ".html", ".htm", ".docx", ".pdf", ".pptx"}
WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
PPT_NAMESPACE = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
DEFAULT_STOPWORDS = {
    "一个",
    "一些",
    "一种",
    "一种",
    "不是",
    "主要",
    "以及",
    "以上",
    "以下",
    "内容",
    "包括",
    "包含",
    "可以",
    "这个",
    "这里",
    "相关",
    "通过",
    "进行",
    "用于",
    "需要",
    "说明",
    "作用",
    "研究",
    "方法",
    "问题",
    "分析",
    "数据",
    "课程",
    "课时",
    "example",
    "portal",
    "slide",
    "slides",
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "using",
}
PDF_ALGORITHMS = [
    "pdftotext_raw_order_extraction",
    "pdftotext_layout_preserving_title_detection",
    "pdfinfo_document_metadata_parsing",
    "pdfimages_page_level_image_census",
    "repeated_header_footer_suppression",
    "duplicate_slide_fingerprint_deduplication",
    "heuristic_page_title_detection",
    "keyword_weighting_and_fact_segmentation",
]
PPTX_ALGORITHMS = [
    "ooxml_zip_parsing",
    "slide_title_placeholder_detection",
    "speaker_notes_extraction",
    "slide_image_count_from_shape_tree",
    "keyword_weighting_and_fact_segmentation",
]
QUESTION_EXTRACTION_FIELDS = {
    "question",
    "answer",
    "explanation",
    "difficulty",
    "type",
    "distractors",
}


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower())
    return slug.strip("-") or "entry"


def _read_plain_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_html_text(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
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


def _run_command(args: list[str], *, optional: bool = False) -> str:
    if not shutil.which(args[0]):
        if optional:
            return ""
        raise RuntimeError(f"Missing required command for SynQuest extraction: {args[0]}")
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    if result.returncode != 0:
        if optional:
            return ""
        raise RuntimeError(result.stderr.strip() or f"Command failed: {' '.join(args)}")
    return result.stdout


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_line_for_hash(line: str) -> str:
    return re.sub(r"\s+", "", line).strip()


def _clean_unstructured_line(line: str) -> str:
    cleaned = _normalize_space(line)
    cleaned = cleaned.strip("•●▪■◆★·-–—:：;；|")
    return cleaned


def _looks_like_contact(line: str) -> bool:
    lowered = line.lower()
    return any(token in lowered for token in ("email:", "@", "wx:", "qq:", "电话", "tel"))


def _looks_like_footer(line: str) -> bool:
    lowered = line.lower()
    if "all rights reserved" in lowered or "copyright" in lowered:
        return True
    if "未经同意" in line and ("转载" in line or "发布" in line):
        return True
    if re.search(r"(?:^|\s)(?:page|页码?)\s*\d+(?:\s*/\s*\d+)?(?:$|\s)", lowered):
        return True
    return False


def _tokenize_for_keywords(text: str) -> list[str]:
    tokens: list[str] = []
    for ascii_token in re.findall(r"[A-Za-z][A-Za-z0-9\-/+.]{1,}", text):
        lowered = ascii_token.lower()
        if lowered not in DEFAULT_STOPWORDS:
            tokens.append(ascii_token)

    for cjk_group in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        compact = cjk_group.strip()
        if len(compact) <= 2:
            if compact not in DEFAULT_STOPWORDS:
                tokens.append(compact)
            continue
        bigrams = [compact[index : index + 2] for index in range(len(compact) - 1)]
        for token in bigrams:
            if token not in DEFAULT_STOPWORDS:
                tokens.append(token)
        if compact not in DEFAULT_STOPWORDS and len(compact) <= 10:
            tokens.append(compact)
    return tokens


def _extract_keywords(*segments: str, limit: int = 8) -> list[str]:
    counter: Counter[str] = Counter()
    for index, segment in enumerate(segments):
        weight = 3 if index == 0 else 2 if index == 1 else 1
        for token in _tokenize_for_keywords(segment):
            if token.isdigit():
                continue
            counter[token] += weight

    keywords: list[str] = []
    for token, _score in counter.most_common():
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= limit:
            break
    return keywords


def _guess_answer_from_line(line: str) -> tuple[str, str]:
    stripped = _clean_unstructured_line(line).strip("。")

    match = re.search(r"([A-Za-z0-9\u4e00-\u9fff（）()\-+/]+)[：:]\s*(.+)", stripped)
    if match:
        subject = match.group(1).strip()
        answer = match.group(2).strip("。 ")
        if 0 < len(answer) <= 80:
            return f"“{subject}”对应的内容是？", answer

    match = re.search(r"(.+?)(?:是|指的是|可定义为)(.+)", stripped)
    if match:
        subject = match.group(1).strip("：:，, ")
        answer = match.group(2).strip("。 ，,")
        if 1 < len(subject) <= 40 and 0 < len(answer) <= 80:
            return f"关于“{subject}”，下列哪项表述正确？", answer

    match = re.search(r"(.+?)(?:包括|包含)(.+)", stripped)
    if match:
        subject = match.group(1).strip("：:，, ")
        answer = match.group(2).strip("。 ，,")
        if 1 < len(subject) <= 40 and 0 < len(answer) <= 80:
            return f"“{subject}”包括下列哪项内容？", answer

    numeric_match = re.search(r"(\d{4}年|\d+(?:\.\d+)?\s*(?:bp|kb|Mb|Gb|cM|cR|%|倍|次|个))", stripped)
    if numeric_match:
        return "根据知识库内容，下列哪个时间或数值是正确的？", numeric_match.group(1).strip()

    return "", stripped


def _line_to_fact(title: str, line: str, keywords: list[str]) -> dict[str, Any]:
    prompt, answer = _guess_answer_from_line(line)
    question = prompt or f"关于“{title}”，下列哪项表述与知识库一致？"
    return {
        "question": question,
        "answer": answer,
        "explanation": line,
        "distractors": [],
        "keywords": keywords[:4],
    }


def _facts_from_lines(title: str, lines: list[str], keywords: list[str]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for line in lines:
        cleaned = _clean_unstructured_line(line)
        if not cleaned or len(cleaned) < 2:
            continue
        facts.append(_line_to_fact(title, cleaned, keywords))
    return facts


def _normalize_unstructured_text(text: str, source_name: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current_title = source_name
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines, current_title
        body = [_clean_unstructured_line(line) for line in current_lines if _clean_unstructured_line(line)]
        if not body:
            return
        keywords = _extract_keywords(current_title, body[0], " ".join(body[:6]))
        entries.append(
            {
                "id": slugify(current_title),
                "module": current_title.split("►", 1)[0].strip() if "►" in current_title else "Imported Source",
                "title": current_title,
                "summary": body[0][:120],
                "keywords": keywords,
                "distractors": [],
                "facts": _facts_from_lines(current_title, body, keywords),
            }
        )
        current_lines = []

    for raw_line in text.splitlines():
        line = _clean_unstructured_line(raw_line)
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

    compact_lines = [_clean_unstructured_line(line) for line in text.splitlines() if _clean_unstructured_line(line)]
    if compact_lines:
        keywords = _extract_keywords(source_name, compact_lines[0], " ".join(compact_lines[:8]))
        return [
            {
                "id": slugify(source_name),
                "module": "Imported Source",
                "title": source_name,
                "summary": compact_lines[0][:120],
                "keywords": keywords,
                "distractors": [],
                "facts": _facts_from_lines(source_name, compact_lines, keywords),
            }
        ]
    return []


def _parse_pdfinfo(output: str) -> dict[str, Any]:
    info: dict[str, Any] = {}
    for raw_line in output.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        info[key.strip()] = value.strip()
    return info


def _parse_pdfimages(output: str) -> dict[int, int]:
    page_counts: defaultdict[int, int] = defaultdict(int)
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("page") or line.startswith("-"):
            continue
        parts = line.split()
        if len(parts) < 3 or not parts[0].isdigit():
            continue
        if parts[2] == "smask":
            continue
        page_counts[int(parts[0])] += 1
    return dict(page_counts)


def _extract_pdf_payload(path: Path) -> dict[str, Any]:
    layout_text = _run_command(["pdftotext", "-layout", str(path), "-"])
    raw_text = _run_command(["pdftotext", "-raw", str(path), "-"])
    info_output = _run_command(["pdfinfo", str(path)], optional=True)
    image_output = _run_command(["pdfimages", "-list", str(path)], optional=True)
    return {
        "layoutPages": layout_text.split("\f"),
        "rawPages": raw_text.split("\f"),
        "info": _parse_pdfinfo(info_output),
        "imageCounts": _parse_pdfimages(image_output),
        "algorithms": PDF_ALGORITHMS,
    }


def _slide_shape_texts(root: ElementTree.Element) -> tuple[list[str], list[str], int]:
    titles: list[str] = []
    bodies: list[str] = []
    pictures = len(root.findall(".//p:pic", PPT_NAMESPACE))

    for shape in root.findall(".//p:sp", PPT_NAMESPACE):
        texts = [
            node.text.strip()
            for node in shape.findall(".//a:t", PPT_NAMESPACE)
            if node.text and node.text.strip()
        ]
        if not texts:
            continue
        content = _normalize_space(" ".join(texts))
        placeholder = shape.find(".//p:ph", PPT_NAMESPACE)
        placeholder_type = placeholder.get("type") if placeholder is not None else ""
        if placeholder_type in {"title", "ctrTitle", "subTitle"}:
            titles.append(content)
        else:
            bodies.append(content)
    return titles, bodies, pictures


def _notes_text(root: ElementTree.Element) -> list[str]:
    notes: list[str] = []
    for paragraph in root.findall(".//a:p", PPT_NAMESPACE):
        texts = [node.text.strip() for node in paragraph.findall(".//a:t", PPT_NAMESPACE) if node.text and node.text.strip()]
        if texts:
            notes.append(_normalize_space(" ".join(texts)))
    return notes


def _extract_pptx_payload(path: Path) -> dict[str, Any]:
    slides: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            (name for name in archive.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name)),
            key=lambda name: int(re.search(r"slide(\d+)\.xml$", name).group(1)),
        )

        for slide_name in slide_names:
            slide_number = int(re.search(r"slide(\d+)\.xml$", slide_name).group(1))
            slide_root = ElementTree.fromstring(archive.read(slide_name))
            title_blocks, body_blocks, picture_count = _slide_shape_texts(slide_root)
            notes_name = f"ppt/notesSlides/notesSlide{slide_number}.xml"
            notes_blocks: list[str] = []
            if notes_name in archive.namelist():
                notes_root = ElementTree.fromstring(archive.read(notes_name))
                notes_blocks = _notes_text(notes_root)

            slides.append(
                {
                    "number": slide_number,
                    "titleBlocks": title_blocks,
                    "bodyBlocks": body_blocks,
                    "notesBlocks": notes_blocks,
                    "imageCount": picture_count,
                }
            )

    return {
        "slides": slides,
        "algorithms": PPTX_ALGORITHMS,
    }


def _line_fingerprint(lines: list[str]) -> tuple[str, ...]:
    return tuple(_normalize_line_for_hash(line) for line in lines if _normalize_line_for_hash(line))


def _should_join_lines(previous: str, current: str) -> bool:
    prev = previous.strip()
    curr = current.strip()
    if not prev or not curr:
        return False
    if prev.endswith(("（", "(", "：", ":", "、", "/", "-", "→")):
        return True
    if curr[:1] in {"）", ")", "、", "，", ",", "；", ";"}:
        return True
    if len(prev) < 18 and len(curr) < 24 and not re.search(r"[。！？!?]$", prev):
        return True
    if re.match(r"^[a-z0-9%/+\-]", curr):
        return True
    return False


def _merge_wrapped_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for raw_line in lines:
        line = _clean_unstructured_line(raw_line)
        if not line:
            continue
        if merged and _should_join_lines(merged[-1], line):
            merged[-1] = _normalize_space(f"{merged[-1]} {line}")
        else:
            merged.append(line)
    return merged


def _collect_repeated_lines(pages: list[list[str]]) -> set[str]:
    counter: Counter[str] = Counter()
    for lines in pages:
        unique_lines = {_normalize_space(line) for line in lines if len(_normalize_space(line)) >= 8}
        counter.update(unique_lines)

    repeated: set[str] = set()
    threshold = max(4, int(len(pages) * 0.12))
    for line, count in counter.items():
        if count >= threshold and (_looks_like_footer(line) or len(line) > 16):
            repeated.add(line)
    return repeated


def _clean_page_lines(lines: list[str], repeated_lines: set[str]) -> list[str]:
    cleaned: list[str] = []
    for raw_line in lines:
        line = _clean_unstructured_line(raw_line)
        if not line:
            continue
        normalized = _normalize_space(line)
        if normalized in repeated_lines:
            continue
        if _looks_like_contact(normalized) or _looks_like_footer(normalized):
            continue
        if re.fullmatch(r"[?？•·●▪■◆★\-–—]+", normalized):
            continue
        cleaned.append(normalized)
    return cleaned


def _score_title_candidate(line: str, position: int) -> float:
    score = 0.0
    length = len(line)
    if 2 <= length <= 36:
        score += 4.0
    elif length <= 60:
        score += 2.0
    else:
        score -= 2.0
    if position == 0:
        score += 1.6
    elif position == 1:
        score += 1.1
    elif position <= 3:
        score += 0.5
    if "第" in line and ("讲" in line or "章" in line):
        score += 3.2
    if "►" in line or "内容概要" in line:
        score += 2.8
    if re.search(r"[A-Za-z\u4e00-\u9fff]", line):
        score += 1.0
    if _looks_like_contact(line):
        score -= 5.0
    if line.endswith("..."):
        score -= 1.0
    return score


def _select_title(lines: list[str], fallback: str) -> str:
    if not lines:
        return fallback
    candidates = lines[:6]
    best_line = max(candidates, key=lambda item: _score_title_candidate(item, candidates.index(item)))
    return best_line or fallback


def _infer_module(title: str, previous_module: str, source_name: str) -> str:
    stripped = title.strip()
    if "►" in stripped:
        return stripped.split("►", 1)[0].strip() or previous_module
    match = re.search(r"第\d+讲(?:（\d+）)?\s*([^\s].+)", stripped)
    if match:
        return match.group(1).strip()
    match = re.search(r"第[一二三四五六七八九十0-9]+章\s*([^\s].+)", stripped)
    if match:
        return match.group(1).strip()
    if "内容概要" in stripped or "引言" in stripped:
        return previous_module
    return previous_module or source_name


def _normalize_pdf_entries(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    payload = _extract_pdf_payload(path)
    layout_pages = [page for page in payload["layoutPages"] if page.strip()]
    raw_pages = [page for page in payload["rawPages"] if page.strip()]
    page_count = int(payload["info"].get("Pages", 0) or max(len(layout_pages), len(raw_pages)))

    raw_line_pages = [[line for line in page.splitlines() if line.strip()] for page in raw_pages[:page_count]]
    repeated_lines = _collect_repeated_lines(raw_line_pages)

    entries: list[dict[str, Any]] = []
    seen_fingerprints: dict[tuple[str, ...], int] = {}
    current_module = path.stem.replace("_", " ").replace("-", " ")

    for page_number in range(1, page_count + 1):
        raw_lines = raw_line_pages[page_number - 1] if page_number - 1 < len(raw_line_pages) else []
        layout_lines = [line for line in layout_pages[page_number - 1].splitlines() if line.strip()] if page_number - 1 < len(layout_pages) else []
        cleaned_raw = _merge_wrapped_lines(_clean_page_lines(raw_lines, repeated_lines))
        cleaned_layout = _clean_page_lines(layout_lines, repeated_lines)
        title = _select_title(cleaned_layout or cleaned_raw, f"{path.stem} page {page_number}")
        body = [
            line
            for line in cleaned_raw
            if _normalize_line_for_hash(line) != _normalize_line_for_hash(title)
        ]

        if not title and not body:
            continue

        current_module = _infer_module(title, current_module, path.stem)
        if not body and cleaned_layout:
            body = [
                line
                for line in cleaned_layout
                if _normalize_line_for_hash(line) != _normalize_line_for_hash(title)
            ]
        if not body:
            body = [title]

        fingerprint = _line_fingerprint([title, *body[:12]])
        if fingerprint in seen_fingerprints:
            entries[seen_fingerprints[fingerprint]]["sourcePages"].append(page_number)
            entries[seen_fingerprints[fingerprint]]["visualSignals"]["imageCount"] = max(
                entries[seen_fingerprints[fingerprint]]["visualSignals"]["imageCount"],
                payload["imageCounts"].get(page_number, 0),
            )
            continue

        keywords = _extract_keywords(title, current_module, " ".join(body[:8]))
        entry = {
            "id": f"{slugify(path.stem)}-p{page_number:04d}",
            "module": current_module,
            "title": title,
            "summary": body[0][:120],
            "keywords": keywords,
            "distractors": [],
            "facts": _facts_from_lines(title, body[:14], keywords),
            "sourcePages": [page_number],
            "visualSignals": {
                "imageCount": payload["imageCounts"].get(page_number, 0),
                "pageKind": "pdf_slide",
            },
        }
        if entry["facts"]:
            seen_fingerprints[fingerprint] = len(entries)
            entries.append(entry)

    info = payload["info"]
    meta = {
        "sourcePath": str(path),
        "sourceType": "pdf",
        "sourcePages": page_count,
        "uniqueEntries": len(entries),
        "creator": info.get("Creator", ""),
        "pageSize": info.get("Page size", ""),
        "algorithms": payload["algorithms"],
    }
    text = "\n\n".join("\n".join(page.splitlines()) for page in raw_pages if page.strip())
    return entries, meta, text


def _normalize_pptx_entries(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    payload = _extract_pptx_payload(path)
    entries: list[dict[str, Any]] = []
    current_module = path.stem.replace("_", " ").replace("-", " ")
    seen_fingerprints: dict[tuple[str, ...], int] = {}
    text_chunks: list[str] = []

    for slide in payload["slides"]:
        title_blocks = [_clean_unstructured_line(item) for item in slide["titleBlocks"] if _clean_unstructured_line(item)]
        body_blocks = [_clean_unstructured_line(item) for item in slide["bodyBlocks"] if _clean_unstructured_line(item)]
        notes_blocks = [_clean_unstructured_line(item) for item in slide["notesBlocks"] if _clean_unstructured_line(item)]
        title = title_blocks[0] if title_blocks else _select_title(body_blocks, f"{path.stem} slide {slide['number']}")
        combined_body = _merge_wrapped_lines(body_blocks + [note for note in notes_blocks if note not in body_blocks])
        current_module = _infer_module(title, current_module, path.stem)

        fingerprint = _line_fingerprint([title, *combined_body[:12]])
        if fingerprint in seen_fingerprints:
            entries[seen_fingerprints[fingerprint]]["sourceSlides"].append(slide["number"])
            entries[seen_fingerprints[fingerprint]]["visualSignals"]["imageCount"] = max(
                entries[seen_fingerprints[fingerprint]]["visualSignals"]["imageCount"],
                slide["imageCount"],
            )
            continue

        if not combined_body:
            combined_body = [title]
        keywords = _extract_keywords(title, current_module, " ".join(combined_body[:8]))
        entry = {
            "id": f"{slugify(path.stem)}-s{slide['number']:04d}",
            "module": current_module,
            "title": title,
            "summary": combined_body[0][:120],
            "keywords": keywords,
            "distractors": [],
            "facts": _facts_from_lines(title, combined_body[:14], keywords),
            "sourceSlides": [slide["number"]],
            "visualSignals": {
                "imageCount": slide["imageCount"],
                "pageKind": "pptx_slide",
            },
        }
        if entry["facts"]:
            seen_fingerprints[fingerprint] = len(entries)
            entries.append(entry)
            text_chunks.append("\n".join([title, *combined_body]))

    meta = {
        "sourcePath": str(path),
        "sourceType": "pptx",
        "sourceSlides": len(payload["slides"]),
        "uniqueEntries": len(entries),
        "algorithms": payload["algorithms"],
    }
    return entries, meta, "\n\n".join(text_chunks)


def build_knowledge_base(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()

    if suffix == ".json":
        raw = json.loads(source.read_text(encoding="utf-8"))
        entries = raw["entries"] if isinstance(raw, dict) and "entries" in raw else raw
        if not isinstance(entries, list):
            raise ValueError("JSON knowledge base must be a list or contain an `entries` list.")
        return {
            "meta": {
                "sourcePath": str(source),
                "sourceType": "json",
                "algorithms": ["structured_json_passthrough"],
            },
            "entries": entries,
        }

    if suffix in {".md", ".txt", ".html", ".htm", ".docx"}:
        text = read_knowledge_text(source)
        entries = _normalize_unstructured_text(text, source.stem.replace("_", " ").replace("-", " "))
        return {
            "meta": {
                "sourcePath": str(source),
                "sourceType": suffix.lstrip("."),
                "algorithms": ["text_section_segmentation", "keyword_weighting_and_fact_segmentation"],
            },
            "entries": entries,
        }

    if suffix == ".pdf":
        entries, meta, _text = _normalize_pdf_entries(source)
        return {"meta": meta, "entries": entries}

    if suffix == ".pptx":
        entries, meta, _text = _normalize_pptx_entries(source)
        return {"meta": meta, "entries": entries}

    raise ValueError(f"Unsupported knowledge source: {suffix}")


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
    if suffix == ".pdf":
        return _normalize_pdf_entries(source)[2]
    if suffix == ".pptx":
        return _normalize_pptx_entries(source)[2]
    raise ValueError(f"Unsupported knowledge source: {suffix}")


def load_knowledge_entries(path: str | Path) -> list[dict[str, Any]]:
    return build_knowledge_base(path)["entries"]


def inspect_knowledge_source(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    text = read_knowledge_text(source)
    payload = build_knowledge_base(source)
    entries = payload["entries"]
    facts = sum(len(entry.get("facts", [])) for entry in entries)
    titles = [entry.get("title", "Untitled") for entry in entries[:5]]
    meta = payload.get("meta", {})
    return {
        "path": str(source),
        "suffix": source.suffix.lower(),
        "characters": len(text),
        "entries": len(entries),
        "facts": facts,
        "titleSamples": titles,
        "algorithms": meta.get("algorithms", []),
        "sourceType": meta.get("sourceType", source.suffix.lower().lstrip(".")),
        "extra": {
            key: value
            for key, value in meta.items()
            if key not in {"algorithms", "sourceType", "sourcePath"}
        },
    }
