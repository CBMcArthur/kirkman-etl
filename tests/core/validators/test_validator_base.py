"""Tests for kirkman_etl.core.validators.BaseValidator."""

import pandas as pd
import pytest

from kirkman_etl.core.models import StageStatus
from kirkman_etl.core.validators import BaseValidator


class RecordingValidator(BaseValidator):
    """Trivial concrete validator that records hook call order and can be
    configured to raise from any hook."""

    def __init__(self, raise_from: str | None = None):
        self.calls: list[str] = []
        self._raise_from = raise_from

    def _pre_validate(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("pre_validate")
        if self._raise_from == "pre_validate":
            raise ValueError("boom in pre_validate")
        return df

    def _validate(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("validate")
        if self._raise_from == "validate":
            raise ValueError("boom in validate")
        # Null out implausible values in "b", drop rows where "a" fails a check.
        df = df.copy()
        df.loc[df["b"] < 0, "b"] = None
        return df

    def _post_validate(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("post_validate")
        if self._raise_from == "post_validate":
            raise ValueError("boom in post_validate")
        return df


class RowDroppingValidator(BaseValidator):
    """Drops rows failing a plausibility check instead of nulling them."""

    def _validate(self, context, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["b"] >= 0]


def test_template_flow_runs_in_order(context, input_df):
    validator = RecordingValidator()

    validator.validate(context, input_df)

    assert validator.calls == ["pre_validate", "validate", "post_validate"]


def test_nulling_attribute_does_not_raise_and_succeeds(context, input_df):
    validator = RecordingValidator()

    df = validator.validate(context, input_df)

    assert df["b"].isna().sum() == 1
    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.status == StageStatus.SUCCESS
    assert record.rows_in == len(input_df)
    assert record.rows_out == len(df)
    assert record.error_message is None


def test_dropping_row_does_not_raise_and_succeeds(context, input_df):
    validator = RowDroppingValidator()

    df = validator.validate(context, input_df)

    assert len(df) == len(input_df) - 1
    record = context.stage_records[0]
    assert record.status == StageStatus.SUCCESS
    assert record.rows_in == len(input_df)
    assert record.rows_out == len(df)


@pytest.mark.parametrize("raise_from", ["pre_validate", "validate", "post_validate"])
def test_hook_exception_produces_failure_record_and_reraises(context, input_df, raise_from):
    validator = RecordingValidator(raise_from=raise_from)

    with pytest.raises(ValueError, match="boom"):
        validator.validate(context, input_df)

    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.stage_name == "validate"
    assert record.status == StageStatus.FAILURE
    assert record.rows_in == len(input_df)
    assert record.rows_out is None
    assert "boom" in record.error_message

    hook_order = ["pre_validate", "validate", "post_validate"]
    failed_index = hook_order.index(raise_from)
    assert validator.calls == hook_order[: failed_index + 1]


def test_validator_cannot_be_instantiated_without_validate_implementation():
    with pytest.raises(TypeError):
        BaseValidator()
