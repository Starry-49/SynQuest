<p align="center">
  <img src="logo.png" alt="SynQuest Logo" width="120">
</p>

<h1 align="center">SynQuest</h1>

<p align="center">
  把知识源转换成结构化题库的可复用 skill 与 Python functions。<br>
  仓库同时附带 Geno 示例门户，用于演示知识阅读、题库浏览、在线答题与新题生成。
</p>

<p align="center">
  Live Demo: <a href="https://starry-49.github.io/SynQuest/">https://starry-49.github.io/SynQuest/</a>
</p>

<p align="center">
  <a href="#中文"><strong>中文</strong></a> ·
  <a href="#english"><strong>English</strong></a>
</p>

<p align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-14532D?style=flat-square" alt="MIT License">
  </a>
  <a href="https://starry-49.github.io/SynQuest/">
    <img src="https://img.shields.io/badge/Demo-Geno%20Portal-CF9E2A?style=flat-square" alt="Geno Demo">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-2F5D50?style=flat-square" alt="Python 3.10+">
  </a>
  <a href="skills/synquest/SKILL.md">
    <img src="https://img.shields.io/badge/Codex-SynQuest-1D6A4F?style=flat-square" alt="Codex SynQuest">
  </a>
</p>

<p align="center">
  <a href="#快速开始"><strong>快速开始</strong></a> ·
  <a href="#核心能力"><strong>核心能力</strong></a> ·
  <a href="#架构"><strong>架构</strong></a> ·
  <a href="#geno-示例"><strong>Geno 示例</strong></a> ·
  <a href="#python-接口"><strong>Python 接口</strong></a> ·
  <a href="#依赖与致谢"><strong>依赖与致谢</strong></a> ·
  <a href="#仓库结构"><strong>仓库结构</strong></a>
</p>

## 中文

### 快速开始

先体验在线示例：

- Demo: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- Repo: [https://github.com/Starry-49/SynQuest](https://github.com/Starry-49/SynQuest)

本地预览 Geno 门户：

```bash
python3 -m http.server 8000
```

打开：

```text
http://localhost:8000/example/
```

用 CLI 检查知识源：

```bash
python3 functions/synquest/cli.py inspect \
  --kb example/data/knowledge-base/genome-informatics-core.json
```

把原始知识源抽取成标准知识库 JSON：

```bash
python3 functions/synquest/cli.py extract \
  --source sum.pdf \
  --out example/data/knowledge-base/sum-course-kb.json
```

基于知识库生成新题：

```bash
python3 functions/synquest/cli.py synthesize \
  --kb example/data/knowledge-base/sum-course-kb.json \
  --count 24 \
  --out example/data/generated/synquest-batch.json
```

如果希望新题更接近现有题库的风格与问法，可以加入旧题检索：

```bash
python3 functions/synquest/cli.py synthesize \
  --kb example/data/knowledge-base/sum-course-kb.json \
  --style-bank example/data/question-bank.json \
  --style-top-k 5 \
  --count 24 \
  --out example/data/generated/sum-course-generated.json
```

把生成题并回题库：

```bash
python3 functions/synquest/cli.py merge \
  --bank example/data/question-bank.json \
  --incoming example/data/generated/sum-course-generated.json
```

### 核心能力

SynQuest 面向三类使用场景：

- 多格式知识源接入：支持 `json`、`md`、`txt`、`html`、`docx`、`pdf`、`pptx`
- 标准知识库生成：统一规整为 `entries[] + facts[]`
- 新题生成与题库扩展：既可直接从知识库出题，也可参考现有题库风格生成同源新题

在这套仓库里：

- `skills/` 提供 Codex 可直接调用的 skill 定义
- `functions/` 提供可复用的 Python functions 与 CLI
- `example/` 提供 Geno 示例门户与示例数据

### 架构

```mermaid
flowchart TB
    A["知识源 / Knowledge Sources<br/>json / md / txt / html / docx / pdf / pptx"]
    B["Skill 层 / Skill Layer<br/>skills/synquest/SKILL.md"]
    C["知识抽取 / Knowledge Loader<br/>functions/synquest/knowledge_loader.py"]
    D["标准知识库 / Normalized Knowledge Base<br/>entries[] + facts[]"]
    E["旧题风格索引 / Style Retrieval Index<br/>BM25 + TF-IDF + RapidFuzz"]
    F["出题引擎 / Question Engine<br/>functions/synquest/question_engine.py"]
    G["题目 JSON / Generated Question JSON"]
    H["Geno 示例门户 / Geno Example Portal<br/>example/"]
    I["正式题库 / Question Bank Merge"]

    A --> C
    B --> C
    C --> D
    D --> F
    I --> E
    E --> F
    F --> G
    D --> H
    G --> H
    I --> H
```

#### 架构单元与字段 / Architecture Units and Fields

| 中文 | English | 作用 |
| --- | --- | --- |
| 知识源 | Knowledge Source | 原始课程材料、文档、网页或课件 |
| 知识条目 | Entry | 一个主题、章节、页面或模块 |
| 事实单元 | Fact | 可被出题的最小知识片段 |
| 标准知识库 | Normalized Knowledge Base | 统一后的 `entries[] + facts[]` 数据层 |
| 现有题库 | Existing Question Bank | 已整理好的正式题目集合 |
| 风格索引 | Style Retrieval Index | 用于召回相近旧题的检索层 |
| 生成题 | Generated Questions | 新生成、待预览或待合并的新题 |

#### 核心字段 / Core Fields

| Field | 中文含义 | English Meaning |
| --- | --- | --- |
| `id` | 条目标识 | entry identifier |
| `module` | 所属模块 | module / chapter |
| `title` | 条目标题 | entry title |
| `summary` | 条目摘要 | entry summary |
| `keywords` | 关键词 | keywords |
| `facts` | 事实列表 | fact list |
| `question` | 候选题干 | question prompt |
| `answer` | 正确答案 | correct answer |
| `explanation` | 解析或依据 | explanation / rationale |
| `distractors` | 干扰项 | distractors |
| `styleRefs` | 参考旧题 | retrieved style exemplars |

### 工作原理

#### 1. 知识抽取

SynQuest 先把不同格式的知识源统一抽成标准知识库。输出的数据结构对前端、CLI 和后续合并流程一致，方便在不同项目里重复使用。

#### 2. 新题生成

SynQuest 提供两种生成模式：

- 知识库直出：从 `facts` 中选择可出题事实，直接组装题目
- 风格对齐生成：在已有题库中检索最相近的旧题，再参考其题型、问法、难度和表达风格生成新题

当前风格对齐链路使用：

- `jieba` 做中文分词
- `BM25` 做词法召回
- `TF-IDF + cosine similarity` 做文本相似度补充
- `RapidFuzz` 做题干近重复过滤

这意味着 SynQuest 不是把 prompt 写死在页面里，而是通过“知识事实 + 旧题风格检索”来生成更接近现有题库的新题。

#### 3. 题库合并

生成题输出为与题库兼容的 JSON。你可以直接：

- 在 Geno 门户里预览
- 导出为独立批次
- 再合并回正式题库

### Geno 示例

```mermaid
flowchart LR
    A["示例知识库 / Example Knowledge Base<br/>example/data/knowledge-base/genome-informatics-core.json"]
    B["PDF 抽取知识库 / Imported Slide KB<br/>example/data/knowledge-base/sum-course-kb.json"]
    C["现有题库 / Existing Question Bank<br/>example/data/question-bank.json"]
    D["检索增强生成题 / Style-Aligned Generated Questions<br/>example/data/generated/sum-course-generated.json"]
    E["答题页 / Practice Page<br/>example/practice.html"]
    F["阅读页 / Reader Page<br/>example/reader.html"]
    G["门户页 / Portal Entry<br/>example/index.html"]

    A --> D
    B --> D
    A --> F
    B --> F
    C --> E
    D --> E
    G --> E
    G --> F
```

Geno 示例门户展示的是 SynQuest 在《基因组信息学》示例数据上的一个完整落地：

- 示例知识库：[`example/data/knowledge-base/genome-informatics-core.json`](example/data/knowledge-base/genome-informatics-core.json)
- PDF 抽取知识库：[`example/data/knowledge-base/sum-course-kb.json`](example/data/knowledge-base/sum-course-kb.json)
- 现有题库：[`example/data/question-bank.json`](example/data/question-bank.json)
- 检索增强生成题：[`example/data/generated/sum-course-generated.json`](example/data/generated/sum-course-generated.json)

在这个 example 中：

- 知识库负责“系统知道什么”
- 现有题库负责“系统已经整理了哪些题”
- 生成题负责“系统可以扩展出哪些新题”

### Python 接口

可复用能力位于 [`functions/synquest/`](functions/synquest/)：

- [`functions/synquest/knowledge_loader.py`](functions/synquest/knowledge_loader.py): 多格式知识源接入与标准化
- [`functions/synquest/question_engine.py`](functions/synquest/question_engine.py): 新题生成、旧题检索、风格对齐
- [`functions/synquest/cli.py`](functions/synquest/cli.py): inspect / extract / synthesize / merge

可以直接在自己的脚本里调用：

```python
from functions.synquest import (
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

### 依赖与致谢

SynQuest 的核心流程以自编脚本为主，同时明确复用了以下通用算法与工具：

- `jieba`: 中文分词
- `rank-bm25`: BM25 词法检索
- `scikit-learn`: TF-IDF 与 cosine similarity
- `RapidFuzz`: 字符串相似度与近重复过滤
- `Poppler` 工具链：`pdftotext`、`pdfinfo`、`pdfimages`，用于 PDF 文本与页面信息抽取

这些组件主要用于两类能力：

- 多格式知识源抽取与标准化
- 基于已有题库的风格检索与新题生成

### 仓库结构

```text
.
├── skills/
│   └── synquest/
│       ├── agents/
│       ├── references/
│       └── SKILL.md
├── functions/
│   ├── build_example_bank.py
│   └── synquest/
│       ├── __init__.py
│       ├── cli.py
│       ├── knowledge_loader.py
│       └── question_engine.py
├── example/
│   ├── assets/
│   ├── data/
│   ├── images/
│   ├── legacy/
│   ├── user_data/
│   ├── index.html
│   ├── practice.html
│   └── reader.html
├── index.html
├── logo.png
├── LICENSE
└── README.md
```

目录职责：

- `skills/`: SynQuest 的 skill 定义、agent 配置与参考说明
- `functions/`: 知识抽取、题目生成、题库合并等可复用 Python 能力
- `example/`: Geno 示例门户、示例题库、示例知识库与前端页面

## English

### Overview

SynQuest is a reusable skill and Python toolkit for turning domain knowledge sources into structured question banks. This repository also ships with a Geno example portal that demonstrates knowledge browsing, practice, reading, and question generation on a real example dataset.

### Quick Start

Open the live demo:

- Demo: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- Repo: [https://github.com/Starry-49/SynQuest](https://github.com/Starry-49/SynQuest)

Preview locally:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/example/
```

Inspect a knowledge source:

```bash
python3 functions/synquest/cli.py inspect \
  --kb example/data/knowledge-base/genome-informatics-core.json
```

Extract a reusable knowledge-base JSON:

```bash
python3 functions/synquest/cli.py extract \
  --source sum.pdf \
  --out example/data/knowledge-base/sum-course-kb.json
```

Generate questions directly from the knowledge base:

```bash
python3 functions/synquest/cli.py synthesize \
  --kb example/data/knowledge-base/sum-course-kb.json \
  --count 24 \
  --out example/data/generated/synquest-batch.json
```

Generate questions that stay closer to an existing bank:

```bash
python3 functions/synquest/cli.py synthesize \
  --kb example/data/knowledge-base/sum-course-kb.json \
  --style-bank example/data/question-bank.json \
  --style-top-k 5 \
  --count 24 \
  --out example/data/generated/sum-course-generated.json
```

### Pipeline

SynQuest separates the workflow into three reusable layers:

- `skills/` for orchestration and agent usage
- `functions/` for extraction, normalization, style retrieval, generation, and merge logic
- `example/` for the Geno demo portal and demo datasets

The current generation engine combines:

- multi-format knowledge extraction
- normalized `entries[] + facts[]` storage
- BM25 retrieval over existing questions
- TF-IDF similarity scoring
- RapidFuzz prompt deduplication
- style-guided question synthesis

### References and Acknowledgements

SynQuest is built mainly as custom repository logic, with these external algorithms and tools used as reusable building blocks:

- `jieba`
- `rank-bm25`
- `scikit-learn`
- `RapidFuzz`
- `Poppler` utilities

## License

This project uses the [MIT License](LICENSE).
