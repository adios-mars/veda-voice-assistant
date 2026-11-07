"""Modern, zero-dependency real-time web interface for JARVIS"""
import json
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse

PORT = 5000

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>JARVIS Assistant Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #0b0f19;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      height: 100vh;
      overflow: hidden;
    }
    .sidebar {
      width: 280px;
      background: #111827;
      border-right: 1px solid #1f2937;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .logo {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: 1px;
      color: #f3f4f6;
    }
    .logo span {
      color: #ff462b;
    }
    .btn-reset {
      background: #1f2937;
      color: #f9fafb;
      border: 1px solid #374151;
      padding: 12px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s;
    }
    .btn-reset:hover {
      background: #374151;
      border-color: #4b5563;
    }
    .status-card {
      background: #1e293b;
      border-radius: 8px;
      padding: 14px;
      border: 1px solid #334155;
    }
    .status-title {
      font-size: 12px;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
    }
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 600;
      font-size: 15px;
    }
    .pulse-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 10px #10b981;
    }
    .status-listening .pulse-dot { background: #3b82f6; box-shadow: 0 0 12px #3b82f6; }
    .status-speaking .pulse-dot { background: #ff462b; box-shadow: 0 0 12px #ff462b; }
    .chat-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow-y: auto;
      padding: 30px;
      gap: 18px;
    }
    .bubble {
      max-width: 75%;
      padding: 16px 20px;
      border-radius: 18px;
      font-size: 16px;
      line-height: 1.5;
      box-shadow: 0 4px 14px rgba(0,0,0,0.25);
      word-break: break-word;
    }
    .bubble.user {
      align-self: flex-end;
      background-color: #1e1b4b;
      border: 1px solid #312e81;
      color: #e0e7ff;
      border-bottom-right-radius: 4px;
    }
    .bubble.jarvis {
      align-self: flex-start;
      background-color: #ff462b;
      color: #ffffff;
      border-bottom-left-radius: 4px;
    }
    .empty-state {
      margin: auto;
      text-align: center;
      color: #64748b;
    }
  </style>
</head>
<body>
  <div class="sidebar">
    <div class="logo">AI <span>JARVIS</span></div>
    <button class="btn-reset" onclick="clearConv()">+ New Conversation</button>
    <div class="status-card" id="statusCard">
      <div class="status-title">Current State</div>
      <div class="status-indicator">
        <div class="pulse-dot"></div>
        <span id="statusText">Idle</span>
      </div>
    </div>
  </div>

  <div class="chat-container" id="chatBox">
    <div class="empty-state">
      <h3>Waiting for voice input...</h3>
      <p style="margin-top: 8px;">Run <code>python main.py</code> and speak into your microphone.</p>
    </div>
  </div>

  <script>
    let lastData = "";
    async function update() {
      try {
        const res = await fetch('/api/state');
        const data = await res.json();
        
        // Update status
        const statusEl = document.getElementById('statusText');
        statusEl.innerText = data.status || 'Idle';
        
        const card = document.getElementById('statusCard');
        card.className = 'status-card';
        if ((data.status || '').toLowerCase().includes('listening')) {
          card.classList.add('status-listening');
        } else if ((data.status || '').toLowerCase().includes('speaking')) {
          card.classList.add('status-speaking');
        }

        // Update chat
        const jsonStr = JSON.stringify(data.conversation);
        if (jsonStr !== lastData) {
          lastData = jsonStr;
          const chat = document.getElementById('chatBox');
          if (!data.conversation || data.conversation.length === 0) {
            chat.innerHTML = '<div class="empty-state"><h3>Waiting for voice input...</h3><p style="margin-top:8px;">Run <code>python main.py</code> and speak into your microphone.</p></div>';
            return;
          }
          chat.innerHTML = '';
          data.conversation.forEach((msg, idx) => {
            if (!msg.trim()) return;
            const bubble = document.createElement('div');
            bubble.className = 'bubble ' + (idx % 2 === 0 ? 'user' : 'jarvis');
            bubble.innerText = msg;
            chat.appendChild(bubble);
          });
          chat.scrollTop = chat.scrollHeight;
        }
      } catch (e) {
        console.error(e);
      }
    }

    async function clearConv() {
      await fetch('/api/clear', { method: 'POST' });
      lastData = "";
      update();
    }

    setInterval(update, 500);
    update();
  </script>
</body>
</html>
"""


class JarvisHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/state":
            status = "Idle"
            if os.path.exists("status.txt"):
                with open("status.txt", "r", encoding="utf-8") as f:
                    status = f.read().strip() or "Idle"
            conv = []
            if os.path.exists("conv.txt"):
                with open("conv.txt", "r", encoding="utf-8") as f:
                    conv = [line.strip() for line in f.readlines() if line.strip()]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": status, "conversation": conv}).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/clear":
            with open("conv.txt", "w", encoding="utf-8") as f:
                f.write("")
            with open("status.txt", "w", encoding="utf-8") as f:
                f.write("Idle")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"success": true}')
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Silence default HTTP access logs to keep terminal clean
        return


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), JarvisHandler)
    print(f"JARVIS Dashboard running at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
