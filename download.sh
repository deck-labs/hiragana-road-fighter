#!/usr/bin/env bash
# ==============================================================================
# Quick Download & Launch Shortcut for Hiragana Road Fighter AppImage
# Usage:
#   curl -sSL https://raw.githubusercontent.com/deck-labs/hiragana-road-fighter/main/download.sh | bash
# ==============================================================================
set -e

APPIMAGE="Hiragana_Road_Fighter-x86_64.AppImage"
URL="https://github.com/deck-labs/hiragana-road-fighter/releases/latest/download/${APPIMAGE}"

echo "=== Downloading Hiragana Road Fighter AppImage ==="
curl -L --progress-bar -o "${APPIMAGE}" "${URL}"
chmod +x "${APPIMAGE}"

echo "=== Download complete! ==="
echo "AppImage saved to: $(pwd)/${APPIMAGE}"
echo "To run the game anytime: ./${APPIMAGE}"

if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    echo "Launching game..."
    exec ./"${APPIMAGE}" "$@"
fi
