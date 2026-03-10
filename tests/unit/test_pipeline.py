"""Unit tests for the PRD generation pipeline."""

from dataclasses import dataclass, field

import pytest

from backend.agents.base_adapter import AdapterError, BaseAdapter
from backend.models import PRDState
from backend.pipelines.pipeline_runner import create_diff, run_pipeline
from backend.services.streamer import StreamerService
from backend.state.base import StateStore


@dataclass
class RecordingStore(StateStore):
    """Minimal in-memory store that records every saved state."""

    history: list[PRDState] = field(default_factory=list)
    backend_name: str = "memory"

    async def save(self, state: PRDState) -> None:
        self.history.append(state)

    async def get(self, run_id: str) -> PRDState | None:
        for state in reversed(self.history):
            if state.run_id == run_id:
                return state
        return None

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class SequenceAdapter(BaseAdapter):
    """Adapter test double that returns a predefined response sequence."""

    def __init__(self, responses: list[str]):
        self.adapter_type = "test"
        self._responses = responses
        self._index = 0

    async def call_llm(self, prompt: str) -> str:
        del prompt
        response = self._responses[self._index]
        self._index += 1
        return response


class FailingAdapter(BaseAdapter):
    """Adapter test double that raises a typed provider error."""

    adapter_type = "test"

    async def call_llm(self, prompt: str) -> str:
        del prompt
        raise AdapterError("test", "provider blew up")


@pytest.mark.asyncio
async def test_run_pipeline_records_truthful_steps() -> None:
    """A successful run records the expected ordered steps."""
    store = RecordingStore()
    streamer = StreamerService()
    adapter = SequenceAdapter(
        [
            "# Outline\n\n- Goals",
            "# Draft\n\nDetailed PRD",
            "No issues found.",
        ]
    )
    initial_state = PRDState(
        run_id="run-1",
        idea="An AI PM assistant",
        step="Outline",
        content="# PRD for An AI PM assistant\n\n_Starting outline generation..._",
        revision=0,
        diff=None,
        error=None,
    )

    await run_pipeline(
        initial_state=initial_state,
        state_store=store,
        adapter=adapter,
        streamer=streamer,
    )

    assert [state.step for state in store.history] == [
        "Outline",
        "Draft",
        "Critique",
        "Complete",
    ]
    assert store.history[-1].step == "Complete"
    assert store.history[-1].error is None


@pytest.mark.asyncio
async def test_run_pipeline_records_terminal_error_state() -> None:
    """Provider failures end the run in an error state instead of completing."""
    store = RecordingStore()
    initial_state = PRDState(
        run_id="run-2",
        idea="A flaky provider",
        step="Outline",
        content="# PRD for A flaky provider\n\n_Starting outline generation..._",
        revision=0,
        diff=None,
        error=None,
    )

    await run_pipeline(
        initial_state=initial_state,
        state_store=store,
        adapter=FailingAdapter(),
        streamer=None,
    )

    assert store.history[-1].step == "Error"
    assert store.history[-1].error == "provider blew up"
    assert all(state.step != "Complete" for state in store.history)


def test_create_diff_returns_patch_text() -> None:
    """Diff generation returns a patch when text changes."""
    diff = create_diff("before", "after")
    assert "@@" in diff
