## Vogelhaus Dashboard API

REST API for programmatic access to the dashboard.

### Authentication

All `/api/*` endpoints require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8088/api/...
```

Set token in `.env`: `DASHBOARD_API_TOKEN=your_secure_token`

### Internal Endpoints (No Auth)

For localhost Web UI only - **not** for external access:

- `GET /internal/status/{mode}` — Generate status (mode: `bb` or `o`)
- `GET /internal/camera` — Get active camera
- `POST /internal/camera/{target}` — Switch camera (target: `pi4` or `noir`)
- `GET /internal/logs?service=...` — Get system logs

---

## Endpoints

### Status

#### `GET /api/status/{mode}`

Generate status report.

**Parameters:**
- `mode` (path): `bb` (Blitz-Bericht) or `o` (Offizieller Bericht)

**Response:**
```json
{
  "success": true,
  "mode": "bb",
  "text": "🐦 BB — 03.03. 21:16\n...",
  "photos": {
    "pi4": "/tmp/vogelhaus-status/snap_pi4.jpg",
    "noir": "/tmp/vogelhaus-status/snap_noir.jpg"
  },
  "timestamp": "2026-03-03T21:16:00"
}
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/status/bb
```

---

### Camera Control

#### `GET /api/camera`

Get currently active camera.

**Response:**
```json
{
  "active": "noir",
  "timestamp": "2026-03-03T21:20:00"
}
```

**Values:** `pi4`, `noir`, `unknown`

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/camera
```

#### `POST /api/camera/{target}`

Switch to specified camera.

**Parameters:**
- `target` (path): `pi4` or `noir`

**Response:**
```json
{
  "success": true,
  "returncode": 0,
  "message": "✅ Switch successful: noir is now active\n",
  "timestamp": "2026-03-03T21:21:00"
}
```

**Return codes:**
- `0` — Success (switched)
- `1` — Error
- `2` — Already active (no change)

**Example:**
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/camera/noir
```

---

### Reports

#### `GET /api/reports`

List recent reports.

**Query Parameters:**
- `limit` (optional, default: 30): Number of reports to return

**Response:**
```json
{
  "reports": [
    {
      "filename": "2026-03-03_21-16-00_bb.json",
      "timestamp": "2026-03-03T21:16:00",
      "mode": "bb",
      "success": true
    }
  ]
}
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/reports?limit=10
```

#### `GET /api/reports/{filename}`

Get specific report by filename.

**Response:**
```json
{
  "success": true,
  "mode": "bb",
  "text": "🐦 BB — 03.03. 21:16\n...",
  "photos": { ... },
  "timestamp": "2026-03-03T21:16:00"
}
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/reports/2026-03-03_21-16-00_bb.json
```

---

### Logs

#### `GET /api/logs`

Get system logs.

**Query Parameters:**
- `service` (optional): Specific service to query
  - systemd services: `mediamtx`, `noir-bridge`, `usb-failover`, `tailscaled`, `netdata`
  - Docker containers: `docker:restreamer`, `docker:portainer`
- `lines` (optional, default: 50): Number of lines per service

**Response (all services):**
```json
{
  "logs": {
    "pi4:mediamtx": ["line1", "line2", ...],
    "docker:restreamer": ["line1", "line2", ...]
  }
}
```

**Response (specific service):**
```json
{
  "service": "mediamtx",
  "logs": ["line1", "line2", ...]
}
```

**Example:**
```bash
# All services
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/logs

# Specific service
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8088/api/logs?service=mediamtx&lines=100"
```

#### `GET /api/logs/stream`

Stream logs via Server-Sent Events (SSE).

**Response:** Continuous event stream

```
data: {"logs": {...}}

data: {"logs": {...}}
```

Updates every 5 seconds.

**Example:**
```bash
curl -N -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8088/api/logs/stream
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message"
}
```

**Common status codes:**
- `400` — Bad Request (invalid parameters)
- `401` — Unauthorized (missing/invalid token)
- `404` — Not Found
- `500` — Internal Server Error

---

## Rate Limiting

No rate limiting currently implemented. Use responsibly.

---

## Web UI

The dashboard provides a web interface at `http://localhost:8088/` with:

- **Dashboard** (`/`) — Status, photos, camera control
- **Reports** (`/reports`) — Report history
- **Logs** (`/logs`) — System log viewer

All Web UI pages use `/internal/*` endpoints (no authentication required from localhost).

---

## Security Notes

- **Change the default API token!**
  ```bash
  openssl rand -hex 32
  echo "DASHBOARD_API_TOKEN=<token>" >> .env
  ```
- API is exposed on `0.0.0.0:8088` — use firewall rules if needed
- `/internal/*` endpoints are **not** protected by auth — ensure they're only accessible from localhost
- Consider using HTTPS proxy (nginx, Caddy) for production

---

## OpenAPI / Swagger

FastAPI auto-generates API documentation:

- **Interactive docs:** `http://localhost:8088/docs`
- **ReDoc:** `http://localhost:8088/redoc`
- **OpenAPI JSON:** `http://localhost:8088/openapi.json`

(These require authentication via the "Authorize" button)
