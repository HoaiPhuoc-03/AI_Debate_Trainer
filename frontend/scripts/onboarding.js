(function () {
  const STORAGE_KEY = "ai_debate_trainer.onboarding.seen";
  const SESSION_KEY = "ai_debate_trainer.onboarding.session";

  const steps = [
    {
      eyebrow: "Lumi chào bạn",
      title: "Chào mừng đến với AI Debate Trainer",
      copy: "App giúp bạn luyện phản biện với AI đóng vai đối thủ tranh luận, chấm CER và theo dõi tiến bộ qua từng phiên.",
      cards: ["AI phản biện trực tiếp", "Chấm Claim, Evidence, Reasoning", "Progress tracking sau mỗi phiên"],
    },
    {
      eyebrow: "Flow sử dụng",
      title: "Từ hồ sơ đến tiến bộ",
      copy: "Bạn sẽ đi qua một luồng ngắn, rõ ràng trước khi xem kết quả.",
      flow: ["Chọn hồ sơ", "Tạo phiên", "Tranh biện", "Xem CER", "Theo dõi tiến bộ"],
    },
    {
      eyebrow: "CER là gì?",
      title: "Claim, Evidence, Reasoning",
      copy: "CER giúp lập luận không chỉ là ý kiến, mà có cấu trúc và sức thuyết phục.",
      cer: [
        ["Claim", "Luận điểm chính"],
        ["Evidence", "Bằng chứng hỗ trợ"],
        ["Reasoning", "Giải thích logic giữa luận điểm và bằng chứng"],
      ],
      example: "Ví dụ: Sinh viên không nên đi làm thêm năm nhất → ảnh hưởng học tập → giảm GPA → thiếu thời gian học.",
    },
    {
      eyebrow: "Tranh biện tốt hơn",
      title: "Đừng chỉ nêu ý kiến",
      copy: "Một lượt mạnh cần ví dụ, nguyên nhân và phản biện trực tiếp vào luận điểm đối phương.",
      cards: ["Luôn có ví dụ", "Giải thích WHY", "Phản biện đúng ý đối phương", "Kết luận bằng tác động"],
    },
    {
      eyebrow: "Sẵn sàng",
      title: "Bắt đầu luyện cùng Lumi",
      copy: "Bạn có thể vào phiên thật ngay hoặc xem demo để hiểu toàn bộ trải nghiệm trước.",
      final: true,
    },
  ];

  let overlay = null;
  let currentStep = 0;
  let previousFocus = null;

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function hasSeen() {
    return localStorage.getItem(STORAGE_KEY) === "true" || sessionStorage.getItem(SESSION_KEY) === "true";
  }

  function markSeen(persistent = true) {
    sessionStorage.setItem(SESSION_KEY, "true");
    if (persistent) localStorage.setItem(STORAGE_KEY, "true");
  }

  function buildBody(step) {
    const cards = step.cards ? `<div class="onboarding-card-grid">${step.cards.map((item) => `<div class="onboarding-mini-card">${item}</div>`).join("")}</div>` : "";
    const flow = step.flow ? `<div class="onboarding-flow">${step.flow.map((item, index) => `<div class="onboarding-flow-step"><span>${index + 1}</span><strong>${item}</strong></div>`).join("")}</div>` : "";
    const cer = step.cer ? `<div class="onboarding-cer-grid">${step.cer.map(([key, text]) => `<div><strong>${key}</strong><span>${text}</span></div>`).join("")}</div>` : "";
    const example = step.example ? `<div class="onboarding-example">${step.example}</div>` : "";
    return `${cards}${flow}${cer}${example}`;
  }

  function render() {
    if (!overlay) return;
    const step = steps[currentStep];
    overlay.querySelector(".onboarding-step-body").innerHTML = `
      <div class="onboarding-eyebrow">${step.eyebrow}</div>
      <h2>${step.title}</h2>
      <p>${step.copy}</p>
      ${buildBody(step)}
    `;
    overlay.querySelector(".onboarding-back").disabled = currentStep === 0;
    overlay.querySelector(".onboarding-next").textContent = step.final ? "Bắt đầu tranh biện" : "Continue";
    overlay.querySelector(".onboarding-progress-bar").style.setProperty("--progress", `${((currentStep + 1) / steps.length) * 100}%`);
    overlay.querySelector(".onboarding-dots").innerHTML = steps.map((_, index) => `<button type="button" aria-label="Tới bước ${index + 1}" class="${index === currentStep ? "active" : ""}" data-step="${index}"></button>`).join("");
  }

  function ensureOverlay() {
    if (overlay) return overlay;
    overlay = document.createElement("div");
    overlay.className = "onboarding-overlay hidden";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-labelledby", "onboarding-title");
    overlay.innerHTML = `
      <div class="onboarding-backdrop" data-onboarding-close></div>
      <section class="onboarding-dialog" tabindex="-1">
        <aside class="onboarding-rail" aria-hidden="true">
          <div class="onboarding-logo">CER</div>
          <div class="onboarding-progress"><span class="onboarding-progress-bar"></span></div>
          <div class="onboarding-dots"></div>
        </aside>
        <main class="onboarding-main">
          <button class="onboarding-skip" type="button" data-onboarding-skip>Skip tutorial</button>
          <div class="onboarding-step-body" id="onboarding-title"></div>
          <footer class="onboarding-actions">
            <button class="secondary-btn onboarding-back" type="button">Back</button>
            <button class="secondary-btn" type="button" data-onboarding-demo>Xem phiên demo</button>
            <button class="primary-btn onboarding-next" type="button">Continue</button>
          </footer>
        </main>
      </section>
    `;
    document.body.appendChild(overlay);
    overlay.addEventListener("click", handleClick);
    document.addEventListener("keydown", handleKeydown);
    return overlay;
  }

  function handleClick(event) {
    const dot = event.target.closest("[data-step]");
    if (dot) {
      currentStep = Number(dot.dataset.step);
      render();
      return;
    }
    if (event.target.closest("[data-onboarding-close], [data-onboarding-skip]")) {
      close(true);
      return;
    }
    if (event.target.closest("[data-onboarding-demo]")) {
      close(true);
      window.AIDebateDemo?.start();
      return;
    }
    if (event.target.closest(".onboarding-back")) {
      currentStep = Math.max(0, currentStep - 1);
      render();
      return;
    }
    if (event.target.closest(".onboarding-next")) {
      if (currentStep < steps.length - 1) {
        currentStep += 1;
        render();
      } else {
        close(true);
        if (typeof goToView === "function") goToView("session");
      }
    }
  }

  function handleKeydown(event) {
    if (!overlay || overlay.classList.contains("hidden")) return;
    if (event.key === "Escape") close(true);
    if (event.key !== "Tab") return;
    const focusable = overlay.querySelectorAll("button, [tabindex]:not([tabindex='-1'])");
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function open(force = false) {
    if (!force && hasSeen()) return;
    previousFocus = document.activeElement;
    currentStep = 0;
    ensureOverlay().classList.remove("hidden");
    document.body.classList.add("onboarding-open");
    render();
    requestAnimationFrame(() => overlay.querySelector(".onboarding-dialog")?.focus());
  }

  function close(persistent = false) {
    if (!overlay) return;
    overlay.classList.add("hidden");
    document.body.classList.remove("onboarding-open");
    markSeen(persistent);
    previousFocus?.focus?.();
  }

  function wrapEnterApp() {
    const originalEnterApp = window.enterApp;
    if (typeof originalEnterApp === "function" && !originalEnterApp.__onboardingWrapped) {
      window.enterApp = function wrappedEnterApp(mode = "guest", view = "home") {
        const result = originalEnterApp.apply(this, arguments);
        if (mode === "account") {
          requestAnimationFrame(() => open(false));
        }
        return result;
      };
      window.enterApp.__onboardingWrapped = true;
    }
  }

  wrapEnterApp();
  ready(wrapEnterApp);

  window.AIDebateOnboarding = {
    open,
    close,
    reset() {
      localStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem(SESSION_KEY);
    },
  };
})();
