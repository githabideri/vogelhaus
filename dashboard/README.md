# Vogelhaus Dashboard

Modern web interface for monitoring and controlling the Vogelhaus bird camera system.

## Features

### 📊 Dashboard
- **Live Status**: bb (quick) and o (official) reports
- **Camera Control**: Switch between Pi4 (day) and NoIR (night) cameras
- **Live Streams**: Embedded iframe views of both cameras
- **Current Snapshots**: Latest photos from both cameras
- **Real-time Updates**: HTMX-powered dynamic updates

### 📋 Reports
- **History**: Last 30 reports stored
- **Archive**: View any past report
- **On-demand Generation**: Generate new reports with one click
- **Format Support**: Both bb (Blitz-Bericht) and o (Official) formats

### 📜 System Logs
- **Aggregated Logs**: All systemd services + Docker containers
- **Filtering**: Search and filter by service
- **Auto-refresh**: Optional 5-second auto-update
- **Live Stream**: Server-Sent Events for real-time log tailing

### 🔌 REST API
- **Token Authentication**: Bearer token for all endpoints
- **Status Generation**: `/api/status/{mode}`
- **Camera Control**: `/api/camera` (GET/POST)
- **Report Access**: `/api/reports`
- **Log Query**: `/api/logs`
- **Log Streaming**: `/api/logs/stream` (SSE)

## Installation

### Prerequisites

```bash
# Python 3.9+
sudo apt install python3 python3-pip python3-venv

# System dependencies
sudo apt install ffmpeg docker.io
```

### Setup

1. **Clone/Deploy**:
   ```bash
   cd /home/vogl/vogelhaus
   ```

2. **Install Python dependencies**:
   ```bash
   cd dashboard
   python3 -m pip install -r requirements.txt
   ```

3. **Configure** (edit `/home/vogl/vogelhaus/.env`):
   ```bash
   DASHBOARD_PORT=8088
   DASHBOARD_API_TOKEN=your_secure_token_here
   STATUS_SCRIPT=/home/vogl/scripts/vogelhaus-local.sh
   CAMERA_SWITCH_SCRIPT=/usr/local/bin/camera-switch.sh
   ```

4. **Install systemd service**:
   ```bash
   sudo cp vogelhaus-dashboard.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable vogelhaus-dashboard
   sudo systemctl start vogelhaus-dashboard
   ```

5. **Verify**:
   ```bash
   sudo systemctl status vogelhaus-dashboard
   curl http://localhost:8088/
   ```

### Replacing Old Dashboard

If you're replacing the old `vogelhaus-web.service`:

```bash
# Stop and disable old service
sudo systemctl stop vogelhaus-web
sudo systemctl disable vogelhaus-web

# Enable new dashboard
sudo systemctl enable vogelhaus-dashboard
sudo systemctl start vogelhaus-dashboard
```

## Usage

### Web Interface

Access the dashboard at: `http://<pi4-ip>:8088/`

**Pages:**
- `/` — Main dashboard (status, streams, photos)
- `/reports` — Report history
- `/logs` — System logs

### API Examples

**Get current status:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/status/o
```

**Switch camera:**
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/camera/noir
```

**Get active camera:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/camera
```

**List reports:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/reports
```

**Get logs (all services):**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/logs
```

**Get logs (specific service):**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8088/api/logs?service=mediamtx&lines=100"
```

**Stream logs (Server-Sent Events):**
```bash
curl -N -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/logs/stream
```

## Configuration

### Environment Variables

All configuration via `/home/vogl/vogelhaus/.env`:

```bash
# Dashboard
DASHBOARD_PORT=8088
DASHBOARD_API_TOKEN=your_secure_token

# Paths
STATUS_SCRIPT=/home/vogl/scripts/vogelhaus-local.sh
CAMERA_SWITCH_SCRIPT=/usr/local/bin/camera-switch.sh
REPORTS_DIR=/var/log/vogelhaus/reports
MEDIA_DIR=/tmp/vogelhaus-status
LOG_DIR=/var/log/vogelhaus

# External URLs
RESTREAMER_URL=http://localhost:8080
MEDIAMTX_HLS_PI4=http://localhost:8554/vogl-cam
MEDIAMTX_HLS_NOIR=http://localhost:8554/vogl-noir
```

### Security

**Important:** Change the default API token!

```bash
# Generate secure token
openssl rand -hex 32

# Add to .env
echo "DASHBOARD_API_TOKEN=<your-token>" >> /home/vogl/vogelhaus/.env

# Restart service
sudo systemctl restart vogelhaus-dashboard
```

## Troubleshooting

### Dashboard Not Starting

```bash
# Check logs
sudo journalctl -u vogelhaus-dashboard -n 50 -f

# Check Python dependencies
cd /home/vogl/vogelhaus/dashboard
python3 -c "import fastapi, uvicorn"

# Test manually
python3 app.py
```

### API Returns 401 Unauthorized

- Verify token in `.env` matches request header
- Ensure `.env` is readable by `vogl` user
- Check `EnvironmentFile` path in systemd service

### Streams Not Loading

- Verify Restreamer is running: `docker ps | grep restreamer`
- Check MediaMTX is active: `systemctl status mediamtx`
- Test RTSP streams: `ffprobe rtsp://localhost:8554/vogl-cam`

### Photos Not Appearing

- Check media directory exists: `ls -la /tmp/vogelhaus-status/`
- Run status script manually: `/home/vogl/scripts/vogelhaus-local.sh o`
- Verify permissions: `chown -R vogl:vogl /tmp/vogelhaus-status/`

## Development

### Run Locally

```bash
cd dashboard
python3 app.py
# Access at http://localhost:8088
```

### Watch Logs

```bash
sudo journalctl -u vogelhaus-dashboard -f
```

### Test API

```bash
# Export token
export TOKEN="your_api_token"

# Test all endpoints
curl -H "Authorization: Bearer $TOKEN" http://localhost:8088/api/status/bb
curl -H "Authorization: Bearer $TOKEN" http://localhost:8088/api/camera
curl -H "Authorization: Bearer $TOKEN" http://localhost:8088/api/reports
curl -H "Authorization: Bearer $TOKEN" http://localhost:8088/api/logs
```

## Architecture

```
dashboard/
├── app.py                      # FastAPI application
├── requirements.txt            # Python dependencies
├── vogelhaus-dashboard.service # systemd unit
├── static/
│   └── dashboard.css          # Shared styles
└── templates/
    ├── dashboard.html         # Main page
    ├── reports.html           # Report history
    └── logs.html              # System logs
```

**Tech Stack:**
- **Backend**: FastAPI (async Python web framework)
- **Frontend**: HTMX (dynamic HTML) + Alpine.js (reactivity)
- **Auth**: Bearer token (HTTP Authorization header)
- **Templating**: Jinja2
- **Server**: Uvicorn (ASGI server)

## License

AGPL-3.0 (same as main Vogelhaus project)
