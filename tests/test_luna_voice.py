"""Dependency-free tests for Luna Voice configuration and reply bridge."""
import io
import json
import unittest
from unittest.mock import patch

import luna_voice


class VoiceConfigurationTests(unittest.TestCase):
    def test_loopback_endpoint_is_allowed_without_remote_opt_in(self):
        self.assertEqual(
            luna_voice.configured_endpoint({"LUNA_CHAT_ENDPOINT": "http://localhost:1234/v1/chat/completions"}),
            "http://localhost:1234/v1/chat/completions",
        )

    def test_remote_endpoint_is_blocked_by_default(self):
        with self.assertRaisesRegex(ValueError, "Remote model endpoints are disabled"):
            luna_voice.configured_endpoint({"LUNA_CHAT_ENDPOINT": "https://example.com/v1/chat/completions"})

    def test_remote_endpoint_requires_explicit_opt_in(self):
        endpoint = "https://example.com/v1/chat/completions"
        self.assertEqual(
            luna_voice.configured_endpoint({
                "LUNA_CHAT_ENDPOINT": endpoint,
                "LUNA_ALLOW_REMOTE": "1",
            }),
            endpoint,
        )

    def test_local_reply_supports_greetings_help_status_and_unknown_requests(self):
        self.assertIn("Hello, Fabian", luna_voice.local_reply("Hola Luna"))
        self.assertIn("connect", luna_voice.local_reply("help"))
        self.assertIn("language model", luna_voice.local_reply("status"))
        self.assertIn("not connected yet", luna_voice.local_reply("explain relativity"))
        self.assertIn("closing", luna_voice.local_reply("goodbye Luna"))


class VoiceModelBridgeTests(unittest.TestCase):
    def test_model_reply_updates_only_the_supplied_in_memory_history(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({
                    "choices": [{"message": {"content": "Hello from the local model."}}]
                }).encode("utf-8")

        history = []
        with patch("luna_voice.urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            answer = luna_voice.ask_model(
                "Hi Luna",
                history,
                environ={"LUNA_CHAT_ENDPOINT": "http://127.0.0.1:1234/v1/chat/completions"},
            )
        self.assertEqual(answer, "Hello from the local model.")
        self.assertEqual(history[-2]["content"], "Hi Luna")
        self.assertEqual(history[-1]["content"], answer)
        self.assertTrue(urlopen.called)

    def test_model_bridge_rejects_remote_endpoint_before_network_call(self):
        with patch("luna_voice.urllib.request.urlopen") as urlopen:
            with self.assertRaisesRegex(ValueError, "Remote model endpoints are disabled"):
                luna_voice.ask_model(
                    "Hi Luna",
                    environ={"LUNA_CHAT_ENDPOINT": "https://example.com/v1/chat/completions"},
                )
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
