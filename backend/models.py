"""Pydantic models for the Agentic PRD Generation platform.

These models define the shape of data used throughout the application,
ensuring type safety and clear contracts between components.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PRDState(BaseModel, frozen=True):
    """
    Represents the complete state of a PRD generation run at a specific moment.

    This is an immutable model; any change in state results in a new instance.
    """

    run_id: str = Field(..., description="Unique identifier for the generation run.")
    step: Literal[
        "Outline", "Research", "Draft", "Critique", "Revise", "Complete", "Error"
    ] = Field(..., description="The current step in the agentic workflow.")
    content: str = Field(..., description="The full Markdown content of the PRD.")
    revision: int = Field(..., description="The revision number, starting from 0.")
    diff: str | None = Field(
        None, description="The unified diff from the previous revision."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this state was created (UTC).",
    )


class GeneratePRDRequest(BaseModel):
    """
    Defines the request payload for initiating a PRD generation run.
    """

    idea: str = Field(..., description="The high-level project idea.", min_length=1)
    autonomy_level: Literal["Full", "Supervised"] = Field(
        "Full", description="The level of autonomy for the agentic workflow."
    )
    adapter: Literal["vanilla_openai", "vanilla_google", "crewai"] = Field(
        "vanilla_openai", description="The agent adapter to use for the run."
    )


class GeneratePRDResponse(BaseModel):
    """
    Defines the response payload after successfully initiating a PRD run.
    """

    run_id: str = Field(..., description="The unique identifier for the new run.")
