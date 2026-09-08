import io
import json
import unittest
from unittest.mock import patch

import screening


SAMPLE_RESULT = {
    "candidate_name": "测试候选人",
    "toc_score": 70,
    "toc_priority": "中优先复核",
    "internal_ai_score": 80,
    "internal_ai_priority": "高优先复核",
    "best_fit_role": "内部提效 AI 产品经理",
    "claimed_ai_depth": "简历自述：搭建过 AI 原型",
    "verification_confidence": "中",
    "ownership_level": "中",
    "strengths": ["有原型经验"],
    "risks": ["上线结果不明确"],
    "unknowns": ["ROI 未说明"],
    "must_verify": ["核验个人实际贡献"],
    "final_recommendation": "建议 HR 在面试中人工复核项目证据。",
}


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class ScreeningTests(unittest.TestCase):
    @patch("screening.PdfReader")
    def test_extract_pdf_text_combines_non_empty_pages(self, reader_cls):
        reader_cls.return_value.is_encrypted = False
        reader_cls.return_value.pages = [FakePage("第一页"), FakePage(None), FakePage("第二页")]
        result = screening.extract_pdf_text(io.BytesIO(b"fake-pdf"))
        self.assertEqual(result, "第一页\n\n第二页")

    @patch("screening.PdfReader", side_effect=Exception("broken"))
    def test_invalid_pdf_has_clear_error(self, _reader_cls):
        with self.assertRaisesRegex(screening.PdfExtractionError, "文件已损坏"):
            screening.extract_pdf_text(io.BytesIO(b"not-a-pdf"))

    def test_empty_resume_is_rejected_before_api_call(self):
        with self.assertRaisesRegex(ValueError, "简历文本为空"):
            screening.screen_resume("   ", api_key="test")

    @patch("screening.OpenAI")
    def test_api_connection_checks_selected_model(self, ark_cls):
        message = type("Message", (), {"content": "连接成功"})()
        choice = type("Choice", (), {"message": message})()
        ark_cls.return_value.chat.completions.create.return_value = type(
            "Completion", (), {"choices": [choice]}
        )()
        reply = screening.test_deepseek_connection(api_key="test-key")
        self.assertEqual(reply, "连接成功")
        ark_cls.assert_called_once_with(
            api_key="test-key", base_url=screening.DEFAULT_DEEPSEEK_BASE_URL, timeout=120, max_retries=0
        )
        kwargs = ark_cls.return_value.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], screening.DEFAULT_DEEPSEEK_MODEL)

    def test_coding_plan_base_url_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "DeepSeek 官方地址"):
            screening.test_deepseek_connection(
                api_key="test-key",
                base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
            )

    @patch("screening.OpenAI")
    def test_model_call_uses_strict_schema_and_returns_json(self, ark_cls):
        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                message = type(
                    "Message", (), {"content": json.dumps(SAMPLE_RESULT, ensure_ascii=False)}
                )()
                choice = type("Choice", (), {"message": message})()
                return type("Completion", (), {"choices": [choice]})()

        ark_cls.return_value.chat.completions = FakeCompletions()
        result = screening.screen_resume("候选人有 AI 原型经验", api_key="test-key")

        self.assertEqual(captured["response_format"], {"type": "json_object"})
        self.assertEqual(captured["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertEqual(result, SAMPLE_RESULT)
        self.assertEqual(captured["model"], screening.DEFAULT_DEEPSEEK_MODEL)
        self.assertIn("不能自动决定录用或淘汰", captured["messages"][0]["content"])
        self.assertIn("完全忽略性别", captured["messages"][0]["content"])

    def test_invalid_model_json_has_clear_error(self):
        with self.assertRaisesRegex(screening.ModelResponseFormatError, "合法 JSON"):
            screening._parse_and_validate_result("这不是 JSON")

    def test_model_json_with_missing_fields_has_clear_error(self):
        with self.assertRaisesRegex(screening.ModelResponseFormatError, "字段不匹配"):
            screening._parse_and_validate_result('{"candidate_name": "测试"}')

    def test_schema_contains_all_requested_fields(self):
        expected = {
            "candidate_name", "toc_score", "toc_priority", "internal_ai_score",
            "internal_ai_priority", "best_fit_role", "claimed_ai_depth",
            "verification_confidence", "ownership_level", "strengths", "risks",
            "unknowns", "must_verify", "final_recommendation",
        }
        self.assertEqual(set(screening.RESULT_SCHEMA["required"]), expected)
        self.assertFalse(screening.RESULT_SCHEMA["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
