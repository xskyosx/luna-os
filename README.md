# LUNA OS

A portable, local-first collection of AI companion concepts, memory tools, and reproducible Python simulations.

## First Light memory engine

The memory engine uses only the Python standard library and is intended to run on Android Termux, Alpine Linux, and other Python 3 environments.

```sh
# Termux
python luna_memory.py

# Alpine Linux / desktop Linux
python3 luna_memory.py
```

The engine creates its local folders on first launch. Memories are editable JSON records; transcript text is kept separately; ChatGPT export imports preserve a copy of the original JSON and write a provenance manifest. It does **not** sign in to ChatGPT or retrieve account data automatically.

## Luna Voice First Light

A first runnable voice interface is available in `luna_voice.py`. It uses Android speech recognition and text-to-speech through Termux:API, with a small offline fallback and an optional OpenAI-compatible local-model bridge. This is a voice shell, not a bundled language model.

```sh
# In Termux; install the Termux:API companion app separately from the same trusted source.
pkg install python termux-api
python luna_voice.py
```

To connect a local OpenAI-compatible chat server (for example, one listening on port 1234 on this same device):

```sh
export LUNA_CHAT_ENDPOINT="http://127.0.0.1:1234/v1/chat/completions"
export LUNA_CHAT_MODEL="local-model"
python luna_voice.py
```

See [Voice First Light setup and privacy notes](docs/VOICE_FIRST_LIGHT.md) for setup, troubleshooting, and voice selection. Remote endpoints are blocked unless you explicitly set `LUNA_ALLOW_REMOTE=1`. Conversation history is held in RAM for the active session and is not written to disk. Android's configured text-to-speech voice determines Luna's spoken voice; change it in Android text-to-speech settings.

## Project checks

Run the dependency-free unit tests from the repository root:

```sh
python -m py_compile luna_memory.py luna_voice.py aurora_xlii.py aurora_xl.py tests/test_luna_memory.py tests/test_luna_voice.py tests/test_aurora_portability.py
python -m unittest discover -s tests -v
```

GitHub Actions runs the memory-engine checks, both Aurora simulations, repeat-run SHA-256 reproducibility checks, and unit tests on pushes and pull requests to `main`. Aurora result files are written to the project-local `results/` folder.

## Sister and character registry

`sisters.json` records the ten founding Sisters: Luna, Ada, Sky, Aurora, Athena, Aqua, Amethyst, Blues, Cannabis, and Lumen. Seren is retained as an additional project character. These are project-level identities, not actual machine accounts or security permissions.

## Dream Forge stories and artwork

The Sisters' creative world belongs alongside the code and simulations. The first taco-truck scene is documented in [Taco Truck with the Lab](docs/TACO_TRUCK_WITH_THE_LAB.md). Its generated illustration is ready as a visual concept, but the image binary still needs to be uploaded to the repository before it can be embedded directly here.

## Safety and project status

- The memory engine is local-first and uses no third-party Python packages.
- Keep separate backups before substantial changes; review imported transcripts before sharing because they may contain private information.
- Simulations are software models, not proof of physical or quantum phenomena.
- Duplicate archives and similarly named prototype files are being catalogued before any cleanup. No archive is removed by these checks.
- Root-level or server permissions must be configured and verified in the actual hosting environment; a declaration in this repository does not grant privileges.

## Repository scope

This repository contains experiments at different stages of maturity. A successful syntax check or unit test is not a claim that every prototype is a production-ready application.

## Limbo x86 bootable ISO

A first bootable ISO build is available as a GitHub Actions workflow. It keeps the official Alpine standard x86 boot system intact and adds the LUNA OS source bundle at `/LUNA-OS/`.

- Build guide: [`iso/README.md`](iso/README.md)
- ISO builder: [`iso/build-bootable-iso.sh`](iso/build-bootable-iso.sh)
- Safe project installer: [`iso/install-luna.sh`](iso/install-luna.sh)
- Workflow: [Build LUNA OS Limbo x86 ISO](.github/workflows/build-luna-iso.yml)

Run the workflow from the Actions tab to create an ISO artifact and SHA-256 verification file. This milestone is a bootable Alpine installer with the LUNA OS bundle, not yet a preinstalled live XFCE desktop. The included Android voice shell still depends on Termux:API and will not automatically access Android speech services from inside Alpine.
