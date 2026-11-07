"""Function for recording audio from a microphone."""
import io
import os
import time
import wave
from pathlib import Path
from typing import Optional

import pyaudio
from rhasspysilence import WebRtcVadRecorder, VoiceCommand, VoiceCommandResult


def get_best_input_device_index(pa: pyaudio.PyAudio) -> Optional[int]:
    """Find the best input device supporting 16000 Hz (prefers pipewire/pulse)."""
    device_count = pa.get_device_count()
    preferred_index = None

    # First pass: check for pipewire or pulse
    for i in range(device_count):
        dev = pa.get_device_info_by_index(i)
        if dev.get("maxInputChannels", 0) > 0:
            name = dev.get("name", "").lower()
            if "pipewire" in name or "pulse" in name or "default" in name:
                try:
                    if pa.is_format_supported(16000, input_device=i, input_channels=1, input_format=pyaudio.paInt16):
                        return i
                except Exception:
                    pass

    # Second pass: check any device that supports 16000 Hz
    for i in range(device_count):
        dev = pa.get_device_info_by_index(i)
        if dev.get("maxInputChannels", 0) > 0:
            try:
                if pa.is_format_supported(16000, input_device=i, input_channels=1, input_format=pyaudio.paInt16):
                    return i
            except Exception:
                pass

    return None


def speech_to_text() -> None:
    """
    Records audio until silence is detected.
    Saves audio to audio/recording.wav
    """
    pa = pyaudio.PyAudio()
    device_index = get_best_input_device_index(pa)

    recorder = WebRtcVadRecorder(
        vad_mode=3,
        silence_seconds=2,
    )
    recorder.start()

    wav_dir = Path("audio")
    wav_dir.mkdir(exist_ok=True)
    wav_path = wav_dir / "recording.wav"

    audio_source = pa.open(
        rate=16000,
        format=pyaudio.paInt16,
        channels=1,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=960,
    )
    audio_source.start_stream()

    def buffer_to_wav(buffer: bytes) -> bytes:
        """Wraps raw audio PCM in WAV container"""
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, mode="wb") as wav_file:
                wav_file.setframerate(16000)
                wav_file.setsampwidth(2)
                wav_file.setnchannels(1)
                wav_file.writeframesraw(buffer)
            return wav_buffer.getvalue()

    try:
        chunk = audio_source.read(960, exception_on_overflow=False)
        while chunk:
            voice_command = recorder.process_chunk(chunk)
            if voice_command:
                audio_data = recorder.stop()
                wav_bytes = buffer_to_wav(audio_data)
                wav_path.write_bytes(wav_bytes)
                break
            chunk = audio_source.read(960, exception_on_overflow=False)
    finally:
        try:
            audio_source.stop_stream()
            audio_source.close()
            pa.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    speech_to_text()
