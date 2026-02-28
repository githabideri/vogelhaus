#!/usr/bin/env bash
# vogelhaus-status.sh — K.u.K. Vogelhaus-Amt Statusbericht
#
# Sammelt Hardware-Daten von beiden Pis, macht Kamera-Fotos,
# gibt formatierten Bericht auf stdout aus.
#
# Konfiguration: Umgebungsvariablen oder .env-Datei
#   PI4_SSH     — SSH-Befehl für Pi 4 (default: "ssh vogl")
#   ZERO_SSH    — SSH-Befehl für Pi Zero (default: "ssh vogl-light")
#   PI4_SCP     — SCP-Prefix für Pi 4 (default: "vogl")
#   OUTPUT_DIR  — Verzeichnis für Fotos (default: "./media")
#   RTSP_CAM    — RTSP-URL Hauptkamera (default: "rtsp://127.0.0.1:8554/vogl-cam")
#   RTSP_NOIR   — RTSP-URL NoIR-Kamera (default: "rtsp://127.0.0.1:8554/vogl-noir")
#
# Aufruf: ./scripts/vogelhaus-status.sh [output_dir]

set -uo pipefail

# --- Konfiguration (Defaults, überschreibbar via env) ---
OUTPUT_DIR="${1:-${OUTPUT_DIR:-./media}}"
PI4_SSH="${PI4_SSH:-ssh vogl}"
ZERO_SSH="${ZERO_SSH:-ssh vogl-light}"
PI4_SCP="${PI4_SCP:-vogl}"
RTSP_CAM="${RTSP_CAM:-rtsp://127.0.0.1:8554/vogl-cam}"
RTSP_NOIR="${RTSP_NOIR:-rtsp://127.0.0.1:8554/vogl-noir}"

mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date -u +"%d. %B %Y, %H:%M UTC")
SNAP_PI4="$OUTPUT_DIR/snap_pi4.jpg"
SNAP_NOIR="$OUTPUT_DIR/snap_noir.jpg"

# Helper: get value from key=value data
get() { echo "$ALL_DATA" | grep "^$1=" | tail -1 | sed "s/^$1=//"; }

# --- FOTOS ---
echo "📸 Fotos aufnehmen..." >&2

PI4_FOTO="FEHLER"
$PI4_SSH "ffmpeg -y -rtsp_transport tcp -i $RTSP_CAM -frames:v 1 -q:v 2 /tmp/snap_pi4.jpg 2>/dev/null" && \
    scp -q "$PI4_SCP:/tmp/snap_pi4.jpg" "$SNAP_PI4" 2>/dev/null && PI4_FOTO="OK"

NOIR_FOTO="FEHLER"
$PI4_SSH "ffmpeg -y -rtsp_transport tcp -i $RTSP_NOIR -frames:v 1 -q:v 2 /tmp/snap_noir.jpg 2>/dev/null" && \
    scp -q "$PI4_SCP:/tmp/snap_noir.jpg" "$SNAP_NOIR" 2>/dev/null && NOIR_FOTO="OK"

echo "📊 Pi 4 Daten..." >&2

# --- PI4 DATEN ---
PI4_RAW=$($PI4_SSH bash << 'REMOTEOF'
TEMP=$(vcgencmd measure_temp | sed "s/temp=//;s/'C//")
echo "PI4_TEMP=$TEMP"
echo "PI4_UPTIME=$(uptime -p | sed 's/up //')"
echo "PI4_LOAD=$(awk '{printf "%s %s %s", $1, $2, $3}' /proc/loadavg)"
echo "SD_USED=$(df -h / | awk 'NR==2{print $3}')"
echo "SD_TOTAL=$(df -h / | awk 'NR==2{print $2}')"
echo "SD_PCT=$(df -h / | awk 'NR==2{print $5}')"
df -h /srv/ssd 2>/dev/null | awk 'NR==2{printf "SSD_USED=%s\nSSD_TOTAL=%s\nSSD_PCT=%s\n",$3,$2,$5}'
df -h /mnt/nas 2>/dev/null | awk 'NR==2{printf "NAS_USED=%s\nNAS_TOTAL=%s\nNAS_PCT=%s\nNAS_FREE=%s\n",$3,$2,$5,$4}'
echo "ETH0_STATE=$(cat /sys/class/net/eth0/operstate 2>/dev/null || echo down)"
echo "ETH0_IP=$(ip addr show eth0 2>/dev/null | awk '/inet /{print $2}' | head -1)"
echo "ETH0_SPEED=$(cat /sys/class/net/eth0/speed 2>/dev/null || echo '?')"
ESSID=$(iw dev wlan0 info 2>/dev/null | awk '/ssid/{print $2}' || echo "nicht_verbunden")
echo "WLAN0_ESSID=$ESSID"
SIGNAL=$(iw dev wlan0 station dump 2>/dev/null | awk '/signal:/{print $2; exit}' || echo "?")
echo "WLAN0_SIGNAL=$SIGNAL"
echo "TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo '?')"
echo "MEDIAMTX=$(systemctl is-active mediamtx 2>/dev/null)"
echo "NOIR_BRIDGE=$(systemctl is-active noir-bridge 2>/dev/null)"
echo "USB_SHARING=$(systemctl is-active usb-internet-sharing 2>/dev/null)"
pgrep -f 'twitch.tv' >/dev/null 2>&1 && echo "TWITCH=LIVE" || echo "TWITCH=OFFLINE"
echo "MIC_COUNT=$(arecord -l 2>/dev/null | grep -c card || echo 0)"
REMOTEOF
)

echo "📊 Pi Zero Daten..." >&2

# --- ZERO DATEN ---
ZERO_RAW=""
ZERO_OK="false"
ZERO_RAW=$($ZERO_SSH bash << 'REMOTEOF' 2>/dev/null
TEMP=$(vcgencmd measure_temp | sed "s/temp=//;s/'C//")
echo "ZERO_TEMP=$TEMP"
echo "ZERO_UPTIME=$(uptime -p | sed 's/up //')"
echo "ZERO_LOAD=$(awk '{printf "%s %s %s", $1, $2, $3}' /proc/loadavg)"
echo "ZERO_STREAM=$(systemctl is-active vogl-noir-stream.service 2>/dev/null)"
echo "ZERO_USB_IP=$(ip addr show usb0 2>/dev/null | awk '/inet /{print $2}' | head -1)"
echo "ZERO_SD_USED=$(df -h / | awk 'NR==2{print $3}')"
echo "ZERO_SD_TOTAL=$(df -h / | awk 'NR==2{print $2}')"
echo "ZERO_SD_PCT=$(df -h / | awk 'NR==2{print $5}')"
REMOTEOF
) && ZERO_OK="true"

ALL_DATA="$PI4_RAW
$ZERO_RAW"

# --- Read values ---
PI4_TEMP=$(get PI4_TEMP); PI4_UPTIME=$(get PI4_UPTIME); PI4_LOAD=$(get PI4_LOAD)
SD_USED=$(get SD_USED); SD_TOTAL=$(get SD_TOTAL); SD_PCT=$(get SD_PCT)
SSD_USED=$(get SSD_USED); SSD_TOTAL=$(get SSD_TOTAL); SSD_PCT=$(get SSD_PCT)
NAS_USED=$(get NAS_USED); NAS_TOTAL=$(get NAS_TOTAL); NAS_PCT=$(get NAS_PCT); NAS_FREE=$(get NAS_FREE)
ETH0_STATE=$(get ETH0_STATE); ETH0_IP=$(get ETH0_IP); ETH0_SPEED=$(get ETH0_SPEED)
WLAN0_ESSID=$(get WLAN0_ESSID); WLAN0_SIGNAL=$(get WLAN0_SIGNAL)
TAILSCALE_IP=$(get TAILSCALE_IP)
MEDIAMTX=$(get MEDIAMTX); NOIR_BRIDGE=$(get NOIR_BRIDGE)
TWITCH=$(get TWITCH); MIC_COUNT=$(get MIC_COUNT)
ZERO_TEMP=$(get ZERO_TEMP); ZERO_UPTIME=$(get ZERO_UPTIME)
ZERO_LOAD=$(get ZERO_LOAD); ZERO_STREAM=$(get ZERO_STREAM); ZERO_USB_IP=$(get ZERO_USB_IP)
ZERO_SD_USED=$(get ZERO_SD_USED); ZERO_SD_TOTAL=$(get ZERO_SD_TOTAL); ZERO_SD_PCT=$(get ZERO_SD_PCT)

# --- Emoji helpers ---
svc_e() { [ "$1" = "active" ] && echo "🟢" || echo "🔴"; }
temp_e() {
    local t="${1%%.*}"
    if [ -z "$t" ] || ! [ "$t" -eq "$t" ] 2>/dev/null; then echo "❓"; return; fi
    if [ "$t" -lt 60 ]; then echo "🟢"
    elif [ "$t" -lt 75 ]; then echo "🟡"
    else echo "🔴"; fi
}

# --- BERICHT ---
cat << REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 STATUSBERICHT — K.u.K. Vogelhaus-Amt
$TIMESTAMP
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐦 BETRIEB
• Twitch: $([ "$TWITCH" = "LIVE" ] && echo "🟢 LIVE" || echo "🔴 OFFLINE")
• Hauptkamera: $(svc_e "$MEDIAMTX") MediaMTX $MEDIAMTX
• Nachtsicht: $(svc_e "$NOIR_BRIDGE") noir-bridge $NOIR_BRIDGE
• Mikrofon: $([ "${MIC_COUNT:-0}" -gt 0 ] 2>/dev/null && echo "🟢 Aktiv" || echo "🔴 Nicht erkannt")
• IR-Beleuchtung: Automatisch (LDR)

📹 KAMERAS
• Hauptkamera (Pi 4): $PI4_FOTO
• Nachtsicht (Pi Zero): $NOIR_FOTO

🌡️ TEMPERATUREN
• Pi 4: $(temp_e "$PI4_TEMP") ${PI4_TEMP:-?}°C (Last: ${PI4_LOAD:-?})
• Pi Zero: $([ "$ZERO_OK" = "true" ] && echo "$(temp_e "$ZERO_TEMP") ${ZERO_TEMP:-?}°C (Last: ${ZERO_LOAD:-?})" || echo "🔴 Nicht erreichbar")

⏱️ BETRIEBSZEIT
• Pi 4: ${PI4_UPTIME:-?}
• Pi Zero: $([ "$ZERO_OK" = "true" ] && echo "${ZERO_UPTIME:-?}" || echo "nicht erreichbar")

💾 SPEICHER
• SD-Karte Pi 4: ${SD_USED:-?} / ${SD_TOTAL:-?} (${SD_PCT:-?})
• SD-Karte Zero: $([ "$ZERO_OK" = "true" ] && echo "${ZERO_SD_USED:-?} / ${ZERO_SD_TOTAL:-?} (${ZERO_SD_PCT:-?})" || echo "nicht erreichbar")
• SSD: ${SSD_USED:-?} / ${SSD_TOTAL:-?} (${SSD_PCT:-?})
• NAS: ${NAS_USED:-?} / ${NAS_TOTAL:-?} (${NAS_PCT:-?}) — ${NAS_FREE:-?} frei

🌐 NETZWERK
• LAN: $([ "$ETH0_STATE" = "up" ] && echo "🟢 ($ETH0_IP, ${ETH0_SPEED} Mbps)" || echo "🔴 Nicht angeschlossen")
• WLAN: $([ -n "$WLAN0_ESSID" ] && [ "$WLAN0_ESSID" != "nicht_verbunden" ] && echo "🟢 $WLAN0_ESSID ($WLAN0_SIGNAL dBm)" || echo "⚪ Nicht verbunden")
• Tailscale: 🟢 $TAILSCALE_IP
• Zero USB: $([ "$ZERO_OK" = "true" ] && echo "🟢 $ZERO_USB_IP" || echo "🔴 Nicht verbunden")

━━━━━━━━━━━━━━━━━━━━━━━━━━━
REPORT

echo ""
echo "FOTOS:"
[ -f "$SNAP_PI4" ] && echo "PI4=$SNAP_PI4"
[ -f "$SNAP_NOIR" ] && echo "NOIR=$SNAP_NOIR"

echo "✅ Bericht fertig." >&2
