---
name: "SynQuest"
description: "Use when generating question banks from domain knowledge bases, normalizing legacy exam assets, synthesizing new quiz items, or wiring a static example portal on top of reusable Python functions."
---

# SynQuest

SynQuest is the reusable skill layer for turning knowledge sources into structured question banks.

## When to use it

- The user provides a knowledge source in `json`, `md`, `txt`, `html`, or `docx` and wants questions.
- A legacy HTML exam page needs to be normalized into reusable JSON.
- A static demo site needs to browse, answer, and extend a question bank without a backend.
- The repo should separate `skills/`, `functions/`, and `example/` cleanly.

## Workflow

1. Inspect the incoming knowledge source.
   - Prefer `json` with `entries[].facts[]` when available.
   - For `md`, `txt`, `html`, and `docx`, let the reusable loader normalize it first.
2. Use the bundled CLI in `functions/`:
   - `python3 functions/synquest/cli.py inspect --kb <path>`
   - `python3 functions/synquest/cli.py synthesize --kb <path> --count 12 --out example/data/generated/synquest.json`
3. Validate the generated question shape against [question_schema.md](references/question_schema.md).
4. Merge curated output back into the example bank or your own bank:
   - `python3 functions/synquest/cli.py merge --bank example/data/question-bank.json --incoming example/data/generated/synquest.json`
5. If a static site is involved, keep browser-generated questions local first, then export JSON for commit.

## Repository layout

- `skills/synquest/`: skill entry, references, agent config
- `functions/synquest/`: reusable Python functions and CLI
- `example/`: Geno example portal, example bank, example KB, legacy assets, and images

## Input guidance

- `json`: Best choice. Use `entries[].facts[]` with `question`, `answer`, `explanation`, and `distractors`.
- `md` / `txt`: Use headings and short factual lines under each section.
- `html`: Prefer semantic headings and lists; the loader strips tags into readable text.
- `docx`: Paragraph text is extracted directly and normalized into entries.

## Output expectations

- Stable IDs such as `sq-hgp-maps-001`
- Explicit `type`, `topic`, `difficulty`, `options`, `answer`, and `analysis`
- JSON that can be reused by both CLI and static frontend demo layers

## References

- Schema: [references/question_schema.md](references/question_schema.md)
- Formats: [references/knowledge_base_formats.md](references/knowledge_base_formats.md)
