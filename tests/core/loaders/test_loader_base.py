"""Tests for kirkman_etl.core.loaders.BaseLoader."""

import pandas as pd
import pytest

from kirkman_etl.core.loaders import BaseLoader
from kirkman_etl.core.models import StageStatus


class RecordingLoader(BaseLoader):
    """Trivial concrete loader that records hook call order, can be
    configured to raise from any hook, and writes fewer rows than it
    received to prove rows_out comes from _load()'s return."""

    def __init__(self, rows_written: int | None = None, raise_from: str | None = None):
        self.calls: list[str] = []
        self._rows_written = rows_written
        self._raise_from = raise_from

    def _pre_load(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("pre_load")
        if self._raise_from == "pre_load":
            raise ValueError("boom in pre_load")
        return df

    def _load(self, context, df: pd.DataFrame) -> int:
        self.calls.append("load")
        if self._raise_from == "load":
            raise ValueError("boom in load")
        return self._rows_written if self._rows_written is not None else len(df)

    def _post_load(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("post_load")
        if self._raise_from == "post_load":
            raise ValueError("boom in post_load")
        return df


def test_template_flow_runs_in_order(context, input_df):
    loader = RecordingLoader()

    loader.load(context, input_df)

    assert loader.calls == ["pre_load", "load", "post_load"]


def test_success_records_success_stage_record(context, input_df):
    loader = RecordingLoader()

    rows_out = loader.load(context, input_df)

    assert rows_out == len(input_df)
    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.stage_name == "load"
    assert record.status == StageStatus.SUCCESS
    assert record.rows_in == len(input_df)
    assert record.rows_out == rows_out
    assert record.error_message is None


def test_rows_out_comes_from_load_return_not_len_df(context, input_df):
    loader = RecordingLoader(rows_written=1)

    rows_out = loader.load(context, input_df)

    assert rows_out == 1
    assert rows_out != len(input_df)
    record = context.stage_records[0]
    assert record.rows_out == 1


def test_zero_rows_written_is_a_valid_success(context, input_df):
    loader = RecordingLoader(rows_written=0)

    rows_out = loader.load(context, input_df)

    assert rows_out == 0
    record = context.stage_records[0]
    assert record.status == StageStatus.SUCCESS
    assert record.rows_out == 0


@pytest.mark.parametrize("raise_from", ["pre_load", "load", "post_load"])
def test_hook_exception_produces_failure_record_and_reraises(context, input_df, raise_from):
    loader = RecordingLoader(raise_from=raise_from)

    with pytest.raises(ValueError, match="boom"):
        loader.load(context, input_df)

    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.stage_name == "load"
    assert record.status == StageStatus.FAILURE
    assert record.rows_in == len(input_df)
    assert record.rows_out is None
    assert "boom" in record.error_message

    hook_order = ["pre_load", "load", "post_load"]
    failed_index = hook_order.index(raise_from)
    assert loader.calls == hook_order[: failed_index + 1]


def test_loader_cannot_be_instantiated_without_load_implementation():
    with pytest.raises(TypeError):
        BaseLoader()
