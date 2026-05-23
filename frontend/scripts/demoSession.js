(function () {
  const demoTurn = {
    source: "frontend-only",
    user_argument: "Trường học nên cấm điện thoại trong giờ học vì điện thoại làm học sinh mất tập trung. Ví dụ, khi có thông báo từ mạng xã hội, học sinh dễ ngắt mạch nghe giảng và bỏ lỡ ý chính. Vì vậy, nếu nhà trường giới hạn điện thoại trong tiết học, chất lượng tập trung sẽ tốt hơn.",
    ai_rebuttal: "Lập luận của bạn có Claim rõ, nhưng lệnh cấm hoàn toàn có thể bỏ qua lợi ích học tập của điện thoại. Một phản biện mạnh hơn là: thay vì cấm tuyệt đối, trường nên đặt quy tắc dùng có kiểm soát. Điện thoại có thể hỗ trợ tra cứu nhanh, làm bài quiz và liên hệ khẩn cấp. Nếu vấn đề chính là mất tập trung, giải pháp hợp lý hơn là giới hạn theo hoạt động lớp học, không loại bỏ công cụ.",
    cer: {
      claim: 78,
      evidence: 65,
      reasoning: 74,
      total: 72,
      overall: 72,
    },
    feedback: {
      strengths: ["Claim rõ và đúng trọng tâm.", "Có ví dụ cụ thể về thông báo mạng xã hội."],
      weaknesses: ["Evidence còn chung, chưa có dữ liệu hoặc tình huống lớp học cụ thể.", "Reasoning nên giải thích thêm vì sao cấm hoàn toàn tốt hơn quản lý có điều kiện."],
      suggestions: ["Thêm số liệu hoặc khảo sát về mức độ xao nhãng.", "So sánh giải pháp cấm hoàn toàn với giải pháp dùng có kiểm soát."],
    },
  };

  let active = false;
  let originalSubmitArgument = null;

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function setButtonState(disabled) {
    ["debate-btn", "voice-input-btn", "voice-record-btn", "voice-submit-btn"].forEach((id) => {
      const button = document.getElementById(id);
      if (button) button.disabled = disabled;
    });
  }

  function insertDemoBanner() {
    const arena = document.getElementById("view-arena");
    if (!arena || arena.querySelector("[data-demo-banner]") || !active) return;
    arena.insertAdjacentHTML("afterbegin", `
      <div class="demo-session-banner" data-demo-banner>
        <div>
          <strong>Phiên demo mẫu</strong>
          <span>Đây là luồng frontend-only để bạn xem nhanh transcript, phản biện và điểm CER.</span>
        </div>
        <div class="demo-session-actions">
          <button class="secondary-btn" type="button" onclick="window.AIDebateDemo?.replay()">Replay demo</button>
          <button class="primary-btn" type="button" onclick="window.AIDebateDemo?.startRealSession()">Start real session</button>
        </div>
      </div>
    `);
  }

  function removeDemoBanner() {
    document.querySelectorAll("[data-demo-banner]").forEach((node) => node.remove());
  }

  function start() {
    active = true;
    if (typeof state !== "undefined") {
      state.topic = "Trường học nên cấm điện thoại";
      state.stance = "Ủng hộ";
      state.difficulty = state.difficulty || "Intermediate";
      state.sessionId = "demo-session";
      state.sessionStatus = "active";
      state.roundCount = 1;
      state.pendingVoiceTranscript = "";
      state.history = [demoTurn];
      state.latest = demoTurn;
      state.isSubmitting = false;
    }

    if (typeof goToView === "function") goToView("arena");
    if (typeof renderArenaShell === "function") renderArenaShell();
    if (typeof state !== "undefined") {
      state.history = [demoTurn];
      state.latest = demoTurn;
      state.roundCount = 1;
    }
    const input = document.getElementById("user-input");
    if (input) input.value = demoTurn.user_argument;
    if (typeof updateCharCount === "function") updateCharCount();
    if (typeof renderTranscript === "function") renderTranscript();
    if (typeof renderCER === "function") renderCER(demoTurn.cer);
    if (typeof renderFeedback === "function") renderFeedback(demoTurn.feedback);
    if (typeof renderArenaStage === "function") renderArenaStage(demoTurn.cer);
    if (typeof renderRebuttal === "function") renderRebuttal(demoTurn.ai_rebuttal, { instant: true });
    setButtonState(true);
    insertDemoBanner();
  }

  function replay() {
    removeDemoBanner();
    start();
  }

  function startRealSession() {
    active = false;
    removeDemoBanner();
    setButtonState(false);
    if (typeof state !== "undefined") {
      state.history = [];
      state.latest = null;
      state.roundCount = 0;
      state.sessionId = null;
      state.sessionStatus = "active";
    }
    if (typeof goToView === "function") goToView("session");
  }

  function wrapSubmit() {
    if (typeof window.submitArgument !== "function" || window.submitArgument.__demoWrapped) return;
    originalSubmitArgument = window.submitArgument;
    const wrapped = async function (...args) {
      if (active) return null;
      return originalSubmitArgument.apply(this, args);
    };
    wrapped.__demoWrapped = true;
    window.submitArgument = wrapped;
  }

  function wrapNavigation() {
    if (typeof window.goToView !== "function" || window.goToView.__demoWrapped) return;
    const original = window.goToView;
    const wrapped = function (...args) {
      const result = original.apply(this, args);
      requestAnimationFrame(() => {
        if (active && args[0] === "arena") insertDemoBanner();
        if (active && args[0] !== "arena") setButtonState(false);
      });
      return result;
    };
    wrapped.__demoWrapped = true;
    window.goToView = wrapped;
  }

  ready(() => {
    wrapSubmit();
    wrapNavigation();
  });

  window.AIDebateDemo = {
    start,
    replay,
    startRealSession,
    get active() {
      return active;
    },
  };
})();
