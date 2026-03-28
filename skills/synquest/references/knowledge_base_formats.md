# Supported Knowledge Source Formats

SynQuest keeps the reusable loader in [`functions/synquest/knowledge_loader.py`](../../../functions/synquest/knowledge_loader.py).

## Preferred JSON

```json
{
  "entries": [
    {
      "id": "hgp-maps",
      "module": "基因组学基础",
      "title": "人类基因组计划与图谱",
      "summary": "描述 HGP、遗传图与物理图的核心概念。",
      "keywords": ["HGP", "遗传图", "物理图"],
      "distractors": ["2001年", "化学降解法", "RNA聚合酶III"],
      "facts": [
        {
          "question": "中国是在哪一年加入人类基因组计划的？",
          "answer": "1999年",
          "explanation": "中国于1999年加入 HGP。",
          "distractors": ["1990年", "2000年", "2001年"]
        }
      ]
    }
  ]
}
```

## Markdown / TXT

```md
## 人类基因组计划与图谱
- 中国于1999年加入人类基因组计划。
- 遗传图通常使用 cM 表示距离。
- 物理图常用 bp 或 cR 表示距离。
```

## HTML

- Use headings for modules.
- Put facts inside `ul > li` lists whenever possible.
- Avoid deeply nested tables if you want deterministic parsing.

## DOCX

- Paragraph text will be extracted directly from the Word document.
- Use headings or clearly separated paragraph groups when possible.
- Keep one topic per section if you want cleaner entry boundaries.

## PDF

- SynQuest reads PDF text with `pdftotext`.
- It uses raw-order text for page content and layout-preserving text for title detection.
- Repeated headers / footers are removed automatically by cross-page repetition detection.
- Repeated slides can be deduplicated by text fingerprint before becoming `entries`.

## PPTX

- SynQuest parses `pptx` directly as OOXML.
- It reads slide title placeholders, body text, and notes text.
- Each slide becomes an `entry`, and each extracted statement can become a `fact`.
