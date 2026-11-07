"""Core JARVIS Voice Assistant orchestrator."""
from pathlib import Path
import time
from typing import Dict, List, Optional

from src.audio.player import AudioPlayer
from src.audio.recorder import AudioRecorder
from src.config import config
from src.core.state import AssistantState, StateManager
from src.logger import get_logger
from src.services.llm import get_llm_service
from src.services.stt import SpeechToTextService
from src.services.tts import get_tts_service

logger = get_logger("Orchestrator")


class JarvisAssistant:
    """Production-grade voice assistant coordinator."""

    def __init__(self):
        logger.info("Initializing JARVIS Assistant subsystem...")
        self.state = StateManager()
        self.recorder = AudioRecorder(config.audio)
        self.stt = SpeechToTextService()
        self.llm = get_llm_service()
        self.tts = get_tts_service()
        self.history: List[Dict[str, str]] = []

        # Ensure storage directory exists
        config.audio.storage_dir.mkdir(parents=True, exist_ok=True)
        if not Path("conv.txt").exists():
            Path("conv.txt").write_text("", encoding="utf-8")

        self.state.set_state(AssistantState.IDLE)
        logger.info("JARVIS Assistant initialized and ready.")

    def record_and_transcribe(self) -> Optional[str]:
        """Listens and transcribes user utterance."""
        self.state.set_state(AssistantState.LISTENING)
        audio_file = self.recorder.record_until_silence()

        self.state.set_state(AssistantState.PROCESSING)
        transcript = self.stt.transcribe(audio_file)
        if not transcript:
            logger.info("No speech detected.")
            self.state.set_state(AssistantState.IDLE)
            return None

        # Append to conv.txt
        with open("conv.txt", "a", encoding="utf-8") as f:
            f.write(f"{transcript}\n")

        return transcript

    def think_and_speak(self, prompt: str) -> str:
        """Queries LLM and speaks generated reply."""
        self.state.set_state(AssistantState.PROCESSING)
        reply = self.llm.generate_reply(self.history, prompt)

        # Update conversational memory
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": reply})

        # Append response to conv.txt
        with open("conv.txt", "a", encoding="utf-8") as f:
            f.write(f"{reply}\n")

        # Synthesize Speech
        response_wav = config.audio.response_path
        self.tts.synthesize(reply, response_wav)

        # Playback audio
        self.state.set_state(AssistantState.SPEAKING)
        AudioPlayer.play(response_wav)

        self.state.set_state(AssistantState.IDLE)
        return reply

    def step(self):
        """Executes a single conversational interaction loop."""
        user_input = self.record_and_transcribe()
        if user_input:
            self.think_and_speak(user_input)

    def run_forever(self):
        """Runs the continuous interaction loop."""
        logger.info("Starting active listening cycle. Press Ctrl+C to terminate.")
        try:
            while True:
                self.step()
        except KeyboardInterrupt:
            logger.info("Shutdown signal received. Releasing resources...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleans up hardware resources."""
        self.recorder.close()
        self.state.set_state(AssistantState.IDLE)
        logger.info("Clean shutdown complete.")
