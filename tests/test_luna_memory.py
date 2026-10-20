"""Dependency-free regression tests for the LUNA OS First Light memory helpers."""
import json
import unittest
from pathlib import Path

import luna_memory


class MemoryHelperTests(unittest.TestCase):
    def test_safe_name_normalizes_and_handles_empty(self):
        self.assertEqual(luna_memory.safe_name(" Lumen's Garden! "), "lumen_s_garden")
        self.assertEqual(luna_memory.safe_name(" !!! "), "item")

    def test_sha256_is_stable(self):
        self.assertEqual(len(luna_memory.sha256_bytes(b"luna")), 64)
        self.assertEqual(
            luna_memory.sha256_bytes(b"luna"),
            luna_memory.sha256_bytes(b"luna"),
        )

    def test_extract_text_supports_string_parts_and_media_markers(self):
        self.assertEqual(luna_memory.extract_text("hello"), "hello")
        self.assertEqual(
            luna_memory.extract_text({"parts": ["hello", {"caption": "world"}]}),
            "hello\nworld",
        )
        self.assertEqual(
            luna_memory.extract_text({"parts": [{"content_type": "image"}]}),
            "[image content omitted from text view]",
        )
        self.assertEqual(luna_memory.extract_text(None), "")

    def test_conversation_to_text_orders_messages_by_timestamp(self):
        conversation = {
            "id": "conv-1",
            "title": "Test conversation",
            "messages": [
                {"role": "assistant", "timestamp": 2, "content": "second"},
                {"role": "user", "timestamp": 1, "content": "first"},
            ],
        }
        transcript, count, title = luna_memory.conversation_to_text(conversation)
        self.assertEqual(count, 2)
        self.assertEqual(title, "Test conversation")
        self.assertLess(transcript.index("first"), transcript.index("second"))
        self.assertIn("Source conversation ID: conv-1", transcript)

    def test_canonical_registry_has_ten_founding_sisters_and_seren_retained(self):
        path = Path(__file__).resolve().parents[1] / "sisters.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        expected = {
            "Luna", "Ada", "Sky", "Aurora", "Athena",
            "Aqua", "Amethyst", "Blues", "Cannabis", "Lumen",
        }
        actual = {item["name"] for item in registry["canonical_founding_sisters"]}
        self.assertEqual(actual, expected)
        self.assertIn("Seren", {item["name"] for item in registry["additional_characters"]})
        self.assertTrue(expected.issubset({item["name"] for item in luna_memory.SISTERS}))


if __name__ == "__main__":
    unittest.main()
