import unittest

from services.llm_service import LLMServiceError, generate_llm_response


class LLMServiceTests(unittest.TestCase):
    def test_generate_llm_response_rejects_empty_prompt(self):
        with self.assertRaises(LLMServiceError) as context:
            generate_llm_response("   ")

        self.assertEqual(context.exception.code, "empty_prompt")
        self.assertEqual(context.exception.status_code, 400)

    def test_generate_llm_response_rejects_missing_model(self):
        with self.assertRaises(LLMServiceError) as context:
            generate_llm_response("Hello", model="")

        self.assertEqual(context.exception.code, "missing_model")
        self.assertEqual(context.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
