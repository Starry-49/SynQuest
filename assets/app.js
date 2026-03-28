const BANK_PATH = "data/question-bank.json";
const KB_PATH = "data/knowledge-base/genome-informatics-core.json";
const GENERATED_STORAGE_KEY = "synquest-generated-bank";

const state = {
  bank: null,
  kb: null,
  generatedQuestions: [],
  filters: {
    source: "all",
    topic: "all",
    type: "all",
    search: "",
    module: "all"
  },
  quiz: {
    active: false,
    questions: [],
    index: 0,
    answers: {},
    checked: {},
    score: null
  }
};

function $(selector) {
  return document.querySelector(selector);
}

function getAllQuestions() {
  return [...(state.bank?.questions || []), ...state.generatedQuestions];
}

function getTopicName(topicId) {
  const bankTopic = (state.bank?.meta?.topics || []).find((topic) => topic.id === topicId);
  if (bankTopic) return bankTopic.name;
  const module = (state.kb?.entries || []).find((entry) => slugify(entry.id || entry.title) === topicId);
  return module ? module.title : topicId;
}

function slugify(text) {
  return String(text || "")
    .trim()
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fff]+/g, "-")
    .replace(/^-+|-+$/g, "") || "entry";
}

function normalizeText(text) {
  return String(text || "").trim().toLowerCase().replace(/\s+/g, "");
}

function loadGeneratedQuestions() {
  try {
    const raw = window.localStorage.getItem(GENERATED_STORAGE_KEY);
    state.generatedQuestions = raw ? JSON.parse(raw) : [];
  } catch (error) {
    console.error("Failed to load generated questions:", error);
    state.generatedQuestions = [];
  }
}

function persistGeneratedQuestions() {
  window.localStorage.setItem(GENERATED_STORAGE_KEY, JSON.stringify(state.generatedQuestions));
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
}

function buildSourceFilters() {
  const container = $("#sourceFilterList");
  const sources = ["all", ...new Set(getAllQuestions().map((question) => question.source || "Unknown"))];
  container.innerHTML = sources
    .map((source) => {
      const active = source === state.filters.source ? "active" : "";
      const label = source === "all" ? "全部来源" : source;
      return `<button class="chip ${active}" data-source="${source}">${label}</button>`;
    })
    .join("");

  container.querySelectorAll("[data-source]").forEach((button) => {
    button.addEventListener("click", () => {
      state.filters.source = button.dataset.source;
      render();
    });
  });
}

function populateSelects() {
  const topicSelect = $("#topicSelect");
  const typeSelect = $("#typeSelect");

  const topics = (state.bank?.meta?.topics || []).map((topic) => ({
    id: topic.id,
    name: topic.name
  }));
  const allTopics = [...topics];
  state.generatedQuestions.forEach((question) => {
    if (!allTopics.some((topic) => topic.id === question.topic)) {
      allTopics.push({ id: question.topic, name: question.topicName || question.topic });
    }
  });

  topicSelect.innerHTML = ['<option value="all">全部主题</option>']
    .concat(allTopics.map((topic) => `<option value="${topic.id}">${topic.name}</option>`))
    .join("");
  topicSelect.value = state.filters.topic;

  const types = ["all", ...new Set(getAllQuestions().map((question) => question.type || "single_choice"))];
  typeSelect.innerHTML = types
    .map((type) => `<option value="${type}">${type === "all" ? "全部题型" : type}</option>`)
    .join("");
  typeSelect.value = state.filters.type;
}

function getFilteredQuestions() {
  const search = normalizeText(state.filters.search);
  return getAllQuestions().filter((question) => {
    if (state.filters.source !== "all" && question.source !== state.filters.source) {
      return false;
    }
    if (state.filters.topic !== "all" && question.topic !== state.filters.topic) {
      return false;
    }
    if (state.filters.type !== "all" && question.type !== state.filters.type) {
      return false;
    }
    if (state.filters.module !== "all") {
      const refs = question.knowledgeRefs || [];
      if (!refs.includes(state.filters.module)) {
        return false;
      }
    }
    if (!search) return true;
    const haystack = normalizeText([
      question.prompt,
      question.answer,
      question.analysis,
      question.topicName,
      ...(question.tags || []),
      ...(question.options || []).map((option) => option.text)
    ].join(" "));
    return haystack.includes(search);
  });
}

function sampleQuestions(pool, count) {
  const items = [...pool];
  for (let index = items.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [items[index], items[swapIndex]] = [items[swapIndex], items[index]];
  }
  return items.slice(0, Math.min(count, items.length));
}

function updateStats(filteredQuestions) {
  $("#statQuestionCount").textContent = getAllQuestions().length;
  $("#statKnowledgeCount").textContent = state.kb?.entries?.length || 0;
  $("#statGeneratedCount").textContent = state.generatedQuestions.length;
  $("#statFilteredCount").textContent = filteredQuestions.length;
  $("#statImageCount").textContent = getAllQuestions().filter((question) => question.images?.question).length;
}

function renderKnowledgeBase(filteredQuestions) {
  const container = $("#knowledgeList");
  const questions = getAllQuestions();
  const activeModule = state.filters.module;

  container.innerHTML = (state.kb?.entries || [])
    .map((entry) => {
      const entryQuestions = questions.filter((question) => (question.knowledgeRefs || []).includes(entry.id));
      const activeClass = entry.id === activeModule ? "active" : "";
      return `
        <article class="knowledge-card ${activeClass}" data-module="${entry.id}">
          <div class="question-header">
            <div>
              <div class="badge-row">
                <span class="tag tag-brand">${entry.module}</span>
                <span class="tag tag-accent">${entryQuestions.length} 道相关题</span>
              </div>
              <h3>${entry.title}</h3>
            </div>
          </div>
          <p class="panel-subtitle">${entry.summary}</p>
          <div class="panel-actions">
            <button class="button button-secondary" data-action="filter-module" data-module="${entry.id}">${entry.id === activeModule ? "取消聚焦" : "聚焦本模块"}</button>
            <button class="button button-primary" data-action="generate-module" data-module="${entry.id}">生成 3 题</button>
            <a class="button button-secondary" href="reader.html?module=${encodeURIComponent(entry.id)}">Study Reader</a>
          </div>
        </article>
      `;
    })
    .join("");

  container.querySelectorAll("[data-action='filter-module']").forEach((button) => {
    button.addEventListener("click", () => {
      state.filters.module = state.filters.module === button.dataset.module ? "all" : button.dataset.module;
      render();
    });
  });

  container.querySelectorAll("[data-action='generate-module']").forEach((button) => {
    button.addEventListener("click", () => {
      generateQuestionsFromKnowledge(button.dataset.module, 3);
    });
  });

  $("#activeModuleLabel").textContent = activeModule === "all"
    ? "全部知识模块"
    : (state.kb.entries.find((entry) => entry.id === activeModule)?.title || activeModule);
}

function renderQuestionList(filteredQuestions) {
  const container = $("#questionList");
  const title = $("#resultHeadline");
  title.textContent = `题库浏览 · ${filteredQuestions.length} 题`;

  if (!filteredQuestions.length) {
    container.innerHTML = `
      <section class="empty-state">
        <h3>当前筛选条件下没有题目</h3>
        <p class="muted">可以切换来源、清空关键词，或者直接用 SynQuest 生成新的本地题目。</p>
      </section>
    `;
    return;
  }

  container.innerHTML = filteredQuestions.map(renderQuestionCard).join("");

  container.querySelectorAll("[data-action='toggle-analysis']").forEach((button) => {
    button.addEventListener("click", () => {
      const box = document.getElementById(`analysis-${button.dataset.id}`);
      box.classList.toggle("hidden");
      button.textContent = box.classList.contains("hidden") ? "查看答案" : "收起答案";
    });
  });
}

function renderQuestionCard(question) {
  const options = (question.options || []).map((option) => `
    <div class="option">
      <strong>${option.key || "-"}</strong> · ${option.text}
    </div>
  `).join("");

  const tags = [
    `<span class="tag tag-brand">${question.source || "Unknown"}</span>`,
    `<span class="tag tag-accent">${question.topicName || getTopicName(question.topic)}</span>`,
    `<span class="tag tag-dark">${question.type}</span>`,
    `<span class="tag tag-dark">难度 ${question.difficulty}</span>`
  ].join("");

  const questionImage = question.images?.question
    ? `<img class="question-image" src="${question.images.question}" alt="${question.id} question image">`
    : "";
  const noteImage = question.images?.note
    ? `<img class="question-image" src="${question.images.note}" alt="${question.id} note image">`
    : "";

  return `
    <article class="question-card">
      <div class="question-header">
        <div class="badge-row">${tags}</div>
        <span class="status-pill">${question.id}</span>
      </div>
      <h3 class="question-title">${question.prompt}</h3>
      ${questionImage}
      ${options ? `<div class="question-options">${options}</div>` : ""}
      <div class="panel-actions">
        <button class="button button-secondary" data-action="toggle-analysis" data-id="${question.id}">查看答案</button>
        <a class="button button-secondary" href="reader.html?question=${encodeURIComponent(question.id)}">详细阅读</a>
      </div>
      <div class="analysis-box hidden" id="analysis-${question.id}">
        <p><strong>标准答案：</strong>${question.answer || "未记录"}</p>
        <p><strong>解析：</strong>${question.analysis || "暂无解析"}</p>
        ${question.pdfPage ? `<p><strong>PPT 页码：</strong>${question.pdfPage}</p>` : ""}
        ${noteImage ? `<div class="reader-summary"><strong>辅助笔记：</strong>${noteImage}</div>` : ""}
      </div>
    </article>
  `;
}

function collectQuizAnswer(question) {
  if (question.type === "multiple_choice") {
    const checked = Array.from(document.querySelectorAll(".answer-option input:checked"));
    return checked.map((input) => input.value).sort().join("");
  }
  if (question.type === "short_answer" || question.type === "open_ended") {
    return $("#quizTextAnswer").value.trim();
  }
  const selected = document.querySelector(".answer-option input:checked");
  return selected ? selected.value : "";
}

function isAnswerCorrect(question, answer) {
  if (question.type === "short_answer" || question.type === "open_ended") {
    const expected = normalizeText(question.answer);
    const actual = normalizeText(answer);
    return actual && (actual === expected || actual.includes(expected) || expected.includes(actual));
  }
  return normalizeText(answer) === normalizeText(question.answer);
}

function saveQuizAnswer() {
  if (!state.quiz.active) return;
  const question = state.quiz.questions[state.quiz.index];
  state.quiz.answers[question.id] = collectQuizAnswer(question);
}

function renderQuiz() {
  const shell = $("#quizShell");
  if (!state.quiz.active) {
    shell.classList.add("hidden");
    return;
  }

  shell.classList.remove("hidden");
  const question = state.quiz.questions[state.quiz.index];
  const storedAnswer = state.quiz.answers[question.id] || "";
  const checked = state.quiz.checked[question.id];
  const total = state.quiz.questions.length;
  const progress = `${Math.round(((state.quiz.index + 1) / total) * 100)}%`;

  let answerMarkup = "";
  if (question.type === "multiple_choice") {
    const selectedKeys = storedAnswer ? storedAnswer.split("") : [];
    answerMarkup = `
      <div class="answer-options">
        ${(question.options || []).map((option) => `
          <label class="answer-option">
            <input type="checkbox" value="${option.key}" ${selectedKeys.includes(option.key) ? "checked" : ""}>
            <span><strong>${option.key}</strong> · ${option.text}</span>
          </label>
        `).join("")}
      </div>
    `;
  } else if (question.type === "short_answer" || question.type === "open_ended") {
    answerMarkup = `<textarea id="quizTextAnswer" class="textarea-input" rows="4" placeholder="输入你的答案...">${storedAnswer}</textarea>`;
  } else {
    answerMarkup = `
      <div class="answer-options">
        ${(question.options || []).map((option) => `
          <label class="answer-option">
            <input type="radio" name="quizOption" value="${option.key}" ${storedAnswer === option.key ? "checked" : ""}>
            <span><strong>${option.key}</strong> · ${option.text}</span>
          </label>
        `).join("")}
      </div>
    `;
  }

  shell.innerHTML = `
    <div class="quiz-headline">
      <div>
        <h3>抽题测试</h3>
        <p class="muted">第 ${state.quiz.index + 1} / ${total} 题 · ${question.topicName || getTopicName(question.topic)}</p>
      </div>
      ${state.quiz.score !== null ? `<span class="score-badge">得分 ${state.quiz.score} / ${total}</span>` : ""}
    </div>
    <div class="progress-bar"><div class="progress-value" style="width:${progress};"></div></div>
    <article class="reader-card">
      <div class="badge-row">
        <span class="tag tag-brand">${question.source}</span>
        <span class="tag tag-dark">${question.type}</span>
        <span class="tag tag-accent">难度 ${question.difficulty}</span>
      </div>
      <h3>${question.prompt}</h3>
      ${question.images?.question ? `<img class="reader-image" src="${question.images.question}" alt="${question.id} image">` : ""}
      ${answerMarkup}
      ${checked ? `
        <div class="quiz-result">
          <p><strong>${checked.correct ? "结果：正确" : "结果：错误"}</strong></p>
          <p><strong>标准答案：</strong>${question.answer || "未记录"}</p>
          <p><strong>解析：</strong>${question.analysis || "暂无解析"}</p>
        </div>
      ` : ""}
    </article>
    <div class="quiz-controls">
      <button class="button button-secondary" id="quizPrev" ${state.quiz.index === 0 ? "disabled" : ""}>上一题</button>
      <button class="button button-secondary" id="quizCheck">检查本题</button>
      <button class="button button-primary" id="quizNext">${state.quiz.index === total - 1 ? "完成测验" : "下一题"}</button>
      <button class="button button-danger" id="quizClose">结束测验</button>
    </div>
  `;

  $("#quizPrev").addEventListener("click", () => {
    saveQuizAnswer();
    state.quiz.index -= 1;
    renderQuiz();
  });

  $("#quizCheck").addEventListener("click", () => {
    saveQuizAnswer();
    const currentAnswer = state.quiz.answers[question.id] || "";
    state.quiz.checked[question.id] = {
      answer: currentAnswer,
      correct: isAnswerCorrect(question, currentAnswer)
    };
    renderQuiz();
  });

  $("#quizNext").addEventListener("click", () => {
    saveQuizAnswer();
    if (state.quiz.index === total - 1) {
      finalizeQuiz();
      return;
    }
    state.quiz.index += 1;
    renderQuiz();
  });

  $("#quizClose").addEventListener("click", () => {
    state.quiz = { active: false, questions: [], index: 0, answers: {}, checked: {}, score: null };
    renderQuiz();
  });
}

function finalizeQuiz() {
  let score = 0;
  state.quiz.questions.forEach((question) => {
    const answer = state.quiz.answers[question.id] || "";
    const correct = isAnswerCorrect(question, answer);
    state.quiz.checked[question.id] = { answer, correct };
    if (correct) score += 1;
  });
  state.quiz.score = score;
  renderQuiz();
}

function startQuiz() {
  const pool = getFilteredQuestions();
  const count = Math.max(1, Number($("#quizCount").value || 10));
  const selected = sampleQuestions(pool, count);
  if (!selected.length) {
    window.alert("当前筛选结果为空，无法开始测试。");
    return;
  }

  state.quiz = {
    active: true,
    questions: selected,
    index: 0,
    answers: {},
    checked: {},
    score: null
  };
  renderQuiz();
  $("#quizShell").scrollIntoView({ behavior: "smooth", block: "start" });
}

function generateQuestionsFromKnowledge(moduleId, count) {
  const entries = moduleId === "all"
    ? state.kb.entries
    : state.kb.entries.filter((entry) => entry.id === moduleId);
  const generated = window.SynQuestBrowser.generateQuestions({
    entries,
    count,
    seed: Date.now(),
    existingIds: getAllQuestions().map((question) => question.id)
  });
  state.generatedQuestions = [...generated, ...state.generatedQuestions];
  persistGeneratedQuestions();
  render();
}

function exportGeneratedQuestions() {
  const payload = {
    meta: {
      title: "SynQuest Browser Export",
      exportedAt: new Date().toISOString(),
      count: state.generatedQuestions.length
    },
    questions: state.generatedQuestions
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "synquest-generated-questions.json";
  link.click();
  URL.revokeObjectURL(url);
}

function clearGeneratedQuestions() {
  if (!state.generatedQuestions.length) return;
  const confirmed = window.confirm("确认清空当前浏览器中由 SynQuest 生成的本地题目吗？");
  if (!confirmed) return;
  state.generatedQuestions = [];
  persistGeneratedQuestions();
  render();
}

function bindStaticEvents() {
  $("#searchInput").addEventListener("input", (event) => {
    state.filters.search = event.target.value;
    render();
  });

  $("#topicSelect").addEventListener("change", (event) => {
    state.filters.topic = event.target.value;
    render();
  });

  $("#typeSelect").addEventListener("change", (event) => {
    state.filters.type = event.target.value;
    render();
  });

  $("#startQuizButton").addEventListener("click", startQuiz);

  $("#randomBrowseButton").addEventListener("click", () => {
    const sampled = sampleQuestions(getFilteredQuestions(), Number($("#quizCount").value || 10));
    $("#resultHeadline").textContent = `随机预览 · ${sampled.length} 题`;
    $("#questionList").innerHTML = sampled.map(renderQuestionCard).join("");
    $("#questionList").querySelectorAll("[data-action='toggle-analysis']").forEach((button) => {
      button.addEventListener("click", () => {
        const box = document.getElementById(`analysis-${button.dataset.id}`);
        box.classList.toggle("hidden");
        button.textContent = box.classList.contains("hidden") ? "查看答案" : "收起答案";
      });
    });
  });

  $("#generateButton").addEventListener("click", () => {
    const moduleId = $("#generatorModule").value;
    const count = Number($("#generatorCount").value || 4);
    generateQuestionsFromKnowledge(moduleId, count);
  });

  $("#exportButton").addEventListener("click", exportGeneratedQuestions);
  $("#clearGeneratedButton").addEventListener("click", clearGeneratedQuestions);
}

function renderGeneratorModuleOptions() {
  const select = $("#generatorModule");
  select.innerHTML = ['<option value="all">从全部知识模块生成</option>']
    .concat((state.kb?.entries || []).map((entry) => `<option value="${entry.id}">${entry.title}</option>`))
    .join("");
}

function render() {
  buildSourceFilters();
  populateSelects();
  renderGeneratorModuleOptions();
  const filteredQuestions = getFilteredQuestions();
  updateStats(filteredQuestions);
  renderKnowledgeBase(filteredQuestions);
  renderQuestionList(filteredQuestions);
  renderQuiz();
}

async function init() {
  try {
    const [bank, kb] = await Promise.all([loadJson(BANK_PATH), loadJson(KB_PATH)]);
    state.bank = bank;
    state.kb = kb;
    loadGeneratedQuestions();
    bindStaticEvents();
    render();
  } catch (error) {
    console.error(error);
    $("#questionList").innerHTML = `
      <section class="empty-state">
        <h3>页面初始化失败</h3>
        <p class="muted">请确认 <span class="code">${BANK_PATH}</span> 与 <span class="code">${KB_PATH}</span> 存在。</p>
      </section>
    `;
  }
}

init();
