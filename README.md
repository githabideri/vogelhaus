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

## Project Structure

```
docs/           Hardware specs, assembly guide, troubleshooting
config/         Configuration templates (mediamtx, boot config, etc.)
scripts/        Capture, streaming, and utility scripts
images/         Hardware photos, diagrams
JOURNAL.md      Project diary (the fun parts)
```

## Quick Start

See [docs/hardware.md](docs/hardware.md) for the full parts list and [docs/assembly.md](docs/assembly.md) for build instructions.

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

MIT
