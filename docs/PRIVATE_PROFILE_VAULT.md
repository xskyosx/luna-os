# LUNA OS Private Profile Vault

The private-profile module stores user-entered profile fields in a local encrypted file. It is separate from the public memory/transcript archive and does not contain any personal data by default.

## Security model

- AES-256-GCM authenticated encryption using the established `cryptography` package.
- A key is derived from a passphrase with scrypt; the passphrase is never written to disk.
- Vault writes are atomic and the file is set to owner-only permissions (`0600`) where supported.
- Wrong passphrases and altered ciphertext fail closed.
- The default vault path is `~/.local/share/luna-os/private-profile.vault`, outside the repository.
- The module has no network, upload, or cloud-sync functionality.
- There is no password reset or recovery backdoor. If the passphrase is lost, the encrypted contents cannot be recovered.
- This is protection at rest, not a substitute for device encryption, a secure device account, or protection from malware/root access. Python strings and terminal memory cannot be guaranteed to be securely erased.

## Install

Alpine Linux (package availability depends on repository configuration):

```sh
apk add python3 py3-cryptography
```

Termux, if the package is available from your configured repositories:

```sh
pkg install python cryptography
```

Alternatively, in a suitable Python environment:

```sh
python -m pip install cryptography
```

If the dependency is missing, the module refuses to write any vault data. It never falls back to plaintext.

## Usage

Run from the repository root:

```sh
python3 privacy/private_profile.py init
python3 privacy/private_profile.py set display_name
python3 privacy/private_profile.py set contact_note
python3 privacy/private_profile.py list
python3 privacy/private_profile.py get display_name
python3 privacy/private_profile.py delete contact_note
```

Passphrases and field values are requested interactively rather than passed as command-line arguments. Field values are hidden during entry. `get` prints the requested field to the terminal, so use it only in a private session.

For a test vault at a custom path, add `--file /path/to/test.vault` before the command.

## Backups

The vault file is encrypted, but its contents should still be treated as sensitive. Do not commit it to Git, attach it to issues, or upload it to shared/cloud backups. If making a backup, copy the encrypted vault to an offline location you control and protect the passphrase separately. Deleting a field creates a new encrypted vault; it does not securely erase old copies, snapshots, or backups.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_private_profile.py'
```

The tests require `cryptography`; tests are skipped when it is not installed. This module is an initial security-focused component and should receive review and device testing before being treated as a production password manager.
