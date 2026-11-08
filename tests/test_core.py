"""Comprehensive unit tests for Veda core architecture and configuration."""
import pytest
from pathlib import Path

from src.config import AudioConfig, AssistantConfig, config
from src.core.state import AssistantState, StateManager
from src.services.llm import EchoFallbackLLM, _is_placeholder


def test_audio_config_defaults():
    cfg = AudioConfig()
    assert cfg.sample_rate == 16000
    assert cfg.channels == 1
    assert cfg.frames_per_buffer == 960
    assert cfg.vad_mode == 3
    assert cfg.silence_duration_seconds == 2.0
    assert cfg.recording_path == Path("audio/recording.wav")
    assert cfg.response_path == Path("audio/response.wav")


def test_state_manager_transitions():
    sm = StateManager()
    assert sm.current == AssistantState.IDLE

    history = []
    sm.add_listener(lambda s: history.append(s))

    sm.set_state(AssistantState.LISTENING)
    sm.set_state(AssistantState.PROCESSING)
    sm.set_state(AssistantState.SPEAKING)
    sm.set_state(AssistantState.IDLE)

    assert sm.current == AssistantState.IDLE
    assert history == [
        AssistantState.LISTENING,
        AssistantState.PROCESSING,
        AssistantState.SPEAKING,
        AssistantState.IDLE,
    ]


def test_placeholder_detector():
    assert _is_placeholder("") is True
    assert _is_placeholder("your_api_key_here") is True
    assert _is_placeholder("sk-proj-...") is True
    assert _is_placeholder("sk-...") is True
    assert _is_placeholder("valid_production_api_key_12345") is False


def test_echo_fallback_llm():
    echo = EchoFallbackLLM()
    reply_hello = echo.generate_reply([], "Hello there!")
    assert "ready to help" in reply_hello.lower() or "how can i assist" in reply_hello.lower()

    reply_identity = echo.generate_reply([], "Who are you?")
    assert "veda" in reply_identity.lower()

    reply_general = echo.generate_reply([], "Can you hear me?")
    assert "can you hear me" in reply_general.lower()


def test_assistant_personality_config():
    assert "Veda" in config.system_prompt
    assert "Here to listen, ready to help" in config.system_prompt
