# Streaming Setup

> Last updated: 2026-03

This guide covers setting up the streaming pipeline from cameras through MediaMTX to Restreamer and finally to Twitch.

## Overview

The streaming pipeline consists of:
1. **Camera sources** — Pi Zero NoIR camera and Pi 4 IMX708 camera
2. **MediaMTX** — RTSP server that aggregates camera streams
3. **Restreamer** — Stream processor and restreamer to external platforms
4. **Twitch** — Final destination for live stream

## Architecture

```
Pi Zero W (NoIR) ──USB──┐
                        │
                        ▼
Pi 4 (IMX708) ─────► MediaMTX ──RTSP──► Restreamer ──RTMP──► Twitch
                                            │
                                            ▼
                                      Local WebRTC
                                      (browser view)
```

## MediaMTX Configuration

MediaMTX serves as the RTSP server collecting camera streams.

### Installation

MediaMTX is installed as a systemd service on the Pi 4:

```bash
# Check status
sudo systemctl status mediamtx

# Start/stop/restart
sudo systemctl start mediamtx
sudo systemctl stop mediamtx
sudo systemctl restart mediamtx
```

### Camera Streams

| Stream | URL | Source | Purpose |
|--------|-----|---------|---------|
| `vogl-cam` | `rtsp://127.0.0.1:8554/vogl-cam` | Pi 4 IMX708 | Top-down view, nesting chamber |
| `vogl-noir` | `rtsp://127.0.0.1:8554/vogl-noir` | Pi Zero NoIR | Night camera, nest area |

### Configuration File

MediaMTX configuration is stored in `/etc/mediamtx/mediamtx.yml`. Key settings:

```yaml
rtspAddress: :8554
webrtcAddress: :8889
paths:
  vogl-cam:
    source: pi4_camera_script
  vogl-noir:
    source: pizero_camera_forwarding
```

## Restreamer Setup

Restreamer runs as a Docker container and handles the actual streaming to external platforms.

### Docker Container

```bash
# Check status
docker ps --filter name=restreamer

# View logs
docker logs restreamer

# Restart container
docker restart restreamer
```

### Configuration

Restreamer is configured via web interface at `http://<PI4_IP>:8080`.

### Streams Configuration

- **Input**: RTSP stream from MediaMTX (`rtsp://127.0.0.1:8554/vogl-noir`)
- **Output**: RTMP to Twitch (`rtmp://live.twitch.tv/live/<STREAM_KEY>`)

## Taking Photos from Streams

### Preferred Method (via RTSP)

This method is preferred because it doesn't interrupt streaming services:

```bash
# Pi 4 camera (day camera)
ffmpeg -y -rtsp_transport tcp -i rtsp://127.0.0.1:8554/vogl-cam -frames:v 1 -q:v 2 /tmp/snap.jpg

# Pi Zero camera (night vision)
ffmpeg -y -rtsp_transport tcp -i rtsp://127.0.0.1:8554/vogl-noir -frames:v 1 -q:v 2 /tmp/snap_noir.jpg
```

### Direct Camera Access

Only use when streams are not running:

```bash
# Pi 4 (stop MediaMTX first!)
sudo systemctl stop mediamtx
libcamera-still -o /tmp/snap.jpg --immediate --width 2304 --height 1296
sudo systemctl start mediamtx

# Pi Zero (via SSH)
rpicam-still -o /tmp/snap.jpg --immediate --width 1920 --height 1080
```

## Troubleshooting

### MediaMTX Issues

**Camera not accessible:**
- Check if MediaMTX is running: `sudo systemctl status mediamtx`
- MediaMTX locks camera access — stop service for direct access
- Verify camera connection: `libcamera-hello --list-cameras` (Pi 4) or `rpicam-hello --list-cameras` (Pi Zero)

**Stream not available:**
- Check MediaMTX logs: `sudo journalctl -u mediamtx -f`
- Verify RTSP URL: `ffprobe rtsp://127.0.0.1:8554/vogl-cam`

### Restreamer Issues

**Container not running:**
```bash
docker ps -a  # Check all containers
docker logs restreamer  # Check logs
docker restart restreamer  # Restart if needed
```

**No output to Twitch:**
- Check stream key configuration in Restreamer web UI
- Verify network connectivity: `ping live.twitch.tv`
- Check ffmpeg process: `docker exec restreamer ps aux | grep ffmpeg`

**Stream quality issues:**
- Adjust bitrate in Restreamer configuration
- Check CPU usage: `htop` on Pi 4
- Verify camera resolution settings

### Network Issues

**Pi Zero camera not available:**
- Check USB Gadget connection: `ip addr show usb0` on Pi 4
- Verify Pi Zero is accessible: `ssh vb-light@169.254.246.2`
- Check USB Failover status: `systemctl status usb-failover`

## Performance Optimization

### Pi 4 Resources

Monitor system resources during streaming:
```bash
# CPU usage
htop

# Temperature
vcgencmd measure_temp

# Memory usage
free -h

# GPU memory split (should be at least 128MB)
vcgencmd get_mem gpu
```

### Stream Settings

Recommended settings for 24/7 streaming:
- **Resolution**: 1080p (1920x1080) for main stream
- **Framerate**: 15-30 FPS (balance quality vs. CPU usage)
- **Bitrate**: 2-4 Mbps (depends on network capacity)

### Recording

For local recording alongside streaming:
- Use external SSD (not SD card) for storage
- Configure Restreamer to save local copies
- Implement log rotation to manage disk space

## Integration with Other Services

### Status Monitoring

Check streaming status with the status script:
```bash
./scripts/vogelhaus-status.sh media/
```

This provides:
- MediaMTX service status
- Restreamer container status
- Current camera snapshots
- Network connectivity status

### Remote Access

Access Restreamer web interface remotely via Tailscale:
```
http://<TAILSCALE_PI4_IP>:8080
```

### Automation

Consider setting up:
- Automatic stream restart on failure
- Scheduled camera cleaning notifications
- Alert notifications for extended outages