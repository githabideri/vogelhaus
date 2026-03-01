#!/bin/bash
# USB Internet Sharing for Pi Zero (via USB Gadget)
# Pi4 acts as NAT gateway for Zero over usb0
# Erkennt automatisch das aktive Internet-Interface (wlan0, eth0, etc.)

set -e

# Wait for usb0 to appear (Zero might boot slower)
for i in $(seq 1 30); do
    if ip link show usb0 &>/dev/null; then
        echo "usb0 found after ${i}s"
        break
    fi
    sleep 2
done

if ! ip link show usb0 &>/dev/null; then
    echo "usb0 not found after 60s, giving up"
    exit 1
fi

# Configure usb0
ip addr flush dev usb0 2>/dev/null || true
ip addr add 10.42.0.1/24 dev usb0
ip link set usb0 up

# Enable forwarding
sysctl -w net.ipv4.ip_forward=1

# Detect default route interface (exclude usb0 and docker bridges)
OUTIF=$(ip route show default | grep -v usb0 | awk '{print $5; exit}')
if [ -z "$OUTIF" ]; then
    echo "ERROR: No default route found!"
    exit 1
fi
echo "Detected outgoing interface: $OUTIF"

# NAT: interface-unabhaengig via MASQUERADE auf alle non-usb0 Interfaces
# So funktioniert es egal ob wlan0, eth0, oder was auch immer
iptables -t nat -C POSTROUTING -s 10.42.0.0/24 ! -o usb0 -j MASQUERADE 2>/dev/null || \
    iptables -t nat -A POSTROUTING -s 10.42.0.0/24 ! -o usb0 -j MASQUERADE

iptables -C FORWARD -i usb0 -o "$OUTIF" -j ACCEPT 2>/dev/null || \
    iptables -A FORWARD -i usb0 -o "$OUTIF" -j ACCEPT
iptables -C FORWARD -i "$OUTIF" -o usb0 -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
    iptables -A FORWARD -i "$OUTIF" -o usb0 -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "USB internet sharing configured: 10.42.0.1/24 on usb0, NAT via $OUTIF"
