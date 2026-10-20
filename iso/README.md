# LUNA OS — Limbo x86 bootable ISO

This first ISO milestone keeps Alpine's own bootloader and kernel and adds a
`/LUNA-OS/` directory to the ISO containing the project code, docs, and tests.
It is a **bootable Alpine installer ISO with the LUNA OS bundle**, not yet a
custom live desktop and not an Android APK.

## Build it with GitHub Actions

1. Open the repository's **Actions** tab.
2. Select **Build LUNA OS Limbo x86 ISO**.
3. Choose **Run workflow** on the ISO feature branch.
4. Download the `luna-os-limbo-x86-iso` artifact from the completed run.
5. Verify the ISO using the included `.sha256` file.

The workflow downloads the latest-stable Alpine standard x86 ISO, verifies it
against Alpine's published SHA-256 manifest, and uses xorriso to replay the
original El Torito boot configuration while adding `/LUNA-OS/`.

## Build locally on Linux

Install `curl`, `python3`, `xorriso`, and `coreutils`, then run:

```sh
sh iso/build-bootable-iso.sh
```

The output is `build/out/LUNA-OS-Alpine-i386.iso`. The script verifies the
upstream checksum and writes a local SHA-256 file and boot report.

## Boot in Limbo on Android

- Create a new virtual machine with **Architecture: x86 (32-bit)**.
- Use **PC / i386** machine type if offered and **BIOS** boot.
- Attach the downloaded ISO as the CD-ROM image.
- Start with conservative RAM (512–1024 MB if available) and a small virtual
  disk; the ISO boots independently of the virtual disk.
- Boot the Alpine installer and follow its prompts. The ISO's project bundle
  is available at `/LUNA-OS/` on the boot media after mounting it in the
  running environment.

To install the project tools after Alpine is installed, copy the `LUNA-OS`
directory from the media into the guest, enter that directory, and run:

```sh
doas sh install-luna.sh
```

Use `su -c 'sh install-luna.sh'` instead if `doas` is not configured.
The installer adds Python 3 and project files under `/opt/luna-os`; it does
not repartition disks, alter the bootloader, or install a language model.

## Current limitations

- This is a first bootable installer milestone, not a preinstalled live XFCE
  image. The guest's disk installation and XFCE setup are separate steps.
- The included voice shell relies on Termux:API and is intended for Android
  Termux, so Android speech recognition/TTS will not work inside Alpine
  automatically.
- A conversational model is not bundled. A local model server can be added
  later after hardware and memory requirements are tested.
- The build uses the latest-stable Alpine ISO at build time; record the
  workflow log and SHA-256 alongside each artifact for provenance.
- Never run unreviewed root scripts. Read `install-luna.sh` before running it.
