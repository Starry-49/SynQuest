const READER_BANK_PATH = "./data/question-bank.json";
const READER_KB_PATH = "./data/knowledge-base/genome-informatics-core.json";

const readerState = {
  bank: null,
  kb: null,
  activeModule: null,
  activeQuestion: null
};

function query(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function resolveAssetPath(path) {
  if (!path) return "";
  if (/^(https?:|data:|\/)/.test(path)) return path;
  return String(path).replace(/^\.?\//, "");
}

async function readJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}`);
  }
  return response.json();
}

function renderModuleTree() {
  const container = document.getElementById("moduleTree");
  container.innerHTML = readerState.kb.entries.map((entry) => `
    <button class="tree-item ${entry.id === readerState.activeModule ? "active" : ""}" data-module="${entry.id}">
      <strong>${entry.title}</strong>
      <div class="muted">${entry.module}</div>
    </button>
  `).join("");

  container.querySelectorAll("[data-module]").forEach((button) => {
    button.addEventListener("click", () => {
      readerState.activeModule = button.dataset.module;
      readerState.activeQuestion = null;
      renderReader();
    });
  });
}

function renderQuestionTree() {
  const container = document.getElementById("questionTree");
  const related = readerState.bank.questions.filter((question) => {
    if (readerState.activeQuestion) {
      return question.id === readerState.activeQuestion;
    }
    return (question.knowledgeRefs || []).includes(readerState.activeModule);
  });

  container.innerHTML = related.length
    ? related.map((question) => `
      <button class="tree-item ${question.id === readerState.activeQuestion ? "active" : ""}" data-question="${question.id}">
        <strong>${question.id}</strong>
        <div class="muted">${question.prompt}</div>
      </button>
    `).join("")
    : `<div class="empty-state"><p class="muted">当前模块暂无绑定题目。</p></div>`;

  container.querySelectorAll("[data-question]").forEach((button) => {
    button.addEventListener("click", () => {
      readerState.activeQuestion = button.dataset.question;
      renderReader();
    });
  });
}

function renderModuleSummary(entry) {
  const related = readerState.bank.questions.filter((question) => (question.knowledgeRefs || []).includes(entry.id));
  return `
    <article class="reader-card">
      <div class="reader-header-meta">
        <div class="badge-row">
          <span class="tag tag-brand">${entry.module}</span>
          <span class="tag tag-accent">${related.length} 道关联题</span>
        </div>
      </div>
      <h3>${entry.title}</h3>
      <p>${entry.summary}</p>
      <div class="reader-summary">
        <strong>核心关键词：</strong>${(entry.keywords || []).join("、") || "未标注"}
      </div>
      <div class="reader-list">
        ${(entry.facts || []).map((fact) => `
          <article class="knowledge-card">
            <h3>${fact.question}</h3>
            <p><strong>答案：</strong>${fact.answer}</p>
            <p class="muted">${fact.explanation}</p>
          </article>
        `).join("")}
      </div>
    </article>
  `;
}

function renderQuestionDetail(question) {
  const module = readerState.kb.entries.find((entry) => (question.knowledgeRefs || []).includes(entry.id));
  return `
    <article class="reader-card">
      <div class="reader-header-meta">
        <div class="badge-row">
          <span class="tag tag-brand">${question.source}</span>
          <span class="tag tag-accent">${question.topicName}</span>
          <span class="tag tag-dark">${question.type}</span>
        </div>
        <span class="status-pill">${question.id}</span>
      </div>
      <h3>${question.prompt}</h3>
      ${question.images?.question ? `<img class="reader-image" src="${resolveAssetPath(question.images.question)}" alt="${question.id} image">` : ""}
      ${(question.options || []).length ? `
        <div class="question-options">
          ${question.options.map((option) => `
            <div class="option"><strong>${option.key || "-"}</strong> · ${option.text}</div>
          `).join("")}
        </div>
      ` : ""}
      <div class="analysis-box">
        <p><strong>答案：</strong>${question.answer || "未记录"}</p>
        <p><strong>解析：</strong>${question.analysis || "暂无解析"}</p>
        ${question.pdfPage ? `<p><strong>PPT 页码：</strong>${question.pdfPage}</p>` : ""}
      </div>
      ${question.images?.note ? `<img class="reader-image" src="${resolveAssetPath(question.images.note)}" alt="${question.id} note image">` : ""}
      ${module ? `
        <div class="callout">
          <strong>关联知识模块：</strong>${module.title}<br>
          <span class="muted">${module.summary}</span>
        </div>
      ` : ""}
    </article>
  `;
}

function renderReader() {
  renderModuleTree();
  renderQuestionTree();

  const module = readerState.kb.entries.find((entry) => entry.id === readerState.activeModule) || readerState.kb.entries[0];
  const question = readerState.bank.questions.find((item) => item.id === readerState.activeQuestion);

  document.getElementById("readerTitle").textContent = question ? question.prompt : module.title;
  document.getElementById("readerSubtitle").textContent = question
    ? `题目详情 · ${question.id}`
    : `知识模块 · ${module.module}`;
  document.getElementById("readerContent").innerHTML = question
    ? renderQuestionDetail(question)
    : renderModuleSummary(module);
}

async function initReader() {
  try {
    const [bank, kb] = await Promise.all([readJson(READER_BANK_PATH), readJson(READER_KB_PATH)]);
    readerState.bank = bank;
    readerState.kb = kb;
    readerState.activeModule = query("module") || kb.entries[0].id;
    readerState.activeQuestion = query("question");

    if (readerState.activeQuestion) {
      const question = bank.questions.find((item) => item.id === readerState.activeQuestion);
      if (question && question.knowledgeRefs && question.knowledgeRefs.length) {
        readerState.activeModule = question.knowledgeRefs[0];
      }
    }

    renderReader();
  } catch (error) {
    console.error(error);
    document.getElementById("readerContent").innerHTML = `
      <section class="empty-state">
        <h3>Reader 初始化失败</h3>
        <p class="muted">请确认题库与知识库 JSON 已生成。</p>
      </section>
    `;
  }
}

initReader();
