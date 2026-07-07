"""Tests for kirkman_etl.core.models.PipelineConfig."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from kirkman_etl.core.models import PipelineConfig


def test_constructs_with_valid_input():
    config = PipelineConfig(
        pipeline_name="synthetic-pipeline",
        source_id="county-42",
        output_path=Path("/tmp/output"),
    )

    assert config.pipeline_name == "synthetic-pipeline"
    assert config.source_id == "county-42"
    assert config.enabled_stages == ["extract", "transform", "load"]
    assert config.output_path == Path("/tmp/output")


def test_missing_required_fields_raises():
    with pytest.raises(ValidationError):
        PipelineConfig()


def test_custom_enabled_stages():
    config = PipelineConfig(
        pipeline_name="synthetic-pipeline",
        source_id="county-42",
        enabled_stages=["extract"],
        output_path=Path("/tmp/output"),
    )

    assert config.enabled_stages == ["extract"]


def test_invalid_stage_name_raises():
    with pytest.raises(ValidationError):
        PipelineConfig(
            pipeline_name="synthetic-pipeline",
            source_id="county-42",
            enabled_stages=["extract", "not-a-real-stage"],
            output_path=Path("/tmp/output"),
        )


def test_empty_enabled_stages_raises():
    with pytest.raises(ValidationError):
        PipelineConfig(
            pipeline_name="synthetic-pipeline",
            source_id="county-42",
            enabled_stages=[],
            output_path=Path("/tmp/output"),
        )
