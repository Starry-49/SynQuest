<p align="center">
  <img src="logo.png" alt="SynQuest Logo" width="120">
</p>

<h1 align="center">SynQuest</h1>

<p align="center">
  面向《基因组信息学》的知识库驱动出题系统。<br>
  支持题库整理、抽题测试、知识库生成新题，以及 GitHub Pages 静态演示。
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
  <a href="synquest/SKILL.md">
    <img src="https://img.shields.io/badge/Codex-SynQuest-1D6A4F?style=flat-square" alt="Codex SynQuest">
  </a>
</p>

<p align="center">
  <a href="#quick-start"><strong>Quick Start</strong></a> ·
  <a href="#what-you-can-do"><strong>What You Can Do</strong></a> ·
  <a href="#github-pages"><strong>GitHub Pages</strong></a> ·
  <a href="#project-structure"><strong>Project Structure</strong></a>
</p>

## Quick Start

### 1. 本地启动

先生成整理后的标准题库：

```bash
python3 scripts/build_question_bank.py
```

再启动一个静态服务器：

```bash
python3 -m http.server 8000
```

打开：

```text
http://localhost:8000
```

### 2. 在线体验

- GitHub Pages: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- 仓库地址: [https://github.com/Starry-49/SynQuest](https://github.com/Starry-49/SynQuest)

## What You Can Do

这个项目不是单纯“放题目的网页”，而是一个完整的小型题库系统。

- 浏览我已经整理好的《基因组信息学》题库
- 按主题、题型、年份和关键词快速筛题
- 从当前筛选结果中抽指定数量的题进行测试
- 基于课程知识库生成新的练习题
- 把生成的新题先保存在浏览器本地，再导出为 JSON
- 后续通过仓库内脚本把新题并回正式题库

## Why SynQuest

我希望把原本散落在 HTML、截图和笔记里的内容整理成一个更清晰、可扩展、可复用的仓库。

SynQuest 主要解决了这几件事：

- 把原始题目从旧版 HTML 中抽取成结构化 JSON
- 把课程知识点单独整理成知识库，而不是继续把题目写死在页面里
- 把“知识库 -> 出题 -> 题库扩充 -> 静态展示”串成一个闭环
- 保留原始资料，方便回溯和继续修订

## GitHub Pages

首页是一个纯静态页面，不依赖后端，适合直接放在 GitHub Pages 上。

### 页面支持

- 题库浏览与筛选
- 抽题测试
- 基于知识模块生成新题
- 本地导出生成题目
- Study Reader 阅读知识模块与题目详情

### 页面入口

- 首页: [`index.html`](index.html)
- Reader: [`reader.html`](reader.html)

## SynQuest Skill

主 skill 位于 [`synquest/SKILL.md`](synquest/SKILL.md)。

它是这个仓库的核心入口，但内部不是一团混在一起的实现，而是分层组织：

- `SKILL.md`: 说明什么时候用、怎么触发
- `references/`: 说明题目 schema 和知识库格式
- `scripts/synquest.py`: 命令行生成、检查、合并
- `assets/synquest-browser.js`: 浏览器端轻量生成器

这意味着它可以和别的 skill 联用，但结构上仍然保持清楚：

- 一个主 skill
- 多个清晰子模块
- 页面、数据、脚本各自独立

### CLI 示例

检查知识库：

```bash
python3 synquest/scripts/synquest.py inspect \
  --kb data/knowledge-base/genome-informatics-core.json
```

生成新题：

```bash
python3 synquest/scripts/synquest.py synthesize \
  --kb data/knowledge-base/genome-informatics-core.json \
  --count 12 \
  --out data/generated/synquest-batch.json
```

把新题并回正式题库：

```bash
python3 synquest/scripts/synquest.py merge \
  --bank data/question-bank.json \
  --incoming data/generated/synquest-batch.json
```

## Data Overview

当前仓库里已经整理出的正式题库位于：

- [`data/question-bank.json`](data/question-bank.json)

课程知识库位于：

- [`data/knowledge-base/genome-informatics-core.json`](data/knowledge-base/genome-informatics-core.json)

浏览器导出或 CLI 生成的新题样例位于：

- [`data/generated/`](data/generated/)

## Project Structure

```text
.
├── assets/
│   ├── app.js
│   ├── reader.js
│   ├── styles.css
│   └── synquest-browser.js
├── data/
│   ├── generated/
│   ├── knowledge-base/
│   └── question-bank.json
├── images/
├── legacy/
│   ├── index.legacy.html
│   └── reader.legacy.html
├── scripts/
│   └── build_question_bank.py
├── synquest/
│   ├── agents/openai.yaml
│   ├── references/
│   ├── scripts/synquest.py
│   └── SKILL.md
├── user_data/
├── index.html
├── reader.html
├── logo.png
├── LICENSE
└── README.md
```

### 目录职责

- `assets/`: 页面逻辑与样式
- `data/`: 正式题库、知识库、生成结果
- `legacy/`: 原始旧页面备份
- `scripts/`: 数据迁移与构建脚本
- `synquest/`: 主 skill 与生成工具
- `user_data/`: 原始答案、笔记和截图来源

## License

This project uses the [MIT License](LICENSE).
