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

ROOT_INDEX_URL="https://dl-cdn.alpinelinux.org/alpine/"
ROOT_INDEX="$BASE_DIR/root-index.html"
curl --fail --location --silent --show-error "$ROOT_INDEX_URL" -o "$ROOT_INDEX"

VERSION_DIR=$(python3 - "$ROOT_INDEX" <<'PY'
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
            match = re.search(r"(?:^|/)v([0-9]+)\.([0-9]+)/?$", href)
            if match:
                self.items.append(f"v{match.group(1)}.{match.group(2)}/")

parser = Links()
parser.feed(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))
if not parser.items:
    raise SystemExit("Could not find a stable version directory in the Alpine index.")
def version(name):
    return tuple(int(part) for part in re.fullmatch(r"v([0-9]+)\.([0-9]+)/", name).groups())
print(sorted(set(parser.items), key=version)[-1])
PY
)

INDEX_URL="${ROOT_INDEX_URL}${VERSION_DIR}releases/x86/"
INDEX="$BASE_DIR/index.html"
echo "Fetching Alpine release index: $INDEX_URL"
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
            name = href.rsplit("/", 1)[-1]
            if re.fullmatch(r"alpine-standard-[0-9.]+-x86\.iso", name):
                self.items.append(name)

parser = Links()
parser.feed(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))
if not parser.items:
    raise SystemExit("Could not find an Alpine standard x86 ISO in the release index.")
def version(name):
    return tuple(int(part) for part in re.search(r"standard-([0-9.]+)-x86", name).group(1).split("."))
print(sorted(set(parser.items), key=version)[-1])
PY
)

echo "Selected Alpine ISO: $ISO_NAME"
BASE_ISO="$BASE_DIR/$ISO_NAME"
CHECKSUM_FILE="$BASE_DIR/$ISO_NAME.sha256"
curl --fail --location --silent --show-error "$INDEX_URL$ISO_NAME" -o "$BASE_ISO"
# Alpine publishes a checksum beside each ISO; there is no sha256sums.txt
# in the release directory.
curl --fail --location --silent --show-error "$INDEX_URL$ISO_NAME.sha256" -o "$CHECKSUM_FILE"

(
  cd "$BASE_DIR"
  # Normalize the checksum file's target to the locally downloaded filename.
  EXPECTED_SHA=$(awk 'NR == 1 {print $1}' "$ISO_NAME.sha256")
  test "${#EXPECTED_SHA}" -eq 64
  printf '%s  %s\n' "$EXPECTED_SHA" "$ISO_NAME" > "$ISO_NAME.verify"
  sha256sum -c "$ISO_NAME.verify"
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
