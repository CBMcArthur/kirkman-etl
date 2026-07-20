"""Tests for kirkman_etl.core.models.RunContext and StageRecord."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from kirkman_etl.core.models import RunContext, StageRecord, StageStatus


def _stage_record(**overrides):
    started_at = overrides.pop("started_at", datetime.now(UTC))
    completed_at = overrides.pop("completed_at", started_at + timedelta(seconds=1))
    defaults = {
        "stage_name": "extract",
        "status": StageStatus.SUCCESS,
        "started_at": started_at,
        "completed_at": completed_at,
        "rows_in": 100,
        "rows_out": 100,
    }
    defaults.update(overrides)
    return StageRecord(**defaults)


def test_constructs_with_valid_input():
    context = RunContext(pipeline_name="synthetic-pipeline", source_id="county-42")

    assert context.pipeline_name == "synthetic-pipeline"
    assert context.source_id == "county-42"
    assert context.run_id
    assert context.stage_records == []


def test_missing_required_fields_raises():
    with pytest.raises(ValidationError):
        RunContext()


def test_identity_fields_are_immutable():
    context = RunContext(pipeline_name="synthetic-pipeline", source_id="county-42")

    with pytest.raises(ValidationError):
        context.pipeline_name = "renamed-pipeline"

    with pytest.raises(ValidationError):
        context.run_id = "new-run-id"


def test_add_stage_record_appends():
    context = RunContext(pipeline_name="synthetic-pipeline", source_id="county-42")
    record = _stage_record()

    context.add_stage_record(record)

    assert context.stage_records == [record]


def test_add_stage_record_does_not_replace_existing_records():
    context = RunContext(pipeline_name="synthetic-pipeline", source_id="county-42")
    first = _stage_record(stage_name="extract")
    second = _stage_record(stage_name="transform")

    context.add_stage_record(first)
    context.add_stage_record(second)

    assert context.stage_records == [first, second]


def test_stage_record_is_immutable_once_appended():
    record = _stage_record()

    with pytest.raises(ValidationError):
        record.status = StageStatus.FAILURE


def test_stage_record_failure_requires_error_message():
    with pytest.raises(ValidationError):
        _stage_record(status=StageStatus.FAILURE, error_message=None)


def test_stage_record_completed_before_started_raises():
    started_at = datetime.now(UTC)
    with pytest.raises(ValidationError):
        _stage_record(started_at=started_at, completed_at=started_at - timedelta(seconds=1))


def test_stage_record_duration_seconds():
    started_at = datetime.now(UTC)
    record = _stage_record(started_at=started_at, completed_at=started_at + timedelta(seconds=5))

    assert record.duration_seconds == 5.0


def test_stage_record_accepts_validate_stage_name():
    record = _stage_record(stage_name="validate")

    assert record.stage_name == "validate"


def test_stage_record_invalid_stage_name_raises():
    with pytest.raises(ValidationError):
        _stage_record(stage_name="not-a-real-stage")
