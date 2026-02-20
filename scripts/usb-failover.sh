#!/bin/bash
# usb-failover.sh — WiFi failover between two Raspberry Pis connected via USB Gadget
#
# When local WiFi goes down, this script routes traffic through the USB-connected
# peer Pi which (hopefully) still has WiFi. When local WiFi comes back, it reverts.
#
# Designed for a Pi 4 + Pi Zero W connected via USB OTG cable with g_ether gadget.
#
# Usage: usb-failover.sh [--install|--uninstall|--status]
#   No args: run one check cycle (intended for cron/systemd timer)
#   --install: set up systemd timer for periodic checks
#   --uninstall: remove systemd timer
#   --status: show current failover state

set -euo pipefail

# --- Configuration (override via /etc/usb-failover.conf) ---
USB_IFACE="usb0"
WLAN_IFACE="wlan0"
PEER_USB_IP=""          # must be set in config
CHECK_HOST="1.1.1.1"   # ping target to verify internet
CHECK_INTERVAL=30       # seconds between checks (for systemd timer)
METRIC_NORMAL=300       # normal wlan route metric
METRIC_FAILOVER=50      # failover route metric (lower = preferred)
STATE_FILE="/run/usb-failover.state"
LOG_TAG="usb-failover"

# Load config
CONF="/etc/usb-failover.conf"
if [[ -f "$CONF" ]]; then
    # shellcheck source=/dev/null
    source "$CONF"
fi

log() { logger -t "$LOG_TAG" "$*"; echo "[$(date '+%H:%M:%S')] $*"; }

get_state() {
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE"
    else
        echo "normal"
    fi
}

set_state() {
    echo "$1" > "$STATE_FILE"
}

check_internet_via() {
    local iface="$1"
    # Try to ping through specific interface
    ping -c 1 -W 3 -I "$iface" "$CHECK_HOST" &>/dev/null
}

check_link() {
    local iface="$1"
    # USB ethernet gadgets report state UNKNOWN (no physical link detection)
    ip link show "$iface" 2>/dev/null | grep -qE "state (UP|UNKNOWN)"
}

enable_forwarding() {
    sysctl -w net.ipv4.ip_forward=1 &>/dev/null
    # Masquerade traffic going out via wlan
    if ! iptables -t nat -C POSTROUTING -o "$WLAN_IFACE" -j MASQUERADE 2>/dev/null; then
        iptables -t nat -A POSTROUTING -o "$WLAN_IFACE" -j MASQUERADE
    fi
}

activate_failover() {
    local state
    state=$(get_state)
    if [[ "$state" == "failover" ]]; then
        return 0
    fi

    if [[ -z "$PEER_USB_IP" ]]; then
        log "ERROR: PEER_USB_IP not configured in $CONF"
        return 1
    fi

    log "FAILOVER: local WiFi down, routing via USB peer ($PEER_USB_IP)"

    # Get our local USB IP for source-based routing
    local local_usb_ip
    local_usb_ip=$(ip -4 addr show "$USB_IFACE" 2>/dev/null | grep -oP 'inet \K[\d.]+')

    # Add default route via USB peer with correct source IP
    # Source IP MUST be the USB address, not the WiFi address — otherwise
    # return packets get routed via LAN instead of back through USB
    if [[ -n "$local_usb_ip" ]]; then
        ip route replace default via "$PEER_USB_IP" dev "$USB_IFACE" src "$local_usb_ip" metric "$METRIC_FAILOVER" 2>/dev/null || true
    else
        ip route replace default via "$PEER_USB_IP" dev "$USB_IFACE" metric "$METRIC_FAILOVER" 2>/dev/null || true
    fi

    set_state "failover"
    log "FAILOVER: active (local USB IP: ${local_usb_ip:-unknown})"
}

deactivate_failover() {
    local state
    state=$(get_state)
    if [[ "$state" == "normal" ]]; then
        return 0
    fi

    log "RECOVERY: local WiFi back, removing USB failover route"

    # Remove failover route
    ip route del default via "$PEER_USB_IP" dev "$USB_IFACE" metric "$METRIC_FAILOVER" 2>/dev/null || true

    set_state "normal"
    log "RECOVERY: back to normal"
}

do_check() {
    # Sanity: USB interface must be up
    if ! check_link "$USB_IFACE"; then
        log "USB interface $USB_IFACE is down, failover not possible"
        deactivate_failover
        return 0
    fi

    # Check if local WiFi provides internet
    # WiFi must have a default route AND be able to reach the internet
    if ip route show default | grep -q "$WLAN_IFACE" && check_internet_via "$WLAN_IFACE"; then
        deactivate_failover
    else
        # WiFi down — can we reach peer via USB?
        if ping -c 1 -W 2 "$PEER_USB_IP" &>/dev/null; then
            activate_failover

            # Verify failover actually provides internet
            sleep 2
            if ! ping -c 1 -W 3 "$CHECK_HOST" &>/dev/null; then
                log "FAILOVER: USB route set but still no internet (router down?), reverting"
                deactivate_failover
            fi
        else
            log "WARNING: WiFi down AND USB peer unreachable"
            deactivate_failover
        fi
    fi
}

do_status() {
    echo "=== USB Failover Status ==="
    echo "State: $(get_state)"
    echo ""
    echo "Local WiFi ($WLAN_IFACE):"
    if check_link "$WLAN_IFACE"; then
        local ip
        ip=$(ip -4 addr show "$WLAN_IFACE" 2>/dev/null | grep -oP 'inet \K[\d.]+')
        echo "  Link: UP (IP: ${ip:-none})"
        if check_internet_via "$WLAN_IFACE"; then
            echo "  Internet: OK"
        else
            echo "  Internet: UNREACHABLE"
        fi
    else
        echo "  Link: DOWN"
    fi
    echo ""
    echo "USB ($USB_IFACE):"
    if check_link "$USB_IFACE"; then
        local usb_ip
        usb_ip=$(ip -4 addr show "$USB_IFACE" 2>/dev/null | grep -oP 'inet \K[\d.]+')
        echo "  Link: UP (IP: ${usb_ip:-none})"
        if [[ -n "$PEER_USB_IP" ]]; then
            if ping -c 1 -W 2 "$PEER_USB_IP" &>/dev/null; then
                echo "  Peer ($PEER_USB_IP): REACHABLE"
            else
                echo "  Peer ($PEER_USB_IP): UNREACHABLE"
            fi
        else
            echo "  Peer: NOT CONFIGURED"
        fi
    else
        echo "  Link: DOWN"
    fi
    echo ""
    echo "Routes:"
    ip route show | grep -E "default|$USB_IFACE" | sed 's/^/  /'
}

run_daemon() {
    log "Starting failover daemon (check every ${CHECK_INTERVAL}s)"
    while true; do
        do_check
        sleep "$CHECK_INTERVAL"
    done
}

install_systemd() {
    cat > /etc/systemd/system/usb-failover.service << EOF
[Unit]
Description=USB WiFi Failover Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/usb-failover.sh --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    if [[ "$(realpath "$0")" != "/usr/local/bin/usb-failover.sh" ]]; then
        cp "$0" /usr/local/bin/usb-failover.sh
        chmod +x /usr/local/bin/usb-failover.sh
    fi

    # Remove old timer if present
    systemctl disable --now usb-failover.timer 2>/dev/null || true
    rm -f /etc/systemd/system/usb-failover.timer

    systemctl daemon-reload
    systemctl enable --now usb-failover.service
    log "Installed and started usb-failover service (check every ${CHECK_INTERVAL}s)"
}

uninstall_systemd() {
    systemctl disable --now usb-failover.service 2>/dev/null || true
    systemctl disable --now usb-failover.timer 2>/dev/null || true
    rm -f /etc/systemd/system/usb-failover.service
    rm -f /etc/systemd/system/usb-failover.timer
    rm -f /usr/local/bin/usb-failover.sh
    systemctl daemon-reload
    deactivate_failover
    log "Uninstalled usb-failover"
}

case "${1:-check}" in
    --daemon)    run_daemon ;;
    --install)   install_systemd ;;
    --uninstall) uninstall_systemd ;;
    --status)    do_status ;;
    check|"")    do_check ;;
    *)           echo "Usage: $0 [--daemon|--install|--uninstall|--status]"; exit 1 ;;
esac
