#!/usr/bin/env bash
# vogelhaus-web.sh — Generiert statische HTML-Statusseite + startet Mini-Webserver
# Aufruf: ~/scripts/vogelhaus-web.sh [port]
# Default Port: 8088
# Seite unter http://<pi4-ip>:8088/

set -uo pipefail

PORT="${1:-8088}"
WEB_DIR="/tmp/vogelhaus-web"
mkdir -p "$WEB_DIR/img"

generate_page() {
    # Run the local status script in o-mode, capture output
    local STATUS
    STATUS=$(~/scripts/vogelhaus-local.sh o 2>/dev/null)
    
    # Copy snapshots to web dir
    cp /tmp/vogelhaus-status/snap_pi4.jpg "$WEB_DIR/img/" 2>/dev/null
    cp /tmp/vogelhaus-status/snap_noir.jpg "$WEB_DIR/img/" 2>/dev/null
    
    local NOW=$(date -u +"%d.%m.%Y %H:%M:%S UTC")
    
    cat > "$WEB_DIR/index.html" << HTMLEOF
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🐦 Vogelhaus Status — K.u.K. Vogelhaus-Amt</title>
<style>
  :root { --bg: #1a1a2e; --card: #16213e; --accent: #e94560; --text: #eee; --dim: #8892a4; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Courier New', monospace; background: var(--bg); color: var(--text); padding: 1rem; max-width: 900px; margin: 0 auto; }
  h1 { text-align: center; color: var(--accent); margin-bottom: 0.5rem; font-size: 1.3rem; }
  .subtitle { text-align: center; color: var(--dim); margin-bottom: 1rem; font-size: 0.85rem; }
  .cameras { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1rem; }
  .cameras img { width: 100%; border-radius: 4px; border: 1px solid #333; }
  .cameras .label { text-align: center; color: var(--dim); font-size: 0.75rem; margin-top: 2px; }
  .status-block { background: var(--card); border-radius: 6px; padding: 1rem; margin-bottom: 1rem; white-space: pre-wrap; font-size: 0.8rem; line-height: 1.5; overflow-x: auto; }
  .actions { text-align: center; margin: 1rem 0; }
  .btn { background: var(--accent); color: white; border: none; padding: 0.6rem 1.5rem; border-radius: 4px; cursor: pointer; font-family: inherit; font-size: 0.9rem; margin: 0 0.3rem; }
  .btn:hover { opacity: 0.85; }
  .btn.secondary { background: #333; }
  .footer { text-align: center; color: var(--dim); font-size: 0.7rem; margin-top: 1rem; }
  @media (max-width: 600px) { .cameras { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<h1>🐦 K.u.K. Vogelhaus-Amt</h1>
<p class="subtitle">Standort „Thomas" — Aktualisiert: $NOW</p>

<div class="cameras">
  <div>
    <img src="img/snap_pi4.jpg?t=$(date +%s)" alt="Pi4 Hauptkamera" onerror="this.alt='Foto nicht verfügbar'">
    <div class="label">Hauptkamera (Pi 4, Top-Down)</div>
  </div>
  <div>
    <img src="img/snap_noir.jpg?t=$(date +%s)" alt="NoIR Nachtsicht" onerror="this.alt='Foto nicht verfügbar'">
    <div class="label">Nachtsicht (Pi Zero, NoIR)</div>
  </div>
</div>

<div class="status-block">$(echo "$STATUS" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')</div>

<div class="actions">
  <button class="btn" onclick="location.href='/refresh'">🔄 Aktualisieren</button>
  <a href="https://www.twitch.tv/<YOUR_TWITCH_CHANNEL>" target="_blank"><button class="btn secondary">📺 Twitch</button></a>
</div>

<div class="footer">K.u.K. Vogelhaus-Amt — Dienststellenautomation<br>Pi 4 (voglberry) | Port $PORT</div>
</body>
</html>
HTMLEOF
}

# ---- SIMPLE HTTP SERVER WITH REFRESH ----
# We use a tiny Python server that handles /refresh by regenerating
cat > "$WEB_DIR/server.py" << 'PYEOF'
import http.server
import subprocess
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
WEB_DIR = "/tmp/vogelhaus-web"
REFRESH_SCRIPT = os.path.expanduser("~/scripts/vogelhaus-web.sh")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)
    
    def do_GET(self):
        if self.path == '/refresh' or self.path == '/refresh/':
            # Regenerate the page
            subprocess.run([REFRESH_SCRIPT, str(PORT)], 
                         capture_output=True, timeout=120,
                         env={**os.environ, 'REGEN_ONLY': '1'})
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            super().do_GET()
    
    def log_message(self, format, *args):
        pass  # suppress logs

print(f"🐦 Vogelhaus-Status auf http://0.0.0.0:{PORT}/")
http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
PYEOF

# If REGEN_ONLY is set, just regenerate and exit
if [ "${REGEN_ONLY:-}" = "1" ]; then
    generate_page
    exit 0
fi

# Generate initial page
echo "Generiere Statusseite..." >&2
generate_page
echo "Starte Webserver auf Port $PORT..." >&2
exec python3 "$WEB_DIR/server.py" "$PORT"
