"""Functional async pipeline for running the agentic workflow."""

from collections.abc import Awaitable, Callable

from backend.agents.base_adapter import BaseAdapter
from backend.models import PRDState
from backend.services.streamer import StreamerService
from backend.state.base import StateStore


async def outline_step(
    current_state: PRDState, state_store: StateStore, adapter: BaseAdapter
) -> PRDState:
    """Generate the outline for the PRD."""
    # TODO: Implement actual logic
    print("Running outline step...")
    prompt = f"Create a PRD outline for: {current_state.content}"
    new_content = await adapter.call_llm(prompt)
    new_state = current_state.copy(
        update={"step": "Draft", "content": new_content, "revision": 1}
    )
    state_store.save(new_state)
    return new_state


async def draft_step(
    current_state: PRDState, state_store: StateStore, adapter: BaseAdapter
) -> PRDState:
    """Generate the draft for the PRD."""
    # TODO: Implement actual logic
    print("Running draft step...")
    prompt = f"Create a PRD draft for: {current_state.content}"
    new_content = await adapter.call_llm(prompt)
    new_state = current_state.copy(
        update={"step": "Critique", "content": new_content, "revision": 2}
    )
    state_store.save(new_state)
    return new_state


async def critique_step(
    current_state: PRDState, state_store: StateStore, adapter: BaseAdapter
) -> PRDState:
    """Critique the PRD draft."""
    # TODO: Implement actual logic
    print("Running critique step...")
    prompt = f"Critique the following PRD: {current_state.content}"
    critique = await adapter.call_llm(prompt)
    new_state = current_state.copy(
        update={
            "step": "Revise",
            "content": f"{current_state.content}\n\nCritique: {critique}",
            "revision": 3,
        }
    )
    state_store.save(new_state)
    return new_state


async def revise_step(
    current_state: PRDState, state_store: StateStore, adapter: BaseAdapter
) -> PRDState:
    """Revise the PRD based on critique."""
    # TODO: Implement actual logic
    print("Running revise step...")
    prompt = f"Revise the following PRD based on the critique: {current_state.content}"
    new_content = await adapter.call_llm(prompt)
    new_state = current_state.copy(
        update={"step": "Complete", "content": new_content, "revision": 4}
    )
    state_store.save(new_state)
    return new_state


PIPELINE_STAGES: list[
    Callable[[PRDState, StateStore, BaseAdapter], Awaitable[PRDState]]
] = [outline_step, draft_step, critique_step, revise_step]


async def run_pipeline(
    initial_state: PRDState,
    state_store: StateStore,
    adapter: BaseAdapter,
    streamer: StreamerService | None = None,
) -> None:
    """
    Runs the full agentic pipeline from outline to completion.

    Args:
        initial_state: The starting state of the PRD.
        state_store: The state manager to save progress.
        adapter: The agent adapter for LLM calls.
    """
    current_state = initial_state

    # Push the initial state to the stream so the UI shows something immediately.
    if streamer:
        await streamer.push_data(current_state.run_id, current_state.model_dump())

    for step_func in PIPELINE_STAGES:
        current_state = await step_func(current_state, state_store, adapter)

        # Stream the updated state after each step.
        if streamer:
            await streamer.push_data(current_state.run_id, current_state.model_dump())

    print("Pipeline complete.")
