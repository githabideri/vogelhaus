#!/usr/bin/env python3
"""
Patch script to add streaming controls + timezone fix to app.py
"""

import re

def patch_app_py():
    with open('app.py', 'r') as f:
        content = f.read()
    
    # 1. Add zoneinfo import
    content = content.replace(
        'from datetime import datetime, timedelta',
        'from datetime import datetime, timedelta\nfrom zoneinfo import ZoneInfo'
    )
    
    # 2. Fix all datetime.now() calls to use Vienna timezone
    content = re.sub(
        r"datetime\.now\(\)\.isoformat\(\)",
        "datetime.now(ZoneInfo('Europe/Vienna')).isoformat()",
        content
    )
    content = re.sub(
        r"datetime\.now\(\)\.strftime\(",
        "datetime.now(ZoneInfo('Europe/Vienna')).strftime(",
        content
    )
    
    # 3. Add streaming control endpoints before "if __name__"
    streaming_functions = '''
@app.get("/internal/streaming/status")
async def internal_streaming_status():
    """Check if Twitch stream is running"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'restreamer', 'ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'rtmp://live.twitch.tv' in result.stdout:
            return {"status": "live"}
        else:
            return {"status": "offline"}
    except:
        return {"status": "unknown"}

@app.post("/internal/streaming/{action}")
async def internal_streaming_control(action: str):
    """Start or stop Twitch streaming"""
    if action not in ('start', 'stop'):
        raise HTTPException(400, "Invalid action")
    
    process_id = "restreamer-ui:egress:twitch:16ee3bc7-a98d-421c-9863-83c693ba4c0a"
    
    try:
        # Build JSON payload
        json_payload = '{"command":"' + action + '"}'
        url = f"http://localhost:8080/api/v3/process/{process_id}/command"
        
        # Build wget command as list (avoid shell escaping hell)
        wget_args = [
            "wget", "-q", "-O-",
            "--user=admin",
            "--password=duhundduvogl",
            "--header=Content-Type: application/json",
            f"--post-data={json_payload}",
            url
        ]
        
        # Execute via docker exec
        result = subprocess.run(
            ["docker", "exec", "restreamer"] + wget_args,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {"success": True, "message": f"Streaming {action}ed"}
        else:
            return {"success": False, "message": f"Failed: {result.stderr}"}
    except Exception as e:
        raise HTTPException(500, str(e))

'''
    
    # Insert before "if __name__"
    content = content.replace(
        '\nif __name__ == "__main__":',
        streaming_functions + '\nif __name__ == "__main__":'
    )
    
    with open('app.py', 'w') as f:
        f.write(content)
    
    print("✅ Patched app.py successfully")
    print("   - Added zoneinfo import")
    print("   - Fixed datetime to use Europe/Vienna")
    print("   - Added /internal/streaming/status")
    print("   - Added /internal/streaming/{action}")

if __name__ == '__main__':
    patch_app_py()
