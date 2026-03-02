# Bill of Materials

> Last updated: 2026-03

## Raspberry Pi Hardware

### Primary Unit (Pi 4)
- **Raspberry Pi 4** (4GB+ recommended)
- **Aluminum passive cooling case**
- **Official Raspberry Pi USB-C power supply**
- **IMX708 Wide Camera Module** (Pi Camera Module 3, 12MP) - ~70€
- **50cm flex ribbon cable** for camera connection
- **MicroSD card** (32GB+ recommended, Class 10)

### Secondary Unit (Pi Zero W)  
- **Raspberry Pi Zero W v1.1**
- **OV5647 NoIR camera module** (5MP, compatible with Kuman SC15)
- **MicroSD card** (16GB+ recommended, Class 10)
- **USB-A to micro-USB cable** for power and data connection to Pi 4

## Night Vision Components

### IR Illumination
- **2x 850nm IR LEDs** (~3W each)
- **Light sensor** (LDR/photoresistor with adjustable potentiometer)
- **Buck converter** (5V to 3.3V) for external LED power (optional but recommended)
- **Heatsinks** for IR LEDs (required for thermal management)

## GPIO Serial Link (Recommended)

For emergency recovery and out-of-band access:
- **3x jumper wires** (Ground, TX, RX)
- **Level shifter** (optional, for safety)

## Network Components

### WiFi Requirements
- **Router with 5GHz WiFi** (Pi 4 connectivity)
- **Tailscale account** (for remote access)

### Optional Network Hardware
- **Ethernet cable** (for wired Pi 4 connection)
- **Network switch** (if multiple wired devices)

## Power Architecture

- **Single USB-C power supply** (Official Raspberry Pi recommended)
- Power flows: USB-C → Pi 4 → Pi Zero (via USB)
- External 3.3V supply recommended for IR LEDs to prevent brownouts

## Software Requirements

### Operating Systems
- **Pi 4**: Raspberry Pi OS (Bookworm, 64-bit)
- **Pi Zero**: Raspberry Pi OS Legacy Lite (Bookworm, 32-bit)

### Services
- **MediaMTX** (RTSP streaming server)
- **Restreamer** (streaming to external platforms)
- **Tailscale** (VPN for remote access)

## Cost Estimate

| Item | Approximate Cost |
|------|------------------|
| Pi 4 (4GB) | €80-90 |
| Pi Zero W | €15-20 |
| IMX708 Camera | €70 |
| OV5647 NoIR | €30-40 |
| IR LEDs + LDR | €15-25 |
| Cases + cables | €20-30 |
| MicroSD cards | €20-30 |
| Power supply | €10-15 |
| **Total** | **€260-320** |

## Important Notes

### Power Considerations
- Pi Zero's 3.3V regulator limited to 1.0-1.5A
- Both IR LEDs draw ~1.8A combined - external power recommended
- Single USB-C supply powers entire system through Pi 4

### Compatibility Warnings
- **Do NOT use Trixie OS** on Pi Zero W v1.1 (WiFi broken, USB gadget broken)
- Use Bookworm-based Legacy Lite OS for Pi Zero
- Pi 4 requires `libcamera-still`, Pi Zero uses `rpicam-still`

### Network Architecture
- Pi Zero gets internet via USB Gadget mode through Pi 4
- No direct network connection required for Pi Zero
- GPIO UART provides fallback access independent of network