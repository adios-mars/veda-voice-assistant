"""Speech-to-Text (STT) service using Deepgram Nova-2."""
from pathlib import Path
import time
from typing import Optional, Union

from deepgram import DeepgramClient
from src.config import config
from src.logger import get_logger

logger = get_logger("STT")


class SpeechToTextService:
    """Handles audio transcription via Deepgram's cloud API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.deepgram_api_key
        if not self.api_key:
            raise ValueError("Deepgram API Key is missing. Please set DEEPGRAM_API_KEY in .env")
        self.client = DeepgramClient(api_key=self.api_key)

    def transcribe(self, audio_file: Union[str, Path], model: str = "nova-2") -> str:
        """
        Transcribes the provided WAV audio file to text.
        Returns the formatted transcript string.
        """
        path = Path(audio_file)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        start_time = time.perf_counter()
        audio_bytes = path.read_bytes()

        try:
            response = self.client.listen.v1.media.transcribe_file(
                request=audio_bytes,
                model=model,
                smart_format=True,
            )
            elapsed = time.perf_counter() - start_time
            transcript = response.results.channels[0].alternatives[0].transcript
            logger.info(f"Transcribed in {elapsed:.2f}s: \"{transcript}\"")
            return transcript.strip()
        except Exception as e:
            logger.error(f"Deepgram transcription error: {e}")
            raise
