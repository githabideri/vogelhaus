#!/usr/bin/env python3
"""
Add live report streaming to app.py
"""

def patch_for_live_reporting():
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Add SSE import
    if 'from fastapi.responses import StreamingResponse' not in content:
        print("⚠️  StreamingResponse already imported")
    
    # Add live report endpoint before "if __name__"
    live_report_endpoint = '''
@app.get("/internal/status/{mode}/stream")
async def internal_status_stream(mode: str):
    """Stream status generation live (Server-Sent Events)"""
    if mode not in ('bb', 'o'):
        raise HTTPException(400, "Invalid mode")
    
    async def event_stream():
        import asyncio
        
        # Start status script
        proc = await asyncio.create_subprocess_exec(
            STATUS_SCRIPT, mode,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        # Stream output line by line
        async for line in proc.stdout:
            line_text = line.decode('utf-8')
            # Skip FOTO_ lines (internal metadata)
            if not line_text.startswith('FOTO_'):
                yield f"data: {line_text}\\n\\n"
        
        await proc.wait()
        
        # Signal completion
        yield f"data: __COMPLETE__\\n\\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

'''
    
    # Insert before "if __name__"
    if '/internal/status/{mode}/stream' not in content:
        content = content.replace(
            '\nif __name__ == "__main__":',
            live_report_endpoint + '\nif __name__ == "__main__":'
        )
        
        with open('app.py', 'w') as f:
            f.write(content)
        print("✅ Added /internal/status/{mode}/stream endpoint")
    else:
        print("⚠️  Live streaming endpoint already exists")

if __name__ == '__main__':
    patch_for_live_reporting()
