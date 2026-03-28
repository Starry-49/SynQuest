#!/usr/bin/env python3
"""SynQuest CLI: inspect, synthesize, and merge quiz banks."""

from __future__ import annotations

import argparse
import json
import random
import re
from html import unescape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower())
    return slug.strip("-") or "entry"


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def parse_markdown_like(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("## "):
            if current:
                entries.append(current)
            title = stripped[3:].strip()
            current = {
                "id": slugify(title),
                "module": "知识条目",
                "title": title,
                "summary": "",
                "keywords": [],
                "distractors": [],
                "facts": [],
            }
            continue
        if current is None:
            continue
        if stripped.startswith("- "):
            current["facts"].append(
                {
                    "question": f"下列哪项关于“{current['title']}”的说法是正确的？",
                    "answer": stripped[2:].strip("。 "),
                    "explanation": stripped[2:].strip(),
                    "distractors": [],
                }
            )
        elif not current["summary"]:
            current["summary"] = stripped

    if current:
        entries.append(current)
    return entries


def normalize_entries(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        raw = load_json(path)
        entries = raw["entries"] if isinstance(raw, dict) and "entries" in raw else raw
        if not isinstance(entries, list):
            raise ValueError("JSON knowledge base must be a list or contain an `entries` list.")
        return entries
    if suffix in {".md", ".txt"}:
        return parse_markdown_like(path.read_text(encoding="utf-8"))
    if suffix == ".html":
        html_text = strip_html(unescape(path.read_text(encoding="utf-8")))
        return parse_markdown_like(html_text.replace("  ", "\n"))
    raise ValueError(f"Unsupported knowledge base format: {path.suffix}")


def build_options(correct: str, fact_distractors: list[str], entries: list[dict[str, Any]], rng: random.Random) -> list[dict[str, str]]:
    distractors = [item.strip() for item in fact_distractors if item.strip()]
    if len(distractors) < 3:
        pool: list[str] = []
        for entry in entries:
            pool.extend(item.strip() for item in entry.get("distractors", []) if item.strip())
            for fact in entry.get("facts", []):
                candidate = str(fact.get("answer", "")).strip()
                if candidate and candidate != correct:
                    pool.append(candidate)
        for candidate in pool:
            if candidate != correct and candidate not in distractors:
                distractors.append(candidate)
            if len(distractors) >= 3:
                break
    while len(distractors) < 3:
        distractors.append(f"不正确的备选项{len(distractors) + 1}")

    candidates = [correct, *distractors[:3]]
    rng.shuffle(candidates)
    labels = ["A", "B", "C", "D"]
    return [{"key": labels[idx], "text": text} for idx, text in enumerate(candidates)]


def synthesize_questions(entries: list[dict[str, Any]], count: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    flat_facts: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for entry in entries:
        for fact in entry.get("facts", []):
            flat_facts.append((entry, fact))

    if not flat_facts:
        raise ValueError("No facts found in the knowledge base.")

    rng.shuffle(flat_facts)
    selected = flat_facts[: min(count, len(flat_facts))]
    questions: list[dict[str, Any]] = []

    for idx, (entry, fact) in enumerate(selected, start=1):
        correct = str(fact.get("answer", "")).strip()
        options = build_options(correct, fact.get("distractors", []), entries, rng)
        answer_key = next(option["key"] for option in options if option["text"] == correct)
        topic = slugify(entry.get("id") or entry.get("title", "entry"))
        questions.append(
            {
                "id": f"sq-{topic}-{idx:03d}",
                "source": "synquest",
                "origin": "generated",
                "year": None,
                "topic": topic,
                "topicName": entry.get("title", "SynQuest 条目"),
                "difficulty": int(fact.get("difficulty", 2)),
                "type": fact.get("type", "single_choice"),
                "prompt": fact.get("question") or f"下列哪项关于“{entry.get('title', '该主题')}”的说法是正确的？",
                "options": options,
                "answer": answer_key,
                "analysis": fact.get("explanation") or correct,
                "knowledgeRefs": [entry.get("id", topic)],
                "tags": sorted(
                    {
                        topic,
                        "synquest",
                        fact.get("type", "single_choice"),
                        *(entry.get("keywords") or []),
                    }
                ),
                "images": {"question": "", "note": ""},
                "pdfPage": None,
            }
        )

    return {
        "meta": {
            "title": "SynQuest Generated Questions",
            "count": len(questions),
            "seed": seed,
        },
        "questions": questions,
    }


def merge_bank(bank_path: Path, incoming_path: Path) -> dict[str, Any]:
    bank = load_json(bank_path)
    incoming = load_json(incoming_path)
    existing = {question["id"]: question for question in bank.get("questions", [])}

    for question in incoming.get("questions", []):
        existing[question["id"]] = question

    merged_questions = list(existing.values())
    bank["questions"] = merged_questions
    bank.setdefault("meta", {})
    bank["meta"]["totalQuestions"] = len(merged_questions)
    return bank


def cmd_inspect(args: argparse.Namespace) -> None:
    entries = normalize_entries(Path(args.kb))
    print(f"entries: {len(entries)}")
    for entry in entries[:10]:
        print(f"- {entry.get('id', 'entry')} :: {entry.get('title', 'Untitled')} :: facts={len(entry.get('facts', []))}")


def cmd_synthesize(args: argparse.Namespace) -> None:
    entries = normalize_entries(Path(args.kb))
    payload = synthesize_questions(entries, args.count, args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {payload['meta']['count']} questions to {out_path}")


def cmd_merge(args: argparse.Namespace) -> None:
    merged = merge_bank(Path(args.bank), Path(args.incoming))
    out_path = Path(args.out or args.bank)
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"merged bank written to {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SynQuest knowledge-base question generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a knowledge base")
    inspect_parser.add_argument("--kb", required=True, help="Path to a json/md/txt/html knowledge base")
    inspect_parser.set_defaults(func=cmd_inspect)

    synth_parser = subparsers.add_parser("synthesize", help="Generate question JSON from a knowledge base")
    synth_parser.add_argument("--kb", required=True, help="Path to a json/md/txt/html knowledge base")
    synth_parser.add_argument("--count", type=int, default=12, help="Number of questions to generate")
    synth_parser.add_argument("--seed", type=int, default=7, help="Random seed")
    synth_parser.add_argument("--out", default=str(ROOT / "data" / "generated" / "synquest-output.json"))
    synth_parser.set_defaults(func=cmd_synthesize)

    merge_parser = subparsers.add_parser("merge", help="Merge generated questions into the main bank")
    merge_parser.add_argument("--bank", required=True, help="Existing bank JSON path")
    merge_parser.add_argument("--incoming", required=True, help="Generated questions JSON path")
    merge_parser.add_argument("--out", help="Optional output path; defaults to overwriting --bank")
    merge_parser.set_defaults(func=cmd_merge)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
