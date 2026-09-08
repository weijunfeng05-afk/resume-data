import unittest
from pathlib import Path
from unittest.mock import patch

import screening
from streamlit.testing.v1 import AppTest


class DeepSeekTests(unittest.TestCase):
    @patch("screening.OpenAI")
    def test_empty_key_never_creates_client(self, client):
        with self.assertRaisesRegex(ValueError, "DEEPSEEK_API_KEY"):
            screening.screen_resume("测试简历", "   ")
        client.assert_not_called()

    @patch("screening.OpenAI")
    def test_only_official_endpoints_receive_key(self, client):
        for url in ("https://api.deepseek.com.evil.test", "http://api.deepseek.com", "https://ark.cn-beijing.volces.com/api/v3"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                screening._deepseek_client("test-key", url)
        client.assert_not_called()

    @patch("screening.OpenAI")
    def test_v1_endpoint_and_whitespace(self, client):
        screening._deepseek_client(" test-key ", " https://api.deepseek.com/v1/ ")
        client.assert_called_once_with(api_key="test-key", base_url="https://api.deepseek.com/v1", timeout=120, max_retries=0)

    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "", "ARK_API_KEY": "legacy-key"})
    @patch("screening.OpenAI")
    def test_page_starts_and_missing_key_does_not_call_api(self, client):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertIn("DeepSeek", app.title[0].value)
        self.assertIn("DeepSeek API Key", [x.label for x in app.sidebar.text_input])
        app.sidebar.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("请先输入", app.error[0].value)
        client.assert_not_called()
