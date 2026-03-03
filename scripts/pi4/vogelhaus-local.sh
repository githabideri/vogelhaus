#!/usr/bin/env bash
# vogelhaus-local.sh — Status direkt auf dem Pi 4 ausführen
# Kein SSH nötig — alles lokal + Zero via USB/Tailscale
#
# Aufruf: ~/scripts/vogelhaus-local.sh [bb|o]
# bb = Blitz-Bericht (5 Zeilen)
# o  = Offizieller Bericht (voll, Default)

set -uo pipefail

MODE="${1:-o}"
SNAP_DIR="/tmp/vogelhaus-status"
mkdir -p "$SNAP_DIR"

ZERO_SSH="ssh -o ConnectTimeout=5 -o BatchMode=yes vb-light@10.42.0.2"
ZERO_TS="ssh -o ConnectTimeout=5 -o BatchMode=yes -i ~/.ssh/id_ed25519 vb-light@100.108.95.56"

TIMESTAMP=$(date +"%d.%m.%Y %H:%M CET")
DATE_SHORT=$(date +"%d.%m. %H:%M")

# ---- PI4 LOCAL DATA ----
PI4_TEMP=$(vcgencmd measure_temp | sed 's/temp=//;s/'"'"'C//')
PI4_UPTIME=$(uptime -p | sed 's/up //')
PI4_LOAD=$(awk '{printf "%s %s %s", $1, $2, $3}' /proc/loadavg)
SD_INFO=$(df -h / | awk 'NR==2{printf "%s/%s (%s)",$3,$2,$5}')
SSD_INFO=$(df -h /srv/ssd 2>/dev/null | awk 'NR==2{printf "%s/%s (%s)",$3,$2,$5}')
NAS_INFO=$(df -h /mnt/nas 2>/dev/null | awk 'NR==2{printf "%s/%s (%s) — %s frei",$3,$2,$5,$4}')
MEDIAMTX=$(systemctl is-active mediamtx 2>/dev/null)
NOIR_BRIDGE=$(systemctl is-active noir-bridge 2>/dev/null)
pgrep -f 'twitch.tv' >/dev/null 2>&1 && TWITCH="LIVE" || TWITCH="OFFLINE"
MIC_COUNT=$(arecord -l 2>/dev/null | grep -c card || echo 0)

# Network
ETH0_STATE=$(cat /sys/class/net/eth0/operstate 2>/dev/null || echo down)
ETH0_IP=$(ip addr show eth0 2>/dev/null | awk '/inet /{print $2}' | head -1)
ESSID=$(iwconfig wlan0 2>/dev/null | grep -oP 'ESSID:"\K[^"]+' || echo "—")
SIGNAL=$(iwconfig wlan0 2>/dev/null | grep -oP 'Signal level=\K[^ ]+' || echo "?")
TS_IP=$(tailscale ip -4 2>/dev/null || echo "?")

# ---- FOTOS ----
PI4_FOTO="FAIL"
ffmpeg -y -rtsp_transport tcp -i rtsp://127.0.0.1:8554/vogl-cam -frames:v 1 -q:v 2 "$SNAP_DIR/snap_pi4.jpg" 2>/dev/null && PI4_FOTO="OK"

NOIR_FOTO="FAIL"
ffmpeg -y -rtsp_transport tcp -i rtsp://127.0.0.1:8554/vogl-noir -frames:v 1 -q:v 2 "$SNAP_DIR/snap_noir.jpg" 2>/dev/null && NOIR_FOTO="OK"

# ---- ZERO DATA ----
ZERO_OK="false"
ZERO_RAW=""
# Try USB first, then Tailscale
ZERO_RAW=$($ZERO_SSH bash -s 2>/dev/null << 'ZEOF'
echo "ZERO_TEMP=$(vcgencmd measure_temp | sed "s/temp=//;s/'C//")"
echo "ZERO_UPTIME=$(uptime -p | sed 's/up //')"
echo "ZERO_LOAD=$(awk '{printf "%s %s %s", $1, $2, $3}' /proc/loadavg)"
echo "ZERO_STREAM=$(systemctl is-active vogl-noir-stream.service 2>/dev/null)"
echo "ZERO_USB_IP=$(ip addr show usb0 2>/dev/null | awk '/inet /{print $2}' | head -1)"
echo "ZERO_SD=$(df -h / | awk 'NR==2{printf "%s/%s (%s)",$3,$2,$5}')"
ZEOF
) && ZERO_OK="true"

if [ "$ZERO_OK" != "true" ]; then
    ZERO_RAW=$($ZERO_TS bash -s 2>/dev/null << 'ZEOF'
echo "ZERO_TEMP=$(vcgencmd measure_temp | sed "s/temp=//;s/'C//")"
echo "ZERO_UPTIME=$(uptime -p | sed 's/up //')"
echo "ZERO_LOAD=$(awk '{printf "%s %s %s", $1, $2, $3}' /proc/loadavg)"
echo "ZERO_STREAM=$(systemctl is-active vogl-noir-stream.service 2>/dev/null)"
echo "ZERO_USB_IP=$(ip addr show usb0 2>/dev/null | awk '/inet /{print $2}' | head -1)"
echo "ZERO_SD=$(df -h / | awk 'NR==2{printf "%s/%s (%s)",$3,$2,$5}')"
ZEOF
    ) && ZERO_OK="true"
fi

# Parse zero data
zget() { echo "$ZERO_RAW" | grep "^$1=" | tail -1 | sed "s/^$1=//"; }
ZERO_TEMP=$(zget ZERO_TEMP)
ZERO_UPTIME=$(zget ZERO_UPTIME)
ZERO_LOAD=$(zget ZERO_LOAD)
ZERO_STREAM=$(zget ZERO_STREAM)
ZERO_USB_IP=$(zget ZERO_USB_IP)
ZERO_SD=$(zget ZERO_SD)

# ---- UART CHECK ----
UART_STATUS="?"
if [ -c /dev/ttyAMA0 ]; then
    echo "" > /dev/ttyAMA0 2>/dev/null
    UART_DATA=$(timeout 2 head -c 200 /dev/ttyAMA0 2>/dev/null || true)
    if echo "$UART_DATA" | grep -qi "login\|voglberry-light\|Linux"; then
        UART_STATUS="🟢 Aktiv"
    else
        UART_STATUS="🟡 Gerät da, keine Daten"
    fi
else
    UART_STATUS="🔴 Nicht verfügbar"
fi

# ---- EMOJI HELPERS ----
svc_e() { [ "$1" = "active" ] && echo "🟢" || echo "🔴"; }
temp_e() {
    local t="${1%%.*}"
    [ -z "$t" ] && { echo "❓"; return; }
    [ "$t" -lt 60 ] 2>/dev/null && echo "🟢" && return
    [ "$t" -lt 75 ] 2>/dev/null && echo "🟡" && return
    echo "🔴"
}

# ========== OUTPUT ==========

if [ "$MODE" = "bb" ]; then
    # ---- BLITZ-BERICHT ----
    echo "🐦 BB — $DATE_SHORT"
    echo "Pi4: $(temp_e "$PI4_TEMP") ${PI4_TEMP}°C Load:${PI4_LOAD} | Zero: $([ "$ZERO_OK" = "true" ] && echo "$(temp_e "$ZERO_TEMP") ${ZERO_TEMP}°C Load:${ZERO_LOAD}" || echo "🔴 offline")"
    echo "💾 SSD $SSD_INFO | NAS $NAS_INFO"
    echo "🎥 Twitch: $TWITCH | $(svc_e "$MEDIAMTX") MTX $(svc_e "$NOIR_BRIDGE") NoIR"
    echo "📡 WLAN $ESSID ($SIGNAL dBm) | TS $TS_IP | UART $UART_STATUS"
    echo ""
    [ "$PI4_FOTO" = "OK" ] && echo "📸 Pi4: $SNAP_DIR/snap_pi4.jpg"
    [ "$NOIR_FOTO" = "OK" ] && echo "📸 NoIR: $SNAP_DIR/snap_noir.jpg"
else
    # ---- OFFIZIELLER BERICHT ----
    cat << REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 STATUSBERICHT — K.u.K. Vogelhaus-Amt
Standort „Thomas" | $TIMESTAMP
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐦 VOGELHAUS-BETRIEB
• Twitch-Stream: $([ "$TWITCH" = "LIVE" ] && echo "🟢 LIVE" || echo "🔴 OFFLINE") auf twitch.tv/meisen_aus_urfahr
• Hauptkamera: $(svc_e "$MEDIAMTX") MediaMTX $MEDIAMTX
• Nachtsicht-Bridge: $(svc_e "$NOIR_BRIDGE") noir-bridge $NOIR_BRIDGE
• Mikrofon: $([ "$MIC_COUNT" -gt 0 ] 2>/dev/null && echo "🟢 Aktiv" || echo "🔴 Nicht erkannt")
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
• SD-Karte Pi 4: $SD_INFO
• SD-Karte Zero: $([ "$ZERO_OK" = "true" ] && echo "$ZERO_SD" || echo "nicht erreichbar")
• SSD: $SSD_INFO
• NAS (Synology): $NAS_INFO

🌐 NETZWERK
• LAN: $([ "$ETH0_STATE" = "up" ] && echo "🟢 $ETH0_IP" || echo "🔴 Nicht angeschlossen")
• WLAN: $([ "$ESSID" != "—" ] && echo "🟢 $ESSID ($SIGNAL dBm)" || echo "⚪ Nicht verbunden")
• Tailscale: 🟢 $TS_IP
• Pi Zero USB: $([ "$ZERO_OK" = "true" ] && echo "🟢 $ZERO_USB_IP" || echo "🔴")

🔌 UART-SCHMALSPURBAHN
• Pi4 ↔ Zero: $UART_STATUS

━━━━━━━━━━━━━━━━━━━━━━━━━━━

FOTOS:
$([ "$PI4_FOTO" = "OK" ] && echo "PI4=$SNAP_DIR/snap_pi4.jpg")
$([ "$NOIR_FOTO" = "OK" ] && echo "NOIR=$SNAP_DIR/snap_noir.jpg")
REPORT
fi
