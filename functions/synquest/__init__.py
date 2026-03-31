"""SynQuest reusable package surface."""

from typing import Any

__version__ = "0.1.1"

from .knowledge_loader import (  # noqa: E402
    SUPPORTED_SUFFIXES,
    build_knowledge_base,
    inspect_knowledge_source,
    load_knowledge_entries,
    read_knowledge_text,
)


def load_question_bank(path: Any) -> Any:
    from .question_engine import load_question_bank as _load_question_bank

    return _load_question_bank(path)


def synthesize_questions(*args: Any, **kwargs: Any) -> Any:
    from .question_engine import synthesize_questions as _synthesize_questions

    return _synthesize_questions(*args, **kwargs)


__all__ = [
    "__version__",
    "SUPPORTED_SUFFIXES",
    "build_knowledge_base",
    "inspect_knowledge_source",
    "load_question_bank",
    "load_knowledge_entries",
    "read_knowledge_text",
    "synthesize_questions",
]
