<p align="center">
  <img src="logo.png" alt="SynQuest Logo" width="120">
</p>

<h1 align="center">SynQuest</h1>

<p align="center">
  一个可复用的 skill 与 Python toolkit，用来把多格式知识源转换成结构化知识库，并生成可并入题库的新题。
</p>

<p align="center">
  <a href="README.en.md"><strong>English</strong></a> ·
  <a href="https://starry-49.github.io/SynQuest/"><strong>Live Demo</strong></a> ·
  <a href="https://github.com/Starry-49/SynQuest/releases/tag/v0.2.1"><strong>Release</strong></a>
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

## 快速开始

先看在线示例：

- Demo: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- Repo: [https://github.com/Starry-49/SynQuest](https://github.com/Starry-49/SynQuest)

安装 Python CLI：

```bash
pip install "git+https://github.com/Starry-49/SynQuest.git@v0.2.1"
synquest --help
```

如果你已经下载 release 源码包，或者本地 clone 了仓库，也可以直接安装内置 skill：

```bash
python3 scripts/install_codex_skill.py
```

本地预览 Geno：

```bash
python3 -m http.server 8000
```

打开：

```text
http://localhost:8000/example/
```

## 核心能力

SynQuest 围绕三层能力设计：

- 多格式知识源接入：支持 `json`、`md`、`txt`、`html`、`docx`、`pdf`、`pptx`
- 标准知识库构建：统一规整为 `entries[] + facts[] + metadata`
- 检索增强出题：可直接从知识事实出题，也可参考已有题库风格生成同源新题

仓库结构对应三层：

- `skills/`：Codex skill 定义
- `functions/`：可复用 Python functions 与 CLI
- `example/`：Geno 示例门户与示例数据

## 架构

<p align="center">
  <img src="structure.png" alt="SynQuest architecture" width="100%">
</p>

## 工作原理

### 1. Knowledge Ingestion

SynQuest 先把不同格式的知识源统一抽成标准知识库。当前仓库中已经接入的抽取链路包括：

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

SynQuest 当前主用的生成路径是 semantic retrieval + hybrid rerank。已接入组件包括：

- `jieba`
- `BM25`
- `TF-IDF + cosine similarity`
- `sentence-transformers`
- hybrid rerank
- `RapidFuzz`
- adaptive similarity fallback
- rule-based prompt diversification
- style-guided prompt adaptation

这条路径会结合：

- 知识库中的事实
- 现有题库中的旧题风格
- 去重与过滤规则

输出与现有题库兼容的 JSON 题目批次。

### 3. Figure Track

仓库里保留了一条独立的 figure track，用于从带图知识源中：

- 筛选带图页面
- 自动截图或复制图像
- 绑定近缘文字
- 生成要求解释图意的带图题

当前 figure track 代码仍然保留在仓库中，但 Geno 在线题库默认不展示 figure 题。

## Geno 示例

Geno 是 SynQuest 的示例门户，而不是核心引擎本身。它用来展示：

- 首页入口
- Practice 答题页
- Reader 知识阅读页

当前 Geno 在线题库默认展示经过整理的示例题和一批内置的 `SynQuest semantic` 题。figure track 的代码、脚本和生成批次仍保留在 repo 中，方便你本地继续扩展。

与 Geno 相关的主要数据资产包括：

- 示例知识库：[`example/data/knowledge-base/genome-informatics-core.json`](example/data/knowledge-base/genome-informatics-core.json)
- 正式题库：[`example/data/question-bank.json`](example/data/question-bank.json)
- 生成批次目录：[`example/data/generated/`](example/data/generated/)
- 示例门户：[`example/`](example/)

## CLI 用法

检查知识源：

```bash
synquest inspect \
  --kb example/data/knowledge-base/genome-informatics-core.json
```

抽取标准知识库：

```bash
synquest extract \
  --source sum.pdf \
  --out example/data/knowledge-base/sum-course-kb.json
```

生成新题：

```bash
synquest synthesize \
  --kb example/data/knowledge-base/sum-course-kb.json \
  --style-bank example/data/question-bank.json \
  --semantic-model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
  --style-top-k 5 \
  --count 24 \
  --out example/data/generated/synquest-batch.json
```

并回题库：

```bash
synquest merge \
  --bank example/data/question-bank.json \
  --incoming example/data/generated/synquest-batch.json
```

生成 figure 题：

```bash
synquest synthesize-figure-questions \
  --source sum.pdf \
  --kb example/data/knowledge-base/sum-course-kb.json \
  --count 2 \
  --asset-dir example/assets/figures \
  --out example/data/generated/figure-demo-two.json
```

## Python API

可复用逻辑位于 [`functions/synquest/`](functions/synquest/)：

- [`functions/synquest/knowledge_loader.py`](functions/synquest/knowledge_loader.py)
- [`functions/synquest/question_engine.py`](functions/synquest/question_engine.py)
- [`functions/synquest/figure_track.py`](functions/synquest/figure_track.py)
- [`functions/synquest/cli.py`](functions/synquest/cli.py)

示例：

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

## 依赖与致谢

SynQuest 的主流程以仓库内自编逻辑为主，同时复用了这些通用算法与工具：

- `jieba`
- `rank-bm25`
- `scikit-learn`
- `sentence-transformers`
- `RapidFuzz`
- `Poppler` utilities
- `pdftoppm`

Release 页面：

- [v0.2.1](https://github.com/Starry-49/SynQuest/releases/tag/v0.2.1)

## 仓库结构

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
