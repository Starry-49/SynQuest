#!/usr/bin/env python3
"""Normalize SynQuest generated payloads and merge them into the Geno example bank."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_TOPICS: dict[str, dict[str, str]] = {
    "alignment-homology": {
        "name": "序列比对与同源推断",
        "knowledgeRef": "alignment-homology",
    },
    "annotation-prediction": {
        "name": "基因注释与结构建模",
        "knowledgeRef": "annotation-pipeline",
    },
    "general": {
        "name": "综合题",
        "knowledgeRef": "course-overview",
    },
    "genome-assembly": {
        "name": "基因组组装与图算法",
        "knowledgeRef": "assembly-graphs",
    },
    "genome-databases": {
        "name": "基因组数据库与资源",
        "knowledgeRef": "genome-databases",
    },
    "hmm-regulation": {
        "name": "HMM 与顺式调控元件",
        "knowledgeRef": "hmm-regulation",
    },
    "human-genome-project": {
        "name": "人类基因组计划与图谱",
        "knowledgeRef": "hgp-maps",
    },
    "sequencing-methods": {
        "name": "测序方法与读段模拟",
        "knowledgeRef": "sequencing-tech",
    },
}

TOPIC_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "sequencing-methods",
        (
            "测序",
            "read",
            "illumina",
            "sanger",
            "sam",
            "aln",
            "art_illumina",
            "reads",
            "读段",
            "双端",
            "paired-end",
            "pacbio",
            "nanopore",
            "454",
        ),
    ),
    (
        "alignment-homology",
        (
            "比对",
            "blast",
            "hsp",
            "homology",
            "similarity",
            "clustal",
            "pam",
            "blosum",
            "smith-waterman",
            "needleman",
            "同源",
            "相似性",
        ),
    ),
    (
        "hmm-regulation",
        (
            "hmm",
            "cpg",
            "viterbi",
            "隐马尔可夫",
            "顺式",
            "状态路径",
            "转移概率",
            "启动子",
            "调控",
        ),
    ),
    (
        "genome-assembly",
        (
            "组装",
            "contig",
            "scaffold",
            "de bruijn",
            "debruijn",
            "overlap",
            "olc",
            "n50",
            "拼接",
            "graph",
        ),
    ),
    (
        "annotation-prediction",
        (
            "注释",
            "transcript",
            "转录本",
            "gff",
            "gff3",
            "外显子",
            "内含子",
            "orf",
            "gene prediction",
            "基因结构",
            "功能元件",
        ),
    ),
    (
        "human-genome-project",
        (
            "人类基因组",
            "遗传图",
            "物理图",
            "图谱",
            "hgp",
            "snp图谱",
        ),
    ),
    (
        "genome-databases",
        (
            "数据库",
            "genbank",
            "ensembl",
            "ucsc",
            "refseq",
            "pubmed",
            "dbsnp",
            "omim",
            "ncbi",
            "ebi",
        ),
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def slugify(text: str) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "-", str(text or "").strip().lower())
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "item"


def detect_canonical_topic(question: dict[str, Any]) -> str:
    blob = " ".join(
        [
            question.get("topic", ""),
            question.get("topicName", ""),
            question.get("prompt", ""),
            question.get("analysis", ""),
            " ".join(question.get("tags") or []),
        ]
    )
    normalized = normalize_text(blob)
    for topic_id, keywords in TOPIC_RULES:
        if any(keyword in normalized for keyword in keywords):
            return topic_id
    return "general"


def apply_canonical_topic(question: dict[str, Any], topic_id: str) -> None:
    topic_info = CANONICAL_TOPICS[topic_id]
    question["topic"] = topic_id
    question["topicName"] = topic_info["name"]
    question["knowledgeRefs"] = [topic_info["knowledgeRef"]]
    tags = set(question.get("tags") or [])
    tags.add(topic_id)
    question["tags"] = sorted(tags)


def next_semantic_index(existing_questions: list[dict[str, Any]]) -> int:
    max_index = 0
    for question in existing_questions:
        if question.get("source") != "SynQuest":
            continue
        match = re.search(r"-(\d{3})$", question.get("id", ""))
        if match:
            max_index = max(max_index, int(match.group(1)))
    return max_index + 1


def next_figure_index(existing_questions: list[dict[str, Any]]) -> int:
    max_index = 0
    for question in existing_questions:
        if question.get("source") != "SynQuest-Figure":
            continue
        match = re.search(r"-(\d{3})$", question.get("id", ""))
        if match:
            max_index = max(max_index, int(match.group(1)))
    return max_index + 1


def normalize_existing_figures(bank_questions: list[dict[str, Any]]) -> None:
    for question in bank_questions:
        if question.get("source") != "SynQuest-Figure":
            continue
        apply_canonical_topic(question, detect_canonical_topic(question))


def normalize_semantic_payload(payload: dict[str, Any], existing_questions: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_questions: list[dict[str, Any]] = []
    counter = next_semantic_index(existing_questions)
    for question in payload.get("questions", []):
        item = json.loads(json.dumps(question, ensure_ascii=False))
        topic_id = item.get("topic")
        if topic_id not in CANONICAL_TOPICS:
            topic_id = detect_canonical_topic(item)
        apply_canonical_topic(item, topic_id)
        item["id"] = f"sq-{topic_id}-{counter:03d}"
        item["source"] = "SynQuest"
        item["origin"] = "semantic-generated"
        normalized_questions.append(item)
        counter += 1
    payload["questions"] = normalized_questions
    payload.setdefault("meta", {})["count"] = len(normalized_questions)
    return payload


def normalize_figure_payload(payload: dict[str, Any], existing_questions: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_questions: list[dict[str, Any]] = []
    counter = next_figure_index(existing_questions)
    for question in payload.get("questions", []):
        item = json.loads(json.dumps(question, ensure_ascii=False))
        topic_id = detect_canonical_topic(item)
        apply_canonical_topic(item, topic_id)
        label = slugify(item.get("topicName") or topic_id)
        item["id"] = f"sqfig-{label}-{counter:03d}"
        item["source"] = "SynQuest-Figure"
        item["origin"] = "figure-context-generated"
        normalized_questions.append(item)
        counter += 1
    payload["questions"] = normalized_questions
    payload.setdefault("meta", {})["count"] = len(normalized_questions)
    return payload


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


def merge_payload(bank: dict[str, Any], incoming_questions: list[dict[str, Any]]) -> dict[str, Any]:
    existing = {question["id"]: question for question in bank.get("questions", [])}
    for question in incoming_questions:
        existing[question["id"]] = question
    bank["questions"] = list(existing.values())
    refresh_bank_meta(bank)
    return bank


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize SynQuest generated payloads and merge them into Geno.")
    parser.add_argument("--bank", required=True, help="Path to the Geno question-bank.json")
    parser.add_argument("--semantic-in", required=True, help="Raw semantic-generated SynQuest payload")
    parser.add_argument("--semantic-out", required=True, help="Normalized semantic payload output path")
    parser.add_argument("--figure-in", required=True, help="Raw figure-generated SynQuest payload")
    parser.add_argument("--figure-out", required=True, help="Normalized figure payload output path")
    parser.add_argument("--out", help="Output bank path; defaults to overwriting --bank")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bank_path = Path(args.bank)
    bank = load_json(bank_path)
    normalize_existing_figures(bank.get("questions", []))

    semantic_payload = normalize_semantic_payload(load_json(Path(args.semantic_in)), bank.get("questions", []))
    figure_payload = normalize_figure_payload(load_json(Path(args.figure_in)), bank.get("questions", []) + semantic_payload.get("questions", []))

    write_json(Path(args.semantic_out), semantic_payload)
    write_json(Path(args.figure_out), figure_payload)

    merged = merge_payload(bank, semantic_payload.get("questions", []) + figure_payload.get("questions", []))
    write_json(Path(args.out) if args.out else bank_path, merged)

    print(f"semantic questions: {len(semantic_payload.get('questions', []))}")
    print(f"figure questions: {len(figure_payload.get('questions', []))}")
    print(f"merged total: {merged['meta']['totalQuestions']}")


if __name__ == "__main__":
    main()
