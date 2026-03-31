#!/usr/bin/env python3
"""SynQuest CLI: inspect, extract, synthesize, and merge quiz banks."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FUNCTIONS_ROOT = Path(__file__).resolve().parents[1]
if str(FUNCTIONS_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_ROOT))

from synquest.knowledge_loader import build_knowledge_base, inspect_knowledge_source, load_knowledge_entries  # noqa: E402
from synquest.figure_track import build_figure_track, load_figure_track, synthesize_figure_questions  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def refresh_bank_meta(bank: dict[str, Any]) -> None:
    questions = bank.get("questions", [])
    topic_counter = Counter(question.get("topic", "unknown") for question in questions)
    type_counter = Counter(question.get("type", "single_choice") for question in questions)
    topic_names: dict[str, str] = {}
    for question in questions:
        topic_id = question.get("topic", "unknown")
        topic_names.setdefault(topic_id, question.get("topicName") or topic_id)

    meta = bank.setdefault("meta", {})
    meta["totalQuestions"] = len(questions)
    meta["sources"] = sorted({question.get("source", "Unknown") for question in questions})
    meta["topics"] = [
        {"id": topic_id, "name": topic_names.get(topic_id, topic_id), "count": count}
        for topic_id, count in sorted(topic_counter.items())
    ]
    meta["types"] = dict(sorted(type_counter.items()))
    meta["imageQuestionCount"] = sum(1 for question in questions if question.get("images", {}).get("question"))
    meta["noteImageCount"] = sum(1 for question in questions if question.get("images", {}).get("note"))


def merge_bank(bank_path: Path, incoming_path: Path) -> dict[str, Any]:
    bank = load_json(bank_path)
    incoming = load_json(incoming_path)
    existing = {question["id"]: question for question in bank.get("questions", [])}

    for question in incoming.get("questions", []):
        existing[question["id"]] = question

    merged_questions = list(existing.values())
    bank["questions"] = merged_questions
    refresh_bank_meta(bank)
    return bank


def cmd_inspect(args: argparse.Namespace) -> None:
    report = inspect_knowledge_source(Path(args.kb))
    print(f"path: {report['path']}")
    print(f"suffix: {report['suffix']}")
    print(f"characters: {report['characters']}")
    print(f"entries: {report['entries']}")
    print(f"facts: {report['facts']}")
    if report.get("algorithms"):
        print("algorithms:")
        for algorithm in report["algorithms"]:
            print(f"- {algorithm}")
    for key, value in report.get("extra", {}).items():
        print(f"{key}: {value}")
    for title in report["titleSamples"]:
        print(f"- {title}")


def cmd_extract(args: argparse.Namespace) -> None:
    payload = build_knowledge_base(Path(args.source))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote knowledge base with {len(payload['entries'])} entries to {out_path}")


def cmd_synthesize(args: argparse.Namespace) -> None:
    from synquest.question_engine import load_question_bank, synthesize_questions

    entries = load_knowledge_entries(Path(args.kb))
    style_bank_questions = load_question_bank(Path(args.style_bank)) if args.style_bank else None
    payload = synthesize_questions(
        entries,
        args.count,
        args.seed,
        style_bank_questions=style_bank_questions,
        style_top_k=args.style_top_k,
        semantic_model=args.semantic_model,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {payload['meta']['count']} questions to {out_path}")


def cmd_merge(args: argparse.Namespace) -> None:
    merged = merge_bank(Path(args.bank), Path(args.incoming))
    out_path = Path(args.out or args.bank)
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"merged bank written to {out_path}")


def cmd_extract_figures(args: argparse.Namespace) -> None:
    payload = build_figure_track(
        Path(args.source),
        knowledge_base_path=Path(args.kb) if args.kb else None,
        candidate_limit=args.candidate_limit,
        context_window=args.context_window,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {payload['meta']['candidateCount']} figure candidates to {out_path}")


def cmd_synthesize_figure_questions(args: argparse.Namespace) -> None:
    if args.figure_track:
        payload = load_figure_track(Path(args.figure_track))
    else:
        if not args.source:
            raise ValueError("Either --figure-track or --source must be provided.")
        payload = build_figure_track(
            Path(args.source),
            knowledge_base_path=Path(args.kb) if args.kb else None,
            candidate_limit=args.candidate_limit,
            context_window=args.context_window,
        )
    questions = synthesize_figure_questions(
        payload,
        count=args.count,
        seed=args.seed,
        asset_dir=Path(args.asset_dir),
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {questions['meta']['count']} figure questions to {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SynQuest knowledge-base question generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a knowledge base")
    inspect_parser.add_argument("--kb", required=True, help="Path to a json/md/txt/html/docx/pdf/pptx knowledge base")
    inspect_parser.set_defaults(func=cmd_inspect)

    extract_parser = subparsers.add_parser("extract", help="Normalize a source file into SynQuest knowledge-base JSON")
    extract_parser.add_argument("--source", required=True, help="Path to a json/md/txt/html/docx/pdf/pptx source")
    extract_parser.add_argument(
        "--out",
        default=str(ROOT / "example" / "data" / "knowledge-base" / "synquest-extracted.json"),
        help="Output JSON path",
    )
    extract_parser.set_defaults(func=cmd_extract)

    synth_parser = subparsers.add_parser("synthesize", help="Generate question JSON from a knowledge base")
    synth_parser.add_argument("--kb", required=True, help="Path to a json/md/txt/html/docx/pdf/pptx knowledge base")
    synth_parser.add_argument("--style-bank", help="Optional existing question-bank JSON used for style retrieval and adaptation")
    synth_parser.add_argument("--style-top-k", type=int, default=5, help="How many similar old questions to retrieve per fact")
    synth_parser.add_argument("--semantic-model", help="Optional sentence-transformers model used for semantic style retrieval")
    synth_parser.add_argument("--count", type=int, default=12, help="Number of questions to generate")
    synth_parser.add_argument("--seed", type=int, default=7, help="Random seed")
    synth_parser.add_argument("--out", default=str(ROOT / "example" / "data" / "generated" / "synquest-output.json"))
    synth_parser.set_defaults(func=cmd_synthesize)

    merge_parser = subparsers.add_parser("merge", help="Merge generated questions into the main bank")
    merge_parser.add_argument("--bank", required=True, help="Existing bank JSON path")
    merge_parser.add_argument("--incoming", required=True, help="Generated questions JSON path")
    merge_parser.add_argument("--out", help="Optional output path; defaults to overwriting --bank")
    merge_parser.set_defaults(func=cmd_merge)

    extract_figures_parser = subparsers.add_parser("extract-figures", help="Build an independent figure track from an image-backed source")
    extract_figures_parser.add_argument("--source", required=True, help="Path to a pdf/png/jpg/jpeg source")
    extract_figures_parser.add_argument("--kb", help="Optional existing SynQuest knowledge-base JSON used for nearby text binding")
    extract_figures_parser.add_argument("--candidate-limit", type=int, default=24, help="How many figure candidates to keep after scoring")
    extract_figures_parser.add_argument("--context-window", type=int, default=1, help="How many neighboring entries to use for figure context")
    extract_figures_parser.add_argument("--out", default=str(ROOT / "example" / "data" / "generated" / "figure-track.json"))
    extract_figures_parser.set_defaults(func=cmd_extract_figures)

    synth_figure_parser = subparsers.add_parser("synthesize-figure-questions", help="Generate image-backed questions from the independent figure track")
    synth_figure_parser.add_argument("--figure-track", help="Optional prebuilt figure-track JSON")
    synth_figure_parser.add_argument("--source", help="Path to a pdf/png/jpg/jpeg source")
    synth_figure_parser.add_argument("--kb", help="Optional existing SynQuest knowledge-base JSON used for nearby text binding")
    synth_figure_parser.add_argument("--candidate-limit", type=int, default=24, help="How many figure candidates to keep after scoring")
    synth_figure_parser.add_argument("--context-window", type=int, default=1, help="How many neighboring entries to use for figure context")
    synth_figure_parser.add_argument("--count", type=int, default=2, help="Number of figure questions to generate")
    synth_figure_parser.add_argument("--seed", type=int, default=7, help="Random seed")
    synth_figure_parser.add_argument(
        "--asset-dir",
        default=str(ROOT / "example" / "data" / "generated" / "figure-assets"),
        help="Directory where rendered figure screenshots will be written",
    )
    synth_figure_parser.add_argument("--out", default=str(ROOT / "example" / "data" / "generated" / "figure-questions.json"))
    synth_figure_parser.set_defaults(func=cmd_synthesize_figure_questions)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
