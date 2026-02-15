#!/bin/bash
# capture.sh — Take a photo from the connected camera
# Works on both Pi 4 (libcamera) and Pi Zero (rpicam)

set -euo pipefail

OUTPUT="${1:-/tmp/capture_$(date +%Y%m%d_%H%M%S).jpg}"
WIDTH="${2:-1296}"
HEIGHT="${3:-972}"
TIMEOUT="${4:-2000}"

# Detect which camera tool is available
if command -v rpicam-still &>/dev/null; then
    CAM_CMD="rpicam-still"
elif command -v libcamera-still &>/dev/null; then
    CAM_CMD="libcamera-still"
else
    echo "Error: No camera tool found (rpicam-still or libcamera-still)" >&2
    exit 1
fi

echo "Using $CAM_CMD — capturing ${WIDTH}x${HEIGHT} → $OUTPUT"
$CAM_CMD -o "$OUTPUT" --width "$WIDTH" --height "$HEIGHT" -t "$TIMEOUT" 2>&1

if [ -f "$OUTPUT" ]; then
    SIZE=$(stat -c%s "$OUTPUT")
    echo "✓ Captured: $OUTPUT ($SIZE bytes)"
else
    echo "✗ Capture failed" >&2
    exit 1
fi
