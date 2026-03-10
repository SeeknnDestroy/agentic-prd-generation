"""Pydantic models for the Agentic PRD Generation platform."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

WorkflowStep = Literal["Outline", "Draft", "Critique", "Revise", "Complete", "Error"]
AdapterType = Literal["vanilla_openai", "vanilla_google"]


class PRDState(BaseModel, frozen=True):
    """
    Represents the complete state of a PRD generation run at a specific moment.

    This is an immutable model; any change in state results in a new instance.
    """

    run_id: str = Field(..., description="Unique identifier for the generation run.")
    idea: str = Field(..., description="The original product idea for the run.")
    step: WorkflowStep = Field(..., description="The current step in the workflow.")
    content: str = Field(..., description="The full Markdown content of the PRD.")
    revision: int = Field(..., description="The revision number, starting from 0.")
    diff: str | None = Field(
        None, description="The unified diff from the previous revision."
    )
    error: str | None = Field(
        None,
        description="Terminal error details when the run ends in an error state.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when this state was created (UTC).",
    )

    def to_event_payload(self) -> dict[str, Any]:
        """Return the public SSE payload for this run state."""
        return self.model_dump(
            mode="json",
            include={
                "run_id",
                "step",
                "content",
                "revision",
                "diff",
                "error",
                "created_at",
            },
        )


class GeneratePRDRequest(BaseModel):
    """
    Defines the request payload for initiating a PRD generation run.
    """

    idea: str = Field(..., description="The high-level project idea.", min_length=1)
    adapter: AdapterType = Field(
        "vanilla_openai",
        description="The implemented agent adapter to use for the run.",
    )


class GeneratePRDResponse(BaseModel):
    """
    Defines the response payload after successfully initiating a PRD run.
    """

    run_id: str = Field(..., description="The unique identifier for the new run.")
