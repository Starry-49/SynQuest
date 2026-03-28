# Supported Knowledge Base Formats

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

## Markdown

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
