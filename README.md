<p align="center">
  <img src="logo.png" alt="SynQuest Logo" width="120">
</p>

<h1 align="center">SynQuest</h1>

<p align="center">
  一个可复用的 skill + Python functions 组合，用来把知识源转换成结构化题库。<br>
  仓库内同时附带一个 Geno 示例门户网站，用来展示题库浏览、在线答题、知识阅读与新题生成。
</p>

<p align="center">
  在线演示: <a href="https://starry-49.github.io/SynQuest/">https://starry-49.github.io/SynQuest/</a>
</p>

<p align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-14532D?style=flat-square" alt="MIT License">
  </a>
  <a href="https://starry-49.github.io/SynQuest/">
    <img src="https://img.shields.io/badge/GitHub%20Pages-ready-CF9E2A?style=flat-square" alt="GitHub Pages Ready">
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
  <a href="#可复用-functions"><strong>可复用 Functions</strong></a> ·
  <a href="#geno-示例门户"><strong>Geno 示例门户</strong></a> ·
  <a href="#仓库结构"><strong>仓库结构</strong></a>
</p>

## 快速开始

### 1. 先打开在线 demo

- Live Demo: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- Repo: [https://github.com/Starry-49/SynQuest](https://github.com/Starry-49/SynQuest)

### 2. 本地预览 Geno 门户

仓库已经带了示例题库和示例知识库，不需要先手动生成题目。

```bash
python3 -m http.server 8000
```

打开：

```text
http://localhost:8000/example/
```

### 3. 用 CLI 处理知识源

检查知识源：

```bash
python3 functions/synquest/cli.py inspect \
  --kb example/data/knowledge-base/genome-informatics-core.json
```

生成新题：

```bash
python3 functions/synquest/cli.py synthesize \
  --kb example/data/knowledge-base/genome-informatics-core.json \
  --count 12 \
  --out example/data/generated/synquest-batch.json
```

把新题并回题库：

```bash
python3 functions/synquest/cli.py merge \
  --bank example/data/question-bank.json \
  --incoming example/data/generated/synquest-batch.json
```

### 4. 可选：重建 Geno 示例题库

只有当你想重新从旧版 HTML 素材提取示例题库时，才需要执行：

```bash
python3 functions/build_example_bank.py
```

## 可复用 Functions

仓库里最核心的 Python 能力位于 [`functions/synquest/`](functions/synquest/)。

目前提供的可复用入口包括：

- [`functions/synquest/knowledge_loader.py`](functions/synquest/knowledge_loader.py): 统一读取知识源
- [`functions/synquest/cli.py`](functions/synquest/cli.py): inspect / synthesize / merge
- [`functions/build_example_bank.py`](functions/build_example_bank.py): 从旧版 HTML 重建 Geno 示例题库

支持的知识源格式：

- `json`
- `md`
- `txt`
- `html`
- `docx`

如果你想在自己的脚本里直接复用：

```python
from functions.synquest import (
    SUPPORTED_SUFFIXES,
    inspect_knowledge_source,
    load_knowledge_entries,
    read_knowledge_text,
)

report = inspect_knowledge_source("notes.docx")
entries = load_knowledge_entries("notes.docx")
```

## Geno 示例门户

门户页面位于 [`example/`](example/)。

它负责展示三类能力：

- 题库浏览与在线答题：[`example/practice.html`](example/practice.html)
- 知识阅读与题目映射：[`example/reader.html`](example/reader.html)
- 统一入口首页：[`example/index.html`](example/index.html)

示例数据也全部集中在 `example/` 内：

- 示例题库：[`example/data/question-bank.json`](example/data/question-bank.json)
- 示例知识库：[`example/data/knowledge-base/genome-informatics-core.json`](example/data/knowledge-base/genome-informatics-core.json)
- 示例图片：[`example/images/`](example/images/)
- 历史旧页面：[`example/legacy/`](example/legacy/)
- 原始答案与截图：[`example/user_data/`](example/user_data/)

也就是说：

- `SynQuest` 负责 skill 和 functions
- `Geno` 负责 example 门户和示例数据

## 仓库结构

现在仓库主目录收成三层：

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
│       └── knowledge_loader.py
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
├── reader.html
├── logo.png
├── LICENSE
└── README.md
```

目录职责：

- `skills/`: SynQuest 的 skill 定义与参考说明
- `functions/`: 可复用 Python functions 与 CLI
- `example/`: Geno 示例门户、示例题库、旧版素材与图像资源

## 相关入口

- Skill: [`skills/synquest/SKILL.md`](skills/synquest/SKILL.md)
- Formats: [`skills/synquest/references/knowledge_base_formats.md`](skills/synquest/references/knowledge_base_formats.md)
- Schema: [`skills/synquest/references/question_schema.md`](skills/synquest/references/question_schema.md)

## License

This project uses the [MIT License](LICENSE).
