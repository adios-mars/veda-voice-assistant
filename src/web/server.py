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
  <title>J.A.R.V.I.S. // Stark Industries Tactical HUD</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #050811;
      --panel-bg: rgba(10, 16, 30, 0.75);
      --border-cyan: rgba(0, 240, 255, 0.25);
      --cyan: #00f0ff;
      --cyan-glow: 0 0 20px rgba(0, 240, 255, 0.6);
      --red: #ef4444;
      --red-glow: 0 0 20px rgba(239, 68, 68, 0.7);
      --amber: #f59e0b;
      --text: #e2e8f0;
      --text-dim: #64748b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Rajdhani', sans-serif;
      height: 100vh;
      overflow: hidden;
      display: flex;
      background-image: 
        radial-gradient(circle at 50% 30%, rgba(0, 240, 255, 0.08) 0%, transparent 60%),
        linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
      background-size: 100% 100%, 40px 40px, 40px 40px;
    }

    /* Left HUD Panel: Arc Reactor & Telemetry */
    .hud-left {
      width: 440px;
      height: 100vh;
      background: var(--panel-bg);
      backdrop-filter: blur(16px);
      border-right: 1px solid var(--border-cyan);
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 24px;
      gap: 24px;
      position: relative;
      box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5);
    }
    .hud-header {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border-cyan);
      padding-bottom: 16px;
    }
    .stark-brand {
      font-family: 'Orbitron', sans-serif;
      font-weight: 900;
      font-size: 22px;
      letter-spacing: 2px;
      color: var(--cyan);
      text-shadow: var(--cyan-glow);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .stark-sub {
      font-size: 11px;
      letter-spacing: 3px;
      color: var(--text-dim);
      font-weight: 600;
    }
    .protocol-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      background: rgba(0, 240, 255, 0.1);
      border: 1px solid var(--cyan);
      color: var(--cyan);
      padding: 4px 8px;
      border-radius: 4px;
      letter-spacing: 1px;
    }

    /* ARC REACTOR VISUALIZER */
    .reactor-container {
      position: relative;
      width: 240px;
      height: 240px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 10px 0;
    }
    .reactor-ring-outer {
      position: absolute;
      width: 230px;
      height: 230px;
      border: 2px dashed rgba(0, 240, 255, 0.4);
      border-radius: 50%;
      animation: rotateRing 20s linear infinite;
    }
    .reactor-ring-mid {
      position: absolute;
      width: 180px;
      height: 180px;
      border: 3px solid rgba(0, 240, 255, 0.6);
      border-top-color: transparent;
      border-bottom-color: transparent;
      border-radius: 50%;
      animation: rotateRingRev 10s linear infinite;
    }
    .reactor-core {
      position: absolute;
      width: 110px;
      height: 110px;
      border-radius: 50%;
      background: radial-gradient(circle, #ffffff 0%, var(--cyan) 50%, rgba(0, 240, 255, 0.2) 100%);
      box-shadow: 0 0 40px var(--cyan), inset 0 0 20px #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      animation: coreBreath 3s ease-in-out infinite;
      transition: all 0.4s ease;
    }
    .reactor-inner-icon {
      font-family: 'Orbitron', sans-serif;
      font-size: 28px;
      font-weight: 900;
      color: #050811;
      text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
    }

    /* State Visual Variants */
    .state-listening .reactor-core {
      background: radial-gradient(circle, #ffffff 0%, #38bdf8 50%, rgba(56, 189, 248, 0.4) 100%);
      box-shadow: 0 0 60px #38bdf8, inset 0 0 30px #ffffff;
      animation: pulseFast 1s ease-in-out infinite;
    }
    .state-processing .reactor-core {
      background: radial-gradient(circle, #ffffff 0%, var(--amber) 50%, rgba(245, 158, 11, 0.3) 100%);
      box-shadow: 0 0 60px var(--amber), inset 0 0 30px #ffffff;
      animation: rotateRing 1.5s linear infinite;
    }
    .state-speaking .reactor-core {
      background: radial-gradient(circle, #ffffff 0%, var(--red) 50%, rgba(239, 68, 68, 0.4) 100%);
      box-shadow: 0 0 70px var(--red), inset 0 0 30px #ffffff;
      animation: pulseFast 0.8s ease-in-out infinite;
    }

    @keyframes rotateRing {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    @keyframes rotateRingRev {
      from { transform: rotate(360deg); }
      to { transform: rotate(0deg); }
    }
    @keyframes coreBreath {
      0%, 100% { transform: scale(1); opacity: 0.9; }
      50% { transform: scale(1.05); opacity: 1; }
    }
    @keyframes pulseFast {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.12); }
    }

    /* Audio Equalizer Bars */
    .equalizer-bar-box {
      display: flex;
      align-items: center;
      gap: 5px;
      height: 36px;
      margin-bottom: 5px;
    }
    .eq-bar {
      width: 4px;
      height: 8px;
      background: var(--cyan);
      border-radius: 2px;
      transition: height 0.1s ease;
      box-shadow: 0 0 8px var(--cyan);
    }

    /* Status Banner */
    .status-hud-card {
      width: 100%;
      background: rgba(0, 240, 255, 0.05);
      border: 1px solid var(--border-cyan);
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      text-align: center;
    }
    .status-title {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 2px;
      color: var(--text-dim);
      text-transform: uppercase;
    }
    .status-text {
      font-family: 'Orbitron', sans-serif;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 1.5px;
      color: var(--cyan);
      text-shadow: var(--cyan-glow);
      transition: all 0.3s ease;
    }
    .state-listening .status-text { color: #38bdf8; text-shadow: 0 0 15px #38bdf8; }
    .state-processing .status-text { color: var(--amber); text-shadow: 0 0 15px var(--amber); }
    .state-speaking .status-text { color: var(--red); text-shadow: var(--red-glow); }

    /* Telemetry Info */
    .telemetry-grid {
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      margin-top: auto;
    }
    .telem-item {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 6px;
      padding: 10px;
    }
    .telem-label { color: var(--text-dim); margin-bottom: 2px; font-size: 10px; }
    .telem-val { color: var(--cyan); font-weight: 600; }

    .btn-clear {
      width: 100%;
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #fca5a5;
      font-family: 'Orbitron', sans-serif;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 1px;
      padding: 12px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s;
    }
    .btn-clear:hover {
      background: rgba(239, 68, 68, 0.25);
      border-color: var(--red);
      color: #ffffff;
      box-shadow: var(--red-glow);
    }

    /* Right Main Panel: Holographic Conversation */
    .hud-main {
      flex: 1;
      height: 100vh;
      display: flex;
      flex-direction: column;
      position: relative;
    }
    .main-topbar {
      padding: 24px 40px;
      border-bottom: 1px solid rgba(0, 240, 255, 0.15);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(5, 8, 17, 0.8);
      backdrop-filter: blur(8px);
    }
    .topbar-title {
      font-family: 'Orbitron', sans-serif;
      font-size: 16px;
      letter-spacing: 2px;
      color: var(--text);
    }
    .topbar-title span { color: var(--cyan); }
    .companion-tag {
      font-size: 13px;
      color: #f472b6;
      font-weight: 600;
      letter-spacing: 1px;
    }

    .conversation-log {
      flex: 1;
      overflow-y: auto;
      padding: 30px 40px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      scroll-behavior: smooth;
    }
    .conversation-log::-webkit-scrollbar { width: 6px; }
    .conversation-log::-webkit-scrollbar-thumb {
      background: rgba(0, 240, 255, 0.2);
      border-radius: 3px;
    }

    .bubble {
      max-width: 72%;
      padding: 16px 22px;
      border-radius: 12px;
      font-size: 16px;
      line-height: 1.6;
      position: relative;
      animation: slideIn 0.25s ease-out;
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .bubble-author {
      font-family: 'Orbitron', sans-serif;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.5px;
      margin-bottom: 6px;
      text-transform: uppercase;
    }

    /* Ruth / User Message */
    .bubble-user {
      align-self: flex-end;
      background: linear-gradient(135deg, rgba(30, 27, 75, 0.8), rgba(49, 46, 129, 0.8));
      border: 1px solid rgba(129, 140, 248, 0.4);
      color: #e0e7ff;
      border-bottom-right-radius: 2px;
      box-shadow: 0 4px 20px rgba(49, 46, 129, 0.25);
    }
    .bubble-user .bubble-author { color: #a5b4fc; }

    /* JARVIS Message */
    .bubble-jarvis {
      align-self: flex-start;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(185, 28, 28, 0.25));
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #ffffff;
      border-bottom-left-radius: 2px;
      box-shadow: 0 4px 25px rgba(239, 68, 68, 0.15);
    }
    .bubble-jarvis .bubble-author { color: #f87171; }

    .empty-state {
      margin: auto;
      text-align: center;
      max-width: 440px;
    }
    .empty-title {
      font-family: 'Orbitron', sans-serif;
      font-size: 20px;
      color: var(--cyan);
      margin-bottom: 10px;
      letter-spacing: 1px;
    }
    .empty-desc {
      color: var(--text-dim);
      font-size: 15px;
      line-height: 1.6;
    }
  </style>
</head>
<body id="hudBody">
  <!-- Left Telemetry & Arc Reactor Column -->
  <aside class="hud-left">
    <div class="hud-header">
      <div>
        <div class="stark-brand">J.A.R.V.I.S.</div>
        <div class="stark-sub">TACTICAL VOICE OS</div>
      </div>
      <div class="protocol-tag">SYS-v2.5</div>
    </div>

    <!-- Arc Reactor -->
    <div class="reactor-container">
      <div class="reactor-ring-outer"></div>
      <div class="reactor-ring-mid"></div>
      <div class="reactor-core">
        <div class="reactor-inner-icon">AI</div>
      </div>
    </div>

    <!-- Live Audio Equalizer -->
    <div class="equalizer-bar-box" id="eqBox">
      <div class="eq-bar" style="height: 10px;"></div>
      <div class="eq-bar" style="height: 18px;"></div>
      <div class="eq-bar" style="height: 28px;"></div>
      <div class="eq-bar" style="height: 14px;"></div>
      <div class="eq-bar" style="height: 24px;"></div>
      <div class="eq-bar" style="height: 32px;"></div>
      <div class="eq-bar" style="height: 19px;"></div>
      <div class="eq-bar" style="height: 12px;"></div>
      <div class="eq-bar" style="height: 26px;"></div>
      <div class="eq-bar" style="height: 15px;"></div>
    </div>

    <!-- Status Display -->
    <div class="status-hud-card">
      <div class="status-title">Core Subsystem Status</div>
      <div class="status-text" id="statusLabel">ONLINE</div>
    </div>

    <!-- Telemetry -->
    <div class="telemetry-grid">
      <div class="telem-item">
        <div class="telem-label">AI BRAIN</div>
        <div class="telem-val">Gemini 3.5 Lite</div>
      </div>
      <div class="telem-item">
        <div class="telem-label">VOICE RECOG</div>
        <div class="telem-val">Deepgram Nova-2</div>
      </div>
      <div class="telem-item">
        <div class="telem-label">SYNTHESIS</div>
        <div class="telem-val">Edge Neural</div>
      </div>
      <div class="telem-item">
        <div class="telem-label">AUDIO HOST</div>
        <div class="telem-val">PipeWire 16kHz</div>
      </div>
    </div>

    <button class="btn-clear" onclick="resetConversation()">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
      CLEAR COMMS LOG
    </button>
  </aside>

  <!-- Right Holographic Conversation Log -->
  <main class="hud-main">
    <div class="main-topbar">
      <div class="topbar-title">TACTICAL COMMS // <span>LIVE CHANNEL</span></div>
      <div class="companion-tag">PRIMARY USER: RUTH</div>
    </div>

    <div class="conversation-log" id="chatContainer">
      <div class="empty-state">
        <div class="empty-title">Awaiting Voice Transmission</div>
        <div class="empty-desc">Speak naturally into your microphone. J.A.R.V.I.S. is listening and will transcribe and respond in real-time.</div>
      </div>
    </div>
  </main>

  <script>
    let cachedJson = "";
    const bars = document.querySelectorAll('.eq-bar');

    function animateEqualizer(isActive) {
      bars.forEach(bar => {
        if (isActive) {
          const h = Math.floor(Math.random() * 30) + 6;
          bar.style.height = h + 'px';
        } else {
          bar.style.height = '6px';
        }
      });
    }

    async function syncState() {
      try {
        const res = await fetch('/api/state');
        const data = await res.json();
        
        const rawStatus = data.status || 'Idle';
        document.getElementById('statusLabel').innerText = rawStatus.toUpperCase();

        const body = document.getElementById('hudBody');
        body.className = '';
        const st = rawStatus.toLowerCase();
        
        let isActive = false;
        if (st.includes('listen')) {
          body.classList.add('state-listening');
          isActive = true;
        } else if (st.includes('process')) {
          body.classList.add('state-processing');
          isActive = true;
        } else if (st.includes('speak')) {
          body.classList.add('state-speaking');
          isActive = true;
        }

        animateEqualizer(isActive);

        // Update conversation
        const jsonStr = JSON.stringify(data.conversation);
        if (jsonStr !== cachedJson) {
          cachedJson = jsonStr;
          const container = document.getElementById('chatContainer');
          if (!data.conversation || data.conversation.length === 0) {
            container.innerHTML = `
              <div class="empty-state">
                <div class="empty-title">Awaiting Voice Transmission</div>
                <div class="empty-desc">Speak naturally into your microphone. J.A.R.V.I.S. is listening and will transcribe and respond in real-time.</div>
              </div>`;
            return;
          }
          container.innerHTML = '';
          data.conversation.forEach((msg, idx) => {
            if (!msg.trim()) return;
            const bubble = document.createElement('div');
            const isUser = (idx % 2 === 0);
            bubble.className = 'bubble ' + (isUser ? 'bubble-user' : 'bubble-jarvis');
            
            const author = document.createElement('div');
            author.className = 'bubble-author';
            author.innerText = isUser ? 'RUTH' : 'J.A.R.V.I.S.';
            
            const text = document.createElement('div');
            text.innerText = msg;
            
            bubble.appendChild(author);
            bubble.appendChild(text);
            container.appendChild(bubble);
          });
          container.scrollTop = container.scrollHeight;
        }
      } catch (e) {
        console.error("HUD Sync Error:", e);
      }
    }

    async function resetConversation() {
      await fetch('/api/clear', { method: 'POST' });
      cachedJson = "";
      syncState();
    }

    setInterval(syncState, 350);
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
