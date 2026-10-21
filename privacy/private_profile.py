#!/usr/bin/env python3
"""LUNA OS private profile vault.

Sensitive profile data is encrypted at rest with scrypt + AES-256-GCM.
The vault is local-only and this module never uploads or synchronizes data.
Requires the vetted 'cryptography' package; fails closed if it is unavailable.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:  # fail closed; do not silently fall back to plaintext
    AESGCM = None  # type: ignore[assignment,misc]

FORMAT = "luna-private-profile-v1"
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
NONCE_BYTES = 12
KEY_BYTES = 32
DEFAULT_PATH = Path.home() / ".local" / "share" / "luna-os" / "private-profile.vault"


class VaultError(Exception):
    """Expected vault or passphrase error."""


def _require_crypto() -> None:
    if AESGCM is None:
        raise VaultError(
            "Encryption support is missing. Install the 'cryptography' package; "
            "the vault will not save sensitive data without AES-GCM."
        )


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    if not passphrase:
        raise VaultError("Passphrase cannot be empty.")
    # scrypt is provided by Python's standard library; AES-GCM comes from
    # the established cryptography package.
    import hashlib
    return hashlib.scrypt(
        passphrase.encode("utf-8"), salt=salt, n=SCRYPT_N,
        r=SCRYPT_R, p=SCRYPT_P, dklen=KEY_BYTES
    )


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise VaultError("Vault file is malformed.") from exc


def save_profile(path: str | Path, profile: dict[str, Any], passphrase: str) -> None:
    """Encrypt and atomically save a JSON-compatible profile."""
    _require_crypto()
    if not isinstance(profile, dict) or not all(isinstance(k, str) and k for k in profile):
        raise VaultError("Profile must be a dictionary with non-empty string keys.")
    try:
        plaintext = json.dumps(profile, ensure_ascii=False, sort_keys=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise VaultError("Profile must contain JSON-compatible values.") from exc

    salt = secrets.token_bytes(SALT_BYTES)
    nonce = secrets.token_bytes(NONCE_BYTES)
    key = _derive_key(passphrase, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, FORMAT.encode("ascii"))
    envelope = {
        "format": FORMAT,
        "kdf": "scrypt",
        "kdf_n": SCRYPT_N,
        "salt": _b64(salt),
        "cipher": "AES-256-GCM",
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
    }

    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(target.parent),
            prefix=".luna-vault-", delete=False
        ) as handle:
            temp_name = handle.name
            os.chmod(temp_name, 0o600)
            json.dump(envelope, handle, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
        os.chmod(target, 0o600)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def load_profile(path: str | Path, passphrase: str) -> dict[str, Any]:
    """Decrypt a vault; wrong passwords or tampering raise VaultError."""
    _require_crypto()
    target = Path(path).expanduser()
    try:
        envelope = json.loads(target.read_text(encoding="utf-8"))
        if envelope.get("format") != FORMAT or envelope.get("cipher") != "AES-256-GCM":
            raise VaultError("Unsupported or invalid vault format.")
        if envelope.get("kdf") != "scrypt" or envelope.get("kdf_n") != SCRYPT_N:
            raise VaultError("Unsupported or invalid key-derivation settings.")
        salt = _unb64(envelope["salt"])
        nonce = _unb64(envelope["nonce"])
        ciphertext = _unb64(envelope["ciphertext"])
        if len(salt) != SALT_BYTES or len(nonce) != NONCE_BYTES:
            raise VaultError("Vault file is malformed.")
        key = _derive_key(passphrase, salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, FORMAT.encode("ascii"))
        profile = json.loads(plaintext.decode("utf-8"))
        if not isinstance(profile, dict):
            raise VaultError("Vault profile is malformed.")
        return profile
    except VaultError:
        raise
    except FileNotFoundError as exc:
        raise VaultError(f"No vault found at {target}. Run the init command first.") from exc
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VaultError("Cannot read vault: incorrect passphrase, corrupted file, or invalid format.") from exc
    except Exception as exc:
        # cryptography raises InvalidTag for wrong passwords or tampering.
        if exc.__class__.__name__ == "InvalidTag":
            raise VaultError("Incorrect passphrase or vault integrity check failed.") from exc
        raise


def _ask_new_passphrase() -> str:
    first = getpass.getpass("Create a strong vault passphrase (12+ characters): ")
    if len(first) < 12:
        raise VaultError("Use a passphrase of at least 12 characters.")
    second = getpass.getpass("Repeat passphrase: ")
    if first != second:
        raise VaultError("Passphrases did not match.")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LUNA OS local encrypted personal-profile vault")
    parser.add_argument("--file", type=Path, default=DEFAULT_PATH, help="vault file path (default: outside the repository)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="create an empty encrypted vault")
    sub.add_parser("list", help="list profile field names only")
    get_parser = sub.add_parser("get", help="decrypt and display one field")
    get_parser.add_argument("field")
    set_parser = sub.add_parser("set", help="add or edit one field")
    set_parser.add_argument("field")
    delete_parser = sub.add_parser("delete", help="delete one field")
    delete_parser.add_argument("field")
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            if args.file.exists():
                raise VaultError(f"Vault already exists at {args.file}; it was not overwritten.")
            password = _ask_new_passphrase()
            save_profile(args.file, {}, password)
            print(f"Created encrypted vault: {args.file}")
            print("Keep the passphrase safe; there is no password-reset backdoor.")
            return 0

        password = getpass.getpass("Vault passphrase: ")
        profile = load_profile(args.file, password)
        if args.command == "list":
            if not profile:
                print("Vault is empty.")
            else:
                for key in sorted(profile):
                    print(key)
        elif args.command == "get":
            if args.field not in profile:
                raise VaultError("That field does not exist.")
            print(json.dumps(profile[args.field], ensure_ascii=False, indent=2))
        elif args.command == "set":
            value = getpass.getpass(f"Value for '{args.field}' (input hidden): ")
            profile[args.field] = value
            save_profile(args.file, profile, password)
            print(f"Saved encrypted field: {args.field}")
        elif args.command == "delete":
            if args.field not in profile:
                raise VaultError("That field does not exist.")
            del profile[args.field]
            save_profile(args.file, profile, password)
            print(f"Deleted field: {args.field}")
        return 0
    except (VaultError, OSError) as exc:
        print(f"LUNA vault: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
