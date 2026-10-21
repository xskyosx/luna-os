"""Standard-library unittest coverage for the encrypted LUNA profile vault."""
import json
import tempfile
import unittest
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
except ImportError:
    AESGCM = None

from privacy.private_profile import VaultError, load_profile, save_profile


@unittest.skipIf(AESGCM is None, "install cryptography to test AES-GCM vault")
class PrivateProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "profile.vault"
        self.password = "correct horse battery staple"

    def tearDown(self):
        self.temp.cleanup()

    def test_round_trip_and_ciphertext_does_not_expose_profile_values(self):
        profile = {"display_name": "Example Person", "notes": "private note"}
        save_profile(self.path, profile, self.password)
        self.assertEqual(load_profile(self.path, self.password), profile)
        raw = self.path.read_text(encoding="utf-8")
        self.assertNotIn("Example Person", raw)
        self.assertNotIn("private note", raw)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_wrong_passphrase_fails_closed(self):
        save_profile(self.path, {"secret": "value"}, self.password)
        with self.assertRaises(VaultError):
            load_profile(self.path, "this is the wrong passphrase")

    def test_tampering_fails_integrity_check(self):
        save_profile(self.path, {"secret": "value"}, self.password)
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        envelope["ciphertext"] = envelope["ciphertext"][:-4] + "AAAA"
        self.path.write_text(json.dumps(envelope), encoding="utf-8")
        with self.assertRaises(VaultError):
            load_profile(self.path, self.password)

    def test_empty_passphrase_rejected(self):
        with self.assertRaises(VaultError):
            save_profile(self.path, {"secret": "value"}, "")


if __name__ == "__main__":
    unittest.main()
