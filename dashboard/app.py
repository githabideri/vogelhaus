#!/usr/bin/env python3
"""
Vogelhaus Dashboard — FastAPI Web Interface
Features:
- Live status (bb/o reports)
- Camera streams (iframe embed)
- Report history
- Camera switching
- System logs
- REST API
"""

import os
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import asyncio

from fastapi import FastAPI, Request, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
import uvicorn

# ============================================================
# CONFIG
# ============================================================

# Load .env if exists
ENV_FILE = Path(__file__).parent.parent / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key, val)

PORT = int(os.getenv('DASHBOARD_PORT', '8088'))
API_TOKEN = os.getenv('DASHBOARD_API_TOKEN', 'changeme')
STATUS_SCRIPT = os.getenv('STATUS_SCRIPT', '/home/vogl/scripts/vogelhaus-local.sh')
CAMERA_SWITCH_SCRIPT = os.getenv('CAMERA_SWITCH_SCRIPT', '/usr/local/bin/camera-switch.sh')
REPORTS_DIR = Path(os.getenv('REPORTS_DIR', '/var/log/vogelhaus/reports'))
MEDIA_DIR = Path(os.getenv('MEDIA_DIR', '/tmp/vogelhaus-status'))
LOG_DIR = Path(os.getenv('LOG_DIR', '/var/log/vogelhaus'))

RESTREAMER_URL = os.getenv('RESTREAMER_URL', 'http://localhost:8080')
MEDIAMTX_HLS_PI4 = os.getenv('MEDIAMTX_HLS_PI4', 'http://localhost:8554/vogl-cam')
MEDIAMTX_HLS_NOIR = os.getenv('MEDIAMTX_HLS_NOIR', 'http://localhost:8554/vogl-noir')

# Services to monitor
SERVICES_PI4 = ['mediamtx', 'noir-bridge', 'usb-failover', 'tailscaled', 'netdata']
SERVICES_ZERO = ['vogl-noir-stream', 'usb-network', 'tailscaled']
DOCKER_CONTAINERS = ['restreamer', 'portainer']

# Create directories
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# APP
# ============================================================

app = FastAPI(title="Vogelhaus Dashboard", version="1.0.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
security = HTTPBearer()

# Mount static files (for CSS/JS)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount media (for snapshots)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

# ============================================================
# AUTH
# ============================================================

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token"""
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return credentials.credentials

# ============================================================
# STATUS GENERATION
# ============================================================

async def generate_status(mode: str = 'o') -> dict:
    """Generate status report (bb or o)"""
    try:
        result = subprocess.run(
            [STATUS_SCRIPT, mode],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode not in (0, 2):  # 0=OK, 2=partial
            return {
                'success': False,
                'error': f"Status script failed: {result.stderr}"
            }
        
        # Extract photo paths from output
        photos = {}
        for line in result.stdout.split('\n'):
            if line.startswith('FOTO_PI4='):
                photos['pi4'] = line.split('=', 1)[1]
            elif line.startswith('FOTO_NOIR='):
                photos['noir'] = line.split('=', 1)[1]
        
        # Get report text (everything before FOTO_ lines)
        report_lines = []
        for line in result.stdout.split('\n'):
            if line.startswith('FOTO_'):
                break
            report_lines.append(line)
        
        report_text = '\n'.join(report_lines).strip()
        
        return {
            'success': True,
            'mode': mode,
            'text': report_text,
            'photos': photos,
            'timestamp': datetime.now().isoformat()
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Status generation timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def save_report(report: dict):
    """Save report to filesystem"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{timestamp}_{report['mode']}.json"
    filepath = REPORTS_DIR / filename
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)

# ============================================================
# CAMERA SWITCHING
# ============================================================

async def get_active_camera() -> str:
    """Get currently active camera (pi4 or noir)"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'restreamer', 'grep', '-oP', 'rtsp://[^"]+', '/core/config/db.json'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'vogl-cam' in result.stdout:
            return 'pi4'
        elif 'vogl-noir' in result.stdout:
            return 'noir'
        return 'unknown'
    except:
        return 'unknown'

async def switch_camera(target: str) -> dict:
    """Switch camera (pi4 or noir)"""
    try:
        result = subprocess.run(
            [CAMERA_SWITCH_SCRIPT, target],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            'success': result.returncode in (0, 2),  # 0=switched, 2=already active
            'returncode': result.returncode,
            'message': result.stdout + result.stderr,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# ============================================================
# LOGS
# ============================================================

async def get_service_logs(service: str, lines: int = 50) -> List[str]:
    """Get systemd service logs"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', service, '-n', str(lines), '--no-pager'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.split('\n')
    except:
        return []

async def get_docker_logs(container: str, lines: int = 50) -> List[str]:
    """Get Docker container logs"""
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail', str(lines), container],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.split('\n')
    except:
        return []

async def aggregate_logs(lines_per_source: int = 30) -> dict:
    """Aggregate logs from all services"""
    logs = {}
    
    # Pi4 systemd services
    for service in SERVICES_PI4:
        logs[f"pi4:{service}"] = await get_service_logs(service, lines_per_source)
    
    # Docker containers
    for container in DOCKER_CONTAINERS:
        logs[f"docker:{container}"] = await get_docker_logs(container, lines_per_source)
    
    # TODO: Pi Zero services (via SSH)
    
    return logs

# ============================================================
# ROUTES — WEB UI
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    status = await generate_status('bb')
    active_camera = await get_active_camera()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "status": status,
        "active_camera": active_camera,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Report history page"""
    reports = sorted(REPORTS_DIR.glob("*.json"), reverse=True)[:30]
    
    report_list = []
    for r in reports:
        with open(r) as f:
            data = json.load(f)
            report_list.append({
                'filename': r.name,
                'timestamp': data.get('timestamp', ''),
                'mode': data.get('mode', ''),
                'success': data.get('success', False)
            })
    
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "reports": report_list
    })

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """System logs page"""
    return templates.TemplateResponse("logs.html", {
        "request": request
    })

# ============================================================
# ROUTES — API
# ============================================================

@app.get("/api/status/{mode}")
async def api_status(mode: str, token: str = Depends(verify_token)):
    """Generate status report (bb or o)"""
    if mode not in ('bb', 'o'):
        raise HTTPException(400, "Invalid mode. Use 'bb' or 'o'.")
    
    status = await generate_status(mode)
    await save_report(status)
    return status

@app.get("/api/camera")
async def api_get_camera(token: str = Depends(verify_token)):
    """Get active camera"""
    active = await get_active_camera()
    return {"active": active, "timestamp": datetime.now().isoformat()}

@app.post("/api/camera/{target}")
async def api_switch_camera(target: str, token: str = Depends(verify_token)):
    """Switch camera"""
    if target not in ('pi4', 'noir'):
        raise HTTPException(400, "Invalid target. Use 'pi4' or 'noir'.")
    
    result = await switch_camera(target)
    return result

@app.get("/api/reports")
async def api_list_reports(limit: int = 30, token: str = Depends(verify_token)):
    """List recent reports"""
    reports = sorted(REPORTS_DIR.glob("*.json"), reverse=True)[:limit]
    
    report_list = []
    for r in reports:
        with open(r) as f:
            data = json.load(f)
            report_list.append({
                'filename': r.name,
                'timestamp': data.get('timestamp', ''),
                'mode': data.get('mode', ''),
                'success': data.get('success', False)
            })
    
    return {"reports": report_list}

@app.get("/api/reports/{filename}")
async def api_get_report(filename: str, token: str = Depends(verify_token)):
    """Get specific report"""
    filepath = REPORTS_DIR / filename
    if not filepath.exists() or not filename.endswith('.json'):
        raise HTTPException(404, "Report not found")
    
    with open(filepath) as f:
        return json.load(f)

@app.get("/api/logs")
async def api_get_logs(service: Optional[str] = None, lines: int = 50, token: str = Depends(verify_token)):
    """Get system logs"""
    if service:
        if service.startswith('docker:'):
            container = service.split(':', 1)[1]
            log_lines = await get_docker_logs(container, lines)
        else:
            log_lines = await get_service_logs(service, lines)
        return {"service": service, "logs": log_lines}
    else:
        logs = await aggregate_logs(lines)
        return {"logs": logs}

@app.get("/api/logs/stream")
async def api_logs_stream(token: str = Depends(verify_token)):
    """Stream logs via Server-Sent Events"""
    async def event_generator():
        while True:
            logs = await aggregate_logs(10)
            yield f"data: {json.dumps(logs)}\n\n"
            await asyncio.sleep(5)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
