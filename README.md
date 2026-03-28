<p align="center">
  <img src="logo.png" alt="SynQuest Logo" width="120">
</p>

<h1 align="center">SynQuest</h1>

<p align="center">
  一个可复用的 skill / toolchain，用来把任意领域知识库转成结构化题库。<br>
  支持把知识点、题库、网页演示和生成流程组织成一个可复用项目。
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
  <a href="synquest/SKILL.md">
    <img src="https://img.shields.io/badge/Codex-SynQuest-1D6A4F?style=flat-square" alt="Codex SynQuest">
  </a>
</p>

<p align="center">
  <a href="#quick-start"><strong>Quick Start</strong></a> ·
  <a href="#what-you-can-do"><strong>What You Can Do</strong></a> ·
  <a href="#live-demo"><strong>Live Demo</strong></a> ·
  <a href="#project-structure"><strong>Project Structure</strong></a>
</p>

## Quick Start

### 1. 先看在线 demo

- Live Demo: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- Repo: [https://github.com/Starry-49/SynQuest](https://github.com/Starry-49/SynQuest)

### 2. 本地预览 demo

如果你只是想本地打开网页 demo，不需要先“生成题库”。仓库里已经带了示例数据。

直接启动一个静态服务器：

```bash
python3 -m http.server 8000
```

打开：

```text
http://localhost:8000/example/
```

### 3. 可选：重建示例题库

只有当你想重新从旧版 HTML 素材提取示例题库时，才需要执行：

```bash
python3 scripts/build_question_bank.py
```

## What You Can Do

SynQuest 的核心不是“这批题”，而是“从知识库稳定地产生题目”的能力。

- 给定某个领域的知识库，生成结构化题目
- 让生成结果同时可被 CLI、静态网页和后续脚本复用
- 先在浏览器里快速验证题目效果，再导出成 JSON
- 把人工审核后的结果合并回正式题库
- 用 GitHub Pages 把一个 skill 直接展示成可交互 demo

## Why SynQuest

我想做的不是单独整理一门课的题库，而是把“知识库 -> 题目生成 -> 题库扩展 -> 静态展示”抽象成一个可以复用的 skill。

SynQuest 主要解决了这几件事：

- 把已有题库从页面代码中剥离出来，变成结构化数据
- 把知识点单独组织成知识库，作为出题来源
- 提供一个主 skill，让题目生成过程可复用、可组合
- 给这个 skill 配一套 GitHub Pages 演示前端，方便直接展示

## What Is Example Here

这个仓库里和《基因组信息学》相关的内容，定位是示例：

- 示例知识库：[`data/knowledge-base/genome-informatics-core.json`](data/knowledge-base/genome-informatics-core.json)
- 示例题库：[`data/question-bank.json`](data/question-bank.json)
- 示例前端页面：[`index.html`](index.html) 与 [`reader.html`](reader.html)

也就是说：

- `SynQuest` 才是核心
- 题目与课程内容只是一个 example，方便演示 skill 如何工作

## Live Demo

这个仓库带了一个可直接打开的在线 demo，用来展示 SynQuest 生成题目后的实际交互效果。

### Demo 能做什么

- 浏览示例题库
- 抽题测试
- 基于示例知识模块生成新题
- 本地导出生成题目
- Study Reader 阅读知识模块与题目详情

### Demo 地址

- 在线首页: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- Demo 首页: [`example/index.html`](example/index.html)
- 答题页: [`example/practice.html`](example/practice.html)
- 阅读页: [`example/reader.html`](example/reader.html)

## SynQuest Skill

主 skill 位于 [`synquest/SKILL.md`](synquest/SKILL.md)。

它才是这个仓库真正的核心入口。页面、示例题库和示例知识库，都是围绕这个 skill 来组织的。

内部不是一团混在一起的实现，而是分层组织：

- `SKILL.md`: 说明什么时候用、怎么触发
- `references/`: 说明题目 schema 和知识库格式
- `scripts/synquest.py`: 命令行生成、检查、合并
- `example/assets/synquest-browser.js`: 浏览器端轻量生成器

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

当前仓库中的数据层分成两类：

### 1. skill 的示例输入 / 输出

- [`data/question-bank.json`](data/question-bank.json)
- [`data/knowledge-base/genome-informatics-core.json`](data/knowledge-base/genome-informatics-core.json)
- [`data/generated/`](data/generated/)

### 2. 原始历史素材

- [`legacy/`](legacy/)
- [`user_data/`](user_data/)

## Project Structure

```text
.
├── data/
│   ├── generated/
│   ├── knowledge-base/
│   └── question-bank.json
├── example/
│   ├── assets/
│   │   ├── app.js
│   │   ├── reader.js
│   │   ├── styles.css
│   │   └── synquest-browser.js
│   ├── index.html
│   ├── practice.html
│   └── reader.html
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

- `data/`: 正式题库、知识库、生成结果
- `example/`: 整个网页 demo，明确标记为 example
- `legacy/`: 原始旧页面备份
- `scripts/`: 数据迁移与构建脚本
- `synquest/`: 主 skill 与生成工具
- `user_data/`: 原始答案、笔记和截图来源

## License

This project uses the [MIT License](LICENSE).
