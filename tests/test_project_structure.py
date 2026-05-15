import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class ProjectStructureTests(unittest.TestCase):
    def test_root_requirements_aggregates_runtime_dependencies(self):
        requirements = (ROOT_DIR / "requirements.txt").read_text(encoding="utf-8")

        self.assertIn("-r backend/requirements.txt", requirements)
        self.assertIn("-r requirements-desktop.txt", requirements)

    def test_groq_check_script_lives_under_scripts(self):
        self.assertTrue((ROOT_DIR / "scripts" / "check_groq_provider.py").exists())
        self.assertFalse((ROOT_DIR / "backend" / "test_groq_provider.py").exists())

    def test_ai_provider_http_client_is_isolated(self):
        ai_service = (ROOT_DIR / "backend" / "app" / "services" / "ai_service.py").read_text(encoding="utf-8")
        groq_client = (ROOT_DIR / "backend" / "app" / "services" / "groq_client.py").read_text(encoding="utf-8")

        self.assertNotIn("import httpx", ai_service)
        self.assertIn("import httpx", groq_client)
        self.assertIn("from app.services.prompt_builder import build_groq_messages", ai_service)

    def test_removed_empty_frontend_scratch_file(self):
        self.assertFalse((ROOT_DIR / "frontend" / "a").exists())


if __name__ == "__main__":
    unittest.main()
