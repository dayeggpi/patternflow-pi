#!/usr/bin/env bash
# Update an existing LED Matrix install from this project folder.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${INSTALL_DIR:-/opt/led-matrix}"
SERVICE="${SERVICE:-led-matrix.service}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash update.sh" >&2
  exit 1
fi

if [ ! -f "$SCRIPT_DIR/main.py" ] || [ ! -f "$SCRIPT_DIR/led-matrix.service" ]; then
  echo "ERROR: run this from the project folder containing main.py and led-matrix.service" >&2
  exit 1
fi

echo "=== LED Matrix Updater ==="
echo "Source dir:  $SCRIPT_DIR"
echo "Install dir: $INSTALL_DIR"
echo ""

mkdir -p "$INSTALL_DIR"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude '.agents/' \
    --exclude '.codex/' \
    --exclude 'config.json' \
    --exclude '.spotify_token_cache' \
    "$SCRIPT_DIR"/ "$INSTALL_DIR"/
else
  echo "rsync not found; using cp fallback without deleting removed files."
  for f in api.py config.py main.py requirements.txt led-matrix.service wait-for-network.sh install.sh update.sh README.md spotify_preview.png; do
    if [ -f "$SCRIPT_DIR/$f" ]; then
      cp -a "$SCRIPT_DIR/$f" "$INSTALL_DIR/"
    fi
  done
  for d in modes static templates; do
    if [ -d "$SCRIPT_DIR/$d" ]; then
      cp -a "$SCRIPT_DIR/$d" "$INSTALL_DIR/"
    fi
  done
fi

find "$INSTALL_DIR" -maxdepth 1 -type f \( -name "*.sh" -o -name "*.service" \) -exec sed -i 's/\r$//' {} +
chmod +x "$INSTALL_DIR/wait-for-network.sh"
chmod +x "$INSTALL_DIR/update.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/install.sh" 2>/dev/null || true

install -m 644 "$INSTALL_DIR/led-matrix.service" /etc/systemd/system/led-matrix.service
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"

echo ""
echo "=== Updated and restarted ==="
systemctl status "$SERVICE" --no-pager -l
