import unittest

from fastapi.testclient import TestClient

import main


class StockQuizApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def test_health_reports_loaded_data(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total_quizzes"], 0)
        self.assertGreater(data["total_cards"], 0)

    def test_public_quizzes_do_not_expose_answers(self):
        response = self.client.get("/api/quizzes/all", params={"stage": 1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())
        self.assertNotIn("answer_index", response.json()[0])
        self.assertNotIn("explanation", response.json()[0])

    def test_random_quiz_count_is_bounded(self):
        for invalid_count in (-1, 0, 101):
            with self.subTest(count=invalid_count):
                response = self.client.get(
                    "/api/quizzes", params={"stage": 1, "count": invalid_count}
                )
                self.assertEqual(response.status_code, 422)

    def test_verify_rejects_out_of_range_options(self):
        quiz = main.QUIZ_DATABASE[0]
        for selected_index in (-2, len(quiz["options"])):
            with self.subTest(selected_index=selected_index):
                response = self.client.post(
                    "/api/quiz/verify",
                    json={"quiz_id": quiz["id"], "selected_index": selected_index},
                )
                self.assertEqual(response.status_code, 422)

    def test_verify_accepts_timeout_sentinel(self):
        quiz = main.QUIZ_DATABASE[0]
        response = self.client.post(
            "/api/quiz/verify",
            json={"quiz_id": quiz["id"], "selected_index": -1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_correct"])


if __name__ == "__main__":
    unittest.main()
