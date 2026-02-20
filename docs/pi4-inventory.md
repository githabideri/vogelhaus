# Pi 4 System Inventory

Full system inventory of the main compute unit, last surveyed 2026-02-15.

## Hardware

| Component | Details |
|-----------|---------|
| Model | Raspberry Pi 4B, Cortex-A72 (4 cores, aarch64) |
| RAM | 3.5 GB |
| SD Card | 32 GB (mmcblk0) |
| SSD | SanDisk SSD Plus 1TB via USB (JMicron JMS578 SATA adapter) |
| Camera | IMX708 Wide (Sony, 12MP) |
| Audio | USB Sound Card (Texas Instruments PCM2902) |
| Network | WiFi (wlan0) + Tailscale (tailscale0) |

## Operating System

| | |
|---|---|
| OS | Debian Bullseye (11) |
| Kernel | 6.1.21-v8+ (aarch64) |
| First boot | ~May 2023 |
| User | `vogl` (uid 1000) |

## Storage

### SD Card (32 GB, `/`)

Typical usage ~30% after cleanup. Main consumers:
- `/var/lib/docker/` — Docker images + overlays (~4.4 GB)
- `/usr/` — system packages (~2.8 GB)
- `/var/log/` — logs (~300 MB, journal ~160-225 MB)

**Docker log rotation configured** (`/etc/docker/daemon.json`): max 50 MB × 3 files per container.

### SSD (1 TB, `/srv/ssd`)

Mounted as ext4 at `/srv/ssd`. Contains:
- `recordings/` — hourly MP4 segments from camera stream (~1-2.6 GB/hour)
- `frigate/` — NVR clips and exports (~1.4 GB)
- `hello-daumas.txt` — first SSD access marker (Jan 2024)

**Status (Feb 2026):** 100% full with ~25 days of recordings from April-May 2025.

## Software Stack

### Native Services (systemd)

| Service | Purpose | Status |
|---------|---------|--------|
| mediamtx | RTSP/WebRTC video server | enabled, auto-start |
| tailscaled | Tailscale VPN | running |
| netdata | System monitoring | running |
| smbd/nmbd | Samba file sharing | running |
| docker | Container runtime | running |
| ssh | Remote access | running |

### Docker Containers

| Container | Image | Ports | Purpose | Installed |
|-----------|-------|-------|---------|-----------|
| restreamer | `datarhei/restreamer:rpi-latest` | 8080, 8181, 8558, 1934→1935, 1936, 6000/udp | Video restreaming to Twitch | Jun 2023 |
| portainer | `portainer/portainer-ce:latest` | 9443, 8000 | Docker web UI | Jun 2023 (updated Feb 2026) |
| homepage | `ghcr.io/benphelps/homepage:latest` | 3000 | Dashboard | Jun 2023 |
| filebrowser | `hurlenko/filebrowser` | 1234→8080 | Web file manager | Jun 2023 |
| frigate | `ghcr.io/blakeblackshear/frigate:stable` | — | NVR (stopped) | Jun 2023 |

### MediaMTX Configuration

Path: `/opt/mediamtx/mediamtx.yml`

```yaml
paths:
  vogl-cam:
    source: rpiCamera
```

Streams the IMX708 camera as an RTSP/WebRTC source.

### Restreamer Configuration

Config: `/opt/restreamer/config`
Data: `/opt/restreamer/data`

Takes video input (from MediaMTX or direct camera) and restreams to external platforms (Twitch).

## Network

| Interface | Address | Purpose |
|-----------|---------|---------|
| wlan0 | <PI4_WLAN_IP>/24 | Local WiFi |
| tailscale0 | <TAILSCALE_PI4>/32 | VPN overlay |
| docker0 | 172.17.0.1/16 | Docker default bridge |
| br-* | 172.18-22.0.1/16 | Docker custom networks |

## USB Devices

- JMicron JMS578 SATA → SSD
- Texas Instruments PCM2902 → USB Audio
- VIA Labs Hub

## Timeline

| Date | Event |
|------|-------|
| May 2023 | Pi 4 first boot, OS installed |
| Jun 2023 | Restreamer, Frigate, Homepage, FileBrowser, Portainer deployed |
| Jan 2024 | SSD first accessed (hello-daumas.txt) |
| Apr 2025 | MediaMTX installed/configured |
| Apr-May 2025 | 25 days of continuous recording (~868 GB) |
| Feb 2026 | System audit, Portainer updated, Docker log rotation configured |
