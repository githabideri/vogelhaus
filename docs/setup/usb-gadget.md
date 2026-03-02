# USB Gadget Internet Sharing: Pi Zero ↔ Pi 4

> Last updated: 2026-03

## Overview

The Pi Zero gets internet through a USB Gadget connection (CDC Ethernet) via the Pi 4.
The Pi 4 acts as NAT gateway and forwards the Zero's traffic through its LAN interface.

## Prerequisites

### Pi Zero
- `modules-load=dwc2,g_ether` in `cmdline.txt`
- USB data cable on **middle** micro-USB port (DATA, not PWR)

### Pi 4
- `uhubctl` installed (`apt install uhubctl`)
- VL805 firmware ≥ `00137ad` (check: `sudo rpi-eeprom-update`)
- IP forwarding enabled (`net.ipv4.ip_forward=1`)

## Network Configuration

| Device | Interface | IP | Role |
|--------|-----------|----|----- |
| Pi 4 | usb0 | 10.42.0.1/24 | Gateway |
| Pi Zero | usb0 | 10.42.0.2/24 | Client |

DNS on Zero: `nameserver 1.1.1.1`

## Systemd Services

### Pi 4

**`usb-zero-powercycle.service`** — Runs at boot, cycles the USB2 hub (VIA, 1-1) to give the Zero a clean start.

- Script: `/usr/local/bin/usb-zero-powercycle.sh`
- Powers off Hub 1-1 (5s), waits 90s for Zero boot
- SSD (Hub 2, USB3) remains unaffected
- Fallback: individual data port recycle if usb0 missing after 90s

**`usb-internet-sharing.service`** — Configures IP + NAT on usb0 after Zero is detected.

- Script: `/usr/local/bin/usb-internet-sharing.sh`
- Waits up to 60s for usb0
- Sets IP 10.42.0.1/24, enables forwarding + iptables MASQUERADE via eth0

### Pi Zero

**`usb-network.service`** — Configures Zero side of USB connection.

- Script: `/usr/local/bin/usb-network.sh`
- Waits for usb0, sets IP 10.42.0.2/24, default route via Pi 4, DNS

## USB Hub Topology (Pi 4)

```
Hub 2 (USB 3.0, per-port power switching)
  └─ Port 1: SSD (JMicron SATA) ← NOT affected by powercycle!

Hub 1-1 (USB 2.0 VIA, per-port power switching)
  ├─ Port 1: (empty or PWR-only)
  ├─ Port 2: Pi Zero USB Gadget (data cable)
  ├─ Port 3: Audio Codec
  └─ Port 4: (empty or PWR-only)
```

## Cabling

- Data cable (USB-A → Micro-USB) must be on **middle** micro-USB port of Zero (DATA)
- Power cable (PWR) stays on **outer** port
- Recommendation: use high-quality data cable (not just charging cable!)

## Troubleshooting

### usb0 doesn't appear on Pi 4
1. Check if Zero is running: `sudo uhubctl` — Gadget should be visible on Hub 1-1 Port 2
2. Manually recycle port: `sudo uhubctl -l 1-1 -p 2 -a 2`
3. Restart service: `sudo systemctl restart usb-internet-sharing.service`

### Zero has no internet
1. Pi 4: `ip addr show usb0` — IP 10.42.0.1/24 present?
2. Pi 4: `sysctl net.ipv4.ip_forward` — must be 1
3. Pi 4: `sudo iptables -t nat -L POSTROUTING` — MASQUERADE rule present?
4. Zero: `ip route` — Default route via 10.42.0.1?
5. Zero: `cat /etc/resolv.conf` — `nameserver 1.1.1.1`?

### Zero doesn't boot after Pi4 reboot
- **Never use `shutdown -h now` on Zero** when it gets power via Pi4 USB!
- Always use `sudo reboot`
- The `usb-zero-powercycle.service` provides clean USB powercycle on Pi4 boot

## Service Files

### Pi 4 Services

**usb-zero-powercycle.service:**
```ini
[Unit]
Description=USB Zero Power Cycle
After=multi-user.target
Wants=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/usb-zero-powercycle.sh
RemainAfterExit=yes
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
```

**usb-internet-sharing.service:**
```ini
[Unit]
Description=USB Internet Sharing for Pi Zero
After=usb-zero-powercycle.service
Wants=usb-zero-powercycle.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/usb-internet-sharing.sh
RemainAfterExit=yes
TimeoutStartSec=90

[Install]
WantedBy=multi-user.target
```

### Pi Zero Service

**usb-network.service:**
```ini
[Unit]
Description=USB Network Configuration
After=network.target
Wants=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/usb-network.sh
RemainAfterExit=yes
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
```

## IP Address Ranges

The default configuration uses:
- **USB Gadget network:** `10.42.0.0/24`
- **Pi 4 Gateway:** `10.42.0.1`
- **Pi Zero Client:** `10.42.0.2`

This range avoids conflicts with:
- Common home networks (`192.168.x.x`, `10.0.x.x`)
- Link-local addresses (`169.254.x.x`)
- Docker networks (`172.16.x.x` to `172.31.x.x`)