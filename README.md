<p align="center">
  <img src="logo.png" alt="SynQuest Logo" width="120">
</p>

<h1 align="center">SynQuest</h1>

<p align="center">
  A reusable skill and Python toolkit for turning domain knowledge sources into structured question banks.
</p>

<p align="center">
  Demo: <a href="https://starry-49.github.io/SynQuest/">https://starry-49.github.io/SynQuest/</a>
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

<table>
  <tr>
    <td width="50%" valign="top">
      <h2>中文</h2>
      <p>SynQuest 用来把课程材料、文档、网页、课件和结构化知识源转换成标准知识库，并进一步生成可合并进题库的新题。</p>
      <p><a href="README.zh.md"><strong>进入中文文档</strong></a></p>
      <p>适合查看：</p>
      <ul>
        <li>快速开始</li>
        <li>架构与工作原理</li>
        <li>Geno 示例说明</li>
        <li>Python 接口与依赖</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h2>English</h2>
      <p>SynQuest turns domain knowledge sources into normalized knowledge bases and generates new questions that can stay aligned with an existing question bank.</p>
      <p><a href="README.en.md"><strong>Open English documentation</strong></a></p>
      <p>Useful sections:</p>
      <ul>
        <li>Quick start</li>
        <li>Architecture and pipeline</li>
        <li>Geno example portal</li>
        <li>Python API and dependencies</li>
      </ul>
    </td>
  </tr>
</table>

## Quick Links

- Demo: [https://starry-49.github.io/SynQuest/](https://starry-49.github.io/SynQuest/)
- Chinese Docs: [README.zh.md](README.zh.md)
- English Docs: [README.en.md](README.en.md)
- Skill: [skills/synquest/SKILL.md](skills/synquest/SKILL.md)
- Functions: [functions/synquest/](functions/synquest/)
- Example Portal: [example/](example/)

## Current Retrieval Stack

The repository currently includes a retrieval-based generation layer built with:

- `jieba`
- `rank-bm25`
- `scikit-learn` TF-IDF
- `sentence-transformers`
- `RapidFuzz`
- `Poppler` PDF utilities

The current repository already includes semantic retrieval and hybrid reranking.
It does not yet include cross-encoder rerankers or LLM-based rewrite models.

## License

This project uses the [MIT License](LICENSE).
