"""Functional async pipeline for running the agentic workflow."""

from collections.abc import Awaitable, Callable

from diff_match_patch import diff_match_patch
import structlog

from backend.agents.base_adapter import AdapterError, BaseAdapter
from backend.models import PRDState
from backend.pipelines.prompts import (
    CRITIQUE_PROMPT,
    DRAFT_PROMPT,
    OUTLINE_PROMPT,
    REVISE_PROMPT,
)
from backend.services.streamer import StreamerService
from backend.state.base import StateStore

logger = structlog.get_logger(__name__)

MAX_REVISIONS = 3
APPROVAL_PHRASE = "No issues found."
AUTO_DIFF = object()


def create_diff(text1: str, text2: str) -> str:
    """Generates a unified diff between two texts."""
    dmp = diff_match_patch()
    patches = dmp.patch_make(text1, text2)
    diff_text: str = dmp.patch_toText(patches)
    return diff_text


async def outline_step(
    current_state: PRDState,
    state_store: StateStore,
    adapter: BaseAdapter,
    streamer: StreamerService | None,
) -> PRDState:
    """Generate the outline for the PRD."""
    logger.info("pipeline_step_started", run_id=current_state.run_id, step="Outline")
    prompt = OUTLINE_PROMPT.format(idea=current_state.idea)
    new_content: str = await adapter.call_llm(prompt)
    new_state = _next_state(current_state, step="Outline", content=new_content)
    await _persist_state(new_state, state_store, streamer)
    return new_state


async def draft_step(
    current_state: PRDState,
    state_store: StateStore,
    adapter: BaseAdapter,
    streamer: StreamerService | None,
) -> PRDState:
    """Generate the draft for the PRD."""
    logger.info("pipeline_step_started", run_id=current_state.run_id, step="Draft")
    prompt = DRAFT_PROMPT.format(outline=current_state.content)
    new_content: str = await adapter.call_llm(prompt)
    new_state = _next_state(current_state, step="Draft", content=new_content)
    await _persist_state(new_state, state_store, streamer)
    return new_state


async def critique_and_revise_loop(
    current_state: PRDState,
    state_store: StateStore,
    adapter: BaseAdapter,
    streamer: StreamerService | None,
) -> PRDState:
    """Run the critique and revise loop until the PRD is approved."""
    for i in range(MAX_REVISIONS):
        logger.info(
            "pipeline_step_started",
            run_id=current_state.run_id,
            step="Critique",
            revision_attempt=i + 1,
        )
        critique_prompt = CRITIQUE_PROMPT.format(draft=current_state.content)
        critique: str = await adapter.call_llm(critique_prompt)
        critique_state = _next_state(
            current_state,
            step="Critique",
            content=current_state.content,
            diff=None,
        )
        await _persist_state(critique_state, state_store, streamer)
        current_state = critique_state

        if APPROVAL_PHRASE in critique:
            logger.info("pipeline_prd_approved", run_id=current_state.run_id)
            break

        logger.info(
            "pipeline_step_started",
            run_id=current_state.run_id,
            step="Revise",
            revision_attempt=i + 1,
        )
        revise_prompt = REVISE_PROMPT.format(
            draft=current_state.content, critique=critique
        )
        new_content: str = await adapter.call_llm(revise_prompt)
        revised_state = _next_state(
            current_state,
            step="Revise",
            content=new_content,
        )
        await _persist_state(revised_state, state_store, streamer)
        current_state = revised_state

    return current_state


PIPELINE_STAGES: list[
    Callable[
        [PRDState, StateStore, BaseAdapter, StreamerService | None],
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

    try:
        for step_func in PIPELINE_STAGES:
            current_state = await step_func(
                current_state,
                state_store,
                adapter,
                streamer,
            )

        current_state = await critique_and_revise_loop(
            current_state, state_store, adapter, streamer
        )

        final_state = _next_state(
            current_state,
            step="Complete",
            content=current_state.content,
            diff=None,
        )
        await _persist_state(final_state, state_store, streamer)
        logger.info("pipeline_completed", run_id=current_state.run_id)

    except AdapterError as exc:
        logger.warning(
            "pipeline_failed",
            run_id=current_state.run_id,
            provider=exc.provider,
            exc_info=True,
        )
        error_state = _next_state(
            current_state,
            step="Error",
            content=current_state.content,
            diff=None,
            error=str(exc),
        )
        await _persist_state(error_state, state_store, streamer)


def _next_state(
    current_state: PRDState,
    *,
    step: str,
    content: str,
    diff: str | None | object = AUTO_DIFF,
    error: str | None = None,
) -> PRDState:
    """Build the next immutable PRD state."""
    next_diff = (
        create_diff(current_state.content, content) if diff is AUTO_DIFF else diff
    )
    return PRDState(
        run_id=current_state.run_id,
        idea=current_state.idea,
        step=step,
        content=content,
        revision=current_state.revision + 1,
        diff=next_diff,
        error=error,
    )


async def _persist_state(
    state: PRDState,
    state_store: StateStore,
    streamer: StreamerService | None,
) -> None:
    """Persist a state update and publish it to subscribers."""
    await state_store.save(state)
    if streamer:
        await streamer.publish(state.run_id, state.to_event_payload())
