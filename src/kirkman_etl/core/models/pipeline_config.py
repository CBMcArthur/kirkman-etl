"""Pipeline configuration model.

Phase 1 stub: covers pipeline identity and the structural details a future
runner/CLI needs (which stages run, where output goes). Extractor settings,
domain-specific parameters, and environment overrides are out of scope until
real pipelines exist to design against.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

StageName = Literal["extract", "transform", "load"]


class PipelineConfig(BaseModel):
    """Structural configuration for a single pipeline."""

    pipeline_name: str = Field(min_length=1, description="Unique identifier for this pipeline.")
    source_id: str = Field(
        min_length=1, description="Identifier of the SourceConfig this pipeline reads from."
    )
    enabled_stages: list[StageName] = Field(
        default_factory=lambda: ["extract", "transform", "load"],
        min_length=1,
        description="Stages this pipeline runs, in order.",
    )
    output_path: Path = Field(description="Destination path for this pipeline's output.")
