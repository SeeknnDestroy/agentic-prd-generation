"""Functional async pipeline for running the agentic workflow."""

from collections.abc import Awaitable, Callable
import traceback

from diff_match_patch import diff_match_patch

from backend.agents.base_adapter import BaseAdapter
from backend.models import PRDState
from backend.pipelines.prompts import (
    CRITIQUE_PROMPT,
    DRAFT_PROMPT,
    OUTLINE_PROMPT,
    REVISE_PROMPT,
)
from backend.services.streamer import StreamerService
from backend.state.base import StateStore


def create_diff(text1: str, text2: str) -> str:
    """Generates a unified diff between two texts."""
    dmp = diff_match_patch()
    patches = dmp.patch_make(text1, text2)
    diff_text: str = dmp.patch_toText(patches)
    return diff_text


async def outline_step(
    current_state: PRDState, state_store: StateStore, adapter: BaseAdapter
) -> PRDState:
    """Generate the outline for the PRD."""
    print("Running outline step...")
    # The initial content is the project idea.
    idea = current_state.content.replace("# PRD for ", "").replace(
        "\n\n*Initial state.*", ""
    )
    prompt = OUTLINE_PROMPT.format(idea=idea)
    new_content: str = await adapter.call_llm(prompt)

    new_state = PRDState(
        run_id=current_state.run_id,
        step="Draft",
        content=new_content,
        revision=current_state.revision + 1,
        diff=create_diff(current_state.content, new_content),
    )
    state_store.save(new_state)
    return new_state


async def draft_step(
    current_state: PRDState, state_store: StateStore, adapter: BaseAdapter
) -> PRDState:
    """Generate the draft for the PRD."""
    print("Running draft step...")
    prompt = DRAFT_PROMPT.format(outline=current_state.content)
    new_content: str = await adapter.call_llm(prompt)

    new_state = PRDState(
        run_id=current_state.run_id,
        step="Critique",
        content=new_content,
        revision=current_state.revision + 1,
        diff=create_diff(current_state.content, new_content),
    )
    state_store.save(new_state)
    return new_state


async def critique_step(
    current_state: PRDState, state_store: StateStore, adapter: BaseAdapter
) -> PRDState:
    """Critique the PRD draft."""
    print("Running critique step...")
    prompt = CRITIQUE_PROMPT.format(draft=current_state.content)
    critique: str = await adapter.call_llm(prompt)

    # The critique is appended to the content for the revise step.
    # This is a temporary state that is not meant to be final.
    content_with_critique = (
        f"{current_state.content}\n\n---\n\n## Critique\n\n{critique}"
    )

    new_state = PRDState(
        run_id=current_state.run_id,
        step="Revise",
        content=content_with_critique,
        revision=current_state.revision + 1,
        diff=create_diff(current_state.content, content_with_critique),
    )
    state_store.save(new_state)
    return new_state


async def revise_step(
    current_state: PRDState, state_store: StateStore, adapter: BaseAdapter
) -> PRDState:
    """Revise the PRD based on critique."""
    print("Running revise step...")
    # The content from the critique step includes both the draft and the critique.
    # We need to extract them to format the prompt correctly.
    parts = current_state.content.split("\n\n---\n\n## Critique\n\n")
    if len(parts) != 2:
        # Fallback if the critique format is unexpected
        draft = current_state.content
        critique = "No critique found."
    else:
        draft, critique = parts

    prompt = REVISE_PROMPT.format(draft=draft, critique=critique)
    new_content: str = await adapter.call_llm(prompt)

    new_state = PRDState(
        run_id=current_state.run_id,
        step="Complete",
        content=new_content,
        revision=current_state.revision + 1,
        diff=create_diff(current_state.content, new_content),
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
        streamer: The service to stream updates to the frontend.
    """
    current_state = initial_state

    # Push the initial state to the stream so the UI shows something immediately.
    if streamer:
        await streamer.push_data(current_state.run_id, current_state.model_dump())

    for step_func in PIPELINE_STAGES:
        try:
            current_state = await step_func(current_state, state_store, adapter)
            # Stream the updated state after each step.
            if streamer:
                await streamer.push_data(
                    current_state.run_id, current_state.model_dump()
                )
        except Exception:
            error_details = str(traceback.format_exc())
            print(f"Error during pipeline step {step_func.__name__}: {error_details}")
            error_state = PRDState(
                run_id=current_state.run_id,
                step="Error",
                content=f"{current_state.content}\n\n---\n\n**Pipeline Error:**\n`{error_details}`",
                revision=current_state.revision + 1,
                diff=f"Error in step: {step_func.__name__}",
            )
            state_store.save(error_state)
            if streamer:
                await streamer.push_data(error_state.run_id, error_state.model_dump())
            break  # Stop the pipeline on error

    print("Pipeline complete.")
