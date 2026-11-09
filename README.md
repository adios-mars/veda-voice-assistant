# Veda: Conversational AI Voice Assistant and Companion

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue?style=for-the-badge&logo=python" alt="Python Version"/>
  <img src="https://img.shields.io/badge/LLM-Google%20Gemini%203.5%20Lite%20%26%20OpenAI-4285F4?style=for-the-badge&logo=google" alt="LLM"/>
  <img src="https://img.shields.io/badge/Audio-PipeWire%20%7C%20PulseAudio-purple?style=for-the-badge&logo=linux" alt="Linux Audio"/>
  <img src="https://img.shields.io/badge/STT-Deepgram%20Nova--2%20%2B%20Gemini-13ef95?style=for-the-badge" alt="Deepgram"/>
  <img src="https://img.shields.io/badge/TTS-Edge--TTS%20Neural%20%7C%20gTTS-ff462b?style=for-the-badge" alt="TTS"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

> Here to listen, ready to help.

Veda is a low-latency, conversational AI voice assistant and companion built for Linux, macOS, and POSIX-compliant environments. Engineered with automated multi-model failover, resilient cloud fallbacks, pre-upload audio compression, and an ultra-minimalist dark web interface, Veda delivers natural, empathetic dialogue and intelligent problem-solving.

---

## System Architecture

```mermaid
flowchart LR
    A[Microphone Audio Input] -->|pyaudio + WebRTC VAD| B(Voice Activity Detection)
    B -->|ffmpeg MP3 Compression| C[Deepgram Nova-2 STT]
    C -.->|Timeout / Error Fallback| C2[Gemini Multimodal STT]
    C -->|Spoken Transcript| D[Google Gemini 3.5 Lite]
    D -.->|Quota Failover Pool| D2[Gemini 3.1 / Gemma / Gemini 2.5]
    D -->|Conversational Output| E[Microsoft Edge-TTS Neural]
    E -.->|Network Drop Fallback| E2[Google Speech Synthesis]
    E -->|PCM Audio Output| F[Audio Output Sinks]
    
    B -.->|State Transitions| G[Minimalist Web Interface]
    D -.->|Transcript Stream| G
    E -.->|Speaking State| G
```

---

## Core Engineering Features

Never-Fail AI Brain: Uses Gemini Flash-Lite with automatic backups across four alternate models to prevent rate limits and downtime.

Lightweight Audio: Compresses microphone input to 32kbps MP3 on the fly, cutting upload bandwidth by 85% on flaky connections.

Backup-Ready Speech & Voice: Transcribes via Deepgram (backed by Gemini Audio) and speaks via Edge-TTS (backed by gTTS).

Smart Audio Routing: Automatically detects Linux audio servers (PipeWire, PulseAudio, ALSA) and Bluetooth headsets.

Clean Local UI: A lightweight web dashboard on port 5000 showing real-time states (listening, thinking, speaking) with quick chat prompts.

---

## Directory Structure

```
jarvis-voice-assistant/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI workflow
├── src/
│   ├── config.py                # Strongly-typed dataclass configuration
│   ├── logger.py                # Colorized structured logging module
│   ├── audio/
│   │   ├── recorder.py          # VAD microphone stream engine with auto-detection
│   │   └── player.py            # Audio player dispatcher (pw-play, paplay, ffplay)
│   ├── services/
│   │   ├── stt.py               # Deepgram Nova-2 STT with MP3 compression & Gemini fallback
│   │   ├── llm.py               # Gemini multi-model failover pool & OpenAI integration
│   │   └── tts.py               # Dual-engine TTS (Edge-TTS & Google TTS)
│   ├── core/
│   │   ├── state.py             # Event-driven StateManager (Idle, Listening, Processing, Speaking)
│   │   └── assistant.py         # Primary conversation coordinator
│   └── web/
│       └── server.py            # Embedded minimalist web interface and API server
├── tests/
│   ├── test_audio.py            # Audio configuration and state tests
│   └── test_core.py             # Core architecture, personality, and fallback tests
├── .env.example                 # Environment variable template
├── .gitignore                   # Git exclusion rules
├── pyproject.toml               # PEP 517 package configuration
├── requirements.txt             # Python dependency manifest
└── main.py                      # Application entry point with self-healing venv launcher
```

---

## Getting Started

### 1. System Dependencies

#### Arch Linux / Manjaro:
```bash
sudo pacman -S --needed portaudio ffmpeg base-devel pipewire
```

#### Ubuntu / Debian / Linux Mint:
```bash
sudo apt update && sudo apt install -y portaudio19-dev ffmpeg build-essential
```

#### Fedora / RHEL:
```bash
sudo dnf install -y portaudio-devel ffmpeg gcc
```

#### macOS (via Homebrew):
```bash
brew install portaudio ffmpeg
```

### 2. Python Environment Setup

Clone the repository and install dependencies inside a dedicated virtual environment:
```bash
git clone https://github.com/your-username/jarvis-voice-assistant.git
cd jarvis-voice-assistant

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the template configuration:
```bash
cp .env.example .env
```

Edit `.env` with your API credentials:
```ini
# Deepgram (Speech-to-Text): https://console.deepgram.com
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Google Gemini (Primary LLM - Free tier available): https://aistudio.google.com/apikey
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# Optional fallbacks
OPENAI_API_KEY=
ELEVENLABS_API_KEY=

# Server configuration
PORT=5000
HOST=0.0.0.0
```

---

## Execution and CLI Options

### Standard Mode
Launches the voice assistant and automatically opens the web interface in your default browser:
```bash
python main.py
```

### Command-Line Arguments
```bash
# Run voice assistant and web server without launching a browser window:
python main.py --no-browser

# Run only the web interface without microphone initialization:
python main.py --web-only

# Run headlessly in terminal without starting the web server:
python main.py --no-web

# Execute a standalone microphone hardware and VAD diagnostic test:
python main.py --test-mic
```


