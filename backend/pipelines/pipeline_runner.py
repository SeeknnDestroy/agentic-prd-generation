"""Functional async pipeline for running the agentic workflow."""

import asyncio
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

MAX_REVISIONS = 3
APPROVAL_PHRASE = "No issues found."


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
    await state_store.save(new_state)
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
    await state_store.save(new_state)
    return new_state


async def critique_and_revise_loop(
    current_state: PRDState,
    state_store: StateStore,
    adapter: BaseAdapter,
    streamer: StreamerService | None,
) -> PRDState:
    """Run the critique and revise loop until the PRD is approved."""
    for i in range(MAX_REVISIONS):
        print(f"Running critique step (Revision {i + 1}/{MAX_REVISIONS})...")
        critique_prompt = CRITIQUE_PROMPT.format(draft=current_state.content)
        critique: str = await adapter.call_llm(critique_prompt)

        if APPROVAL_PHRASE in critique:
            print("PRD approved. Exiting revision loop.")
            break

        content_with_critique = (
            f"{current_state.content}\n\n---\n\n## Critique\n\n{critique}"
        )
        critique_state = PRDState(
            run_id=current_state.run_id,
            step="Critique",
            content=content_with_critique,
            revision=current_state.revision + 1,
            diff=create_diff(current_state.content, content_with_critique),
        )
        await state_store.save(critique_state)
        if streamer:
            await streamer.push_data(critique_state.run_id, critique_state.model_dump())

        print(f"Running revise step (Revision {i + 1}/{MAX_REVISIONS})...")
        revise_prompt = REVISE_PROMPT.format(
            draft=current_state.content, critique=critique
        )
        new_content: str = await adapter.call_llm(revise_prompt)

        revised_state = PRDState(
            run_id=current_state.run_id,
            step="Critique",  # Stay in critique for the next loop iteration
            content=new_content,
            revision=critique_state.revision + 1,
            diff=create_diff(critique_state.content, new_content),
        )
        await state_store.save(revised_state)
        if streamer:
            await streamer.push_data(revised_state.run_id, revised_state.model_dump())
        current_state = revised_state
        await asyncio.sleep(1)  # Small delay between revisions

    return current_state


PIPELINE_STAGES: list[
    Callable[
        [PRDState, StateStore, BaseAdapter],
        Awaitable[PRDState],
    ]
] = [outline_step, draft_step]


async def run_pipeline(
    initial_state: PRDState,
    state_store: StateStore,
    adapter: BaseAdapter,
    streamer: StreamerService | None = None,
) -> None:
    """
    Runs the full agentic pipeline from outline to completion.
    """
    current_state = initial_state
    if streamer:
        await streamer.push_data(current_state.run_id, current_state.model_dump())

    try:
        for step_func in PIPELINE_STAGES:
            current_state = await step_func(current_state, state_store, adapter)
            if streamer:
                await streamer.push_data(
                    current_state.run_id, current_state.model_dump()
                )

        current_state = await critique_and_revise_loop(
            current_state, state_store, adapter, streamer
        )

        final_state = PRDState(
            run_id=current_state.run_id,
            step="Complete",
            content=current_state.content,
            revision=current_state.revision + 1,
            diff=create_diff(current_state.content, current_state.content),
        )
        await state_store.save(final_state)
        if streamer:
            await streamer.push_data(final_state.run_id, final_state.model_dump())

    except Exception:
        error_details = str(traceback.format_exc())
        print(f"Error during pipeline: {error_details}")
        error_state = PRDState(
            run_id=current_state.run_id,
            step="Error",
            content=f"{current_state.content}\n\n---\n\n**Pipeline Error:**\n`{error_details}`",
            revision=current_state.revision + 1,
            diff="Error occurred.",
        )
        await state_store.save(error_state)
        if streamer:
            await streamer.push_data(error_state.run_id, error_state.model_dump())

    print("Pipeline complete.")
