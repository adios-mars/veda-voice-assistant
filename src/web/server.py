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
  <title>Syntrix // J.A.R.V.I.S. OS</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .mono { font-family: 'JetBrains Mono', monospace; }
    
    /* 3D Iridescent Glass Sphere */
    .glass-orb {
      width: 86px;
      height: 86px;
      border-radius: 50%;
      background: radial-gradient(circle at 32% 28%, #ffffff 0%, #38ef7d 22%, #11998e 45%, #0284c7 72%, #0f172a 100%);
      box-shadow: 
        inset 0 0 16px rgba(255, 255, 255, 0.8),
        inset 0 -10px 20px rgba(2, 132, 199, 0.7),
        0 12px 35px rgba(17, 153, 142, 0.45),
        0 0 55px rgba(56, 239, 125, 0.35);
      position: relative;
      animation: orbFloat 4s ease-in-out infinite;
      transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass-orb::before {
      content: '';
      position: absolute;
      top: 12px;
      left: 16px;
      width: 28px;
      height: 16px;
      border-radius: 50%;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0) 100%);
      transform: rotate(-25deg);
    }
    .glass-orb::after {
      content: '';
      position: absolute;
      bottom: 9px;
      right: 16px;
      width: 22px;
      height: 10px;
      border-radius: 50%;
      background: rgba(56, 239, 125, 0.65);
      filter: blur(2px);
    }

    @keyframes orbFloat {
      0%, 100% { transform: translateY(0px) scale(1); }
      50% { transform: translateY(-7px) scale(1.02); }
    }

    /* Listening state pulse */
    .orb-listening {
      box-shadow: 
        0 0 0 0 rgba(56, 189, 248, 0.7),
        0 0 50px rgba(56, 189, 248, 0.7),
        0 12px 35px rgba(2, 132, 199, 0.8) !important;
      animation: listeningPulse 1.3s ease-out infinite !important;
    }
    @keyframes listeningPulse {
      0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.8); }
      70% { transform: scale(1.1); box-shadow: 0 0 0 25px rgba(56, 189, 248, 0); }
      100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
    }

    /* Speaking state pulse */
    .orb-speaking {
      background: radial-gradient(circle at 32% 28%, #ffffff 0%, #f43f5e 22%, #e11d48 45%, #881337 72%, #0f172a 100%) !important;
      box-shadow: 
        0 0 50px rgba(244, 63, 94, 0.6),
        0 12px 35px rgba(225, 29, 72, 0.7) !important;
      animation: listeningPulse 1.1s ease-out infinite !important;
    }

    /* Processing state */
    .orb-processing {
      background: radial-gradient(circle at 32% 28%, #ffffff 0%, #fbbf24 22%, #d97706 45%, #78350f 72%, #0f172a 100%) !important;
      box-shadow: 0 0 45px rgba(245, 158, 11, 0.6) !important;
      animation: orbFloat 1.2s ease-in-out infinite !important;
    }

    /* Custom thin scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.12); border-radius: 4px; }
  </style>
</head>
<body class="bg-[#080b11] text-slate-100 min-h-screen flex items-center justify-center p-6 antialiased selection:bg-cyan-500/30">
  
  <!-- Outer Floating App Frame (Matching Syntrix reference image) -->
  <div class="w-full max-w-6xl rounded-[36px] bg-[#0c1017] border border-white/[0.08] shadow-[0_30px_90px_-20px_rgba(0,0,0,0.9)] overflow-hidden flex h-[740px] relative">
    
    <!-- Ambient Cyan Glow (Top Right) -->
    <div class="absolute top-0 right-0 w-[550px] h-[400px] bg-gradient-to-bl from-teal-500/15 via-cyan-600/10 to-transparent pointer-events-none rounded-tr-[36px] blur-3xl"></div>

    <!-- LEFT SIDEBAR -->
    <aside class="w-64 bg-[#0f141d]/90 border-r border-white/[0.06] p-6 flex flex-col justify-between shrink-0 z-10 backdrop-blur-md">
      <div>
        <!-- Brand & Search -->
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-3">
            <!-- Mini Orb Icon -->
            <div class="w-7 h-7 rounded-full bg-gradient-to-tr from-teal-400 to-cyan-300 shadow-[0_0_12px_rgba(45,212,191,0.5)] flex items-center justify-center">
              <div class="w-2.5 h-2.5 rounded-full bg-white/95"></div>
            </div>
            <span class="font-bold text-base tracking-tight text-white">Syntrix <span class="text-xs text-cyan-400 font-medium">OS</span></span>
          </div>
          <button class="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-white/[0.05] transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          </button>
        </div>

        <!-- New Chat Button -->
        <button onclick="resetConversation()" class="w-full bg-[#181f2c]/90 hover:bg-[#20293a] border border-white/[0.08] rounded-xl py-2.5 px-3.5 flex items-center gap-2.5 text-xs font-semibold text-slate-200 transition shadow-sm mb-7 group">
          <svg class="w-4 h-4 text-cyan-400 group-hover:scale-110 transition" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>
          New Conversation
        </button>

        <!-- Features Nav -->
        <div class="mb-6">
          <div class="text-[10px] font-bold tracking-wider uppercase text-slate-400 px-2 mb-2.5">Features</div>
          <div class="space-y-1 text-xs">
            <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-300 bg-white/[0.04] font-medium transition">
              <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
              Voice Assistant
            </a>
            <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-white/[0.03] transition">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
              Intelligence
            </a>
            <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-white/[0.03] transition">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/></svg>
              Codex & Tools
            </a>
          </div>
        </div>

        <!-- Recent Sessions -->
        <div>
          <div class="text-[10px] font-bold tracking-wider uppercase text-slate-400 px-2 mb-2">Live Session Log</div>
          <div class="space-y-1 text-xs text-slate-400" id="sidebarChatList">
            <div class="px-3 py-1.5 rounded-lg text-slate-300 truncate">Companion Chat</div>
            <div class="px-3 py-1.5 rounded-lg truncate">Technical Diagnostics</div>
          </div>
        </div>
      </div>

      <!-- Bottom Status Card -->
      <div class="bg-gradient-to-b from-[#161c28] to-[#111622] border border-white/[0.08] rounded-2xl p-3.5 shadow-sm">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-[10px] font-bold uppercase tracking-wider text-cyan-400">Tactical Status</span>
          <span class="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]"></span>
        </div>
        <div class="text-xs font-semibold text-white">Gemini 3.5 Flash Lite</div>
        <div class="text-[11px] text-slate-400">Deepgram STT // PipeWire</div>
      </div>
    </aside>

    <!-- RIGHT MAIN CONTENT -->
    <main class="flex-1 flex flex-col justify-between p-8 relative z-10 overflow-hidden">
      <!-- Top Navigation -->
      <header class="flex items-center justify-between shrink-0">
        <!-- Model Pill -->
        <button class="bg-[#161c28]/90 hover:bg-[#1e2638] border border-white/[0.08] rounded-full py-1.5 px-4 flex items-center gap-2.5 text-xs font-medium text-slate-200 transition shadow-sm">
          <span class="w-1.5 h-1.5 rounded-full bg-teal-400 shadow-[0_0_6px_#2dd4bf]"></span>
          <span>Syntrix v4.2 (Gemini)</span>
          <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>
        </button>

        <!-- Right User Pill & Links -->
        <div class="flex items-center gap-6 text-xs font-medium text-slate-400">
          <a href="#" class="text-white hover:text-cyan-300 transition">Dashboard</a>
          <a href="#" class="hover:text-white transition">Settings</a>
          <a href="#" class="hover:text-white transition">Help & Support</a>
          
          <!-- Ruth Avatar -->
          <div class="flex items-center gap-2.5 pl-3 border-l border-white/[0.1]">
            <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shadow-[0_0_12px_rgba(168,85,247,0.4)] ring-2 ring-white/10">
              R
            </div>
            <span class="text-white font-semibold text-xs">Ruth</span>
          </div>
        </div>
      </header>

      <!-- Center Hero / Conversation Stream -->
      <section class="flex-1 flex flex-col justify-center items-center my-auto overflow-hidden py-4 w-full" id="centerSection">
        
        <!-- Hero Orb View (Visible when idle / empty) -->
        <div id="heroOrbView" class="flex flex-col items-center justify-center text-center">
          <!-- The Floating 3D Orb -->
          <div class="mb-4">
            <div id="centralOrb" class="glass-orb"></div>
          </div>
          <div class="text-[11px] font-bold tracking-[0.25em] text-slate-400 uppercase mb-1.5">Welcome Back, Ruth</div>
          <h1 class="text-3xl font-bold tracking-tight text-white mb-2" id="heroTitle">Bring your ideas to life today</h1>
          <p class="text-xs text-slate-400 max-w-md mb-6" id="statusSubtext">Speak into your microphone or type below. JARVIS is standing by.</p>
        </div>

        <!-- Chat Bubble View (Appears as conversation grows) -->
        <div id="chatStreamView" class="w-full max-w-2xl h-80 overflow-y-auto hidden flex-col gap-3 px-2 mb-4 scroll-smooth">
        </div>

        <!-- Input Bar (Dual Voice & Typing) -->
        <div class="w-full max-w-2xl bg-[#141a24]/90 backdrop-blur-md border border-white/[0.08] rounded-2xl p-3.5 shadow-2xl shrink-0">
          <div class="flex items-center gap-2.5 px-2 pt-1 pb-3">
            <span class="text-cyan-400 text-sm">✦</span>
            <input id="promptInput" type="text" placeholder="Ask me anything... (or speak into your microphone)" class="w-full bg-transparent border-none outline-none text-xs text-white placeholder-slate-400">
          </div>
          <div class="flex items-center justify-between pt-2.5 border-t border-white/[0.06] px-1">
            <div class="flex items-center gap-2">
              <button class="w-6 h-6 rounded-full bg-white/[0.06] hover:bg-white/[0.1] text-slate-300 flex items-center justify-center text-xs transition">+</button>
              <button class="px-3 py-1 rounded-full bg-white/[0.06] hover:bg-white/[0.1] text-[11px] text-slate-300 flex items-center gap-1 transition">
                <span>Tools</span>
                <svg class="w-2.5 h-2.5 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>
              </button>
              <button class="px-3 py-1 rounded-full bg-white/[0.06] hover:bg-white/[0.1] text-[11px] text-slate-300 flex items-center gap-1 transition">
                <span>Deep Think</span>
                <svg class="w-2.5 h-2.5 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>
              </button>
            </div>
            <div class="flex items-center gap-2.5">
              <div id="voicePill" class="px-3 py-1 rounded-full bg-white/[0.06] border border-white/[0.08] text-[11px] text-slate-300 flex items-center gap-2 transition">
                <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
                <span id="voiceStatusText">Voice (Ready)</span>
              </div>
              <button onclick="handleSendText()" class="w-7 h-7 rounded-full bg-white hover:bg-slate-200 text-slate-900 flex items-center justify-center text-xs transition shadow-md font-bold">
                ➤
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Bottom 3 Feature Cards (Matching reference) -->
      <footer class="grid grid-cols-3 gap-4 shrink-0">
        <!-- Card 1 -->
        <div class="bg-[#131924]/80 hover:bg-[#18202e] border border-white/[0.06] rounded-2xl p-4 flex flex-col justify-between transition cursor-pointer group shadow-sm">
          <div class="flex items-center justify-between mb-3">
            <div class="w-8 h-8 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
            </div>
            <span class="text-slate-400 group-hover:text-white transition text-xs">↗</span>
          </div>
          <div>
            <div class="text-xs font-semibold text-white">Voice Recognition</div>
            <div class="text-[11px] text-slate-400 mt-0.5">Deepgram Nova-2 + 32k MP3</div>
          </div>
        </div>

        <!-- Card 2 -->
        <div class="bg-[#131924]/80 hover:bg-[#18202e] border border-white/[0.06] rounded-2xl p-4 flex flex-col justify-between transition cursor-pointer group shadow-sm">
          <div class="flex items-center justify-between mb-3">
            <div class="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
            </div>
            <span class="text-slate-400 group-hover:text-white transition text-xs">↗</span>
          </div>
          <div>
            <div class="text-xs font-semibold text-white">Gemini 3.5 Intelligence</div>
            <div class="text-[11px] text-slate-400 mt-0.5">Warm, witty & loyal conversation</div>
          </div>
        </div>

        <!-- Card 3 -->
        <div class="bg-[#131924]/80 hover:bg-[#18202e] border border-white/[0.06] rounded-2xl p-4 flex flex-col justify-between transition cursor-pointer group shadow-sm">
          <div class="flex items-center justify-between mb-3">
            <div class="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
            </div>
            <span class="text-slate-400 group-hover:text-white transition text-xs">↗</span>
          </div>
          <div>
            <div class="text-xs font-semibold text-white">Neural Speech Engine</div>
            <div class="text-[11px] text-slate-400 mt-0.5">PipeWire Bluetooth output</div>
          </div>
        </div>
      </footer>
    </main>
  </div>

  <script>
    let cachedJson = "";
    const orb = document.getElementById('centralOrb');
    const voicePill = document.getElementById('voicePill');
    const voiceStatusText = document.getElementById('voiceStatusText');

    async function syncState() {
      try {
        const res = await fetch('/api/state');
        const data = await res.json();
        
        const rawStatus = (data.status || 'Idle').toLowerCase();
        
        // Update Orb & Voice Pill reaction
        orb.className = 'glass-orb';
        voicePill.className = 'px-3 py-1 rounded-full bg-white/[0.06] border border-white/[0.08] text-[11px] text-slate-300 flex items-center gap-2 transition';
        
        if (rawStatus.includes('listen')) {
          orb.classList.add('orb-listening');
          voicePill.className = 'px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-400 text-[11px] text-cyan-200 flex items-center gap-2 transition shadow-[0_0_12px_rgba(6,182,212,0.4)]';
          voiceStatusText.innerText = 'Listening to Ruth...';
        } else if (rawStatus.includes('process')) {
          orb.classList.add('orb-processing');
          voicePill.className = 'px-3 py-1 rounded-full bg-amber-500/20 border border-amber-400 text-[11px] text-amber-200 flex items-center gap-2 transition';
          voiceStatusText.innerText = 'Thinking...';
        } else if (rawStatus.includes('speak')) {
          orb.classList.add('orb-speaking');
          voicePill.className = 'px-3 py-1 rounded-full bg-rose-500/20 border border-rose-400 text-[11px] text-rose-200 flex items-center gap-2 transition shadow-[0_0_15px_rgba(244,63,94,0.4)]';
          voiceStatusText.innerText = 'JARVIS Speaking...';
        } else {
          voiceStatusText.innerText = 'Voice (Ready)';
        }

        // Update conversation view
        const jsonStr = JSON.stringify(data.conversation);
        if (jsonStr !== cachedJson) {
          cachedJson = jsonStr;
          const streamView = document.getElementById('chatStreamView');
          const heroOrbView = document.getElementById('heroOrbView');

          if (!data.conversation || data.conversation.length === 0) {
            streamView.classList.add('hidden');
            streamView.classList.remove('flex');
            heroOrbView.classList.remove('hidden');
            return;
          }

          // Switch to stream view
          heroOrbView.classList.add('hidden');
          streamView.classList.remove('hidden');
          streamView.classList.add('flex');
          streamView.innerHTML = '';

          data.conversation.forEach((msg, idx) => {
            if (!msg.trim()) return;
            const bubble = document.createElement('div');
            const isUser = (idx % 2 === 0);
            
            if (isUser) {
              bubble.className = 'bg-indigo-950/70 border border-indigo-500/40 rounded-2xl p-3 text-xs leading-relaxed self-end max-w-lg text-slate-100 shadow-sm';
              bubble.innerHTML = `<div class="font-bold text-indigo-300 text-[10px] uppercase tracking-wider mb-1">Ruth</div><div>${escapeHtml(msg)}</div>`;
            } else {
              bubble.className = 'bg-[#181e2b]/95 border border-white/[0.08] rounded-2xl p-3 text-xs leading-relaxed self-start max-w-lg text-slate-100 shadow-sm';
              bubble.innerHTML = `<div class="font-bold text-teal-400 text-[10px] uppercase tracking-wider mb-1">Syntrix (JARVIS)</div><div>${escapeHtml(msg)}</div>`;
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

    function handleSendText() {
      const input = document.getElementById('promptInput');
      const val = input.value.trim();
      if (!val) return;
      input.value = '';
    }

    document.getElementById('promptInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSendText();
    });

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
