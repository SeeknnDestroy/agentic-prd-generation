"""
In-memory implementation of the state store for local development and testing.
"""
from backend.models import PRDState
from backend.state.base import StateStore


class InMemoryStore(StateStore):
    """
    A simple in-memory key-value store using a Python dictionary.

    This class is not thread-safe and is intended for single-instance,
    local development scenarios.
    """

    _store: dict[str, PRDState]

    def __init__(self) -> None:
        self._store = {}

    def save(self, state: PRDState) -> None:
        """Saves the PRD state to the in-memory dictionary."""
        self._store[state.run_id] = state

    def get(self, run_id: str) -> PRDState | None:
        """Retrieves a PRD state from the in-memory dictionary."""
        return self._store.get(run_id)
