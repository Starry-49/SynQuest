"""Independent figure-question track for image-backed SynQuest items."""

from __future__ import annotations

import json
import random
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional, Union

from .knowledge_loader import build_knowledge_base


ROOT = Path(__file__).resolve().parents[2]
LETTERS = ["A", "B", "C", "D"]
SUPPORTED_FIGURE_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg"}
GENERIC_TITLES = {
    "内容概要",
    "绪论",
    "引言",
    "引 言",
    "小结",
    "总结",
    "overview",
    "contents",
}
FIGURE_TRACK_ALGORITHMS = [
    "pdf_page_image_presence_filtering",
    "pdftoppm_page_screenshot_rendering",
    "neighbor_text_context_window",
    "keyword_overlap_distractor_retrieval",
    "rule_based_figure_meaning_explanation",
]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower())
    return slug.strip("-") or "entry"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def informative_tokens(text: str) -> set[str]:
    cleaned = normalize_text(text)
    tokens = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9\-/+.]{1,}", cleaned):
        tokens.add(token.lower())
    for token in re.findall(r"[\u4e00-\u9fff]{2,}", cleaned):
        tokens.add(token)
    return tokens


def looks_like_low_information_text(text: str) -> bool:
    lowered = normalize_text(text).lower()
    if any(marker in lowered for marker in ("email:", "@", "wx:", "qq:", "tel", "phone", "http://", "https://", "www.")):
        return True
    org_terms = {"大学", "学院", "学校", "系", "实验室", "college", "school", "department", "faculty", "university", "institute"}
    tokens = informative_tokens(text)
    if tokens and tokens.issubset(org_terms):
        return True
    return False


def _run_command(args: list[str]) -> str:
    if not shutil.which(args[0]):
        raise RuntimeError(f"Missing required command for figure track: {args[0]}")
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {' '.join(args)}")
    return result.stdout


def _load_kb_payload(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "entries" in raw:
        return raw
    if isinstance(raw, list):
        return {"meta": {"sourcePath": str(path), "sourceType": "json"}, "entries": raw}
    raise ValueError("Knowledge-base JSON must be a list or contain an `entries` list.")


def _context_lines(entries: list[dict[str, Any]], index: int, window: int) -> list[str]:
    lines: list[str] = []
    start = max(0, index - window)
    end = min(len(entries), index + window + 1)
    for current in entries[start:end]:
        title = normalize_text(current.get("title", ""))
        summary = normalize_text(current.get("summary", ""))
        if title:
            lines.append(title)
        if summary and summary != title:
            lines.append(summary)
        for fact in current.get("facts", [])[:3]:
            answer = normalize_text(fact.get("answer", ""))
            if answer and not looks_like_low_information_text(answer):
                lines.append(answer)
    deduped: list[str] = []
    seen = set()
    for line in lines:
        if line not in seen:
            seen.add(line)
            deduped.append(line)
    return deduped[:8]


def _title_penalty(title: str) -> float:
    lowered = normalize_text(title).lower()
    penalty = 0.0
    for token in GENERIC_TITLES:
        if token in lowered:
            penalty += 4.0
    if lowered.startswith("?") or lowered.startswith("？"):
        penalty += 1.5
    if len(lowered) <= 4:
        penalty += 1.0
    return penalty


def _text_noise_penalty(text: str) -> float:
    normalized = normalize_text(text)
    if not normalized:
        return 6.0
    penalty = 0.0
    ascii_words = [token for token in normalized.split() if token.isascii()]
    if ascii_words:
        unique_ratio = len(set(ascii_words)) / max(1, len(ascii_words))
        if len(ascii_words) >= 4 and unique_ratio <= 0.6:
            penalty += 7.0
        if normalized == normalized.lower() and not any("\u4e00" <= ch <= "\u9fff" for ch in normalized):
            penalty += 5.0
    symbol_count = sum(1 for char in normalized if char in "0123456789=+-*/×.%()[]")
    if symbol_count / max(1, len(normalized)) >= 0.18:
        penalty += 6.0
    if normalized.startswith("?") or normalized.startswith("？"):
        penalty += 2.0
    return penalty


def _candidate_score(entry: dict[str, Any], context_lines: list[str]) -> float:
    image_count = float(entry.get("visualSignals", {}).get("imageCount", 0))
    fact_count = float(len(entry.get("facts", [])))
    keyword_count = float(len(entry.get("keywords", [])))
    text_density = min(sum(len(line) for line in context_lines), 220) / 55.0
    title = entry.get("title", "")
    summary = entry.get("summary", "")
    return (
        image_count * 3.0
        + fact_count * 1.2
        + keyword_count * 0.5
        + text_density
        - _title_penalty(title)
        - _text_noise_penalty(title)
        - _text_noise_penalty(summary)
    )


def _is_explainable_candidate(entry: dict[str, Any]) -> bool:
    title = normalize_text(entry.get("title", ""))
    summary = normalize_text(entry.get("summary", ""))
    if not title:
        return False
    if _text_noise_penalty(title) >= 10.0:
        return False
    if _text_noise_penalty(summary) >= 10.0 and len(informative_tokens(summary)) < 4:
        return False
    lowered_title = title.lower()
    if any(token in lowered_title for token in GENERIC_TITLES) and (not summary or summary == title):
        return False
    return True


def _summary_focus(entry: dict[str, Any]) -> str:
    title = normalize_text(entry.get("title", "该图示"))
    summary = normalize_text(entry.get("summary", "")) or title
    noisy_summary = _text_noise_penalty(summary) >= 6.0 or (
        len(informative_tokens(summary)) >= 4
        and not any(marker in summary for marker in ("是", "用于", "说明", "帮助", "表示", "反映"))
    )
    if summary == title or noisy_summary:
        for fact in entry.get("facts", []):
            answer = normalize_text(fact.get("answer", ""))
            if (
                answer
                and len(answer) <= 60
                and not looks_like_low_information_text(answer)
                and _text_noise_penalty(answer) < 6.0
                and any(marker in answer for marker in ("是", "用于", "说明", "帮助", "表示", "反映"))
            ):
                summary = answer
                break
    if summary == title or noisy_summary:
        return title
    return summary


def _meaning_sentence(entry: dict[str, Any]) -> str:
    title = normalize_text(entry.get("title", "该图示"))
    focus = _summary_focus(entry)
    if focus and focus != title:
        return f"该图主要用于解释“{title}”，重点涉及{focus}。"
    return f"该图主要用于帮助理解“{title}”这一知识主题。"


def _analysis_text(candidate: dict[str, Any]) -> str:
    title = candidate["title"]
    focus = candidate["summaryFocus"]
    nearby = "；".join(candidate["contextLines"][:3])
    location = f"第 {candidate['page']} 页" if candidate.get("page") else "当前图示"
    if focus and focus != title:
        return f"这张图来自知识源的{location}，对应主题“{title}”。结合相邻知识文本，图示主要在说明{focus}。相关上下文包括：{nearby}。"
    return f"这张图来自知识源的{location}，对应主题“{title}”。结合相邻知识文本，这张图主要用于帮助理解该主题。相关上下文包括：{nearby}。"


def _similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    score = 0.0
    if a.get("module") and a.get("module") == b.get("module"):
        score += 2.0
    score += len(set(a.get("keywords", [])) & set(b.get("keywords", [])))
    score += len(informative_tokens(a.get("summaryFocus", "")) & informative_tokens(b.get("summaryFocus", ""))) * 0.5
    return score


def _display_ready(candidate: dict[str, Any]) -> bool:
    title = normalize_text(candidate.get("title", ""))
    if not title:
        return False
    lowered = title.lower()
    if any(token in lowered for token in GENERIC_TITLES):
        return False
    if len(title) <= 6 and "►" not in title and "(" not in title and "（" not in title:
        return False
    if _text_noise_penalty(title) >= 8.0:
        return False
    return True


def _relative_for_example(path: Path) -> str:
    path = path.resolve()
    try:
        relative = path.relative_to(ROOT / "example")
        return relative.as_posix()
    except ValueError:
        return path.relative_to(ROOT).as_posix()


def _render_pdf_page(source: Path, page: int, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = output_path.with_suffix("")
    _run_command(
        [
            "pdftoppm",
            "-f",
            str(page),
            "-l",
            str(page),
            "-png",
            "-singlefile",
            str(source),
            str(prefix),
        ]
    )


def build_figure_track(
    source: Union[str, Path],
    *,
    knowledge_base_path: Optional[Union[str, Path]] = None,
    candidate_limit: int = 24,
    context_window: int = 1,
) -> dict[str, Any]:
    source_path = Path(source)
    suffix = source_path.suffix.lower()
    if suffix not in SUPPORTED_FIGURE_SUFFIXES:
        raise ValueError(f"Figure track currently supports: {', '.join(sorted(SUPPORTED_FIGURE_SUFFIXES))}")

    if knowledge_base_path:
        kb_payload = _load_kb_payload(Path(knowledge_base_path))
    elif suffix == ".pdf":
        kb_payload = build_knowledge_base(source_path)
    else:
        kb_payload = {"meta": {"sourcePath": str(source_path), "sourceType": suffix.lstrip(".")}, "entries": []}

    entries = kb_payload.get("entries", [])
    figures: list[dict[str, Any]] = []

    if suffix == ".pdf":
        for index, entry in enumerate(entries):
            image_count = int(entry.get("visualSignals", {}).get("imageCount", 0) or 0)
            source_pages = entry.get("sourcePages", [])
            if image_count <= 0 or not source_pages:
                continue
            if not _is_explainable_candidate(entry):
                continue
            context_lines = _context_lines(entries, index, context_window)
            candidate = {
                "id": f"{slugify(source_path.stem)}-fig-{len(figures) + 1:03d}",
                "entryId": entry.get("id", f"entry-{index + 1:03d}"),
                "page": int(source_pages[0]),
                "sourcePath": str(source_path),
                "sourceType": "pdf",
                "module": entry.get("module", ""),
                "title": entry.get("title", f"{source_path.stem} page {source_pages[0]}"),
                "summary": normalize_text(entry.get("summary", "")),
                "summaryFocus": _summary_focus(entry),
                "contextLines": context_lines,
                "keywords": entry.get("keywords", []),
                "imageCount": image_count,
                "visualSignals": entry.get("visualSignals", {}),
            }
            candidate["score"] = _candidate_score(entry, context_lines)
            figures.append(candidate)
    else:
        title = source_path.stem.replace("_", " ").replace("-", " ")
        candidate = {
            "id": f"{slugify(source_path.stem)}-fig-001",
            "entryId": slugify(title),
            "page": None,
            "sourcePath": str(source_path),
            "sourceType": suffix.lstrip("."),
            "module": "Imported Figure",
            "title": title,
            "summary": title,
            "summaryFocus": title,
            "contextLines": [title],
            "keywords": list(informative_tokens(title))[:8],
            "imageCount": 1,
            "visualSignals": {"pageKind": "standalone_image"},
            "score": 1.0,
        }
        figures.append(candidate)

    figures.sort(key=lambda item: (item["score"], item["imageCount"], item["page"] or 0), reverse=True)
    if candidate_limit > 0:
        figures = figures[:candidate_limit]

    return {
        "meta": {
            "sourcePath": str(source_path),
            "sourceType": suffix.lstrip("."),
            "candidateCount": len(figures),
            "algorithms": FIGURE_TRACK_ALGORITHMS,
        },
        "figures": figures,
    }


def load_figure_track(path: Union[str, Path]) -> dict[str, Any]:
    return _load_kb_payload(Path(path))


def synthesize_figure_questions(
    figure_track: dict[str, Any],
    *,
    count: int,
    seed: int,
    asset_dir: Union[str, Path],
) -> dict[str, Any]:
    rng = random.Random(seed)
    figures = list(figure_track.get("figures", []))
    if not figures:
        raise ValueError("No figure candidates available for synthesis.")

    selected: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for figure in figures:
        if _display_ready(figure):
            selected.append(figure)
        else:
            deferred.append(figure)
        if len(selected) >= count:
            break
    if len(selected) < count:
        for figure in deferred:
            selected.append(figure)
            if len(selected) >= count:
                break
    asset_root = Path(asset_dir)
    asset_root.mkdir(parents=True, exist_ok=True)

    questions: list[dict[str, Any]] = []
    used_meanings: set[str] = set()
    for index, figure in enumerate(selected, start=1):
        correct = _meaning_sentence(figure)
        if correct in used_meanings:
            continue

        ranked_distractors = sorted(
            (candidate for candidate in figures if candidate["id"] != figure["id"] and _display_ready(candidate)),
            key=lambda candidate: _similarity(figure, candidate),
            reverse=True,
        )
        distractors: list[str] = []
        for candidate in ranked_distractors:
            meaning = _meaning_sentence(candidate)
            if meaning == correct or meaning in distractors:
                continue
            distractors.append(meaning)
            if len(distractors) >= 3:
                break
        if len(distractors) < 3:
            filler_pool = [_meaning_sentence(candidate) for candidate in figures if candidate["id"] != figure["id"]]
            rng.shuffle(filler_pool)
            for meaning in filler_pool:
                if meaning != correct and meaning not in distractors:
                    distractors.append(meaning)
                if len(distractors) >= 3:
                    break

        source_path = Path(figure["sourcePath"])
        image_output = asset_root / f"{figure['id']}.png"
        if figure["sourceType"] == "pdf":
            _render_pdf_page(source_path, int(figure["page"]), image_output)
        else:
            shutil.copyfile(source_path, image_output)

        answer_texts = [correct, *distractors[:3]]
        rng.shuffle(answer_texts)
        options = [
            {"key": LETTERS[option_index], "text": text}
            for option_index, text in enumerate(answer_texts[:4])
        ]
        answer_key = next(option["key"] for option in options if option["text"] == correct)
        questions.append(
            {
                "id": f"sqfig-{slugify(figure['title'])}-{index:03d}",
                "source": "SynQuest-Figure",
                "origin": "figure-context-generated",
                "year": None,
                "topic": slugify(figure["module"] or figure["title"]),
                "topicName": figure["title"],
                "difficulty": 2,
                "type": "single_choice",
                "prompt": "根据图示与相邻知识，下列哪项最能解释这张图的核心含义？",
                "options": options,
                "answer": answer_key,
                "analysis": _analysis_text(figure),
                "knowledgeRefs": [figure["entryId"]],
                "styleRefs": [],
                "tags": sorted({"synquest", "figure-question", *(figure.get("keywords") or [])}),
                "images": {"question": _relative_for_example(image_output), "note": ""},
                "pdfPage": figure.get("page"),
            }
        )
        used_meanings.add(correct)

    if not questions:
        raise ValueError("No figure questions were generated.")

    return {
        "meta": {
            "title": "SynQuest Figure Questions",
            "count": len(questions),
            "seed": seed,
            "algorithms": FIGURE_TRACK_ALGORITHMS,
        },
        "questions": questions,
    }
