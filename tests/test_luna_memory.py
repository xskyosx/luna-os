"""Dependency-free regression tests for LUNA OS memory helpers and file safety."""
import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import luna_memory


@contextmanager
def isolated_project(root):
    """Redirect every project path into a temporary directory for safe tests."""
    root = Path(root)
    values = {
        "ROOT": root,
        "MEMORIES": root / "memories",
        "TRANSCRIPTS": root / "transcripts",
        "BACKUPS": root / "backups",
        "IMPORTS": root / "imports",
        "INBOX": root / "imports" / "inbox",
        "ORIGINALS": root / "imports" / "originals",
        "MANIFESTS": root / "imports" / "manifests",
        "REGISTRY": root / "sisters.json",
    }
    with patch.multiple(luna_memory, **values):
        luna_memory.setup()
        yield


class MemoryHelperTests(unittest.TestCase):
    def test_safe_name_normalizes_and_handles_empty(self):
        self.assertEqual(luna_memory.safe_name(" Lumen's Garden! "), "lumen_s_garden")
        self.assertEqual(luna_memory.safe_name(" !!! "), "item")

    def test_sha256_is_stable(self):
        self.assertEqual(len(luna_memory.sha256_bytes(b"luna")), 64)
        self.assertEqual(luna_memory.sha256_bytes(b"luna"), luna_memory.sha256_bytes(b"luna"))

    def test_extract_text_supports_string_parts_and_media_markers(self):
        self.assertEqual(luna_memory.extract_text("hello"), "hello")
        self.assertEqual(
            luna_memory.extract_text({"parts": ["hello", {"caption": "world"}]}),
            "hello\\nworld",
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


class MemoryFileSafetyTests(unittest.TestCase):
    def test_backup_restore_round_trip_in_temporary_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            with isolated_project(root):
                memory = luna_memory.MEMORIES / "kept.json"
                memory.write_text('{"title":"preserve me"}\\n', encoding="utf-8")
                archive = luna_memory.backup("round_trip")
                self.assertTrue(archive.is_file())
                memory.unlink()
                with patch("builtins.input", return_value="1"), contextlib.redirect_stdout(io.StringIO()):
                    luna_memory.restore_backup()
                self.assertTrue(memory.is_file())
                self.assertEqual(json.loads(memory.read_text(encoding="utf-8"))["title"], "preserve me")

    def test_restore_rejects_parent_traversal_before_extracting(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            outside = Path(temp) / "escaped.txt"
            with isolated_project(root):
                hostile = luna_memory.BACKUPS / "hostile.zip"
                with zipfile.ZipFile(hostile, "w") as archive:
                    archive.writestr("../../escaped.txt", "not allowed")
                with patch("builtins.input", return_value="1"), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(ValueError, "Unsafe backup path"):
                        luna_memory.restore_backup()
                self.assertFalse(outside.exists())

    def test_chatgpt_import_preserves_original_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            export = Path(temp) / "conversations.json"
            original_bytes = json.dumps(
                [{"id": "conversation-1", "title": "Lumen", "messages": [
                    {"role": "user", "timestamp": 1, "content": "hello"}
                ]}],
                ensure_ascii=False,
            ).encode("utf-8")
            export.write_bytes(original_bytes)
            with isolated_project(root):
                with patch("builtins.input", side_effect=[str(export), "IMPORT"]), contextlib.redirect_stdout(io.StringIO()):
                    luna_memory.import_chatgpt_export()
                originals = list(luna_memory.ORIGINALS.glob("*.json"))
                transcripts = list(luna_memory.TRANSCRIPTS.glob("*.txt"))
                manifests = list(luna_memory.MANIFESTS.glob("*.json"))
                self.assertEqual(len(originals), 1)
                self.assertEqual(originals[0].read_bytes(), original_bytes)
                self.assertEqual(len(transcripts), 1)
                self.assertEqual(json.loads(manifests[0].read_text(encoding="utf-8"))["transcripts_created"], 1)

                with patch("builtins.input", return_value=str(export)), contextlib.redirect_stdout(io.StringIO()):
                    luna_memory.import_chatgpt_export()
                self.assertEqual(len(list(luna_memory.TRANSCRIPTS.glob("*.txt"))), 1)
                self.assertEqual(len(list(luna_memory.ORIGINALS.glob("*.json"))), 1)
                self.assertEqual(len(list(luna_memory.MANIFESTS.glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
