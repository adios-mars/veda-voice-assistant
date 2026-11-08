"""Embedded web dashboard server for Veda."""
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
  <title>Veda - Here to listen, ready to help</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { font-family: 'Plus Jakarta Sans', sans-serif; }

    body {
      background-color: #0c0c0e;
      background-image: radial-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px);
      background-size: 24px 24px;
    }

    .mic-active {
      color: #38bdf8 !important;
      animation: micPulse 1.2s ease-in-out infinite;
    }
    @keyframes micPulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.25); opacity: 0.7; }
    }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.12); border-radius: 4px; }
  </style>
</head>
<body class="text-zinc-100 min-h-screen flex items-center justify-center p-4 antialiased selection:bg-blue-500/30">
  
  <div class="w-full max-w-2xl flex flex-col justify-between py-8 px-2 min-h-[560px]">

    <!-- Brand Header -->
    <div class="flex flex-col items-center justify-center text-center mb-7">
      <div class="flex items-center gap-2.5 mb-1.5">
        <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
        </svg>
        <h1 class="text-2xl font-bold text-white tracking-tight">Veda</h1>
      </div>
      <p class="text-xs text-zinc-400 font-normal">Here to listen, ready to help</p>
    </div>

    <!-- Live Conversation Stream -->
    <div id="chatStream" class="flex-1 flex flex-col gap-3 overflow-y-auto max-h-64 mb-4 px-1 hidden scroll-smooth">
    </div>

    <!-- Central Input Box (Matches user reference) -->
    <div class="bg-[#17171a] border border-white/[0.08] rounded-[24px] p-4 shadow-2xl transition focus-within:border-white/20 mb-5">
      <!-- Input Area -->
      <div class="mb-3 px-1">
        <textarea 
          id="promptInput" 
          rows="2" 
          placeholder="Ask anything..." 
          class="w-full bg-transparent border-none outline-none resize-none text-sm text-zinc-100 placeholder-zinc-500 leading-relaxed"
          onkeydown="if(event.key==='Enter' && !event.shiftKey){ event.preventDefault(); handleSendText(); }"
        ></textarea>
      </div>

      <!-- Bottom Card Toolbar -->
      <div class="flex items-center justify-between pt-2 border-t border-white/[0.05] text-xs">
        <!-- Left Toolbar Items -->
        <div class="flex items-center gap-2">
          <!-- New Chat / Clear Button -->
          <button onclick="resetConversation()" title="New Chat / Clear Conversation" class="w-7 h-7 rounded-lg bg-zinc-800/80 hover:bg-zinc-700/80 text-zinc-400 hover:text-white flex items-center justify-center transition">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
          </button>

          <!-- Companion Status Pill -->
          <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-800/60 text-zinc-300 font-medium select-none">
            <svg class="w-3.5 h-3.5 text-zinc-400" fill="currentColor" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            <span class="text-xs font-medium">Companion</span>
            <span id="companionBadge" class="text-[10px] text-blue-400 font-semibold px-1.5 py-0.5 rounded bg-blue-500/10 ml-0.5 transition">Live</span>
          </div>
        </div>

        <!-- Right Toolbar Items: Model Selector, Mic, Blue Send Button -->
        <div class="flex items-center gap-2.5">
          <!-- Model selector pill with orange starburst -->
          <div class="flex items-center gap-1.5 text-zinc-300 hover:text-white px-2.5 py-1 rounded-lg bg-zinc-800/50 cursor-pointer transition select-none">
            <svg class="w-3 h-3 text-orange-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14"/>
            </svg>
            <span class="text-xs font-medium">Gemini 3.5</span>
            <svg class="w-3 h-3 text-zinc-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>
          </div>
          
          <!-- Microphone indicator -->
          <div id="micIcon" class="text-zinc-400 p-1 transition cursor-pointer" title="Microphone Active">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
          </div>

          <!-- Circular Blue Send Button with white up arrow -->
          <button onclick="handleSendText()" title="Send Message" class="w-7 h-7 rounded-full bg-[#0084ff] hover:bg-blue-600 active:scale-95 text-white flex items-center justify-center transition shadow-md shadow-blue-500/25">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom 3 Action Cards (Exact user preference) -->
    <div class="grid grid-cols-3 gap-3">
      <!-- Card 1: Talk & Vent -->
      <div onclick="quickSend('I need someone to talk to and vent a little.')" class="bg-[#17171a] hover:bg-[#202024] border border-white/[0.06] rounded-2xl p-4 flex flex-col justify-between transition cursor-pointer group shadow-sm min-h-[96px]">
        <div class="text-zinc-400 group-hover:text-white mb-3 transition">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
        </div>
        <div>
          <div class="text-xs font-semibold text-white tracking-tight">Talk & Vent</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Share what is on your mind</div>
        </div>
      </div>

      <!-- Card 2: Find Solutions -->
      <div onclick="quickSend('Help me brainstorm a solution to a problem.')" class="bg-[#17171a] hover:bg-[#202024] border border-white/[0.06] rounded-2xl p-4 flex flex-col justify-between transition cursor-pointer group shadow-sm min-h-[96px]">
        <div class="text-zinc-400 group-hover:text-white mb-3 transition">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 8V6a2 2 0 0 1 2-2h2"/>
            <path d="M16 4h2a2 2 0 0 1 2 2v2"/>
            <path d="M20 16v2a2 2 0 0 1-2 2h-2"/>
            <path d="M8 20H6a2 2 0 0 1-2-2v-2"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </div>
        <div>
          <div class="text-xs font-semibold text-white tracking-tight">Find Solutions</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Answers, ideas & advice</div>
        </div>
      </div>

      <!-- Card 3: Ask Anything -->
      <div onclick="quickSend('I have a question: ')" class="bg-[#17171a] hover:bg-[#202024] border border-white/[0.06] rounded-2xl p-4 flex flex-col justify-between transition cursor-pointer group shadow-sm min-h-[96px]">
        <div class="text-zinc-400 group-hover:text-white mb-3 transition">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
            <path d="M2 12h20"/>
          </svg>
        </div>
        <div>
          <div class="text-xs font-semibold text-white tracking-tight">Ask Anything</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Code, questions & facts</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let cachedJson = "";
    const micIcon = document.getElementById('micIcon');
    const promptInput = document.getElementById('promptInput');
    const companionBadge = document.getElementById('companionBadge');

    async function syncState() {
      try {
        const res = await fetch('/api/state');
        const data = await res.json();
        
        const rawStatus = (data.status || 'Idle').toLowerCase();
        
        // Update mic & status indicator
        if (rawStatus.includes('listen')) {
          micIcon.classList.add('mic-active');
          companionBadge.innerText = 'Listening';
          companionBadge.className = 'text-[10px] text-cyan-400 font-semibold px-1 py-0.2 rounded bg-cyan-500/10 ml-0.5 animate-pulse';
        } else if (rawStatus.includes('process')) {
          micIcon.classList.remove('mic-active');
          companionBadge.innerText = 'Thinking';
          companionBadge.className = 'text-[10px] text-amber-400 font-semibold px-1 py-0.2 rounded bg-amber-500/10 ml-0.5';
        } else if (rawStatus.includes('speak')) {
          micIcon.classList.remove('mic-active');
          companionBadge.innerText = 'Speaking';
          companionBadge.className = 'text-[10px] text-rose-400 font-semibold px-1 py-0.2 rounded bg-rose-500/10 ml-0.5';
        } else {
          micIcon.classList.remove('mic-active');
          companionBadge.innerText = 'Live';
          companionBadge.className = 'text-[10px] text-blue-400 font-semibold px-1 py-0.2 rounded bg-blue-500/10 ml-0.5';
        }

        // Render live conversation stream
        const jsonStr = JSON.stringify(data.conversation);
        if (jsonStr !== cachedJson) {
          cachedJson = jsonStr;
          const streamView = document.getElementById('chatStream');

          if (!data.conversation || data.conversation.length === 0) {
            streamView.classList.add('hidden');
            return;
          }

          streamView.classList.remove('hidden');
          streamView.innerHTML = '';

          data.conversation.forEach((msg, idx) => {
            if (!msg.trim()) return;
            const bubble = document.createElement('div');
            const isUser = (idx % 2 === 0);
            
            if (isUser) {
              bubble.className = 'bg-[#242428] border border-white/[0.06] rounded-2xl p-3 px-4 text-xs leading-relaxed self-end max-w-lg text-zinc-100 shadow-sm';
              bubble.innerHTML = `<div class="font-bold text-zinc-400 text-[10px] uppercase mb-0.5 tracking-wider">You</div><div>${escapeHtml(msg)}</div>`;
            } else {
              bubble.className = 'bg-[#18181b] border border-white/[0.08] rounded-2xl p-3 px-4 text-xs leading-relaxed self-start max-w-lg text-zinc-100 shadow-sm';
              bubble.innerHTML = `<div class="font-bold text-cyan-400 text-[10px] uppercase mb-0.5 tracking-wider">Veda</div><div>${escapeHtml(msg)}</div>`;
            }
            streamView.appendChild(bubble);
          });
          streamView.scrollTop = streamView.scrollHeight;
        }
      } catch (e) {
        console.error(e);
      }
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.innerText = text;
      return div.innerHTML;
    }

    async function resetConversation() {
      await fetch('/api/clear', { method: 'POST' });
      cachedJson = "";
      syncState();
    }

    async function handleSendText() {
      const val = promptInput.value.trim();
      if (!val) return;

      promptInput.value = '';
      try {
        await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: val })
        });
        syncState();
      } catch (err) {
        console.error('Send error:', err);
      }
    }

    function quickSend(prefix) {
      promptInput.value = prefix;
      promptInput.focus();
    }

    setInterval(syncState, 350);
    syncState();
  </script>
</body>
</html>
"""


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request handler for the Veda dashboard."""

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
        elif self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                user_msg = payload.get("message", "").strip()
                if user_msg:
                    with open("conv.txt", "a", encoding="utf-8") as f:
                        f.write(f"{user_msg}\n")
                    with open("status.txt", "w", encoding="utf-8") as f:
                        f.write("Processing...")

                    import threading
                    def _async_reply():
                        try:
                            from src.services.llm import get_llm_service
                            from src.services.tts import get_tts_service
                            from src.audio.player import AudioPlayer

                            llm = get_llm_service()
                            reply = llm.generate_reply([], user_msg)
                            with open("conv.txt", "a", encoding="utf-8") as f:
                                f.write(f"{reply}\n")

                            with open("status.txt", "w", encoding="utf-8") as f:
                                f.write("Speaking...")

                            tts = get_tts_service()
                            res_wav = config.audio.response_path
                            out = tts.synthesize(reply, res_wav)
                            if out and Path(out).exists():
                                AudioPlayer.play(res_wav)
                        except Exception as err:
                            logger.error(f"Chat processing error: {err}")
                        finally:
                            with open("status.txt", "w", encoding="utf-8") as f:
                                f.write("Idle")

                    threading.Thread(target=_async_reply, daemon=True).start()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"success": true}')
            except Exception as e:
                self.send_error(500, str(e))
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
