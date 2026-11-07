"""Embedded web dashboard server for JARVIS."""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from pathlib import Path
from typing import Tuple

from src.config import config
from src.logger import get_logger

logger = get_logger("WebDashboard")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>JARVIS AI Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --sidebar: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --primary: #ef4444;
      --accent: #38bdf8;
      --bubble-user: #1e1b4b;
      --bubble-bot: #dc2626;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', sans-serif;
      display: flex;
      height: 100vh;
      overflow: hidden;
    }
    .sidebar {
      width: 320px;
      background: var(--sidebar);
      border-right: 1px solid var(--border);
      padding: 30px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      z-index: 10;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, var(--primary), #b91c1c);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: white;
      font-size: 20px;
      box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
    }
    .brand-title {
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }
    .brand-title span { color: var(--primary); }
    .btn-action {
      background: var(--card-bg);
      color: var(--text-main);
      border: 1px solid var(--border);
      padding: 14px 18px;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .btn-action:hover {
      background: #273549;
      border-color: var(--accent);
      transform: translateY(-1px);
    }
    .status-panel {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .status-header {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-sub);
    }
    .status-body {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 16px;
      font-weight: 600;
    }
    .status-indicator {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 12px #10b981;
      transition: all 0.3s ease;
    }
    .status-listening .status-indicator {
      background: #38bdf8;
      box-shadow: 0 0 16px #38bdf8;
      animation: pulse 1.5s infinite;
    }
    .status-speaking .status-indicator {
      background: #ef4444;
      box-shadow: 0 0 16px #ef4444;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.3); opacity: 0.8; }
    }
    .meta-card {
      margin-top: auto;
      background: #0b1120;
      border: 1px solid #1e293b;
      border-radius: 10px;
      padding: 14px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: var(--text-sub);
      line-height: 1.6;
    }
    .chat-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow-y: auto;
      padding: 40px;
      gap: 20px;
    }
    .message-bubble {
      max-width: 70%;
      padding: 18px 24px;
      border-radius: 20px;
      font-size: 15px;
      line-height: 1.6;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
      animation: fadeIn 0.25s ease-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .message-user {
      align-self: flex-end;
      background: #1e1b4b;
      border: 1px solid #3730a3;
      color: #e0e7ff;
      border-bottom-right-radius: 4px;
    }
    .message-jarvis {
      align-self: flex-start;
      background: linear-gradient(145deg, #ef4444, #dc2626);
      color: #ffffff;
      border-bottom-left-radius: 4px;
    }
    .empty-state {
      margin: auto;
      text-align: center;
      color: var(--text-sub);
      max-width: 400px;
    }
    .empty-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }
  </style>
</head>
<body>
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-logo">J</div>
      <div class="brand-title">AI <span>JARVIS</span></div>
    </div>
    <button class="btn-action" onclick="resetConversation()">
      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
      New Conversation
    </button>
    <div class="status-panel" id="statusPanel">
      <div class="status-header">System State</div>
      <div class="status-body">
        <div class="status-indicator"></div>
        <span id="statusLabel">Idle</span>
      </div>
    </div>
    <div class="meta-card">
      <div>Engine: Deepgram Nova-2</div>
      <div>Audio: PipeWire 16kHz</div>
      <div>Platform: Arch Linux</div>
    </div>
  </aside>

  <main class="chat-wrapper" id="chatContainer">
    <div class="empty-state">
      <div class="empty-icon">🎙️</div>
      <h2>Listening for voice...</h2>
      <p style="margin-top: 8px; font-size: 14px;">Speak into your microphone. JARVIS will transcribe, process, and respond verbally.</p>
    </div>
  </main>

  <script>
    let cachedJson = "";
    async function syncState() {
      try {
        const res = await fetch('/api/state');
        const data = await res.json();
        
        // Update status indicator
        document.getElementById('statusLabel').innerText = data.status || 'Idle';
        const panel = document.getElementById('statusPanel');
        panel.className = 'status-panel';
        const st = (data.status || '').toLowerCase();
        if (st.includes('listening')) panel.classList.add('status-listening');
        else if (st.includes('speaking')) panel.classList.add('status-speaking');

        // Update messages
        const jsonStr = JSON.stringify(data.conversation);
        if (jsonStr !== cachedJson) {
          cachedJson = jsonStr;
          const container = document.getElementById('chatContainer');
          if (!data.conversation || data.conversation.length === 0) {
            container.innerHTML = `
              <div class="empty-state">
                <div class="empty-icon">🎙️</div>
                <h2>Listening for voice...</h2>
                <p style="margin-top: 8px; font-size: 14px;">Speak into your microphone. JARVIS will transcribe, process, and respond verbally.</p>
              </div>`;
            return;
          }
          container.innerHTML = '';
          data.conversation.forEach((msg, idx) => {
            if (!msg.trim()) return;
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble ' + (idx % 2 === 0 ? 'message-user' : 'message-jarvis');
            bubble.innerText = msg;
            container.appendChild(bubble);
          });
          container.scrollTop = container.scrollHeight;
        }
      } catch (e) {
        console.error(e);
      }
    }

    async function resetConversation() {
      await fetch('/api/clear', { method: 'POST' });
      cachedJson = "";
      syncState();
    }

    setInterval(syncState, 400);
    syncState();
  </script>
</body>
</html>
"""


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request handler for the JARVIS dashboard."""

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif self.path == "/api/state":
            status = "Idle"
            if Path("status.txt").exists():
                status = Path("status.txt").read_text(encoding="utf-8").strip() or "Idle"

            conversation = []
            if Path("conv.txt").exists():
                conversation = [
                    line.strip()
                    for line in Path("conv.txt").read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": status, "conversation": conversation}).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/clear":
            Path("conv.txt").write_text("", encoding="utf-8")
            Path("status.txt").write_text("Idle", encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"success": true}')
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Silence access logs to keep terminal readable
        return


def run_server(host: str = config.web_host, port: int = config.web_port):
    """Starts the dashboard server."""
    try:
        server = HTTPServer((host, port), DashboardRequestHandler)
        logger.info(f"Dashboard available at http://localhost:{port}")
        server.serve_forever()
    except OSError as e:
        if e.errno == 98:
            logger.info(f"Dashboard is already active on http://localhost:{port}")
        else:
            logger.error(f"Failed to start dashboard: {e}")
    except KeyboardInterrupt:
        logger.info("Stopping dashboard server.")
