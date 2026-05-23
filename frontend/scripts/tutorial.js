(function () {
  const CER_HELP = {
    overall: "Điểm tổng hợp cho Claim, Evidence và Reasoning trong lượt tranh biện.",
    claim: "Luận điểm chính của bạn có rõ ràng và nhất quán không?",
    evidence: "Bạn có đưa ví dụ, dữ liệu hoặc dẫn chứng hỗ trợ không?",
    reasoning: "Bạn có giải thích logic giữa bằng chứng và kết luận không?",
  };

  let knowledgeModal = null;
  let lastHint = "";

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function getKnowledgeModal() {
    if (knowledgeModal) return knowledgeModal;
    const carousel = window.AIDebateKnowledgeCarousel;
    knowledgeModal = document.createElement("div");
    knowledgeModal.className = "knowledge-modal hidden";
    knowledgeModal.setAttribute("role", "dialog");
    knowledgeModal.setAttribute("aria-modal", "true");
    knowledgeModal.setAttribute("aria-labelledby", "knowledge-modal-title");
    knowledgeModal.innerHTML = `
      <div class="knowledge-modal-backdrop" data-knowledge-close></div>
      <section class="knowledge-modal-panel knowledge-carousel-modal" tabindex="-1">
        <header class="knowledge-modal-head">
          <div>
            <div class="hub-label">Debate Fundamentals</div>
            <h2 id="knowledge-modal-title">Kiến thức nền tảng để tranh biện</h2>
            <p>Học từng bước cùng Lumi: Claim, Evidence, Reasoning, lỗi thường gặp và kỹ thuật phản biện cốt lõi.</p>
          </div>
          <button class="icon-button knowledge-close" type="button" aria-label="Đóng kiến thức" data-knowledge-close>×</button>
        </header>
        <div class="knowledge-carousel-root">
          ${carousel?.render?.() || '<div class="empty-message">Không thể tải bài học kiến thức.</div>'}
        </div>
      </section>
    `;
    document.body.appendChild(knowledgeModal);
    carousel?.mount?.(knowledgeModal);
    knowledgeModal.addEventListener("click", (event) => {
      if (event.target.closest("[data-knowledge-close]")) closeKnowledge();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !knowledgeModal.classList.contains("hidden")) closeKnowledge();
    });
    return knowledgeModal;
  }

  function openKnowledge() {
    const modal = getKnowledgeModal();
    modal.classList.remove("hidden");
    document.body.classList.add("modal-open");
    window.AIDebateKnowledgeCarousel?.mount?.(modal);
    requestAnimationFrame(() => modal.querySelector("[data-knowledge-carousel]")?.focus());
  }

  function closeKnowledge() {
    if (!knowledgeModal) return;
    knowledgeModal.classList.add("hidden");
    document.body.classList.remove("modal-open");
  }

  function injectKnowledgeHero() {
    const stack = document.querySelector("#view-home .hub-stack");
    if (!stack || stack.querySelector("[data-knowledge-entry]")) return;
    const html = window.AIDebateKnowledgeHero?.render?.();
    if (!html) return;
    stack.insertAdjacentHTML("afterbegin", html);
  }

  function injectTopbarAction() {
    const actions = document.querySelector(".top-actions");
    if (!actions || actions.querySelector("[data-knowledge-topbar]")) return;
    const button = document.createElement("button");
    button.className = "soft-pill knowledge-topbar-action";
    button.type = "button";
    button.dataset.knowledgeTopbar = "true";
    button.textContent = "Kiến thức";
    button.addEventListener("click", openKnowledge);
    actions.insertBefore(button, actions.firstChild);
  }

  function getHintText(text) {
    const value = text.trim();
    if (!value) return "";
    const lower = value.toLowerCase();
    const sentences = value.split(/[.!?。！？\n]+/).filter(Boolean).length;
    const hasEvidence = /(ví dụ|dẫn chứng|số liệu|nghiên cứu|theo|bởi vì|vì|do|gpa|%|\d+)/i.test(value);
    const hasReasoning = /(nên|vì vậy|do đó|điều này|khiến|dẫn đến|cho thấy|therefore|because|why)/i.test(lower);
    const opinionOnly = /(tôi nghĩ|mình nghĩ|theo tôi|i think|i believe)/i.test(lower) && !hasEvidence;

    if (value.length < 48 || sentences < 2) return "Hãy thêm bằng chứng cụ thể.";
    if (opinionOnly) return "Bạn cần giải thích WHY.";
    if (!hasReasoning) return "Hãy nối bằng chứng với kết luận.";
    if (hasEvidence && hasReasoning && value.length > 120) return "Strong reasoning detected.";
    return "Hãy làm rõ Claim → Evidence → Reasoning.";
  }

  function analyzeArgument(text) {
    return getHintText(text);
  }

  function ensureQuickHint() {
    const input = document.getElementById("user-input");
    if (!input || document.getElementById("quick-argument-hint")) return;
    const hint = document.createElement("div");
    hint.id = "quick-argument-hint";
    hint.className = "quick-argument-hint hidden";
    hint.setAttribute("aria-live", "polite");
    input.insertAdjacentElement("afterend", hint);
    input.addEventListener("input", () => updateQuickHint());
  }

  function updateQuickHint() {
    const input = document.getElementById("user-input");
    const hint = document.getElementById("quick-argument-hint");
    if (!input || !hint) return;
    const next = analyzeArgument(input.value);
    if (!next) {
      hint.classList.add("hidden");
      hint.textContent = "";
      lastHint = "";
      return;
    }
    if (next !== lastHint) {
      hint.textContent = next;
      lastHint = next;
    }
    hint.classList.remove("hidden", "strong");
    hint.classList.toggle("strong", next === "Strong reasoning detected.");
  }

  function tooltipButton(key) {
    return `<button class="cer-info-button" type="button" data-cer-info="${key}" aria-label="Giải thích ${key}">i<span class="cer-tooltip" role="tooltip">${CER_HELP[key]}</span></button>`;
  }

  function enhanceCerTooltips() {
    const total = document.getElementById("cer-total");
    if (total && !total.parentElement.querySelector("[data-cer-info='overall']")) {
      total.insertAdjacentHTML("beforebegin", tooltipButton("overall"));
    }
    document.querySelectorAll("#cer-output .score-line span, #summary-cer .score-line span").forEach((label) => {
      const text = label.textContent.toLowerCase();
      const key = text.includes("claim") || text.includes("luận điểm")
        ? "claim"
        : text.includes("evidence") || text.includes("bằng")
          ? "evidence"
          : text.includes("reason") || text.includes("lập luận")
            ? "reasoning"
            : "";
      if (key && !label.querySelector(".cer-info-button")) {
        label.classList.add("score-label-with-help");
        label.insertAdjacentHTML("beforeend", tooltipButton(key));
      }
    });
  }

  function emptyState(title, text, actionLabel, action) {
    return `
      <div class="tutorial-empty-state">
        <div class="tutorial-empty-icon" aria-hidden="true">✦</div>
        <strong>${title}</strong>
        <span>${text}</span>
        ${actionLabel ? `<button class="secondary-btn" type="button" onclick="${action}">${actionLabel}</button>` : ""}
      </div>
    `;
  }

  function enhanceEmptyStates() {
    document.querySelectorAll(".empty-message").forEach((node) => {
      if (node.dataset.enhancedEmpty === "true" || node.children.length) return;
      const text = node.textContent || "";
      if (/tiến|progress|dữ liệu/i.test(text)) {
        node.innerHTML = emptyState("No debate sessions yet", "Start your first debate để Lumi có dữ liệu theo dõi tiến bộ.", "Start your first debate", "goToView('session')");
      } else if (/CER|Điểm/i.test(text)) {
        node.innerHTML = emptyState("Chưa có điểm CER", "Gửi một lập luận để xem Claim, Evidence và Reasoning.", "Mở kiến thức CER", "window.AIDebateKnowledge?.open()");
      } else if (/Hội thoại|tranh biện/i.test(text)) {
        node.innerHTML = emptyState("Chưa có hội thoại", "Bắt đầu lượt đầu tiên hoặc xem phiên demo mẫu.", "Xem demo", "window.AIDebateDemo?.start()");
      }
      node.dataset.enhancedEmpty = "true";
    });
  }

  function wrapRenderers() {
    const wrappers = [
      ["renderCER", () => enhanceCerTooltips()],
      ["renderFeedback", () => enhanceEmptyStates()],
      ["renderTranscript", () => enhanceEmptyStates()],
      ["renderRebuttal", () => enhanceEmptyStates()],
      ["renderProgressTopics", () => enhanceEmptyStates()],
      ["goToView", () => {
        injectKnowledgeHero();
        ensureQuickHint();
        enhanceEmptyStates();
        enhanceCerTooltips();
      }],
    ];

    wrappers.forEach(([name, after]) => {
      const original = window[name];
      if (typeof original !== "function" || original.__tutorialWrapped) return;
      const wrapped = function (...args) {
        const result = original.apply(this, args);
        if (result && typeof result.then === "function") {
          return result.finally(() => requestAnimationFrame(after));
        }
        requestAnimationFrame(after);
        return result;
      };
      wrapped.__tutorialWrapped = true;
      window[name] = wrapped;
    });
  }

  ready(() => {
    injectKnowledgeHero();
    injectTopbarAction();
    ensureQuickHint();
    enhanceEmptyStates();
    enhanceCerTooltips();
    wrapRenderers();
  });

  window.AIDebateKnowledge = {
    open: openKnowledge,
    close: closeKnowledge,
    analyzeArgument,
    enhanceEmptyStates,
    enhanceCerTooltips,
    updateQuickHint,
  };
})();
