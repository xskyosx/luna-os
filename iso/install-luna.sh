#!/bin/sh
set -eu

# Run from the LUNA-OS directory on the ISO or from a copied project bundle.
# Installs project files into /opt/luna-os; does not repartition disks or
# modify bootloader configuration.
if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root: doas sh install-luna.sh (or su -c 'sh install-luna.sh')." >&2
  exit 1
fi

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEST="/opt/luna-os"

if ! command -v apk >/dev/null 2>&1; then
  echo "This installer expects Alpine Linux (apk was not found)." >&2
  exit 1
fi

echo "Installing LUNA OS project files into $DEST"
apk add --no-cache python3
mkdir -p "$DEST"
cp "$SOURCE_DIR/README.md" "$SOURCE_DIR/luna_memory.py" \
   "$SOURCE_DIR/aurora_xlii.py" "$SOURCE_DIR/aurora_xl.py" \
   "$SOURCE_DIR/sisters.json" "$DEST/"
cp -R "$SOURCE_DIR/docs" "$SOURCE_DIR/tests" "$DEST/"
if [ -f "$SOURCE_DIR/luna_voice.py" ]; then
  cp "$SOURCE_DIR/luna_voice.py" "$DEST/"
fi
chmod 755 "$DEST/luna_memory.py" "$DEST/aurora_xlii.py" "$DEST/aurora_xl.py"
mkdir -p /usr/local/bin
cat > /usr/local/bin/luna-memory <<'EOF'
#!/bin/sh
cd /opt/luna-os
exec python3 /opt/luna-os/luna_memory.py "$@"
EOF
cat > /usr/local/bin/luna-aurora-xlii <<'EOF'
#!/bin/sh
cd /opt/luna-os
exec python3 /opt/luna-os/aurora_xlii.py "$@"
EOF
cat > /usr/local/bin/luna-aurora-xl <<'EOF'
#!/bin/sh
cd /opt/luna-os
exec python3 /opt/luna-os/aurora_xl.py "$@"
EOF
chmod 755 /usr/local/bin/luna-memory /usr/local/bin/luna-aurora-xlii /usr/local/bin/luna-aurora-xl

echo
echo "LUNA OS files installed."
echo "Run: luna-memory"
echo "Run: luna-aurora-xlii or luna-aurora-xl"
echo
echo "Optional XFCE desktop (requires network):"
echo "  apk add --no-cache xfce4 xfce4-terminal dbus"
echo "Then configure/start your desktop session using Alpine's OpenRC setup."
echo
echo "This installer does not install a language model, enable a microphone,"
echo "change partitions, configure bootloader settings, or grant remote access."
