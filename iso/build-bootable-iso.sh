#!/bin/sh
set -eu

# Build a bootable Alpine x86 installer ISO with the LUNA OS project bundle.
# Requires: curl, xorriso, python3, sha256sum, coreutils.
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BUILD_DIR="${LUNA_BUILD_DIR:-$ROOT/build}"
STAGE="$BUILD_DIR/stage"
BASE_DIR="$BUILD_DIR/base"
OUT_DIR="$BUILD_DIR/out"
mkdir -p "$BASE_DIR" "$STAGE" "$OUT_DIR"

INDEX_URL="https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/x86/"
INDEX="$BASE_DIR/index.html"
curl --fail --location --silent --show-error "$INDEX_URL" -o "$INDEX"

ISO_NAME=$(python3 - "$INDEX" <<'PY'
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if re.fullmatch(r"alpine-standard-[0-9.]+-x86\.iso", href):
                self.items.append(href)

parser = Links()
parser.feed(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))
if not parser.items:
    raise SystemExit("Could not find an Alpine standard x86 ISO in the latest-stable index.")
def version(name):
    return tuple(int(part) for part in re.search(r"standard-([0-9.]+)-x86", name).group(1).split("."))
print(sorted(set(parser.items), key=version)[-1])
PY
)

BASE_ISO="$BASE_DIR/$ISO_NAME"
CHECKSUMS="$BASE_DIR/sha256sums.txt"
curl --fail --location --silent --show-error "$INDEX_URL$ISO_NAME" -o "$BASE_ISO"
curl --fail --location --silent --show-error "$INDEX_URL"sha256sums.txt -o "$CHECKSUMS"

(
  cd "$BASE_DIR"
  grep -E "[[:space:]]$ISO_NAME$" "$CHECKSUMS" > "$ISO_NAME.sha256"
  test -s "$ISO_NAME.sha256"
  sha256sum -c "$ISO_NAME.sha256"
)

# Stage only the source, docs, tests, and installer needed on the target system.
rm -rf "$STAGE/LUNA-OS"
mkdir -p "$STAGE/LUNA-OS"
cp "$ROOT/README.md" "$ROOT/luna_memory.py" "$ROOT/luna_voice.py" \
   "$ROOT/aurora_xlii.py" "$ROOT/aurora_xl.py" "$ROOT/sisters.json" "$STAGE/LUNA-OS/"
cp -R "$ROOT/docs" "$ROOT/tests" "$STAGE/LUNA-OS/"
cp "$ROOT/iso/install-luna.sh" "$ROOT/iso/README.md" "$STAGE/LUNA-OS/"

OUTPUT="$OUT_DIR/LUNA-OS-Alpine-i386.iso"
rm -f "$OUTPUT"

# Replay the original ISO's BIOS/El Torito boot configuration and add a
# clearly separated project payload directory. This keeps Alpine's own
# bootloader and kernel intact rather than attempting to replace them.
xorriso -abort_on FAILURE \
  -indev "$BASE_ISO" \
  -outdev "$OUTPUT" \
  -boot_image any replay \
  -map "$STAGE/LUNA-OS" /LUNA-OS

test -s "$OUTPUT"
xorriso -indev "$OUTPUT" -report_el_torito as_mkisofs 2>&1 | tee "$OUT_DIR/boot-report.txt"
grep -qi "eltorito" "$OUT_DIR/boot-report.txt" || {
  echo "ERROR: no El Torito boot information found in the generated ISO." >&2
  exit 1
}
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
printf '\nBuilt ISO: %s\n' "$OUTPUT"
printf 'Alpine source: %s\n' "$ISO_NAME"
printf 'SHA-256: '
sha256sum "$OUTPUT" | awk '{print $1}'
