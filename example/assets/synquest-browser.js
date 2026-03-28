(function () {
  const LETTERS = ["A", "B", "C", "D"];

  function slugify(text) {
    return String(text || "")
      .trim()
      .toLowerCase()
      .replace(/[^\w\u4e00-\u9fff]+/g, "-")
      .replace(/^-+|-+$/g, "") || "entry";
  }

  function shuffle(array, rng) {
    const items = [...array];
    for (let index = items.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(rng() * (index + 1));
      [items[index], items[swapIndex]] = [items[swapIndex], items[index]];
    }
    return items;
  }

  function makeSeededRandom(seed) {
    let value = seed % 2147483647;
    if (value <= 0) value += 2147483646;
    return function () {
      value = (value * 16807) % 2147483647;
      return (value - 1) / 2147483646;
    };
  }

  function collectFallbackDistractors(entries, correct) {
    const pool = [];
    entries.forEach((entry) => {
      (entry.distractors || []).forEach((candidate) => {
        if (candidate && candidate !== correct) pool.push(candidate);
      });
      (entry.facts || []).forEach((fact) => {
        if (fact.answer && fact.answer !== correct) pool.push(fact.answer);
      });
    });
    return pool;
  }

  function buildOptions(correct, fact, entries, rng) {
    const distractors = [...(fact.distractors || [])].filter(Boolean);
    const fallback = collectFallbackDistractors(entries, correct);
    shuffle(fallback, rng).forEach((candidate) => {
      if (candidate !== correct && !distractors.includes(candidate) && distractors.length < 3) {
        distractors.push(candidate);
      }
    });
    while (distractors.length < 3) {
      distractors.push(`不正确的备选项${distractors.length + 1}`);
    }

    const options = shuffle([correct, ...distractors.slice(0, 3)], rng);
    return options.map((text, index) => ({ key: LETTERS[index], text }));
  }

  function generateQuestions({ entries, count = 6, seed = Date.now(), existingIds = [] }) {
    const rng = makeSeededRandom(seed);
    const facts = [];

    entries.forEach((entry) => {
      (entry.facts || []).forEach((fact) => facts.push({ entry, fact }));
    });

    const selected = shuffle(facts, rng).slice(0, Math.min(count, facts.length));
    const existing = new Set(existingIds);
    const questions = [];

    selected.forEach(({ entry, fact }, index) => {
      const correct = fact.answer;
      const options = buildOptions(correct, fact, entries, rng);
      const answerOption = options.find((option) => option.text === correct);
      const baseId = `sq-${slugify(entry.id || entry.title)}-${String(index + 1).padStart(3, "0")}`;
      let finalId = baseId;
      let serial = 1;
      while (existing.has(finalId)) {
        serial += 1;
        finalId = `${baseId}-${serial}`;
      }
      existing.add(finalId);

      questions.push({
        id: finalId,
        year: null,
        source: "SynQuest",
        prompt: fact.question || `下列哪项关于“${entry.title}”的说法是正确的？`,
        type: fact.type || "single_choice",
        topic: slugify(entry.id || entry.title),
        topicName: entry.title,
        difficulty: Number(fact.difficulty || 2),
        options,
        answer: answerOption ? answerOption.key : "A",
        analysis: fact.explanation || correct,
        images: { question: "", note: "" },
        pdfPage: null,
        knowledgeRefs: [entry.id || slugify(entry.title)],
        tags: Array.from(new Set([slugify(entry.id || entry.title), "synquest", ...(entry.keywords || [])])),
        origin: "generated-browser"
      });
    });

    return questions;
  }

  window.SynQuestBrowser = {
    generateQuestions
  };
})();
