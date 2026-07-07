"""Runtime execution metadata for a single pipeline run.

RunContext is passed as a method argument to each pipeline stage (extractor,
transformer, loader) rather than bound to a stage at construction, so stage
instances remain reusable across multiple runs. Identity fields are fixed at
construction; stage_records grows over the run's lifetime as each stage
appends its own record.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class StageStatus(StrEnum):
    """Outcome of a single pipeline stage's execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


class StageRecord(BaseModel):
    """Immutable record of a single stage's execution, appended to a RunContext."""

    model_config = ConfigDict(frozen=True)

    stage_name: str = Field(min_length=1)
    status: StageStatus
    started_at: datetime
    completed_at: datetime
    rows_in: int | None = Field(default=None, ge=0)
    rows_out: int | None = Field(default=None, ge=0)
    error_message: str | None = None

    @computed_field
    @property
    def duration_seconds(self) -> float:
        """Wall-clock duration of the stage, in seconds."""
        return (self.completed_at - self.started_at).total_seconds()

    @model_validator(mode="after")
    def _check_timestamps_and_error(self) -> "StageRecord":
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not be before started_at")
        if self.status is StageStatus.FAILURE and not self.error_message:
            raise ValueError("error_message is required when status is FAILURE")
        return self


class RunContext(BaseModel):
    """Append-only execution metadata for one pipeline run.

    Identity fields (pipeline_name, source_id, run_id, started_at) are fixed
    at construction and cannot be reassigned. stage_records grows as stages
    execute; use add_stage_record() rather than mutating the list directly so
    that a stage can never overwrite a record another stage already appended.
    """

    model_config = ConfigDict(frozen=True)

    pipeline_name: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    run_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stage_records: list[StageRecord] = Field(default_factory=list)

    def add_stage_record(self, record: StageRecord) -> None:
        """Append a new stage's execution record.

        Existing records are never modified or removed by this method.
        """
        self.stage_records.append(record)
