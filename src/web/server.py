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
  <title>Syntrix // J.A.R.V.I.S.</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* 3D Iridescent Glass Sphere */
    .glass-orb {
      width: 78px;
      height: 78px;
      border-radius: 50%;
      background: radial-gradient(circle at 32% 28%, #ffffff 0%, #38ef7d 22%, #11998e 45%, #0284c7 72%, #0f172a 100%);
      box-shadow: 
        inset 0 0 15px rgba(255, 255, 255, 0.8),
        inset 0 -8px 18px rgba(2, 132, 199, 0.7),
        0 10px 30px rgba(17, 153, 142, 0.45),
        0 0 45px rgba(56, 239, 125, 0.3);
      position: relative;
      animation: orbFloat 4s ease-in-out infinite;
      transition: all 0.4s ease;
    }
    .glass-orb::before {
      content: '';
      position: absolute;
      top: 10px;
      left: 14px;
      width: 24px;
      height: 14px;
      border-radius: 50%;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0) 100%);
      transform: rotate(-25deg);
    }

    @keyframes orbFloat {
      0%, 100% { transform: translateY(0px) scale(1); }
      50% { transform: translateY(-6px) scale(1.02); }
    }

    .orb-listening {
      box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7), 0 0 45px rgba(56, 189, 248, 0.7) !important;
      animation: listeningPulse 1.3s ease-out infinite !important;
    }
    @keyframes listeningPulse {
      0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.8); }
      70% { transform: scale(1.08); box-shadow: 0 0 0 20px rgba(56, 189, 248, 0); }
      100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
    }

    .orb-processing {
      background: radial-gradient(circle at 32% 28%, #ffffff 0%, #fbbf24 22%, #d97706 45%, #78350f 72%, #0f172a 100%) !important;
      box-shadow: 0 0 40px rgba(245, 158, 11, 0.6) !important;
    }

    .orb-speaking {
      background: radial-gradient(circle at 32% 28%, #ffffff 0%, #f43f5e 22%, #e11d48 45%, #881337 72%, #0f172a 100%) !important;
      box-shadow: 0 0 45px rgba(244, 63, 94, 0.6) !important;
    }

    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.12); border-radius: 4px; }
  </style>
</head>
<body class="bg-[#080b11] text-slate-100 min-h-screen flex items-center justify-center p-6 antialiased selection:bg-cyan-500/30">
  
  <!-- Clean Floating Container (No fake login, no dead cards) -->
  <div class="w-full max-w-4xl rounded-[32px] bg-[#0c1017] border border-white/[0.08] shadow-[0_30px_90px_-20px_rgba(0,0,0,0.9)] overflow-hidden flex flex-col h-[680px] p-7 relative">
    
    <!-- Ambient Subtle Top Glow -->
    <div class="absolute -top-32 right-1/4 w-96 h-60 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>

    <!-- Minimal Header with New Conversation Tab -->
    <header class="flex items-center justify-between border-b border-white/[0.06] pb-4 mb-4 shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-full bg-gradient-to-tr from-teal-400 to-cyan-300 shadow-[0_0_12px_rgba(45,212,191,0.5)] flex items-center justify-center">
          <div class="w-2.5 h-2.5 rounded-full bg-white"></div>
        </div>
        <div>
          <span class="font-bold text-base tracking-tight text-white">Syntrix <span class="text-xs text-cyan-400 font-normal">// J.A.R.V.I.S.</span></span>
          <div class="text-[10px] text-slate-400">AI Companion & Problem Solver</div>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <span id="statusIndicator" class="text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Ready
        </span>
        <button onclick="resetConversation()" class="text-xs font-semibold text-slate-200 hover:text-white bg-[#18202e] hover:bg-[#222c3d] border border-white/[0.1] px-3.5 py-1.5 rounded-xl transition flex items-center gap-1.5 shadow-sm">
          <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
          New Conversation
        </button>
      </div>
    </header>

    <!-- Center Content / Conversation Stream -->
    <main class="flex-1 overflow-y-auto flex flex-col justify-between py-2" id="mainContainer">
      
      <!-- Living Orb Hero (Shown when idle/empty) -->
      <div id="orbHero" class="flex flex-col items-center justify-center my-auto text-center">
        <div class="glass-orb mb-4" id="centralOrb"></div>
        <div class="text-[11px] font-bold tracking-[0.25em] text-slate-400 uppercase mb-1">Your AI Companion</div>
        <h2 class="text-2xl font-bold tracking-tight text-white mb-2">How may I be of service today, Ma'am?</h2>
        <p class="text-xs text-slate-400 max-w-md">A loyal friend who listens when you need to talk, and an intelligence ready to solve any problem.</p>
      </div>

      <!-- Live Chat Messages -->
      <div id="chatStreamView" class="hidden flex-col gap-3.5 overflow-y-auto pr-2 my-auto max-h-[460px] scroll-smooth">
      </div>
    </main>

    <!-- Working Input Bar (Voice + Typing) -->
    <footer class="mt-4 shrink-0">
      <div class="bg-[#141a24] border border-white/[0.08] rounded-2xl p-2.5 px-4 flex items-center gap-3 shadow-2xl focus-within:border-cyan-500/40 transition">
        <span class="text-cyan-400 text-sm">✦</span>
        <input 
          id="promptInput" 
          type="text" 
          placeholder="Ask me anything... (or speak into your microphone)" 
          class="w-full bg-transparent border-none outline-none text-xs text-white placeholder-slate-400"
          onkeydown="if(event.key==='Enter') handleSendText()"
        />
        <div class="flex items-center gap-2.5 shrink-0">
          <div id="voicePill" class="flex items-center gap-1.5 text-[11px] text-slate-300 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.06]">
            <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
            <span id="voiceStatusText">Voice (Ready)</span>
          </div>
          <button onclick="handleSendText()" class="w-8 h-8 rounded-full bg-white hover:bg-slate-200 text-slate-900 flex items-center justify-center text-xs font-bold transition shadow-md">
            ➤
          </button>
        </div>
      </div>
    </footer>
  </div>

  <script>
    let cachedJson = "";
    const orb = document.getElementById('centralOrb');
    const statusIndicator = document.getElementById('statusIndicator');
    const voiceStatusText = document.getElementById('voiceStatusText');

    async function syncState() {
      try {
        const res = await fetch('/api/state');
        const data = await res.json();
        
        const rawStatus = (data.status || 'Idle').toLowerCase();
        
        orb.className = 'glass-orb';
        if (rawStatus.includes('listen')) {
          orb.classList.add('orb-listening');
          statusIndicator.innerText = 'Listening...';
          statusIndicator.className = 'text-xs font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-3 py-1 rounded-full flex items-center gap-2';
          voiceStatusText.innerText = 'Listening...';
        } else if (rawStatus.includes('process')) {
          orb.classList.add('orb-processing');
          statusIndicator.innerText = 'Thinking...';
          statusIndicator.className = 'text-xs font-mono text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full flex items-center gap-2';
          voiceStatusText.innerText = 'Thinking...';
        } else if (rawStatus.includes('speak')) {
          orb.classList.add('orb-speaking');
          statusIndicator.innerText = 'Speaking...';
          statusIndicator.className = 'text-xs font-mono text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded-full flex items-center gap-2';
          voiceStatusText.innerText = 'Speaking...';
        } else {
          statusIndicator.innerText = 'Ready';
          statusIndicator.className = 'text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full flex items-center gap-2';
          voiceStatusText.innerText = 'Voice (Ready)';
        }

        // Render conversation
        const jsonStr = JSON.stringify(data.conversation);
        if (jsonStr !== cachedJson) {
          cachedJson = jsonStr;
          const streamView = document.getElementById('chatStreamView');
          const heroView = document.getElementById('orbHero');

          if (!data.conversation || data.conversation.length === 0) {
            streamView.classList.add('hidden');
            streamView.classList.remove('flex');
            heroView.classList.remove('hidden');
            return;
          }

          heroView.classList.add('hidden');
          streamView.classList.remove('hidden');
          streamView.classList.add('flex');
          streamView.innerHTML = '';

          data.conversation.forEach((msg, idx) => {
            if (!msg.trim()) return;
            const bubble = document.createElement('div');
            const isUser = (idx % 2 === 0);
            
            if (isUser) {
              bubble.className = 'bg-indigo-950/70 border border-indigo-500/40 rounded-2xl p-3 px-4 text-xs leading-relaxed self-end max-w-lg text-slate-100 shadow-sm';
              bubble.innerHTML = `<div class="font-bold text-indigo-300 text-[10px] uppercase mb-0.5 tracking-wider">You</div><div>${escapeHtml(msg)}</div>`;
            } else {
              bubble.className = 'bg-[#181e2b] border border-white/[0.08] rounded-2xl p-3 px-4 text-xs leading-relaxed self-start max-w-lg text-slate-100 shadow-sm';
              bubble.innerHTML = `<div class="font-bold text-cyan-400 text-[10px] uppercase mb-0.5 tracking-wider">J.A.R.V.I.S.</div><div>${escapeHtml(msg)}</div>`;
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
      const input = document.getElementById('promptInput');
      const val = input.value.trim();
      if (!val) return;

      input.value = '';
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
