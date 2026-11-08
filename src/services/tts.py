"""Text-to-Speech (TTS) engine with ElevenLabs & Edge-TTS auto-fallback."""
from abc import ABC, abstractmethod
import asyncio
from pathlib import Path
import subprocess
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
    """Free, high-quality neural voice synthesis via Microsoft Edge TTS with auto-retry."""

    def __init__(self, voice: Optional[str] = None):
        self.voice = voice or config.edge_tts_voice

    def synthesize(self, text: str, output_path: Union[str, Path]) -> Optional[Path]:
        import edge_tts
        target = Path(output_path)
        temp_mp3 = target.with_suffix(".mp3")
        start = time.perf_counter()

        success = False
        last_error = None

        # Retry up to 3 times to survive momentary DNS/network blips
        for attempt in range(1, 4):
            try:
                async def _run():
                    communicate = edge_tts.Communicate(text, self.voice)
                    await communicate.save(str(temp_mp3))

                asyncio.run(_run())
                success = True
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Edge-TTS attempt {attempt}/3 failed ({e}). Retrying in {attempt * 0.5}s...")
                time.sleep(attempt * 0.5)

        if not success:
            logger.warning(f"Edge-TTS unavailable ({last_error}). Falling back to Google TTS...")
            try:
                from gtts import gTTS
                google_tts = gTTS(text=text, lang="en", tld="com")
                google_tts.save(str(temp_mp3))
                success = True
            except Exception as gtts_err:
                logger.error(f"Both Edge-TTS and Google TTS failed: {gtts_err}")
                return None

        # Convert MP3 to true standard PCM WAV for native Linux audio servers (PipeWire / ALSA)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(temp_mp3), str(target)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Fallback: rename file
            temp_mp3.rename(target)

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
