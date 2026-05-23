import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_HTML = ROOT_DIR / "frontend" / "web.html"


def read_frontend():
    return FRONTEND_HTML.read_text(encoding="utf-8")


class FrontendAuthBindingTests(unittest.TestCase):
    def test_frontend_no_longer_hard_codes_demo_user_identity(self):
        html = read_frontend()

        self.assertNotIn("Minh Nguyen", html)
        self.assertNotIn("minh@debate.trainer", html)
        self.assertNotIn('value="password"', html)
        self.assertNotIn('userName: "Minh Nguyen"', html)

    def test_frontend_login_binds_to_backend_auth_session(self):
        html = read_frontend()

        self.assertIn("/api/v1/auth/login", html)
        self.assertIn("/api/v1/auth/me", html)
        self.assertIn("applyAuthSession(data", html)
        self.assertIn("sessionStorage.getItem(AUTH_TOKEN_KEY)", html)
        self.assertIn("const storage = persist ? localStorage : sessionStorage", html)
        self.assertIn("storage.setItem(AUTH_TOKEN_KEY, token)", html)
        self.assertIn("remember-login", html)
        self.assertIn("request.headers.Authorization", html)

    def test_frontend_logout_clears_auth_state_and_stored_token(self):
        html = read_frontend()

        self.assertIn("/api/v1/auth/logout", html)
        self.assertIn("clearAuthState()", html)
        self.assertIn("localStorage.removeItem(AUTH_TOKEN_KEY)", html)
        self.assertIn("sessionStorage.removeItem(AUTH_TOKEN_KEY)", html)
        self.assertIn("state.currentUser = null", html)

    def test_frontend_progress_uses_backend_current_user_data(self):
        html = read_frontend()

        self.assertIn("/api/v1/debate/progress/overview", html)
        self.assertIn("recent_topics", html)
        self.assertNotIn("const data = [", html)

    def test_frontend_requires_single_session_topic_input(self):
        html = read_frontend()

        self.assertIn("session-topic-input", html)
        self.assertIn("validateSessionTopic", html)
        self.assertIn("setSessionTopic", html)
        self.assertNotIn("topic-options", html)
        self.assertNotIn("const topics = [", html)
        self.assertNotIn("custom_topic:", html)

    def test_frontend_ends_session_from_arena(self):
        html = read_frontend()

        self.assertIn("Kết thúc phiên", html)
        self.assertIn("finishSession()", html)
        self.assertIn("/end", html)
        self.assertNotIn("Rời phiên", html)

    def test_frontend_defaults_to_blue_theme(self):
        html = read_frontend()

        self.assertIn('<body data-theme="blue-pastel">', html)
        self.assertIn('const DEFAULT_THEME = "blue-pastel";', html)
        self.assertIn("return DEFAULT_THEME;", html)

    def test_frontend_login_opens_post_login_navigation_hub(self):
        html = read_frontend()

        self.assertIn('id="view-home"', html)
        self.assertIn("Thiết lập hồ sơ", html)
        self.assertIn("Đấu trường tranh biện", html)
        self.assertIn("Xem tiến độ", html)
        self.assertIn('enterApp("account", "home")', html)
        self.assertIn('enterApp("guest", "home")', html)
        self.assertIn('goToArenaFromHub()', html)
        self.assertIn('goToSummaryFromHub()', html)

    def test_frontend_arena_uses_focus_mode(self):
        html = read_frontend()

        self.assertIn('body[data-view="arena"] .sidebar', html)
        self.assertIn('body[data-view="arena"] .topbar', html)
        self.assertIn('body[data-view="arena"] #view-arena', html)
        self.assertIn("syncArenaFocusMode(view)", html)
        self.assertIn("requestArenaFullscreen()", html)
        self.assertIn("exitArenaFullscreen()", html)

    def test_frontend_hides_voice_controls_for_text_input_mode(self):
        html = read_frontend()

        self.assertIn('id="voice-input-btn"', html)
        self.assertIn("function isTextInputMode()", html)
        self.assertIn('state.inputMode === "Text"', html)
        self.assertIn('voiceButton.classList.toggle("hidden", isTextInputMode())', html)
        self.assertIn('if (key === "inputMode") renderArgumentControls();', html)
        self.assertIn("renderArgumentControls();", html)

    def test_frontend_voice_profile_switches_arena_to_voice_only(self):
        html = read_frontend()

        self.assertIn('id="voice-arena-panel"', html)
        self.assertIn('body[data-view="arena"][data-input-mode="voice"] .arena-layout', html)
        self.assertIn('body[data-view="arena"][data-input-mode="voice"] .voice-arena-panel', html)
        self.assertIn("function isVoiceInputMode()", html)
        self.assertIn("function syncInputModeDataset()", html)
        self.assertIn('document.body.dataset.inputMode = isVoiceInputMode() ? "voice" : "text"', html)
        self.assertIn("function startVoiceTurn()", html)
        self.assertIn("await submitArgument({ fromVoice: true })", html)
        self.assertIn("function playLatestRebuttalSpeech()", html)
        self.assertIn('id="voice-replay-btn"', html)
        self.assertIn("/api/v1/speech/synthesize", html)
        self.assertIn('responseType: "blob"', html)
        self.assertIn("let speechAudioCache = { text: \"\", url: \"\" }", html)
        self.assertIn("function clearSpeechAudioCache()", html)
        self.assertIn("function getRebuttalSpeechUrl(text)", html)
        self.assertIn("speechAudioCache.text === clean", html)
        self.assertIn("Zalo AI đang giới hạn lượt tạo giọng đọc", html)
        self.assertIn("new Audio(audioUrl)", html)
        self.assertNotIn("window.speechSynthesis", html)

    def test_frontend_voice_input_uses_media_recorder_backend_stt_only(self):
        html = read_frontend()

        self.assertIn('id="voice-input-btn" type="button" onclick="startVoiceTurn()"', html)
        self.assertIn("isListening: false", html)
        self.assertIn("let mediaRecorder = null", html)
        self.assertIn("let voiceChunks = []", html)
        self.assertIn("function getMediaRecorderMimeType()", html)
        self.assertIn("function transcribeSpeechBlob(blob)", html)
        self.assertIn('id="voice-live-transcript"', html)
        self.assertIn('id="voice-submit-btn"', html)
        self.assertIn('id="voice-source-audio"', html)
        self.assertIn('id="voice-source-player" controls preload="metadata"', html)
        self.assertIn("let voiceSourceAudio = { url: \"\", type: \"\", size: 0 }", html)
        self.assertIn("function saveVoiceSourceAudio(blob)", html)
        self.assertIn("player.src = voiceSourceAudio.url", html)
        self.assertIn("saveVoiceSourceAudio(blob);", html)
        self.assertIn("Âm thanh gốc đã lưu", html)
        self.assertIn("pendingVoiceTranscript", html)
        self.assertIn("function renderVoiceTranscript()", html)
        self.assertIn("state.pendingVoiceTranscript || state.latest?.user_argument", html)
        self.assertIn("/api/v1/speech/transcribe?language=vi", html)
        self.assertIn('language: "vi"', html)
        self.assertIn("rawBody: blob", html)
        self.assertIn("new MediaRecorder(voiceStream", html)
        self.assertIn("navigator.mediaDevices?.getUserMedia && window.MediaRecorder", html)
        self.assertIn("await startMediaRecorderTurn();", html)
        self.assertIn("function getSpeechLanguage()", html)
        self.assertIn("state.isListening = true", html)
        self.assertIn("document.getElementById(\"user-input\").value = clean", html)
        self.assertIn("state.pendingVoiceTranscript = clean", html)
        self.assertIn("Hãy kiểm tra transcript", html)
        self.assertIn("function submitPendingVoiceTranscript()", html)
        self.assertIn("Chờ bạn kiểm tra và gửi transcript...", html)
        self.assertIn("updateCharCount();", html)
        self.assertIn("await submitArgument({ fromVoice: true })", html)
        self.assertIn("await playAiRebuttalSpeech(turn.ai_rebuttal)", html)
        self.assertIn("không hỗ trợ ghi âm MediaRecorder", html)
        self.assertNotIn("SpeechRecognition", html)
        self.assertNotIn("webkitSpeechRecognition", html)
        self.assertNotIn("startWebSpeechTurn", html)
        self.assertNotIn("voiceRecognition", html)

    def test_frontend_includes_lumi_mascot_companion(self):
        html = read_frontend()

        self.assertIn("assets/lumi-paper-dragon-cutout.png", html)
        self.assertTrue((ROOT_DIR / "frontend" / "assets" / "lumi-paper-dragon-cutout.png").exists())
        self.assertIn('id="lumi-companion"', html)
        self.assertIn("LUMI_MESSAGES", html)
        self.assertIn("renderLumiCompanion()", html)
        self.assertIn("Phản biện của Lumi", html)
        self.assertIn("LUMI_GOOD_CER_THRESHOLD", html)
        self.assertIn("lumiThinking", html)
        self.assertIn("lumiVictory", html)
        self.assertIn("lumiAura", html)
        self.assertIn("lumiWingGlint", html)
        self.assertIn('class="lumi-title-token"', html)
        self.assertIn('body[data-lumi-state="thinking"] .lumi-title-token img', html)
        self.assertIn("prefers-reduced-motion: reduce", html)
        self.assertIn(".lumi-stage-token {\n    position: relative;", html)
        self.assertIn("display: block;\n    overflow: visible;", html)
        self.assertIn(".lumi-stage-token img {\n    position: absolute;", html)
        self.assertIn('syncLumiState("thinking")', html)

    def test_frontend_login_uses_generated_dragon_battle_background(self):
        html = read_frontend()

        self.assertIn('id="auth-home"', html)
        self.assertIn('url("assets/login-dragon-battle-bg.png") center / cover no-repeat', html)
        self.assertTrue((ROOT_DIR / "frontend" / "assets" / "login-dragon-battle-bg.png").exists())
        self.assertNotIn('class="login-dragon-scene"', html)
        self.assertNotIn('class="login-weapon login-sword"', html)
        self.assertNotIn("loginDragonFloat", html)
        self.assertIn("goToAuthView('login')", html)

    def test_frontend_loads_onboarding_tutorial_assets(self):
        html = read_frontend()

        self.assertIn('href="styles/onboarding.css"', html)
        self.assertIn('href="styles/tutorial.css"', html)
        self.assertIn('href="styles/tooltips.css"', html)
        self.assertIn('src="scripts/onboarding.js"', html)
        self.assertIn('src="scripts/tutorial.js"', html)
        self.assertIn('src="scripts/demoSession.js"', html)
        self.assertIn('src="components/knowledge/knowledgeHero.js"', html)

        for path in [
            "frontend/assets/mascot/dragon-clean.png",
            "frontend/assets/mascot/lightbulb.svg",
            "frontend/styles/onboarding.css",
            "frontend/styles/tutorial.css",
            "frontend/styles/tooltips.css",
            "frontend/scripts/onboarding.js",
            "frontend/scripts/tutorial.js",
            "frontend/scripts/demoSession.js",
            "frontend/components/knowledge/knowledgeHero.js",
            "frontend/components/onboarding/README.md",
            "frontend/components/tooltips/README.md",
            "frontend/components/tutorial/README.md",
            "frontend/components/knowledge/README.md",
            "frontend/components/demo/README.md",
        ]:
            self.assertTrue((ROOT_DIR / path).exists(), path)

    def test_onboarding_tutorial_assets_expose_required_features(self):
        onboarding = (ROOT_DIR / "frontend" / "scripts" / "onboarding.js").read_text(encoding="utf-8")
        tutorial = (ROOT_DIR / "frontend" / "scripts" / "tutorial.js").read_text(encoding="utf-8")
        demo = (ROOT_DIR / "frontend" / "scripts" / "demoSession.js").read_text(encoding="utf-8")
        knowledge_hero = (ROOT_DIR / "frontend" / "components" / "knowledge" / "knowledgeHero.js").read_text(encoding="utf-8")

        self.assertIn("ai_debate_trainer.onboarding.seen", onboarding)
        self.assertIn("Chào mừng đến với AI Debate Trainer", onboarding)
        self.assertIn("Xem phiên demo", onboarding)
        self.assertIn("Bắt đầu tranh biện", onboarding)
        self.assertIn("window.enterApp = function wrappedEnterApp", onboarding)

        self.assertIn("Kiến thức nền tảng để tranh biện", tutorial)
        self.assertIn("AIDebateKnowledgeHero?.render", tutorial)
        self.assertIn("Kiến thức nền tảng để tranh biện", knowledge_hero)
        self.assertIn("Nếu bạn là người chưa từng tranh biện, hãy đọc phần này cùng Lumi", knowledge_hero)
        self.assertIn("assets/mascot/dragon-clean.png", knowledge_hero)
        self.assertIn("assets/mascot/lightbulb.svg", knowledge_hero)
        self.assertIn("knowledge-mascot", knowledge_hero)
        self.assertIn("knowledge-copy", knowledge_hero)
        self.assertIn("knowledge-nudge", knowledge_hero)
        self.assertIn("function analyzeArgument", tutorial)
        self.assertIn("Strong reasoning detected.", tutorial)
        self.assertIn("CER_HELP", tutorial)
        self.assertIn("No debate sessions yet", tutorial)

        self.assertIn("frontend-only", demo)
        self.assertIn("Replay demo", demo)
        self.assertIn("Start real session", demo)
        self.assertIn("claim: 78", demo)
        self.assertIn("evidence: 65", demo)
        self.assertIn("reasoning: 74", demo)
        self.assertNotIn("/api/v1/debate/turn", demo)


if __name__ == "__main__":
    unittest.main()
