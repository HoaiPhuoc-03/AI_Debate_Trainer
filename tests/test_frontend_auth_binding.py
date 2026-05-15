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
        self.assertIn("window.SpeechRecognition || window.webkitSpeechRecognition", html)
        self.assertIn("await submitArgument({ fromVoice: true })", html)
        self.assertIn("function speakLatestRebuttal()", html)
        self.assertIn("window.speechSynthesis", html)

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


if __name__ == "__main__":
    unittest.main()
