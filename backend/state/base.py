"""Defines the protocol for state management stores."""

from typing import Protocol

from backend.models import PRDState


class StateStore(Protocol):
    """
    Protocol for a key-value store that persists PRDState.
    """

    async def save(self, state: PRDState) -> None:
        """
        Saves the PRD state.

        Args:
            state: The PRD state object to save. The run_id will be used
                   as the key.
        """
        ...

    async def get(self, run_id: str) -> PRDState | None:
        """
        Retrieves a PRD state by its run ID.

        Args:
            run_id: The unique identifier of the run.

        Returns:
            The PRD state object if found, otherwise None.
        """
        ...
