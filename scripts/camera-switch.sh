#!/usr/bin/env bash
# camera-switch.sh — Switch Restreamer ingest source between cameras
# Usage: camera-switch.sh [pi4|noir]
# Exit codes: 0=OK, 1=Error, 2=Already active

set -euo pipefail

# ============================================================
# CONFIG (override via environment or .env)
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

# Load .env if exists
if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a
fi

RESTREAMER_HOST="${RESTREAMER_HOST:-localhost}"
RESTREAMER_PORT="${RESTREAMER_PORT:-8554}"
RESTREAMER_DOCKER="${RESTREAMER_DOCKER:-restreamer}"
LOG_DIR="${LOG_DIR:-/var/log/vogelhaus}"
LOG_FILE="${LOG_FILE:-$LOG_DIR/camera-switch.log}"

PI4_STREAM="${PI4_STREAM:-rtsp://172.20.0.1:8554/vogl-cam}"
NOIR_STREAM="${NOIR_STREAM:-rtsp://172.20.0.1:8554/vogl-noir}"

# ============================================================
# LOGGING
# ============================================================

log() {
    local timestamp
    timestamp=$(TZ="${TZ:-UTC}" date "+%Y-%m-%d %H:%M:%S %Z")
    echo "[$timestamp] $*" | tee -a "$LOG_FILE" >&2
}

# ============================================================
# MAIN
# ============================================================

# Ensure log dir
mkdir -p "$LOG_DIR"

# Parse arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 [pi4|noir]" >&2
    exit 1
fi

TARGET="$1"

case "$TARGET" in
    pi4|main|day)
        TARGET_STREAM="$PI4_STREAM"
        TARGET_NAME="pi4"
        ;;
    noir|night|ir)
        TARGET_STREAM="$NOIR_STREAM"
        TARGET_NAME="noir"
        ;;
    *)
        echo "ERROR: Invalid target '$TARGET'. Use 'pi4' or 'noir'." >&2
        exit 1
        ;;
esac

log "=== Camera Switch Request: $TARGET_NAME ==="

# Get current ingest source
CURRENT=$(docker exec "$RESTREAMER_DOCKER" cat /core/config/db.json 2>/dev/null | \
    grep -oP 'rtsp://[^"]+' | head -1 || echo "unknown")

log "Current source: $CURRENT"

# Check if already active
if echo "$CURRENT" | grep -q "$(basename "$TARGET_STREAM")"; then
    log "Target '$TARGET_NAME' already active, no change needed."
    exit 2
fi

# Perform switch
log "Switching to: $TARGET_STREAM"

docker exec "$RESTREAMER_DOCKER" sed -i \
    "s|rtsp://[^\"]*|${TARGET_STREAM}|g" \
    /core/config/db.json

if [ $? -ne 0 ]; then
    log "ERROR: Failed to update db.json"
    exit 1
fi

# Restart Restreamer
log "Restarting Restreamer..."
docker restart "$RESTREAMER_DOCKER" >/dev/null 2>&1

if [ $? -ne 0 ]; then
    log "ERROR: Failed to restart Restreamer"
    exit 1
fi

# Wait for restart
sleep 5

# Verify
VERIFY=$(docker exec "$RESTREAMER_DOCKER" ps aux 2>/dev/null | \
    grep ffmpeg | grep -o "vogl-[a-z]*" | head -1 || echo "unknown")

if echo "$VERIFY" | grep -q "$TARGET_NAME"; then
    log "✅ Switch successful: $TARGET_NAME is now active"
    exit 0
else
    log "⚠️  Switch completed but verification unclear (found: $VERIFY)"
    exit 0
fi
