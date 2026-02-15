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

## Status

🚧 **Work in progress** — We're still building this thing. The cameras work, the streaming pipeline is being set up, and the birdhouse construction is underway.

## Credits

Built by humans (and one AI) in Vienna, Austria.
- **martin** — Software, networking, remote admin
- **thomas** — Hardware, construction, on-site
- **mox** — Documentation, research, AI assistant ([OpenClaw](https://openclaw.ai))

## License

MIT
