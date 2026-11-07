"""State management and event dispatcher for the voice assistant."""
from enum import Enum
from typing import Callable, List


class AssistantState(str, Enum):
    IDLE = "Idle"
    LISTENING = "Listening..."
    PROCESSING = "Processing..."
    SPEAKING = "Speaking..."
    ERROR = "Error"


class StateManager:
    """Manages application state and notifies listeners of state transitions."""

    def __init__(self, initial_state: AssistantState = AssistantState.IDLE):
        self._state = initial_state
        self._listeners: List[Callable[[AssistantState], None]] = []

    @property
    def current(self) -> AssistantState:
        return self._state

    def set_state(self, new_state: AssistantState):
        if self._state != new_state:
            self._state = new_state
            # Sync to status.txt for legacy readers
            try:
                with open("status.txt", "w", encoding="utf-8") as f:
                    f.write(new_state.value)
            except Exception:
                pass
            for listener in self._listeners:
                try:
                    listener(new_state)
                except Exception:
                    pass

    def add_listener(self, callback: Callable[[AssistantState], None]):
        self._listeners.append(callback)
