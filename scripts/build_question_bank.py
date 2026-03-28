#!/usr/bin/env python3
"""Normalize the legacy genome informatics HTML bank into structured JSON."""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEGACY_HTML = ROOT / "legacy" / "index.legacy.html"
ANSWERS_JSON = ROOT / "user_data" / "answers.json"
OUTPUT_JSON = ROOT / "data" / "question-bank.json"


TOPIC_RULES = {
    "human-genome-project": [
        "人类基因组计划",
        "HGP",
        "遗传图",
        "物理图",
        "STS",
        "辐射杂交",
        "图谱",
    ],
    "sequencing-methods": [
        "测序",
        "Sanger",
        "链终止",
        "化学降解",
        "ART",
        "Illumina",
        "SAM",
        "读段",
        "平台",
    ],
    "genome-assembly": [
        "组装",
        "de Bru",
        "deBru",
        "DBG",
        "OLC",
        "contig",
        "scaffold",
        "重叠图",
        "mate-pair",
        "paired-end",
        "k-mer",
        "欧拉路径",
        "Hamilton",
    ],
    "alignment-homology": [
        "Blast",
        "BLAST",
        "Clustal",
        "BLOSUM",
        "PAM",
        "同源",
        "比对",
        "蛋白质序列",
    ],
    "annotation-prediction": [
        "注释",
        "GeneMark",
        "GENSCAN",
        "Augustus",
        "RepeatMasker",
        "Gnomon",
        "ProSplign",
        "RNA-Seq",
        "基因结构",
        "新基因",
    ],
    "hmm-regulation": [
        "HMM",
        "隐马尔可夫",
        "CpG",
        "TATA",
        "Forward",
        "Viterbi",
        "Baum-Welch",
        "启动子",
        "转录因子",
    ],
    "genome-databases": [
        "Ensembl",
        "UCSC",
        "Genbank",
        "RefSeq",
        "PubMed",
        "JGI GOLD",
        "数据库",
    ],
}


TOPIC_META = {
    "human-genome-project": {"name": "人类基因组计划与图谱", "knowledge_refs": ["hgp-maps"]},
    "sequencing-methods": {"name": "测序方法与读段模拟", "knowledge_refs": ["sequencing-tech"]},
    "genome-assembly": {"name": "基因组组装与图算法", "knowledge_refs": ["assembly-graphs"]},
    "alignment-homology": {"name": "序列比对与同源推断", "knowledge_refs": ["alignment-homology"]},
    "annotation-prediction": {"name": "基因注释与结构建模", "knowledge_refs": ["annotation-pipeline"]},
    "hmm-regulation": {"name": "HMM 与顺式调控元件", "knowledge_refs": ["hmm-regulation"]},
    "genome-databases": {"name": "基因组数据库与资源", "knowledge_refs": ["genome-databases"]},
    "general": {"name": "综合题", "knowledge_refs": ["course-overview"]},
}


def load_legacy_arrays(html_text: str) -> list[dict[str, Any]]:
    all_questions: list[dict[str, Any]] = []
    for name, year in [("rawData2022", 2022), ("rawData2023", 2023)]:
        match = re.search(rf"const\s+{name}\s*=\s*\[(.*?)\n\s*\];", html_text, re.S)
        if not match:
            raise ValueError(f"Cannot locate {name} in legacy HTML.")

        array_text = "[" + match.group(1) + "]"
        array_text = re.sub(r"//.*", "", array_text)
        array_text = array_text.replace("true", "True").replace("false", "False").replace("null", "None")
        array_text = re.sub(r'([\{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', array_text)
        data = ast.literal_eval(array_text)

        for item in data:
            item["year"] = year
            item["source"] = str(year)
            all_questions.append(item)
    return all_questions


def parse_option(raw_option: str) -> dict[str, str]:
    cleaned = raw_option.strip()
    if not cleaned:
        return {"key": "", "text": ""}
    match = re.match(r"([A-Z])\.(.*)", cleaned)
    if match:
        return {"key": match.group(1), "text": match.group(2).strip()}
    return {"key": "", "text": cleaned}


def infer_type(answer: str, prompt: str, options: list[dict[str, str]]) -> str:
    compact = re.sub(r"\s+", "", answer)
    populated_keys = {opt["key"] for opt in options if opt["key"]}

    if compact and re.fullmatch(r"[A-Z]+", compact) and set(compact).issubset(populated_keys):
        if "[多选]" in prompt or len(compact) > 1:
            return "multiple_choice"
        return "single_choice"
    if options:
        return "short_answer"
    return "open_ended"


def infer_topic(text: str) -> str:
    lower = text.lower()
    for topic_id, keywords in TOPIC_RULES.items():
        if any(keyword.lower() in lower for keyword in keywords):
            return topic_id
    return "general"


def infer_difficulty(prompt: str, qtype: str, has_image: bool, options_count: int) -> int:
    difficulty = 2
    if qtype == "multiple_choice":
        difficulty += 1
    if qtype in {"short_answer", "open_ended"}:
        difficulty += 1
    if has_image:
        difficulty += 1
    if re.search(r"计算|概率|矩阵|图|路径|score|得分|联合输出概率", prompt, re.I):
        difficulty += 1
    if options_count <= 2:
        difficulty += 1
    return max(1, min(5, difficulty))


def infer_tags(prompt: str, analysis: str, topic_id: str, qtype: str, has_image: bool) -> list[str]:
    text = f"{prompt} {analysis}"
    tags = [topic_id, qtype]
    if has_image:
        tags.append("image-based")
    if "[多选]" in prompt:
        tags.append("multi-select")
    if re.search(r"HMM|隐马尔可夫|CpG|TATA", text, re.I):
        tags.append("hmm")
    if re.search(r"BLAST|Clustal|BLOSUM|PAM|同源|比对", text, re.I):
        tags.append("alignment")
    if re.search(r"组装|de Bru|OLC|contig|scaffold|k-mer", text, re.I):
        tags.append("assembly")
    if re.search(r"注释|GeneMark|Augustus|Gnomon|RepeatMasker", text, re.I):
        tags.append("annotation")
    if re.search(r"测序|Sanger|Illumina|ART|SAM", text, re.I):
        tags.append("sequencing")
    return sorted(dict.fromkeys(tags))


def build_question_record(question: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
    answer_meta = answers.get(question["id"], {})
    options = [parse_option(opt) for opt in question.get("opts", [])]
    options = [opt for opt in options if opt["text"]]

    prompt = question["q"].strip()
    answer = str(answer_meta.get("answer", "")).strip()
    analysis = str(answer_meta.get("analysis", "")).strip()
    question_image = question.get("imgSrc", "") or ""
    note_image = answer_meta.get("img_path", "") or ""
    pdf_page = answer_meta.get("pdf_page", "") or ""

    qtype = infer_type(answer, prompt, options)
    topic_id = infer_topic(f"{prompt} {analysis}")
    difficulty = infer_difficulty(prompt, qtype, bool(question_image), len(options))

    return {
        "id": question["id"],
        "year": question["year"],
        "source": question["source"],
        "prompt": prompt,
        "type": qtype,
        "topic": topic_id,
        "topicName": TOPIC_META[topic_id]["name"],
        "difficulty": difficulty,
        "options": options,
        "answer": answer,
        "analysis": analysis,
        "images": {
            "question": question_image,
            "note": note_image,
        },
        "pdfPage": int(str(pdf_page)) if str(pdf_page).isdigit() else None,
        "knowledgeRefs": TOPIC_META[topic_id]["knowledge_refs"],
        "tags": infer_tags(prompt, analysis, topic_id, qtype, bool(question_image)),
        "origin": "legacy-curated",
    }


def build_payload(questions: list[dict[str, Any]]) -> dict[str, Any]:
    topic_counter = Counter(q["topic"] for q in questions)
    type_counter = Counter(q["type"] for q in questions)
    image_count = sum(1 for q in questions if q["images"]["question"])
    note_count = sum(1 for q in questions if q["images"]["note"])

    return {
        "meta": {
            "title": "Genome Informatics Question Bank",
            "subtitle": "Structured archive extracted from the original local HTML bank",
            "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "totalQuestions": len(questions),
            "sources": sorted({q["source"] for q in questions}),
            "topics": [
                {
                    "id": topic_id,
                    "name": TOPIC_META[topic_id]["name"],
                    "count": count,
                }
                for topic_id, count in sorted(topic_counter.items())
            ],
            "types": dict(sorted(type_counter.items())),
            "imageQuestionCount": image_count,
            "noteImageCount": note_count,
        },
        "questions": questions,
    }


def main() -> None:
    html_text = LEGACY_HTML.read_text(encoding="utf-8")
    answers = json.loads(ANSWERS_JSON.read_text(encoding="utf-8"))
    legacy_questions = load_legacy_arrays(html_text)
    records = [build_question_record(item, answers) for item in legacy_questions]

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(build_payload(records), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} questions to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
