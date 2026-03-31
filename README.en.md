<p align="center">
  <img src="logo.png" alt="SynQuest Logo" width="120">
</p>

<h1 align="center">SynQuest</h1>

<p align="center">
  A reusable skill and Python toolkit for turning heterogeneous knowledge sources into structured knowledge bases and style-aligned question banks.
</p>

<p align="center">
  <a href="README.md"><strong>中文</strong></a> ·
  <a href="https://starry-49.github.io/SynQuest/"><strong>Live Demo</strong></a> ·
  <a href="https://github.com/Starry-49/SynQuest/releases/tag/v0.2.0"><strong>Release</strong></a>
</p>

<p align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-14532D?style=flat-square" alt="MIT License">
  </a>
  <a href="https://starry-49.github.io/SynQuest/">
    <img src="https://img.shields.io/badge/Demo-Geno%20Portal-CF9E2A?style=flat-square" alt="Geno Demo">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.9%2B-2F5D50?style=flat-square" alt="Python 3.9+">
  </a>
  <a href="skills/synquest/SKILL.md">
    <img src="https://img.shields.io/badge/Codex-SynQuest-1D6A4F?style=flat-square" alt="Codex SynQuest">
  </a>
</p>

## Quick Start

Start with the live demo:

- Demo: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- Repo: [https://github.com/Starry-49/SynQuest](https://github.com/Starry-49/SynQuest)

Install the Python CLI:

```bash
pip install "git+https://github.com/Starry-49/SynQuest.git@v0.2.0"
synquest --help
```

If you downloaded a release bundle or cloned the repository locally, install the bundled Codex skill with:

```bash
python3 scripts/install_codex_skill.py
```

Preview Geno locally:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/example/
```

## Core Capabilities

SynQuest is organized around three reusable layers:

- multi-format knowledge ingestion for `json`, `md`, `txt`, `html`, `docx`, `pdf`, and `pptx`
- normalized knowledge-base construction as `entries[] + facts[] + metadata`
- retrieval-augmented question generation aligned to an existing curated bank

Repository layers:

- `skills/` for Codex skill orchestration
- `functions/` for reusable Python logic and CLI tools
- `example/` for the Geno portal and demo datasets

## Architecture

<p align="center">
  <img src="structure.png" alt="SynQuest architecture" width="100%">
</p>

## How It Works

### 1. Knowledge Ingestion

SynQuest normalizes heterogeneous source formats into a common knowledge-base schema. The current repository includes:

- JSON passthrough
- text section segmentation
- PDF raw-order extraction
- layout-preserving title detection
- repeated header/footer suppression
- duplicate slide fingerprint deduplication
- keyword weighting
- fact segmentation
- PPTX OOXML parsing

### 2. Semantic Question Generation

The main generation path currently used by Geno is semantic retrieval plus hybrid reranking. The current stack includes:

- `jieba`
- `BM25`
- `TF-IDF + cosine similarity`
- `sentence-transformers`
- hybrid rerank
- `RapidFuzz`
- adaptive similarity fallback
- rule-based prompt diversification
- style-guided prompt adaptation

This path combines:

- facts from the knowledge base
- style cues from an existing question bank
- filtering and deduplication rules

to produce bank-compatible question batches.

### 3. Figure Track

The repository also retains an independent figure track that can:

- identify image-backed pages
- render or copy figure assets
- bind figures to nearby text context
- generate image-based questions that ask for figure interpretation

The figure track code is retained in the repository, but the live Geno bank currently focuses on curated semantic questions.

## Geno Example

Geno is the example portal, not the reusable engine itself. It demonstrates:

- Home
- Practice
- Reader

The live Geno bank currently shows curated example questions together with embedded `SynQuest semantic` questions. Generated figure batches and figure-track code remain available in the repository for local extension.

Main example assets:

- example KB: [`example/data/knowledge-base/genome-informatics-core.json`](example/data/knowledge-base/genome-informatics-core.json)
- main bank: [`example/data/question-bank.json`](example/data/question-bank.json)
- generated batches: [`example/data/generated/`](example/data/generated/)
- portal files: [`example/`](example/)

## CLI Usage

Inspect a knowledge source:

```bash
synquest inspect \
  --kb example/data/knowledge-base/genome-informatics-core.json
```

Extract a reusable knowledge-base JSON:

```bash
synquest extract \
  --source sum.pdf \
  --out example/data/knowledge-base/sum-course-kb.json
```

Generate questions:

```bash
synquest synthesize \
  --kb example/data/knowledge-base/sum-course-kb.json \
  --style-bank example/data/question-bank.json \
  --semantic-model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
  --style-top-k 5 \
  --count 24 \
  --out example/data/generated/synquest-batch.json
```

Merge generated questions:

```bash
synquest merge \
  --bank example/data/question-bank.json \
  --incoming example/data/generated/synquest-batch.json
```

Generate figure questions:

```bash
synquest synthesize-figure-questions \
  --source sum.pdf \
  --kb example/data/knowledge-base/sum-course-kb.json \
  --count 2 \
  --asset-dir example/assets/figures \
  --out example/data/generated/figure-demo-two.json
```

## Python API

Reusable logic lives in [`functions/synquest/`](functions/synquest/):

- [`functions/synquest/knowledge_loader.py`](functions/synquest/knowledge_loader.py)
- [`functions/synquest/question_engine.py`](functions/synquest/question_engine.py)
- [`functions/synquest/figure_track.py`](functions/synquest/figure_track.py)
- [`functions/synquest/cli.py`](functions/synquest/cli.py)

Example:

```python
from synquest import (
    build_knowledge_base,
    inspect_knowledge_source,
    load_knowledge_entries,
    load_question_bank,
    synthesize_questions,
)

report = inspect_knowledge_source("slides.pdf")
kb = build_knowledge_base("slides.pdf")
entries = load_knowledge_entries("slides.pdf")
style_bank = load_question_bank("example/data/question-bank.json")

generated = synthesize_questions(
    entries,
    count=12,
    seed=28,
    style_bank_questions=style_bank,
    style_top_k=5,
)
```

## Dependencies and Acknowledgements

SynQuest is primarily custom repository logic, with these reusable external components:

- `jieba`
- `rank-bm25`
- `scikit-learn`
- `sentence-transformers`
- `RapidFuzz`
- `Poppler` utilities
- `pdftoppm`

Release page:

- [v0.2.0](https://github.com/Starry-49/SynQuest/releases/tag/v0.2.0)

## Repository Structure

```text
.
├── skills/
├── functions/
├── example/
├── scripts/
├── index.html
├── logo.png
├── structure.png
├── LICENSE
├── README.md
└── README.en.md
```

## License

This project uses the [MIT License](LICENSE).
