"""Tests for kirkman_etl.core.extractors.BaseExtractor."""

import pandas as pd
import pytest

from kirkman_etl.core.extractors import BaseExtractor
from kirkman_etl.core.models import StageStatus


class RecordingExtractor(BaseExtractor):
    """Trivial concrete extractor that records hook call order and can be
    configured to raise from any hook."""

    def __init__(self, raw_writer, raise_from: str | None = None):
        super().__init__(raw_writer)
        self.calls: list[str] = []
        self._raise_from = raise_from

    def _pre_extract(self, context) -> None:
        self.calls.append("pre_extract")
        if self._raise_from == "pre_extract":
            raise ValueError("boom in pre_extract")

    def _extract(self, context) -> pd.DataFrame:
        self.calls.append("extract")
        if self._raise_from == "extract":
            raise ValueError("boom in extract")
        return pd.DataFrame({"a": [1, 2, 3]})

    def _post_extract(self, context, df: pd.DataFrame) -> pd.DataFrame:
        self.calls.append("post_extract")
        if self._raise_from == "post_extract":
            raise ValueError("boom in post_extract")
        return df


class RaisingRawWriter:
    def write(self, df, context) -> None:
        raise ValueError("boom in raw writer")


def test_template_flow_runs_in_order(raw_writer, context):
    extractor = RecordingExtractor(raw_writer)

    extractor.extract(context)

    assert extractor.calls == ["pre_extract", "extract", "post_extract"]


def test_raw_writer_called_once_after_post_extract(raw_writer, context):
    extractor = RecordingExtractor(raw_writer)

    df = extractor.extract(context)

    assert len(raw_writer.calls) == 1
    written_df, written_context = raw_writer.calls[0]
    assert written_df.equals(df)
    assert written_context is context


def test_raw_writer_is_required_constructor_argument():
    with pytest.raises(TypeError):
        RecordingExtractor()


def test_success_records_success_stage_record(raw_writer, context):
    extractor = RecordingExtractor(raw_writer)

    df = extractor.extract(context)

    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.stage_name == "extract"
    assert record.status == StageStatus.SUCCESS
    assert record.rows_in is None
    assert record.rows_out == len(df)
    assert record.error_message is None


@pytest.mark.parametrize("raise_from", ["pre_extract", "extract", "post_extract"])
def test_hook_exception_produces_failure_record_and_reraises(raw_writer, context, raise_from):
    extractor = RecordingExtractor(raw_writer, raise_from=raise_from)

    with pytest.raises(ValueError, match="boom"):
        extractor.extract(context)

    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.stage_name == "extract"
    assert record.status == StageStatus.FAILURE
    assert record.rows_in is None
    assert record.rows_out is None
    assert "boom" in record.error_message

    # Confirm nothing later in the sequence ran.
    hook_order = ["pre_extract", "extract", "post_extract"]
    failed_index = hook_order.index(raise_from)
    assert extractor.calls == hook_order[: failed_index + 1]

    # Raw writer must not be called if extraction itself failed.
    assert raw_writer.calls == []


def test_raw_writer_exception_produces_failure_record_and_reraises(context):
    extractor = RecordingExtractor(RaisingRawWriter())

    with pytest.raises(ValueError, match="boom in raw writer"):
        extractor.extract(context)

    assert extractor.calls == ["pre_extract", "extract", "post_extract"]
    assert len(context.stage_records) == 1
    record = context.stage_records[0]
    assert record.status == StageStatus.FAILURE
    assert record.rows_in is None
    assert record.rows_out is None
    assert "boom in raw writer" in record.error_message


def test_extractor_cannot_be_instantiated_without_extract_implementation(raw_writer):
    with pytest.raises(TypeError):
        BaseExtractor(raw_writer)
