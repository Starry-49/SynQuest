"""Reusable question synthesis with knowledge facts plus style retrieval."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Union

try:
    import jieba
except ImportError:  # pragma: no cover - optional dependency for style retrieval
    jieba = None

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - optional dependency for style retrieval
    BM25Okapi = None

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - optional dependency for style retrieval
    fuzz = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # pragma: no cover - optional dependency for style retrieval
    TfidfVectorizer = None
    cosine_similarity = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - optional dependency for semantic retrieval
    SentenceTransformer = None


LETTERS = ["A", "B", "C", "D"]
GENERIC_PROMPT_PATTERNS = (
    re.compile(r"^关于[“\"]?.+[”\"]?，下列哪项"),
    re.compile(r"^下列哪项关于[“\"]?.+[”\"]?"),
    re.compile(r"^根据知识库内容，下列哪个"),
)


def ensure_style_packages() -> None:
    missing = []
    if jieba is None:
        missing.append("jieba")
    if BM25Okapi is None:
        missing.append("rank-bm25")
    if fuzz is None:
        missing.append("rapidfuzz")
    if TfidfVectorizer is None or cosine_similarity is None:
        missing.append("scikit-learn")
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "Style retrieval requires external packages. "
            f"Install them first: {joined}"
        )


def ensure_semantic_packages() -> None:
    if SentenceTransformer is None:
        raise RuntimeError(
            "Semantic retrieval requires sentence-transformers. "
            "Install it first: sentence-transformers"
        )


@lru_cache(maxsize=2)
def load_sentence_model(model_name: str) -> Any:
    ensure_semantic_packages()
    return SentenceTransformer(model_name)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower())
    return slug.strip("-") or "entry"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def tokenize_text(text: str) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []

    tokens: list[str] = []
    if jieba is not None:
        for token in jieba.lcut_for_search(cleaned):
            token = token.strip().lower()
            if len(token) >= 2:
                tokens.append(token)

    for token in re.findall(r"[A-Za-z][A-Za-z0-9\-/+.]{1,}", cleaned):
        tokens.append(token.lower())

    for token in re.findall(r"[\u4e00-\u9fff]{2,}", cleaned):
        if len(token) <= 12:
            tokens.append(token)

    deduped: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token not in seen:
            seen.add(token)
            deduped.append(token)
    return deduped


def informative_tokens(text: str) -> set[str]:
    return set(tokenize_text(text))


def looks_like_low_information_text(text: str) -> bool:
    lowered = normalize_text(text).lower()
    if any(marker in lowered for marker in ("email:", "@", "wx:", "qq:", "tel", "phone", "http://", "https://", "www.")):
        return True
    org_terms = {"大学", "学院", "学校", "系", "实验室", "college", "school", "department", "faculty", "university", "institute"}
    tokens = informative_tokens(text)
    if tokens and tokens.issubset(org_terms):
        return True
    return False


def is_fact_usable(entry: dict[str, Any], fact: dict[str, Any]) -> bool:
    answer = normalize_text(fact.get("answer", ""))
    if not answer or len(answer) > 96:
        return False
    if looks_like_low_information_text(answer):
        return False
    title_terms = informative_tokens(str(entry.get("title", "")))
    answer_terms = informative_tokens(answer)
    if title_terms and answer_terms and len(title_terms & answer_terms) / max(1, len(title_terms)) >= 0.8 and len(answer_terms) <= len(title_terms) + 2:
        return False
    return True


def entry_similarity(source_entry: dict[str, Any], candidate_entry: dict[str, Any]) -> int:
    score = 0
    if source_entry.get("module") and source_entry.get("module") == candidate_entry.get("module"):
        score += 3
    source_terms = set(source_entry.get("keywords") or []) | informative_tokens(str(source_entry.get("title", "")))
    candidate_terms = set(candidate_entry.get("keywords") or []) | informative_tokens(str(candidate_entry.get("title", "")))
    score += len(source_terms & candidate_terms)
    return score


def answer_signature(text: str) -> str:
    value = normalize_text(text)
    lowered = value.lower()
    if re.fullmatch(r"\d{2,4}(?:年|月|日)?", value) or re.fullmatch(r"\d+(?:\.\d+)?\s*(?:bp|kb|mb|gb|cm|cr|%|倍|次|个)?", lowered):
        return "numeric"
    if any(marker in value for marker in ("--", ">", "|", "/", ".py", ".sh", "nohup", "conda", "datasets ", "dataformat ")):
        return "command"
    if re.fullmatch(r"[A-Z][A-Za-z0-9\-/+. ]{1,24}", value):
        return "acronym"
    if re.fullmatch(r"[\u4e00-\u9fff]{2,12}", value):
        return "short_cjk"
    if len(value) <= 32:
        return "short_phrase"
    return "sentence"


def signature_compatible(correct_signature: str, candidate_signature: str) -> bool:
    if correct_signature == candidate_signature:
        return True
    compatible = {
        "short_cjk": {"short_phrase"},
        "short_phrase": {"short_cjk"},
        "numeric": set(),
        "acronym": {"short_phrase"},
        "command": set(),
        "sentence": {"short_phrase"},
    }
    return candidate_signature in compatible.get(correct_signature, set())


def is_generic_prompt(prompt: str, entry_title: str) -> bool:
    normalized = normalize_text(prompt)
    if not normalized:
        return True
    if entry_title and entry_title in normalized:
        return any(pattern.search(normalized) for pattern in GENERIC_PROMPT_PATTERNS)
    return any(pattern.search(normalized) for pattern in GENERIC_PROMPT_PATTERNS)


def question_to_document(question: dict[str, Any]) -> str:
    parts = [
        question.get("prompt", ""),
        question.get("analysis", ""),
        question.get("topicName", ""),
        question.get("topic", ""),
        question.get("type", ""),
        " ".join(question.get("tags", [])),
        " ".join(option.get("text", "") for option in question.get("options", [])),
    ]
    return normalize_text(" ".join(part for part in parts if part))


def normalize_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if abs(high - low) < 1e-9:
        return [1.0 if high > 0 else 0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


@dataclass
class StyleMatch:
    question: dict[str, Any]
    score: float
    bm25: float
    tfidf: float
    fuzzy: float
    semantic: float = 0.0


class QuestionStyleIndex:
    def __init__(self, questions: list[dict[str, Any]], *, semantic_model: Optional[str] = None) -> None:
        ensure_style_packages()
        self.questions = questions
        self.documents = [question_to_document(question) for question in questions]
        self.prompts = [normalize_text(question.get("prompt", "")) for question in questions]
        self.tokens = [tokenize_text(document) for document in self.documents]
        self.bm25 = BM25Okapi(self.tokens)
        self.vectorizer = TfidfVectorizer(
            tokenizer=tokenize_text,
            token_pattern=None,
            lowercase=False,
            ngram_range=(1, 2),
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
        self.semantic_model_name = semantic_model
        self.semantic_model = None
        self.semantic_matrix = None
        if semantic_model and self.documents:
            self.semantic_model = load_sentence_model(semantic_model)
            self.semantic_matrix = self.semantic_model.encode(
                self.documents,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

    def search(self, query_text: str, *, top_k: int = 5, desired_type: Optional[str] = None) -> list[StyleMatch]:
        if not self.questions:
            return []

        query_tokens = tokenize_text(query_text)
        if not query_tokens:
            return []

        bm25_raw = list(self.bm25.get_scores(query_tokens))
        tfidf_raw = list(cosine_similarity(self.vectorizer.transform([query_text]), self.tfidf_matrix)[0])
        fuzzy_raw = [float(fuzz.token_set_ratio(query_text, prompt)) / 100.0 for prompt in self.prompts]

        bm25_scores = normalize_scores(bm25_raw)
        tfidf_scores = normalize_scores(tfidf_raw)
        fuzzy_scores = normalize_scores(fuzzy_raw)
        semantic_scores = [0.0 for _ in self.questions]
        if self.semantic_model is not None and self.semantic_matrix is not None:
            query_embedding = self.semantic_model.encode(
                [query_text],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            semantic_raw = list(cosine_similarity(query_embedding, self.semantic_matrix)[0])
            semantic_scores = normalize_scores([float(value) for value in semantic_raw])

        matches: list[StyleMatch] = []
        for index, question in enumerate(self.questions):
            type_bonus = 0.08 if desired_type and question.get("type") == desired_type else 0.0
            if self.semantic_model is not None:
                score = (
                    0.24 * bm25_scores[index]
                    + 0.18 * tfidf_scores[index]
                    + 0.12 * fuzzy_scores[index]
                    + 0.38 * semantic_scores[index]
                    + type_bonus
                )
            else:
                score = 0.45 * bm25_scores[index] + 0.35 * tfidf_scores[index] + 0.20 * fuzzy_scores[index] + type_bonus
            matches.append(
                StyleMatch(
                    question=question,
                    score=score,
                    bm25=bm25_scores[index],
                    tfidf=tfidf_scores[index],
                    fuzzy=fuzzy_scores[index],
                    semantic=semantic_scores[index],
                )
            )

        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:top_k]

    def max_prompt_similarity(self, prompt: str) -> float:
        normalized = normalize_text(prompt)
        if not normalized:
            return 0.0
        return max((float(fuzz.token_set_ratio(normalized, existing)) for existing in self.prompts if existing), default=0.0)


def question_query_text(entry: dict[str, Any], fact: dict[str, Any]) -> str:
    segments = [
        entry.get("module", ""),
        entry.get("title", ""),
        entry.get("summary", ""),
        " ".join(entry.get("keywords", [])),
        fact.get("question", ""),
        fact.get("answer", ""),
        fact.get("explanation", ""),
    ]
    return normalize_text(" ".join(str(segment) for segment in segments if segment))


def prompt_from_exemplar(entry: dict[str, Any], fact: dict[str, Any], exemplar: Optional[dict[str, Any]]) -> str:
    title = normalize_text(entry.get("title", "该主题"))
    existing = normalize_text(fact.get("question", ""))
    if existing and not is_generic_prompt(existing, title):
        return existing

    answer = normalize_text(fact.get("answer", ""))
    signature = answer_signature(answer)
    exemplar_prompt = normalize_text(exemplar.get("prompt", "")) if exemplar else ""

    if "哪一年" in exemplar_prompt or "何时" in exemplar_prompt or "什么时候" in exemplar_prompt:
        return f"关于“{title}”，下列哪一年是正确的？"
    if "最适合" in exemplar_prompt:
        return f"下列哪一项最适合描述“{title}”？"
    if "是什么" in exemplar_prompt or "是指" in exemplar_prompt:
        return f"“{title}”是指什么？"
    if signature == "numeric":
        return f"关于“{title}”，下列哪个时间或数值是正确的？"
    if signature == "acronym":
        return f"关于“{title}”，下列哪一项术语或缩写是正确的？"
    if signature == "command":
        return f"关于“{title}”，下列哪项命令或参数写法是正确的？"
    return f"关于“{title}”，下列哪项表述正确？"


def candidate_distractors_from_bank(matches: list[StyleMatch], correct: str) -> list[str]:
    signature = answer_signature(correct)
    candidates: list[str] = []
    for match in matches:
        question = match.question
        for option in question.get("options", []):
            candidate = normalize_text(option.get("text", ""))
            if not candidate or candidate == correct:
                continue
            if len(candidate) > 96 or looks_like_low_information_text(candidate):
                continue
            if not signature_compatible(signature, answer_signature(candidate)):
                continue
            candidates.append(candidate)
    return candidates


def candidate_distractors_from_entries(source_entry: dict[str, Any], entries: list[dict[str, Any]], correct: str) -> list[str]:
    signature = answer_signature(correct)
    ranked_entries = [
        (entry, entry_similarity(source_entry, entry))
        for entry in entries
        if entry is not source_entry
    ]
    ranked_entries.sort(key=lambda item: item[1], reverse=True)
    pool: list[str] = []
    for entry, score in ranked_entries:
        if score <= 0:
            continue
        for distractor in entry.get("distractors", []):
            candidate = normalize_text(distractor)
            if candidate and candidate != correct and signature_compatible(signature, answer_signature(candidate)):
                pool.append(candidate)
        for fact in entry.get("facts", []):
            candidate = normalize_text(fact.get("answer", ""))
            if candidate and candidate != correct and is_fact_usable(entry, fact) and signature_compatible(signature, answer_signature(candidate)):
                pool.append(candidate)
        if len(pool) >= 24:
            break
    return pool


def build_options(
    correct: str,
    fact_distractors: list[str],
    source_entry: dict[str, Any],
    entries: list[dict[str, Any]],
    style_matches: list[StyleMatch],
    rng: random.Random,
) -> list[dict[str, str]]:
    distractors = [normalize_text(item) for item in fact_distractors if normalize_text(item)]
    candidate_pool = [
        *candidate_distractors_from_bank(style_matches, correct),
        *candidate_distractors_from_entries(source_entry, entries, correct),
    ]
    for candidate in candidate_pool:
        if candidate != correct and candidate not in distractors:
            distractors.append(candidate)
        if len(distractors) >= 3:
            break
    while len(distractors) < 3:
        distractors.append(f"不正确的备选项{len(distractors) + 1}")

    options = [correct, *distractors[:3]]
    rng.shuffle(options)
    return [{"key": LETTERS[index], "text": text} for index, text in enumerate(options)]


def load_question_bank(path: Union[str, Path]) -> list[dict[str, Any]]:
    payload = load_json(Path(path))
    return payload.get("questions", []) if isinstance(payload, dict) else payload


def synthesize_questions(
    entries: list[dict[str, Any]],
    count: int,
    seed: int,
    *,
    style_bank_questions: Optional[list[dict[str, Any]]] = None,
    style_top_k: int = 5,
    semantic_model: Optional[str] = None,
) -> dict[str, Any]:
    rng = random.Random(seed)
    style_index = (
        QuestionStyleIndex(style_bank_questions or [], semantic_model=semantic_model)
        if style_bank_questions
        else None
    )

    candidate_records: list[dict[str, Any]] = []
    for entry in entries:
        for fact in entry.get("facts", []):
            if not is_fact_usable(entry, fact):
                continue
            matches: list[StyleMatch] = []
            style_score = 0.0
            if style_index is not None:
                matches = style_index.search(question_query_text(entry, fact), top_k=style_top_k, desired_type=str(fact.get("type", "single_choice")))
                style_score = matches[0].score if matches else 0.0
            candidate_records.append(
                {
                    "entry": entry,
                    "fact": fact,
                    "matches": matches,
                    "style_score": style_score,
                    "tie_breaker": rng.random(),
                }
            )

    if not candidate_records:
        raise ValueError("No usable facts found in the knowledge base.")

    if style_index is not None:
        candidate_records.sort(key=lambda item: (item["style_score"], item["tie_breaker"]), reverse=True)
    else:
        rng.shuffle(candidate_records)

    selected_questions: list[dict[str, Any]] = []
    seen_prompts: set[str] = set()
    for record in candidate_records:
        if len(selected_questions) >= count:
            break

        entry = record["entry"]
        fact = record["fact"]
        matches = record["matches"]
        correct = normalize_text(fact.get("answer", ""))
        exemplar = matches[0].question if matches else None
        prompt = prompt_from_exemplar(entry, fact, exemplar)
        normalized_prompt = normalize_text(prompt)
        if normalized_prompt in seen_prompts:
            continue
        if style_index is not None and style_index.max_prompt_similarity(prompt) >= 96.0:
            continue

        options = build_options(correct, fact.get("distractors", []), entry, entries, matches, rng)
        answer_key = next(option["key"] for option in options if option["text"] == correct)
        topic = (exemplar.get("topic") if exemplar else None) or slugify(entry.get("id") or entry.get("title", "entry"))
        topic_name = (exemplar.get("topicName") if exemplar else None) or entry.get("title", "SynQuest 条目")
        difficulty = int(fact.get("difficulty") or (exemplar.get("difficulty") if exemplar else 2) or 2)
        selected_questions.append(
            {
                "id": f"sq-{topic}-{len(selected_questions) + 1:03d}",
                "source": "SynQuest",
                "origin": "semantic-generated" if semantic_model else "generated",
                "year": None,
                "topic": topic,
                "topicName": topic_name,
                "difficulty": difficulty,
                "type": fact.get("type") or (exemplar.get("type") if exemplar else "single_choice") or "single_choice",
                "prompt": prompt,
                "options": options,
                "answer": answer_key,
                "analysis": normalize_text(fact.get("explanation") or correct),
                "knowledgeRefs": [entry.get("id", topic)],
                "styleRefs": [match.question.get("id") for match in matches[:3] if match.question.get("id")],
                "tags": sorted(
                    {
                        topic,
                        "synquest",
                        fact.get("type", "single_choice"),
                        *(entry.get("keywords") or []),
                        *([exemplar.get("topic")] if exemplar and exemplar.get("topic") else []),
                    }
                ),
                "images": {"question": "", "note": ""},
                "pdfPage": None,
            }
        )
        seen_prompts.add(normalized_prompt)

    if not selected_questions:
        raise ValueError("No questions survived the style-homology and duplicate filters.")

    return {
        "meta": {
            "title": "SynQuest Generated Questions",
            "count": len(selected_questions),
            "seed": seed,
            "styleBankQuestions": len(style_bank_questions or []),
            "styleTopK": style_top_k if style_bank_questions else 0,
            "semanticModel": semantic_model or "",
            "algorithms": [
                "knowledge_fact_filtering",
                "jieba_tokenization" if jieba is not None else "regex_tokenization",
                "bm25_style_retrieval" if style_bank_questions else "knowledge_only_sampling",
                "tfidf_style_retrieval" if style_bank_questions else "none",
                "semantic_embedding_retrieval" if semantic_model else "none",
                "hybrid_style_rerank" if semantic_model else "none",
                "rapidfuzz_prompt_dedup" if style_bank_questions else "none",
                "style_guided_prompt_adaptation" if style_bank_questions else "generic_prompt_assembly",
            ],
        },
        "questions": selected_questions,
    }
