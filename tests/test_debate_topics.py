import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


class DebateTopicsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_topics_returns_seed_bank(self):
        response = self.client.get("/api/v1/debate/topics")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["topics"], list)
        self.assertGreaterEqual(data["total"], 50)
        self.assertIn("id", data["topics"][0])
        self.assertIn("tags", data["topics"][0])

    def test_get_topics_filters_category(self):
        response = self.client.get("/api/v1/debate/topics?category=Giáo dục")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["topics"])
        self.assertTrue(all(topic["category"] == "Giáo dục" for topic in data["topics"]))

    def test_get_topics_filters_difficulty_alias(self):
        response = self.client.get("/api/v1/debate/topics?difficulty=Trung bình")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["topics"])
        self.assertTrue(all(topic["difficulty"] == "Trung cấp" for topic in data["topics"]))

    def test_get_topics_searches_title_category_and_tags(self):
        response = self.client.get("/api/v1/debate/topics?q=AI")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["topics"])
        self.assertTrue(
            any(
                "AI" in topic["title"]
                or "AI" in topic["category"]
                or "AI" in topic["tags"]
                for topic in data["topics"]
            )
        )

    def test_get_topics_filters_tag_and_limit(self):
        response = self.client.get("/api/v1/debate/topics?tag=AI&limit=2")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(data["total"], 2)
        self.assertTrue(all("AI" in topic["tags"] for topic in data["topics"]))

    def test_get_topic_categories_returns_counts(self):
        response = self.client.get("/api/v1/debate/topic-categories")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["categories"]), 10)
        self.assertTrue(all(category["count"] >= 5 for category in data["categories"]))


if __name__ == "__main__":
    unittest.main()
