"""Audio playback service supporting PipeWire, PulseAudio, and FFplay."""
from pathlib import Path
import subprocess
from typing import Union
from src.logger import get_logger

logger = get_logger("Player")


class AudioPlayer:
    """Dispatches audio output through native Linux audio servers."""

    COMMANDS = [
        ["pw-play"],
        ["paplay"],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
        ["aplay"],
    ]

    @classmethod
    def play(cls, audio_path: Union[str, Path]) -> bool:
        """Plays audio file synchronously via available audio backends."""
        path_str = str(audio_path)
        for base_cmd in cls.COMMANDS:
            cmd = base_cmd + [path_str]
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except FileNotFoundError:
                continue
            except subprocess.CalledProcessError:
                continue
            except Exception as e:
                logger.debug(f"Player command {base_cmd[0]} failed: {e}")
                continue

        logger.error(f"No functional audio player found to play {audio_path}")
        return False
