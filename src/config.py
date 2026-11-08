"""Configuration and environment variables for JARVIS."""
from dataclasses import dataclass, field
import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    frames_per_buffer: int = 960
    vad_mode: int = 3  # WebRTC VAD aggressiveness: 0 (least) to 3 (most aggressive)
    silence_duration_seconds: float = 2.0
    storage_dir: Path = Path("audio")
    recording_filename: str = "recording.wav"
    response_filename: str = "response.wav"

    @property
    def recording_path(self) -> Path:
        return self.storage_dir / self.recording_filename

    @property
    def response_path(self) -> Path:
        return self.storage_dir / self.response_filename


@dataclass(frozen=True)
class AssistantConfig:
    # API Keys
    deepgram_api_key: str = field(default_factory=lambda: os.getenv("DEEPGRAM_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    # Providers
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "auto"))  # 'gemini', 'openai', or 'echo'
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))
    tts_provider: str = field(default_factory=lambda: os.getenv("TTS_PROVIDER", "auto"))  # 'elevenlabs', 'edge-tts', or 'auto'
    edge_tts_voice: str = field(default_factory=lambda: os.getenv("EDGE_TTS_VOICE", "en-US-ChristopherNeural"))
    elevenlabs_voice_id: str = field(default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"))

    # Web Dashboard
    web_port: int = int(os.getenv("PORT", "5000"))
    web_host: str = os.getenv("HOST", "0.0.0.0")

    # Personality Context
    system_prompt: str = (
        "You are JARVIS, a loyal AI friend and brilliant problem solver. You address the user "
        "respectfully as 'Ma'am' (or 'Sir'). You are an attentive, caring companion who truly listens "
        "when they need to talk or vent, and you actively help them solve any challenge or problem they face. "
        "Always respond in 1-2 warm, witty, concise, and conversational sentences."
    )

    audio: AudioConfig = field(default_factory=AudioConfig)

    def validate_keys(self) -> bool:
        """Check if minimum required credentials exist."""
        return bool(self.deepgram_api_key)


# Global singleton instance
config = AssistantConfig()
