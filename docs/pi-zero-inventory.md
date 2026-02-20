# Pi Zero W System Inventory

Full system inventory of the camera unit, last surveyed 2026-02-15.

## Hardware

| Component | Details |
|-----------|---------|
| Model | Raspberry Pi Zero W Rev 1.1 (BCM2835, ARMv6l) |
| RAM | 364 MB (shared with GPU) |
| SD Card | 32 GB (mmcblk0) |
| Camera | OV5647 NoIR + 2x 850nm IR LEDs (LDR-controlled) |
| Network | WiFi only (wlan0) |
| Power | USB from Pi 4 (no own PSU) |

## Operating System

| | |
|---|---|
| OS | Raspbian Bookworm (12) |
| Kernel | 6.12.47+rpt-rpi-v6 (armv6l, 32-bit) |
| User | `vb-light` (uid 1000) |

## Storage

### SD Card (32 GB)

- 8% used (~2.1 GB), 25 GB free
- Boot partition: `/boot/firmware` (512 MB, vfat)
- Root partition: `/` (28.7 GB, ext4)

## Software Stack

Minimal installation — no Docker, no web services.

### Native Services (systemd)

| Service | Purpose | Status |
|---------|---------|--------|
| tailscaled | Tailscale VPN | installed but **logged out** |
| ssh | Remote access | running |
| wpa_supplicant | WiFi | running |
| NetworkManager | Network management | running |

### Camera

- Detected as OV5647 at `/base/soc/i2c0mux/i2c@1/ov5647@36`
- Tuning file: `/usr/share/libcamera/ipa/rpi/vc4/ov5647.json`
- Command: `rpicam-still` (not `libcamera-still`)

Available modes:

| Resolution | FPS | Crop |
|-----------|-----|------|
| 640×480 | 58.9 | 2560×1920 center |
| 1296×972 | 46.3 | Full sensor |
| 1920×1080 | 32.8 | 1928×1080 center |
| 2592×1944 | 15.6 | Full sensor |

## Network

| Interface | Address | Purpose |
|-----------|---------|---------|
| wlan0 | <ZERO_LAN_IP>/24 | Local WiFi |
| tailscale0 | — (logged out) | VPN overlay (not active) |

## Access

- Direct SSH via ProxyJump through Pi 4
- No Tailscale direct access until `sudo tailscale up` is run

## Notes

- Extremely resource-constrained (364 MB RAM, single-core ARMv6)
- Cannot run ffmpeg encoding efficiently — designed as camera source only
- Pi 4 handles all encoding and streaming
- USB Gadget Mode configured (`dtoverlay=dwc2`) but untested
