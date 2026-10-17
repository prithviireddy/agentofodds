"""Offline Gemini client and M0 structured-output tests."""
from io import BytesIO
import json
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from backend.app.adapters.llm_gemini import GeminiClient, ModelError, validate_m0_output


class GeminiTests(unittest.TestCase):
    def test_missing_key_prevents_request(self):
        with self.assertRaises(ModelError) as caught:
            GeminiClient("")
        self.assertEqual(caught.exception.status, "missing_configuration")

    def test_request_schema_and_safe_metadata(self):
        generated = {"company": "MSFT", "status": "insufficient_evidence", "source_ids": ["a", "b"], "limitation": "No passages."}
        response = {"candidates": [{"content": {"parts": [{"text": json.dumps(generated)}]}}],
                    "usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 9, "totalTokenCount": 20}}
        opener = Mock(return_value=BytesIO(json.dumps(response).encode()))
        result, metadata = GeminiClient("test-key", opener).generate_structured("test")
        request = opener.call_args.args[0]
        request_body = json.loads(request.data)
        self.assertEqual(request_body["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(request_body["generationConfig"]["maxOutputTokens"], 256)
        self.assertEqual(request_body["generationConfig"]["thinkingConfig"]["thinkingLevel"], "minimal")
        self.assertEqual(request.headers["X-goog-api-key"], "test-key")
        self.assertNotIn("test-key", json.dumps(metadata))
        self.assertEqual(metadata["usage"]["totalTokenCount"], 20)
        self.assertEqual(result, generated)

    def test_invalid_model_or_budget_rejected(self):
        client = GeminiClient("key", Mock())
        with self.assertRaises(ValueError):
            client.generate_structured("x", model="other")
        with self.assertRaises(ValueError):
            client.generate_structured("x", max_output_tokens=257)
        client.opener.assert_not_called()

    def test_invalid_response_and_http_no_retry(self):
        with self.assertRaises(ModelError) as caught:
            GeminiClient("key", Mock(return_value=BytesIO(b"{}"))).generate_structured("x")
        self.assertEqual(caught.exception.status, "failed_validation")
        self.assertEqual(caught.exception.details["stage"], "candidate")
        self.assertEqual(caught.exception.details["candidate_count"], 0)
        opener = Mock(side_effect=HTTPError("url", 429, "", {}, None))
        with self.assertRaises(ModelError) as caught:
            GeminiClient("key", opener).generate_structured("x")
        self.assertEqual(caught.exception.status, "awaiting_quota")
        self.assertEqual(opener.call_count, 1)
        unavailable = Mock(side_effect=HTTPError("url", 503, "", {}, None))
        with self.assertRaises(ModelError) as caught:
            GeminiClient("key", unavailable).generate_structured("x")
        self.assertEqual(caught.exception.status, "service_unavailable")
        self.assertEqual(unavailable.call_count, 1)

    def test_invalid_candidate_json_has_safe_shape_diagnostics(self):
        response = {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "{bad"}]}}],
                    "usageMetadata": {"totalTokenCount": 256}}
        with self.assertRaises(ModelError) as caught:
            GeminiClient("key", Mock(return_value=BytesIO(json.dumps(response).encode()))).generate_structured("x")
        details = caught.exception.details
        self.assertEqual(details["stage"], "candidate_json")
        self.assertEqual(details["finish_reasons"], ["MAX_TOKENS"])
        self.assertTrue(details["has_text"])
        self.assertNotIn("{bad", json.dumps(details))

    def test_strict_output_validation(self):
        good = {"company": "MSFT", "status": "insufficient_evidence", "source_ids": ["a", "b"], "limitation": "No passages."}
        self.assertEqual(validate_m0_output(good, "MSFT", ["a", "b"]), good)
        for bad in ({**good, "extra": "x"}, {**good, "status": "success"}, {**good, "source_ids": ["a"]}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    validate_m0_output(bad, "MSFT", ["a", "b"])

    def test_general_json_request_has_bounded_application_budget(self):
        generated = {"company": "MSFT"}
        response = {"candidates": [{"content": {"parts": [{"text": json.dumps(generated)}]}}]}
        opener = Mock(return_value=BytesIO(json.dumps(response).encode()))
        schema = {"type": "object", "properties": {"company": {"type": "string"}}}
        result, _ = GeminiClient("test-key", opener).generate_json("research", schema, max_output_tokens=768)
        body = json.loads(opener.call_args.args[0].data)
        self.assertEqual(result, generated)
        self.assertEqual(body["generationConfig"]["responseJsonSchema"], schema)
        self.assertEqual(body["generationConfig"]["maxOutputTokens"], 768)
        with self.assertRaises(ValueError):
            GeminiClient("key", Mock()).generate_json("x", schema, max_output_tokens=1025)
        with self.assertRaises(ValueError):
            GeminiClient("key", Mock()).generate_json("x", schema, thinking_level="high")


if __name__ == "__main__":
    unittest.main()



