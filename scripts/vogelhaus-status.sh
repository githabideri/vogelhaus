#!/usr/bin/env bash
# vogelhaus-status.sh — K.u.K. Vogelhaus-Amt Statusbericht
# Sammelt Daten von beiden Pis, macht Fotos, gibt formatierten Bericht aus.
# Ausgabe: Bericht auf stdout, Bilder in $OUTPUT_DIR
#
# Aufruf: ./scripts/vogelhaus-status.sh [output_dir]

set -uo pipefail

OUTPUT_DIR="${1:-./media}"
mkdir -p "$OUTPUT_DIR"

PI4_SSH="ssh -o ConnectTimeout=8 vogl"
ZERO_SSH="ssh -o ConnectTimeout=8 -i $HOME/.ssh/id_ed25519_vogl vb-light@<TAILSCALE_ZERO>"

TIMESTAMP=$(date -u +"%d. %B %Y, %H:%M UTC")
SNAP_PI4="$OUTPUT_DIR/snap_pi4.jpg"
SNAP_NOIR="$OUTPUT_DIR/snap_noir.jpg"

# Helper: get value from key=value data (handles spaces in values)
get() { echo "$ALL_DATA" | grep "^$1=" | tail -1 | sed "s/^$1=//"; }

# --- FOTOS ---
echo "📸 Fotos aufnehmen..." >&2

PI4_FOTO="FEHLER"
$PI4_SSH "ffmpeg -y -rtsp_transport tcp -i rtsp://127.0.0.1:8554/vogl-cam -frames:v 1 -q:v 2 /tmp/snap_pi4.jpg 2>/dev/null" && \
    scp -q vogl:/tmp/snap_pi4.jpg "$SNAP_PI4" 2>/dev/null && PI4_FOTO="OK"

NOIR_FOTO="FEHLER"
$PI4_SSH "ffmpeg -y -rtsp_transport tcp -i rtsp://127.0.0.1:8554/vogl-noir -frames:v 1 -q:v 2 /tmp/snap_noir.jpg 2>/dev/null" && \
    scp -q vogl:/tmp/snap_noir.jpg "$SNAP_NOIR" 2>/dev/null && NOIR_FOTO="OK"

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
echo "ETH0_SPEED=$(cat /sys/class/net/eth0/speed 2>/dev/null || echo ?)"
ESSID=$(/sbin/iwconfig wlan0 2>/dev/null | grep -oP 'ESSID:"\K[^"]+' || echo "nicht_verbunden")
echo "WLAN0_ESSID=$ESSID"
echo "WLAN0_SIGNAL=$(/sbin/iwconfig wlan0 2>/dev/null | grep -oP 'Signal level=\K[^ ]+' || echo ?)"
echo "TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo ?)"
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

# --- UART CHECK ---
echo "📊 UART prüfen..." >&2
UART_STATUS="❓ Nicht geprüft"
UART_RAW=$($PI4_SSH "test -c /dev/ttyAMA0 && echo 'DEV_OK' || echo 'NO_DEV'; echo '' > /dev/ttyAMA0 2>/dev/null; timeout 2 head -c 200 /dev/ttyAMA0 2>/dev/null; echo 'UART_DONE'" 2>/dev/null)
if echo "$UART_RAW" | grep -q "NO_DEV"; then
    UART_STATUS="🔴 /dev/ttyAMA0 nicht verfügbar"
elif echo "$UART_RAW" | grep -qi "login\|voglberry-light\|Linux"; then
    UART_STATUS="🟢 Aktiv (Login-Prompt empfangen)"
elif echo "$UART_RAW" | grep -q "DEV_OK"; then
    UART_STATUS="🟡 Gerät vorhanden, keine Daten empfangen"
else
    UART_STATUS="🔴 Nicht erreichbar"
fi

ALL_DATA="$PI4_RAW
$ZERO_RAW"

# --- Read values ---
PI4_TEMP=$(get PI4_TEMP)
PI4_UPTIME=$(get PI4_UPTIME)
PI4_LOAD=$(get PI4_LOAD)
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
Standort „Thomas" | $TIMESTAMP
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐦 VOGELHAUS-BETRIEB
• Twitch-Stream: $([ "$TWITCH" = "LIVE" ] && echo "🟢 LIVE" || echo "🔴 OFFLINE") auf twitch.tv/<YOUR_TWITCH_CHANNEL>
• Hauptkamera: $(svc_e "$MEDIAMTX") MediaMTX $MEDIAMTX
• Nachtsicht-Stream: $(svc_e "$NOIR_BRIDGE") noir-bridge $NOIR_BRIDGE
• Mikrofon: $([ "${MIC_COUNT:-0}" -gt 0 ] 2>/dev/null && echo "🟢 Aktiv" || echo "🔴 Nicht erkannt")
• IR-Beleuchtung: Automatisch (LDR-gesteuert)

📹 KAMERAS
• Hauptkamera (Pi 4): Foto $PI4_FOTO
• Nachtsicht (Pi Zero): Foto $NOIR_FOTO

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
• NAS (Synology): ${NAS_USED:-?} / ${NAS_TOTAL:-?} (${NAS_PCT:-?}) — ${NAS_FREE:-?} frei

🌐 NETZWERK
• LAN: $([ "$ETH0_STATE" = "up" ] && echo "🟢 Verbunden ($ETH0_IP, ${ETH0_SPEED} Mbps)" || echo "🔴 Nicht angeschlossen")
• WLAN: $([ -n "$WLAN0_ESSID" ] && [ "$WLAN0_ESSID" != "nicht_verbunden" ] && echo "🟢 $WLAN0_ESSID (Signal: $WLAN0_SIGNAL dBm)" || echo "⚪ Nicht verbunden")
• Tailscale: 🟢 $TAILSCALE_IP
• Pi Zero USB: $([ "$ZERO_OK" = "true" ] && echo "🟢 $ZERO_USB_IP" || echo "🔴 Nicht verbunden")

🔌 UART-SCHMALSPURBAHN
• Pi4 ↔ Zero: $UART_STATUS

━━━━━━━━━━━━━━━━━━━━━━━━━━━

FOTOS:
$([ -f "$SNAP_PI4" ] && echo "PI4=$SNAP_PI4")
$([ -f "$SNAP_NOIR" ] && echo "NOIR=$SNAP_NOIR")
REPORT

echo "✅ Bericht fertig." >&2
