"""High-performance audio recording and Voice Activity Detection (VAD)."""
import io
import time
import wave
from pathlib import Path
from typing import Optional

import pyaudio
from rhasspysilence import WebRtcVadRecorder

from src.config import AudioConfig
from src.logger import get_logger

logger = get_logger("Recorder")


class AudioRecorder:
    """Manages audio capture with Voice Activity Detection (VAD)."""

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.config.storage_dir.mkdir(parents=True, exist_ok=True)
        self._pa = pyaudio.PyAudio()

    def find_optimal_input_device(self) -> Optional[int]:
        """Auto-detect optimal 16kHz audio input device (prefers PipeWire/PulseAudio)."""
        device_count = self._pa.get_device_count()

        # Check PipeWire or PulseAudio virtual sink
        for i in range(device_count):
            dev = self._pa.get_device_info_by_index(i)
            if dev.get("maxInputChannels", 0) > 0:
                name = dev.get("name", "").lower()
                if "pipewire" in name or "pulse" in name or "default" in name:
                    try:
                        if self._pa.is_format_supported(
                            self.config.sample_rate,
                            input_device=i,
                            input_channels=self.config.channels,
                            input_format=pyaudio.paInt16,
                        ):
                            return i
                    except Exception:
                        pass

        # Fallback to any device supporting the sample rate
        for i in range(device_count):
            dev = self._pa.get_device_info_by_index(i)
            if dev.get("maxInputChannels", 0) > 0:
                try:
                    if self._pa.is_format_supported(
                        self.config.sample_rate,
                        input_device=i,
                        input_channels=self.config.channels,
                        input_format=pyaudio.paInt16,
                    ):
                        return i
                except Exception:
                    pass

        return None

    def record_until_silence(self, output_path: Optional[Path] = None) -> Path:
        """
        Listens to microphone, captures speech, and terminates once silence is detected.
        Returns the path of the saved WAV file.
        """
        target_path = output_path or self.config.recording_path
        device_index = self.find_optimal_input_device()

        recorder = WebRtcVadRecorder(
            vad_mode=self.config.vad_mode,
            silence_seconds=self.config.silence_duration_seconds,
        )
        recorder.start()

        stream = self._pa.open(
            rate=self.config.sample_rate,
            format=pyaudio.paInt16,
            channels=self.config.channels,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.config.frames_per_buffer,
        )
        stream.start_stream()

        try:
            chunk = stream.read(self.config.frames_per_buffer, exception_on_overflow=False)
            while chunk:
                voice_command = recorder.process_chunk(chunk)
                if voice_command:
                    audio_data = recorder.stop()
                    wav_bytes = self._buffer_to_wav(audio_data)
                    target_path.write_bytes(wav_bytes)
                    break
                chunk = stream.read(self.config.frames_per_buffer, exception_on_overflow=False)
        finally:
            stream.stop_stream()
            stream.close()

        return target_path

    def _buffer_to_wav(self, buffer: bytes) -> bytes:
        """Wraps raw PCM buffer into standard WAV container."""
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, mode="wb") as wav_file:
                wav_file.setframerate(self.config.sample_rate)
                wav_file.setsampwidth(2)
                wav_file.setnchannels(self.config.channels)
                wav_file.writeframesraw(buffer)
            return wav_buffer.getvalue()

    def close(self):
        """Releases PyAudio hardware resources."""
        self._pa.terminate()
