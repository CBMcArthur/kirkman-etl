"""Source configuration model.

Phase 1 stub: describes a data source only well enough to drive a synthetic
test pipeline. Field definitions here are deliberately minimal and will be
expanded once real connectors and extractors exist to design against.
"""

from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    """Identifies a single data source within a pipeline run."""

    source_id: str = Field(min_length=1, description="Unique identifier for this source.")
    name: str = Field(min_length=1, description="Human-readable name for this source.")
