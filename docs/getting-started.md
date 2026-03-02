# Getting Started

> Last updated: 2026-03

## Overview

Vogelhaus is a multi-camera bird observation system using Raspberry Pi devices to provide live streaming and monitoring capabilities. The system consists of:

- **Primary Pi 4**: Main processing unit with wide-angle camera for overview shots
- **Pi Zero W**: Secondary unit with NoIR camera for detailed nest area monitoring with IR illumination
- **Streaming Pipeline**: MediaMTX + Restreamer for live streaming to platforms like Twitch
- **Remote Access**: Tailscale VPN for secure remote management

## What You Need

### Hardware
- Raspberry Pi 4 (4GB+ recommended)
- Raspberry Pi Zero W
- Camera modules (see [Camera Modules](hardware/camera-modules.md))
- MicroSD cards (32GB+ recommended)
- Power supplies and cables
- See complete [Bill of Materials](hardware/bill-of-materials.md)

### Software Prerequisites
- Basic Linux command line knowledge
- SSH client for remote access
- Understanding of networking concepts

## Quick Start Guide

1. **Hardware Setup**: Follow the [Assembly Guide](hardware/assembly.md)
2. **Pi Zero Setup**: Flash and configure using [Pi Zero Flash Guide](setup/pi-zero-flash.md)
3. **USB Gadget**: Configure USB networking with [USB Gadget Setup](setup/usb-gadget.md)
4. **Streaming**: Set up the streaming pipeline with [Streaming Setup](setup/streaming.md)
5. **Network**: Configure networking using [Network Topology](operations/network-topology.md)

## Troubleshooting

If you encounter issues:
- Check [Known Issues](reference/known-issues.md) for common problems
- Review [Troubleshooting Guide](operations/troubleshooting.md)
- Verify hardware with [Pi4 Inventory](reference/pi4-inventory.md) and [Pi Zero Inventory](reference/pi-zero-inventory.md)

## Advanced Features

- **UART Recovery**: Emergency access via [UART Recovery](setup/uart-recovery.md)
- **USB Failover**: Automatic network switching with [USB Failover](operations/usb-failover.md)
- **Video Analysis**: Machine learning capabilities in [Video Analysis](reference/video-analysis.md)
- **WSL GPU**: Windows analysis setup in [WSL GPU Analysis](setup/wsl-gpu-analysis.md)