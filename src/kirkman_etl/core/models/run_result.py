"""Flat, queryable summary of a completed pipeline run.

RunResult is the durable artifact a future run-metadata store persists (one
row per run). It is derived from a completed RunContext but intentionally
flat -- full per-stage detail belongs to RunContext, not here.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class RunStatus(StrEnum):
    """Overall outcome of a pipeline run."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class RunResult(BaseModel):
    """Summary of a completed pipeline run."""

    model_config = ConfigDict(frozen=True)

    pipeline_name: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    status: RunStatus
    started_at: datetime
    completed_at: datetime
    rows_in: int | None = Field(default=None, ge=0)
    rows_out: int | None = Field(default=None, ge=0)
    error_message: str | None = None

    @computed_field
    @property
    def duration_seconds(self) -> float:
        """Wall-clock duration of the run, in seconds."""
        return (self.completed_at - self.started_at).total_seconds()

    @model_validator(mode="after")
    def _check_timestamps_and_error(self) -> "RunResult":
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not be before started_at")
        if self.status is RunStatus.FAILURE and not self.error_message:
            raise ValueError("error_message is required when status is FAILURE")
        return self
