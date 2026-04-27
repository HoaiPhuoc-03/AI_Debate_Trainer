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


if __name__ == "__main__":
    unittest.main()
