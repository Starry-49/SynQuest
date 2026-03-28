# SynQuest Question Schema

Each generated question should follow this structure:

```json
{
  "id": "sq-hgp-maps-001",
  "source": "synquest",
  "origin": "generated",
  "topic": "human-genome-project",
  "topicName": "人类基因组计划与图谱",
  "difficulty": 2,
  "type": "single_choice",
  "prompt": "中国是在哪一年加入人类基因组计划的？",
  "options": [
    {"key": "A", "text": "1990年"},
    {"key": "B", "text": "1999年"},
    {"key": "C", "text": "2000年"},
    {"key": "D", "text": "2001年"}
  ],
  "answer": "B",
  "analysis": "中国于1999年加入人类基因组计划。",
  "knowledgeRefs": ["hgp-maps"],
  "tags": ["human-genome-project", "single_choice"],
  "images": {
    "question": "",
    "note": ""
  },
  "pdfPage": null
}
```

Required fields:

- `id`
- `topic`
- `topicName`
- `difficulty`
- `type`
- `prompt`
- `options`
- `answer`
- `analysis`
- `knowledgeRefs`
- `tags`
- `images`

Recommended constraints:

- Use `single_choice`, `multiple_choice`, `short_answer`, or `open_ended`.
- Keep `difficulty` in the `1..5` range.
- Use four options for single-choice questions when possible.
- Keep `analysis` short but specific enough for feedback rendering.
