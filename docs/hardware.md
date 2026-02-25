# Hardware

## Raspberry Pi 4

- **Model:** Raspberry Pi 4 (exact RAM TBD)
- **Case:** Aluminum passive cooling case
- **PSU:** Official Raspberry Pi USB-C power supply
- **Camera:** IMX708 Wide (Pi Camera Module 3), 12MP, ~70€
- **Cable:** ~50cm flex ribbon cable to camera
- **OS:** Raspberry Pi OS (Bookworm)
- **Role:** Main compute unit — encodes video from Pi Zero, runs Restreamer, streams to Twitch
- **Software:** mediamtx + Restreamer (systemd service)

### Notes
- mediamtx locks the camera — must `sudo systemctl stop mediamtx` before manual capture
- Use `libcamera-still` (not `rpicam-still`) for photo capture
- Connected via Tailscale for remote access

## Raspberry Pi Zero W

- **Model:** Raspberry Pi Zero W v1.1 (2017)
- **Architecture:** ARMv6, 32-bit only
- **OS:** Raspberry Pi OS Legacy Lite (Bookworm-based, 32-bit)
- **Camera:** OV5647 NoIR with IR LEDs (see below)
- **Role:** Night vision camera source for nest monitoring
- **Software:** rpicam-still/rpicam-hello (libcamera-apps-lite)

### Notes
- **Do NOT use Trixie** on Pi Zero W v1.1 — WiFi broken, USB gadget broken, generally unstable on ARMv6
- `vcgencmd get_camera` shows `detected=0` but camera works fine
- Use `rpicam-still` (not `libcamera-still`)
- USB Gadget Mode configured (`dtoverlay=dwc2`, `modules-load=dwc2,g_ether`)

## Serial Fallback Link (Recommended)

A dedicated 3-wire GPIO UART link between Pi 4 and Pi Zero is recommended as a recovery path:
- independent from Wi-Fi
- independent from USB networking
- supports direct shell access via serial getty

See [GPIO UART Setup](gpio-uart-setup.md) for wiring and service configuration.

## Night Vision Camera Module

- **Sensor:** OmniVision OV5647, 5MP
- **Type:** NoIR (no infrared filter) — compatible with Kuman SC15
- **IR LEDs:** 2x 850nm, ~3W each
- **Light sensor:** LDR (photoresistor) with adjustable potentiometer
- **Auto mode:** LEDs turn on automatically in darkness (LDR-controlled)

### Specifications

| Parameter | Value |
|-----------|-------|
| Resolution | 2592x1944 (15fps), 1920x1080 (30fps), 1296x972 (46fps), 640x480 (59fps) |
| FOV | 72.4° |
| IR LED wavelength | 850nm |
| IR LED power | ~3W each |
| IR LED current | ~909mA @ 3.3V per LED |
| Total IR draw | ~1.8A from 3.3V rail |
| Effective IR range | 1-3 meters |
| I2C address | 0x36 |
| Interface | CSI (flex ribbon cable) |

### ⚠️ Power Warning

Both IR LEDs together draw ~1.8A from the 3.3V rail. The Pi Zero's 3.3V regulator can only supply 1.0-1.5A total (including SoC). Running both LEDs from the Pi's power causes brownouts and freezes.

**Solutions:**
1. Run only ONE LED (sufficient for small birdhouse interior, 15-20cm distance)
2. External 3.3V power supply (5V→3.3V buck converter) for the LEDs
3. GPIO-controlled switching with external power (see [scripts/ir-led-control.py](../scripts/ir-led-control.py))

### IR LED Thermal Notes

- Missing heatsinks cause LEDs to glow visibly brighter/redder (more current due to lower forward voltage at higher temperature)
- Risk of thermal runaway without heatsinks
- The 850nm wavelength has a faint red glow visible to humans but NOT to birds (songbirds see UV, not IR)
- Wavelength drift: ~0.1-0.3 nm/°C (shifts further into IR, not more visible)

## Day Camera (IMX708 Wide)

- **Sensor:** Sony IMX708, 12MP
- **Type:** Pi Camera Module 3 (Wide)
- **Role:** Entrance/outside monitoring (B-camera, on-demand)
- **Notes:** Has IR-cut filter — no night vision without additional IR illumination

## Networking

- Pi 4 connects via WiFi (5 GHz) or Ethernet to local network
- Pi 4 has Tailscale for remote access
- **Pi Zero gets internet via USB-Gadget (CDC Ethernet) through the Pi 4** — see [USB Gadget Setup](usb-gadget-setup.md)
- Pi Zero has Tailscale for direct remote SSH access
- Streaming: Pi Zero → Pi 4 (USB network) → Twitch (internet)
- Out-of-band fallback: Pi 4 ↔ Pi Zero over GPIO UART (no IP required) — see [GPIO UART Setup](gpio-uart-setup.md)

### USB Hub Topology (Pi 4)

The Pi 4's VL805 USB controller supports per-port power switching via `uhubctl`:

- **Hub 2 (USB 3.0):** SSD on Port 1
- **Hub 1-1 (USB 2.0, VIA):** Zero Gadget on Port 2, Audio on Port 3

At boot, `usb-zero-powercycle.service` cycles Hub 1-1 to ensure the Zero gets a clean start. The SSD on Hub 2 is unaffected.

## Power Architecture

Single USB-C power supply → Pi 4 → Pi Zero (via USB)

Only one cable exits the birdhouse. Pi 4 powers the Pi Zero through its USB port.
