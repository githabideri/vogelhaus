# 🐦 Vogelhaus — DIY Raspberry Pi Birdhouse Camera

A Raspberry Pi–powered birdhouse with night vision, live streaming to Twitch, and AI-assisted monitoring.

## What is this?

A complete guide to building a smart birdhouse with:
- **Night vision camera** (OV5647 NoIR + IR LEDs) inside the nesting area
- **Wide-angle day camera** (IMX708) watching the entrance
- **Live streaming** to Twitch via Restreamer
- **Remote access** via Tailscale + SSH
- Two Raspberry Pis working together (Pi 4 as encoder/streamer, Pi Zero W as camera source)

## Hardware

| Component | Model | Role |
|-----------|-------|------|
| Pi 4 | Raspberry Pi 4 (aluminum case) | Encoder, streamer, jump host |
| Pi Zero W | Raspberry Pi Zero W v1.1 | Night vision camera source |
| Night cam | OV5647 NoIR + 2x 850nm IR LEDs (Kuman SC15 compatible) | 24/7 nest monitoring |
| Day cam | IMX708 Wide (Pi Camera Module 3) | Entrance/outside view |
| Power | Single USB-C PSU for Pi 4, Pi Zero powered via USB from Pi 4 |

## Architecture

```
┌─────────────────────────────────┐
│         Birdhouse               │
│                                 │
│  ┌──────────┐   ┌───────────┐  │
│  │ Pi Zero W│   │   Pi 4    │  │
│  │ + NoIR   │◄──│ + IMX708  │  │
│  │ (nest)   │USB│ (entrance)│  │
│  └──────────┘   └─────┬─────┘  │
│                       │USB-C   │
└───────────────────────┼────────┘
                        │
                    Power supply
                        │
                   ┌────┴────┐
                   │ Router  │
                   │ (WiFi)  │
                   └────┬────┘
                        │
                   ┌────┴────┐
                   │ Twitch  │
                   └─────────┘
```

### Data + control paths

- **Primary media/data path:** Pi Zero ↔ Pi 4 over USB
- **Recovery control path:** Pi 4 ↔ Pi Zero over 3-wire GPIO UART
- **Remote management path:** Wi-Fi + Tailscale (when available)

## Project Structure

```
docs/
├── getting-started.md          # Project overview and quick start
├── hardware/                   # Hardware specifications and assembly
│   ├── bill-of-materials.md    # Complete parts list and costs
│   ├── assembly.md             # Build instructions and design
│   └── camera-modules.md       # Camera specifications and setup
├── setup/                      # Installation and configuration
│   ├── pi-zero-flash.md        # Pi Zero OS installation guide
│   ├── usb-gadget.md          # USB networking setup
│   ├── uart-recovery.md       # Emergency serial access
│   ├── streaming.md           # MediaMTX and Restreamer setup
│   └── wsl-gpu-analysis.md    # Windows video analysis setup
├── operations/                 # Daily operations and maintenance
│   ├── troubleshooting.md     # Common issues and solutions
│   ├── usb-failover.md        # Automatic network failover
│   └── network-topology.md    # Complete network reference
└── reference/                  # Technical specifications
    ├── pi4-inventory.md        # Pi 4 system documentation
    ├── pi-zero-inventory.md    # Pi Zero system documentation
    ├── known-issues.md         # Documented problems and workarounds
    └── video-analysis.md       # Motion detection and AI analysis

config/         Configuration templates (mediamtx, boot config, etc.)
scripts/        Capture, streaming, and utility scripts
training/       Machine learning models and datasets
.env.template   Environment configuration template
JOURNAL.md      Project diary (the fun parts)
```

## Quick Start

1. **Get started**: Read [docs/getting-started.md](docs/getting-started.md) for project overview
2. **Hardware**: Follow [docs/hardware/bill-of-materials.md](docs/hardware/bill-of-materials.md) and [docs/hardware/assembly.md](docs/hardware/assembly.md)
3. **Setup**: Use [docs/setup/pi-zero-flash.md](docs/setup/pi-zero-flash.md) for installation
4. **Configuration**: Copy `.env.template` to `.env` and customize for your environment
5. **Troubleshooting**: Check [docs/operations/troubleshooting.md](docs/operations/troubleshooting.md) if needed

## Software Stack (Pi 4)

| Component | Purpose |
|-----------|---------|
| MediaMTX | RTSP/WebRTC camera server |
| Restreamer | Video restreaming to Twitch |
| Netdata | System monitoring |
| Docker | Container runtime for Restreamer et al. |
| Tailscale | Remote VPN access |

The Pi Zero runs a minimal headless setup — just SSH and the camera.

## Project History

| When | What |
|------|------|
| Mid 2023 | Pi 4 set up, Docker stack deployed (Restreamer, Frigate NVR, monitoring) |
| Early 2024 | External SSD added for video storage |
| Spring 2025 | MediaMTX added, ~25 days of continuous recording captured |
| Early 2026 | Pi Zero W added with NoIR camera, IR-LED research, birdhouse construction started |

## Status

🚧 **Work in progress** — Cameras work, streaming pipeline is being configured, birdhouse construction is underway.

## Credits

Built by humans (and one AI) in Vienna, Austria.

## License

AGPL-3.0 — see [LICENSE](LICENSE) file for details.

This project is licensed under the GNU Affero General Public License v3.0, ensuring that any modifications or network-based usage remain open source.
