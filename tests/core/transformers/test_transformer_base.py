"""Tests for kirkman_etl.core.transformers.BaseTransformer."""

import pandas as pd
import pytest

from kirkman_etl.core.models import StageStatus
from kirkman_etl.core.transformers import BaseTransformer


class RecordingTransformer(BaseTransformer):
    """Trivial concrete transformer that records hook call order and can be
    configured to raise from any hook."""

    def __init__(self, raise_from: str | None = None):
        self.calls: list[str] = []
        self._raise_from = raise_from

    def _pre_transform(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("pre_transform")
        if self._raise_from == "pre_transform":
            raise ValueError("boom in pre_transform")
        return df

    def _transform(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("transform")
        if self._raise_from == "transform":
            raise ValueError("boom in transform")
        return df.assign(a=df["a"].astype(int))

    def _post_transform(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("post_transform")
        if self._raise_from == "post_transform":
            raise ValueError("boom in post_transform")
        return df


def test_template_flow_runs_in_order(context, input_df):
    transformer = RecordingTransformer()

    transformer.transform(context, input_df)

    assert transformer.calls == ["pre_transform", "transform", "post_transform"]


def test_success_records_success_stage_record(context, input_df):
    transformer = RecordingTransformer()

    df = transformer.transform(context, input_df)

    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.stage_name == "transform"
    assert record.status == StageStatus.SUCCESS
    assert record.rows_in == len(input_df)
    assert record.rows_out == len(df)
    assert record.error_message is None
    assert df["a"].dtype == int


@pytest.mark.parametrize("raise_from", ["pre_transform", "transform", "post_transform"])
def test_hook_exception_produces_failure_record_and_reraises(context, input_df, raise_from):
    transformer = RecordingTransformer(raise_from=raise_from)

    with pytest.raises(ValueError, match="boom"):
        transformer.transform(context, input_df)

    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.stage_name == "transform"
    assert record.status == StageStatus.FAILURE
    assert record.rows_in == len(input_df)
    assert record.rows_out is None
    assert "boom" in record.error_message

    hook_order = ["pre_transform", "transform", "post_transform"]
    failed_index = hook_order.index(raise_from)
    assert transformer.calls == hook_order[: failed_index + 1]


def test_transformer_cannot_be_instantiated_without_transform_implementation():
    with pytest.raises(TypeError):
        BaseTransformer()
