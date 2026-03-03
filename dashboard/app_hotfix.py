#!/usr/bin/env python3
"""
Hotfix for dashboard - adds internal endpoints without auth
"""

# Quick fixes to add after imports in app.py:

INTERNAL_ENDPOINTS = """
# ============================================================
# INTERNAL ROUTES (NO AUTH) - For Web UI only
# ============================================================

@app.get("/internal/status/{mode}")
async def internal_status(mode: str):
    '''Generate status without auth (localhost only)'''
    if mode not in ('bb', 'o'):
        raise HTTPException(400, "Invalid mode")
    status = await generate_status(mode)
    await save_report(status)
    return {"text": status.get('text', 'Error')}

@app.get("/internal/camera")
async def internal_get_camera():
    '''Get active camera without auth'''
    active = await get_active_camera()
    return {"active": active}

@app.post("/internal/camera/{target}")
async def internal_switch_camera(target: str):
    '''Switch camera without auth'''
    if target not in ('pi4', 'noir'):
        raise HTTPException(400, "Invalid target")
    result = await switch_camera(target)
    return result

@app.get("/internal/logs")
async def internal_logs(service: Optional[str] = None, lines: int = 50):
    '''Get logs without auth'''
    if service:
        if service.startswith('docker:'):
            container = service.split(':', 1)[1]
            log_lines = await get_docker_logs(container, lines)
        else:
            log_lines = await get_service_logs(service, lines)
        return {"logs": log_lines}
    else:
        logs = await aggregate_logs(lines)
        return logs
"""

print(INTERNAL_ENDPOINTS)
