"""Text-to-Speech (TTS) engine with ElevenLabs & Edge-TTS auto-fallback."""
from abc import ABC, abstractmethod
import asyncio
from pathlib import Path
import time
from typing import Optional, Union

from src.config import config
from src.logger import get_logger

logger = get_logger("TTS")


class BaseTTS(ABC):
    """Abstract interface for speech synthesis."""

    @abstractmethod
    def synthesize(self, text: str, output_path: Union[str, Path]) -> Path:
        """Converts text into an audio file."""
        pass


class ElevenLabsTTS(BaseTTS):
    """ElevenLabs high-fidelity voice generator."""

    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None):
        self.api_key = api_key or config.elevenlabs_api_key
        self.voice_id = voice_id or config.elevenlabs_voice_id
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("Valid ELEVENLABS_API_KEY required in .env")

        from elevenlabs.client import ElevenLabs
        self.client = ElevenLabs(api_key=self.api_key)

    def synthesize(self, text: str, output_path: Union[str, Path]) -> Path:
        target = Path(output_path)
        start = time.perf_counter()

        audio_stream = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id="eleven_multilingual_v2",
        )
        with open(target, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        elapsed = time.perf_counter() - start
        logger.info(f"ElevenLabs synthesis complete in {elapsed:.2f}s")
        return target


class EdgeTTS(BaseTTS):
    """Free, high-quality neural voice synthesis via Microsoft Edge TTS."""

    def __init__(self, voice: Optional[str] = None):
        self.voice = voice or config.edge_tts_voice

    def synthesize(self, text: str, output_path: Union[str, Path]) -> Path:
        import edge_tts
        target = Path(output_path)
        start = time.perf_counter()

        async def _run():
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(str(target))

        asyncio.run(_run())
        elapsed = time.perf_counter() - start
        logger.info(f"Edge-TTS synthesis ({self.voice}) complete in {elapsed:.2f}s")
        return target


def get_tts_service() -> BaseTTS:
    """Factory creating configured TTS service with graceful fallback."""
    if config.tts_provider == "elevenlabs" or (
        config.tts_provider == "auto"
        and config.elevenlabs_api_key
        and not config.elevenlabs_api_key.startswith("your_")
    ):
        try:
            return ElevenLabsTTS()
        except Exception as e:
            logger.warning(f"Failed to initialize ElevenLabs ({e}). Falling back to Edge-TTS.")

    # High quality free neural TTS fallback
    logger.info("Using Edge-TTS (Free Neural Voices).")
    return EdgeTTS()
