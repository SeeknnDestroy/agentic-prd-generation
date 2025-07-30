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
