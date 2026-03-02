# Pi 4 System Inventory

> Last updated: 2026-03

Full system inventory of the main compute unit (voglberry).

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

| Parameter | Value |
|-----------|-------|
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
- Project data and backups

**Status**: Used for high-volume data that shouldn't stress SD card.

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
  vogl-noir:
    source: pi_zero_forwarding
```

Streams the IMX708 camera and Pi Zero NoIR camera as RTSP/WebRTC sources.

### Restreamer Configuration

Config: `/opt/restreamer/config`
Data: `/opt/restreamer/data`

Takes video input (from MediaMTX or direct camera) and restreams to external platforms (Twitch).

## Network Configuration

| Interface | Address | Purpose |
|-----------|---------|---------|
| wlan0 | `<PI4_WLAN_IP>/24` | Local WiFi |
| eth0 | `<PI4_LAN_IP>/24` | Ethernet (when connected) |
| usb0 | `<PI4_USB_IP>/16` | USB Gadget host |
| tailscale0 | `<TAILSCALE_PI4>/32` | VPN overlay |
| docker0 | 172.17.0.1/16 | Docker default bridge |
| br-* | 172.18-22.0.1/16 | Docker custom networks |

## USB Devices

| Device | Manufacturer | Purpose |
|--------|--------------|---------|
| JMicron JMS578 | SATA Bridge | SSD connection |
| Texas Instruments PCM2902 | Audio Codec | USB Audio |
| VIA Labs Hub | USB Hub | Port expansion |
| Pi Zero W | USB Gadget | Camera source |

## Power and Thermal

| Parameter | Typical Value | Notes |
|-----------|---------------|-------|
| Power consumption | 8-12W | Varies with load |
| CPU temperature | 45-65°C | Aluminum passive case |
| Throttling | Rare | Only under extreme load |
| PSU | Official Raspberry Pi USB-C | 15W rated |

## Performance Characteristics

### CPU Usage
- **Idle**: 5-15%
- **Video streaming**: 30-60%
- **Video encoding**: 60-90%
- **Docker containers**: 10-20%

### Memory Usage
- **Base system**: ~500MB
- **Docker + containers**: ~800MB-1.2GB
- **Available for applications**: ~2GB

### Network Throughput
- **WiFi 5GHz**: 100-300 Mbps
- **Ethernet**: 1000 Mbps (when connected)
- **USB Gadget**: ~480 Mbps theoretical

## Maintenance Schedule

### Daily
- Automatic log rotation
- System monitoring via Netdata
- Container health checks

### Weekly
- Automatic security updates
- Disk space monitoring
- Service status verification

### Monthly
- Manual system review
- Container image updates
- Performance monitoring

## Timeline

| Date | Event |
|------|-------|
| May 2023 | Pi 4 first boot, OS installed |
| Jun 2023 | Restreamer, Frigate, Homepage, FileBrowser, Portainer deployed |
| Jan 2024 | SSD integrated |
| Apr 2025 | MediaMTX installed/configured |
| Apr-May 2025 | Continuous recording period |
| Feb 2026 | System audit, Portainer updated, Docker log rotation configured |
| Mar 2026 | Pi Zero integration, USB Gadget setup |

## Access Information

### SSH Access
```bash
# Via Tailscale
ssh vogl@<TAILSCALE_PI4>

# Via local network
ssh vogl@<PI4_WLAN_IP>
ssh vogl@<PI4_LAN_IP>
```

### Web Services
- **MediaMTX WebRTC**: `http://<PI4_IP>:8889`
- **Restreamer**: `http://<PI4_IP>:8080`
- **Portainer**: `https://<PI4_IP>:9443`
- **Netdata**: `http://<PI4_IP>:19999`
- **Homepage**: `http://<PI4_IP>:3000`
- **FileBrowser**: `http://<PI4_IP>:1234`