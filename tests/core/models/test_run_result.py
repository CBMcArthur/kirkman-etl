"""Tests for kirkman_etl.core.models.RunResult."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from kirkman_etl.core.models import RunResult, RunStatus


def _run_result(**overrides):
    started_at = overrides.pop("started_at", datetime.now(UTC))
    completed_at = overrides.pop("completed_at", started_at + timedelta(seconds=10))
    defaults = {
        "pipeline_name": "synthetic-pipeline",
        "source_id": "county-42",
        "run_id": "run-1",
        "status": RunStatus.SUCCESS,
        "started_at": started_at,
        "completed_at": completed_at,
        "rows_in": 100,
        "rows_out": 100,
    }
    defaults.update(overrides)
    return RunResult(**defaults)


def test_constructs_with_valid_input():
    result = _run_result()

    assert result.status is RunStatus.SUCCESS
    assert result.duration_seconds == 10.0


def test_missing_required_fields_raises():
    with pytest.raises(ValidationError):
        RunResult()


def test_failure_requires_error_message():
    with pytest.raises(ValidationError):
        _run_result(status=RunStatus.FAILURE, error_message=None)


def test_failure_with_error_message_succeeds():
    result = _run_result(status=RunStatus.FAILURE, error_message="extractor timed out")

    assert result.error_message == "extractor timed out"


def test_completed_before_started_raises():
    started_at = datetime.now(UTC)
    with pytest.raises(ValidationError):
        _run_result(started_at=started_at, completed_at=started_at - timedelta(seconds=1))


def test_is_immutable():
    result = _run_result()

    with pytest.raises(ValidationError):
        result.status = RunStatus.FAILURE
