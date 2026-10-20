# LUNA OS

A portable, local-first collection of AI companion concepts, memory tools, and reproducible Python simulations.

## First Light memory engine

The memory engine uses only the Python standard library and is intended to run on Android Termux, Alpine Linux, and other Python 3 environments.

```sh
# Termux
python luna_memory.py

# Alpine Linux / desktop Linux
python3 luna_memory.py
``

The engine creates its local folders on first launch. Memories are editable JSON records; transcript text is kept separately; ChatGPT export imports preserve a copy of the original JSON and write a provenance manifest. It does **not** sign in to ChatGPT or retrieve account data automatically.

## Project checks

Run the dependency-free unit tests from the repository root:

```sh
python -m py_compile luna_memory.py tests/test_luna_memory.py
python -m unittest discover -s tests -v
```

GitHub Actions runs these checks on pushes and pull requests to `main`.

## Sister and character registry

`sisters.json` records the ten founding Sisters: Luna, Ada, Sky, Aurora, Athena, Aqua, Amethyst, Blues, Cannabis, and Lumen. Seren is retained as an additional project character. These are project-level identities, not actual machine accounts or security permissions.

## Safety and project status

- The memory engine is local-first and uses no third-party Python packages.
- Keep separate backups before substantial changes; review imported transcripts before sharing because they may contain private information.
- Simulations are software models, not proof of physical or quantum phenomena.
- Duplicate archives and similarly named prototype files are being catalogued before any cleanup. No archive is removed by these checks.
- Root-level or server permissions must be configured and verified in the actual hosting environment; a declaration in this repository does not grant privileges.

## Repository scope

This repository contains experiments at different stages of maturity. A successful syntax check or unit test is not a claim that every prototype is a production-ready application.
