"""Speech-to-Text (STT) service using Deepgram Nova-2 with MP3 compression & Gemini fallback."""
from pathlib import Path
import subprocess
import time
from typing import Optional, Union

from deepgram import DeepgramClient
from src.config import config
from src.logger import get_logger

logger = get_logger("STT")


class SpeechToTextService:
    """Handles audio transcription via Deepgram's cloud API with Gemini fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.deepgram_api_key
        if not self.api_key:
            raise ValueError("Deepgram API Key is missing. Please set DEEPGRAM_API_KEY in .env")
        self.client = DeepgramClient(api_key=self.api_key)

    def _compress_audio(self, wav_path: Path) -> Path:
        """Compresses PCM WAV to 32kbps MP3 (reduces upload size by ~85% for instant network transfer)."""
        mp3_path = wav_path.with_suffix(".mp3")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(wav_path),
                    "-c:a", "libmp3lame", "-b:a", "32k",
                    str(mp3_path)
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return mp3_path
        except Exception as e:
            logger.debug(f"Audio compression skipped ({e}); sending raw WAV.")
            return wav_path

    def _transcribe_with_gemini(self, audio_bytes: bytes, mime_type: str) -> Optional[str]:
        """Fallback STT provider using Gemini multimodal audio capabilities."""
        if not config.gemini_api_key or config.gemini_api_key.startswith("your_"):
            return None
        try:
            from google import genai
            from google.genai import types

            gemini_client = genai.Client(
                api_key=config.gemini_api_key,
                http_options={"api_version": "v1beta"}
            )
            response = gemini_client.models.generate_content(
                model=config.gemini_model,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    "Transcribe this audio verbatim. Output only the transcribed spoken words, with no punctuation added other than standard sentences. Do not add commentary.",
                ],
            )
            text = (response.text or "").strip()
            return text if text else None
        except Exception as e:
            logger.error(f"Gemini fallback STT error: {e}")
            return None

    def transcribe(self, audio_file: Union[str, Path], model: str = "nova-2") -> str:
        """
        Transcribes the audio file to text.
        Compresses audio before upload to prevent network timeouts.
        Falls back to Gemini STT if Deepgram encounters network errors.
        """
        path = Path(audio_file)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        start_time = time.perf_counter()

        # 1. Compress to MP3 for ultrafast network upload
        target_file = self._compress_audio(path)
        audio_bytes = target_file.read_bytes()
        mime_type = "audio/mp3" if target_file.suffix == ".mp3" else "audio/wav"

        # 2. Try Deepgram Nova-2
        try:
            response = self.client.listen.v1.media.transcribe_file(
                request=audio_bytes,
                model=model,
                smart_format=True,
            )
            elapsed = time.perf_counter() - start_time
            transcript = response.results.channels[0].alternatives[0].transcript or ""
            logger.info(f"Transcribed via Deepgram in {elapsed:.2f}s: \"{transcript}\"")
            return transcript.strip()
        except Exception as dg_err:
            logger.warning(f"Deepgram transcription error ({dg_err}). Attempting Gemini fallback...")

        # 3. Fallback to Gemini Multimodal STT
        gemini_transcript = self._transcribe_with_gemini(audio_bytes, mime_type)
        if gemini_transcript:
            elapsed = time.perf_counter() - start_time
            logger.info(f"Transcribed via Gemini Fallback in {elapsed:.2f}s: \"{gemini_transcript}\"")
            return gemini_transcript.strip()

        logger.error("All STT providers failed for this audio cycle.")
        return ""
