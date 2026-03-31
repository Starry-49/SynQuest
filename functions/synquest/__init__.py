"""SynQuest reusable package surface."""

from typing import Any

__version__ = "0.2.0"

from .knowledge_loader import (  # noqa: E402
    SUPPORTED_SUFFIXES,
    build_knowledge_base,
    inspect_knowledge_source,
    load_knowledge_entries,
    read_knowledge_text,
)


def build_figure_track(*args: Any, **kwargs: Any) -> Any:
    from .figure_track import build_figure_track as _build_figure_track

    return _build_figure_track(*args, **kwargs)


def load_figure_track(path: Any) -> Any:
    from .figure_track import load_figure_track as _load_figure_track

    return _load_figure_track(path)


def load_question_bank(path: Any) -> Any:
    from .question_engine import load_question_bank as _load_question_bank

    return _load_question_bank(path)


def synthesize_questions(*args: Any, **kwargs: Any) -> Any:
    from .question_engine import synthesize_questions as _synthesize_questions

    return _synthesize_questions(*args, **kwargs)


def synthesize_figure_questions(*args: Any, **kwargs: Any) -> Any:
    from .figure_track import synthesize_figure_questions as _synthesize_figure_questions

    return _synthesize_figure_questions(*args, **kwargs)


__all__ = [
    "__version__",
    "SUPPORTED_SUFFIXES",
    "build_knowledge_base",
    "build_figure_track",
    "inspect_knowledge_source",
    "load_figure_track",
    "load_question_bank",
    "load_knowledge_entries",
    "read_knowledge_text",
    "synthesize_figure_questions",
    "synthesize_questions",
]
