(function () {
  const SAMPLE_ARGUMENT =
    "Trường học nên cấm điện thoại trong giờ học vì điện thoại làm học sinh mất tập trung. Ví dụ, khi có thông báo từ mạng xã hội, học sinh dễ ngắt mạch nghe giảng và bỏ lỡ ý chính. Vì vậy, nếu nhà trường giới hạn điện thoại trong tiết học, chất lượng tập trung sẽ tốt hơn.";
  const VOICE_SAMPLE_TRANSCRIPT =
    "Trường học nên cấm điện thoại trong giờ học vì điện thoại làm học sinh mất tập trung.";

  let active = false;
  let originalSubmitArgument = null;
  let originalStartVoiceDraft = null;
  let originalGoToView = null;
  let demoVoiceTimer = null;
  let demoVoiceAutoStop = null;
  let demoSessionPromise = null;

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function wait(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function getInput() {
    return document.getElementById("user-input");
  }

  function insertDemoBanner() {
    const arena = document.getElementById("view-arena");
    if (!arena || arena.querySelector("[data-demo-banner]") || !active) return;
    arena.insertAdjacentHTML(
      "afterbegin",
      `
      <div class="demo-session-banner" data-demo-banner>
        <div>
          <strong>Phiên demo mẫu</strong>
          <span>Đây là luồng chạy thử trên giao diện để bạn nhập lập luận, nhận phản biện và xem điểm CER.</span>
        </div>
        <div class="demo-session-actions">
          <button class="secondary-btn" type="button" onclick="window.AIDebateDemo?.replay()">Phát lại demo</button>
          <button class="primary-btn" type="button" onclick="window.AIDebateDemo?.startRealSession()">Bắt đầu phiên thật</button>
        </div>
      </div>
    `
    );
  }

  function removeDemoBanner() {
    document.querySelectorAll("[data-demo-banner]").forEach((node) => node.remove());
  }

  function resetDemoVoiceState() {
    window.clearInterval(demoVoiceTimer);
    window.clearTimeout(demoVoiceAutoStop);
    demoVoiceTimer = null;
    demoVoiceAutoStop = null;
    if (typeof state !== "undefined") {
      state.isListening = false;
      state.voiceDraftState = "idle";
      state.voiceDraftMessage = "";
      state.voiceRecordingStartedAt = 0;
      state.pendingVoiceTranscript = "";
    }
    if (typeof renderVoiceControls === "function") renderVoiceControls();
  }

  function resetDemoState({ keepSampleInput = true } = {}) {
    demoSessionPromise = null;
    resetDemoVoiceState();
    if (typeof state !== "undefined") {
      state.topic = "Trường học nên cấm điện thoại";
      state.stance = "Ủng hộ";
      state.difficulty = state.difficulty || "Intermediate";
      state.sessionId = null;
      state.sessionStatus = "active";
      state.roundCount = 0;
      state.pendingVoiceTranscript = "";
      state.history = [];
      state.latest = null;
      state.isSubmitting = false;
      state.rebuttalAudioState = "idle";
      state.rebuttalAudioMessage = "";
    }
    if (typeof clearSpeechAudioCache === "function") clearSpeechAudioCache();
    if (typeof clearVoiceSourceAudio === "function") clearVoiceSourceAudio();
    if (typeof renderArenaShell === "function") renderArenaShell();
    const input = getInput();
    if (input) {
      input.disabled = false;
      input.value = keepSampleInput ? SAMPLE_ARGUMENT : "";
    }
    if (typeof updateCharCount === "function") updateCharCount();
    if (typeof startUserTurnTimer === "function" && state?.view === "arena") {
      startUserTurnTimer({ reset: true });
    }
    if (typeof renderRebuttal === "function") renderRebuttal(null);
    if (typeof renderCER === "function") renderCER(null);
    if (typeof renderFeedback === "function") renderFeedback(null);
    if (typeof renderTranscript === "function") renderTranscript();
    if (typeof renderArenaStage === "function") renderArenaStage(null);
    insertDemoBanner();
  }

  function start() {
    active = true;
    if (typeof goToView === "function") goToView("arena");
    resetDemoState({ keepSampleInput: true });
  }

  function replay() {
    removeDemoBanner();
    resetDemoState({ keepSampleInput: true });
  }

  function startRealSession() {
    active = false;
    demoSessionPromise = null;
    removeDemoBanner();
    resetDemoVoiceState();
    if (typeof clearSpeechAudioCache === "function") clearSpeechAudioCache();
    if (typeof state !== "undefined") {
      state.history = [];
      state.latest = null;
      state.roundCount = 0;
      state.sessionId = null;
      state.sessionStatus = "active";
      state.pendingVoiceTranscript = "";
      state.rebuttalAudioState = "idle";
      state.rebuttalAudioMessage = "";
    }
    const input = getInput();
    if (input) {
      input.disabled = false;
      input.value = "";
    }
    if (typeof updateCharCount === "function") updateCharCount();
    if (typeof goToView === "function") goToView("session");
  }

  async function ensureBackendDemoSession() {
    if (typeof state === "undefined") throw new Error("Demo chưa sẵn sàng.");
    if (state.sessionId) return state.sessionId;
    if (demoSessionPromise) return demoSessionPromise;
    if (typeof apiRequest !== "function") throw new Error("Không tìm thấy API client của ứng dụng.");

    demoSessionPromise = apiRequest("/api/v1/debate/session", {
      method: "POST",
      body: {
        topic: state.topic || "Trường học nên cấm điện thoại",
        stance: state.stance || "Ủng hộ",
        difficulty: state.difficulty || "Intermediate",
        input_mode: "text",
        age_group: state.age || "Adult",
        debate_level: state.level || "Intermediate",
        language: "vi",
        response_time: state.responseTime || "90 sec",
      },
    })
      .then((data) => {
        state.sessionId = data.session_id;
        if (!state.sessionId) throw new Error("Backend chưa trả về mã phiên demo.");
        state.sessionStatus = typeof normalizeStatus === "function" ? normalizeStatus(data.status) : (data.status || "active");
        if (typeof renderSessionChips === "function") renderSessionChips();
        return state.sessionId;
      })
      .finally(() => {
        demoSessionPromise = null;
      });
    return demoSessionPromise;
  }

  function boostDemoScore(value, key) {
    const raw = Number(value);
    const score = Number.isFinite(raw) ? raw : 0;
    if (score <= 0) return key === "evidence" ? 16 : 14;
    const boost = key === "evidence" && score < 20 ? 18 : 14;
    return Math.max(0, Math.min(100, Math.round(score + boost)));
  }

  function boostDemoCER(cer) {
    if (!cer || typeof cer !== "object") return cer;
    const boosted = {
      ...cer,
      claim: boostDemoScore(cer.claim, "claim"),
      evidence: boostDemoScore(cer.evidence, "evidence"),
      reasoning: boostDemoScore(cer.reasoning, "reasoning"),
    };
    const total = Math.round((boosted.claim + boosted.evidence + boosted.reasoning) / 3);
    boosted.total = total;
    boosted.overall = total;
    return boosted;
  }

  function applyDemoScoreBoost() {
    if (!active || typeof state === "undefined" || !state.latest?.cer) return;
    state.latest = {
      ...state.latest,
      cer: boostDemoCER(state.latest.cer),
    };
    if (state.history.length) {
      state.history[state.history.length - 1] = state.latest;
    }
    if (typeof renderCER === "function") renderCER(state.latest.cer);
    if (typeof renderArenaStage === "function") renderArenaStage(state.latest.cer);
    if (typeof renderTranscript === "function") renderTranscript();
  }

  async function simulateTurn(userArgument) {
    const input = getInput();
    const argument = String(userArgument ?? input?.value ?? "").trim();
    if (typeof hideError === "function") hideError("form-error");

    if (!argument) {
      if (typeof showError === "function") {
        showError("form-error", "Vui lòng nhập lập luận trước khi gửi.");
      }
      return;
    }
    if (typeof state === "undefined" || state.isSubmitting) return;
    if (typeof originalSubmitArgument !== "function") {
      if (typeof showError === "function") showError("form-error", "Demo chưa kết nối được luồng gửi thật.");
      return;
    }
    try {
      await ensureBackendDemoSession();
      await originalSubmitArgument();
      applyDemoScoreBoost();
    } catch (error) {
      if (typeof renderErrorState === "function") renderErrorState(error.message);
      if (typeof showError === "function") {
        showError("form-error", "Không thể gửi lượt demo tới backend. Hãy kiểm tra backend rồi thử lại.");
      }
    } finally {
      insertDemoBanner();
    }
  }

  async function finishDemoVoiceDraft() {
    window.clearInterval(demoVoiceTimer);
    window.clearTimeout(demoVoiceAutoStop);
    demoVoiceTimer = null;
    demoVoiceAutoStop = null;
    if (typeof state === "undefined" || !active) return;
    state.isListening = false;
    state.voiceRecordingStartedAt = 0;
    state.voiceDraftState = "transcribing";
    if (typeof renderVoiceControls === "function") renderVoiceControls();
    await wait(900);
    if (!active) return;
    if (typeof applyVoiceTranscript === "function") {
      applyVoiceTranscript(VOICE_SAMPLE_TRANSCRIPT);
    } else {
      const input = getInput();
      if (input) {
        input.value = input.value.trim() ? `${input.value.trim()} ${VOICE_SAMPLE_TRANSCRIPT}` : VOICE_SAMPLE_TRANSCRIPT;
      }
      state.pendingVoiceTranscript = input?.value.trim() || VOICE_SAMPLE_TRANSCRIPT;
      state.voiceDraftState = "ready";
      if (typeof updateCharCount === "function") updateCharCount();
      if (typeof renderVoiceControls === "function") renderVoiceControls();
    }
  }

  function startDemoVoiceDraft() {
    if (!active || typeof state === "undefined") return null;
    if (state.isSubmitting) return null;
    if (state.isListening) {
      finishDemoVoiceDraft();
      return null;
    }
    if (typeof hideError === "function") hideError("form-error");
    state.isListening = true;
    state.voiceDraftState = "recording";
    state.voiceDraftMessage = "";
    state.voiceRecordingStartedAt = Date.now();
    if (typeof renderVoiceControls === "function") renderVoiceControls();
    demoVoiceTimer = window.setInterval(() => {
      if (typeof renderVoiceControls === "function") renderVoiceControls();
    }, 500);
    demoVoiceAutoStop = window.setTimeout(finishDemoVoiceDraft, 1600);
    return null;
  }

  function wrapSubmit() {
    if (typeof window.submitArgument !== "function" || window.submitArgument.__demoWrapped) return;
    originalSubmitArgument = window.submitArgument;
    const wrapped = async function (...args) {
      if (active) return simulateTurn(getInput()?.value || "");
      return originalSubmitArgument.apply(this, args);
    };
    wrapped.__demoWrapped = true;
    window.submitArgument = wrapped;
  }

  function wrapVoiceDraft() {
    if (typeof window.startVoiceDraft !== "function" || window.startVoiceDraft.__demoWrapped) return;
    originalStartVoiceDraft = window.startVoiceDraft;
    const wrapped = function (...args) {
      if (active) return startDemoVoiceDraft();
      return originalStartVoiceDraft.apply(this, args);
    };
    wrapped.__demoWrapped = true;
    window.startVoiceDraft = wrapped;
  }

  function wrapNavigation() {
    if (typeof window.goToView !== "function" || window.goToView.__demoWrapped) return;
    originalGoToView = window.goToView;
    const wrapped = function (...args) {
      const result = originalGoToView.apply(this, args);
      requestAnimationFrame(() => {
        if (active && args[0] === "arena") insertDemoBanner();
        if (active && args[0] !== "arena") resetDemoVoiceState();
      });
      return result;
    };
    wrapped.__demoWrapped = true;
    window.goToView = wrapped;
  }

  ready(() => {
    wrapSubmit();
    wrapVoiceDraft();
    wrapNavigation();
  });

  window.AIDebateDemo = {
    start,
    replay,
    startRealSession,
    simulateTurn,
    ensureBackendDemoSession,
    get active() {
      return active;
    },
  };
})();
