"""Basic test cases for configuration and audio components."""
from src.config import config
from src.core.state import AssistantState, StateManager


def test_config_paths():
    assert config.audio.sample_rate == 16000
    assert config.audio.channels == 1
    assert config.audio.recording_filename == "recording.wav"


def test_state_manager():
    sm = StateManager()
    assert sm.current == AssistantState.IDLE

    events = []
    sm.add_listener(lambda s: events.append(s))
    sm.set_state(AssistantState.LISTENING)

    assert sm.current == AssistantState.LISTENING
    assert events == [AssistantState.LISTENING]
