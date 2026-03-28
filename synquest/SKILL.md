---
name: "SynQuest"
description: "Use when generating question banks from a domain knowledge base, normalizing legacy exam questions, synthesizing new quiz items, or merging generated questions into a reusable repository. Applies to curriculum design, exam bank migration, GitHub Pages quiz demos, and domain-specific practice generation."
---

# SynQuest

SynQuest turns a structured domain knowledge base into reusable quiz items and a portable question bank.

## When to use it

- The user provides a knowledge base in `json`, `md`, `txt`, or `html` and wants new questions.
- There is an existing local exam bank that should be normalized into JSON.
- A GitHub Pages demo needs to browse, quiz, and extend a question bank without a backend.
- You need deterministic question synthesis before optional LLM polishing.

## Workflow

1. Inspect the knowledge base format.
   - Prefer `json` with `entries[].facts[]` for higher-quality generation.
   - For `md` or `html`, split by headings and bullet facts first.
2. Generate candidate questions with the bundled CLI:
   - `python3 synquest/scripts/synquest.py inspect --kb <path>`
   - `python3 synquest/scripts/synquest.py synthesize --kb <path> --count 12 --out data/generated/synquest.json`
3. Validate the generated schema against [question_schema.md](references/question_schema.md).
4. Merge curated output into the main bank:
   - `python3 synquest/scripts/synquest.py merge --bank data/question-bank.json --incoming data/generated/synquest.json`
5. If a static site is involved, keep generated questions browser-local first, then export JSON for repo commit.

## Input guidance

- `json`: Best choice. Use `entries[].facts[]` with `question`, `answer`, `explanation`, and `distractors`.
- `md` / `txt`: Use `##` headings for topics and bullet facts below each heading.
- `html`: Use semantic headings and lists when possible. The script strips tags and falls back to paragraph text.

## Output expectations

- Stable IDs such as `sq-hgp-maps-001`.
- Explicit `type`, `topic`, `difficulty`, `options`, `answer`, and `analysis`.
- Distractors drawn from sibling entries or explicit confusion sets.
- JSON that can be committed directly or loaded in a frontend demo.

## Repository notes

- The CLI is intentionally deterministic and dependency-free.
- For better question quality, enrich the KB with confusions and distractors instead of overloading the prompt layer.
- Keep browser-generated questions in `localStorage` or `data/generated/` until they are reviewed.

## References

- Schema: [references/question_schema.md](references/question_schema.md)
- Formats: [references/knowledge_base_formats.md](references/knowledge_base_formats.md)
