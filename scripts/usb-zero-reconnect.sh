#!/bin/bash
# Triggered by udev when Zero USB gadget reconnects (new MAC after RUN-pin reset)
# Re-adds 10.42.0.1/24 to usb0 so Zero is reachable again

LOG="/var/log/usb-zero-reconnect.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') USB Zero reconnect detected (INTERFACE=$INTERFACE)" >> "$LOG"

# Wait a moment for the interface to be fully up
sleep 2

# Flush old addresses and re-add
ip addr flush dev usb0 2>/dev/null
ip addr add 10.42.0.1/24 dev usb0 2>/dev/null
ip link set usb0 up 2>/dev/null

echo "$(date '+%Y-%m-%d %H:%M:%S') usb0 reconfigured: 10.42.0.1/24" >> "$LOG"
