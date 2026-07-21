"""Shared fixtures for extractor tests."""

import pandas as pd
import pytest

from kirkman_etl.core.models import RunContext


class RecordingRawWriter:
    """Minimal in-memory RawStorageWriter test double.

    Records each write() call's arguments so tests can assert on how many
    times it was called and with what. Not a real implementation -- a
    concrete Parquet-backed writer is out of scope for this phase.
    """

    def __init__(self):
        self.calls: list[tuple[pd.DataFrame, RunContext]] = []

    def write(self, df: pd.DataFrame, context: RunContext) -> None:
        self.calls.append((df, context))


@pytest.fixture
def raw_writer() -> RecordingRawWriter:
    return RecordingRawWriter()


@pytest.fixture
def context() -> RunContext:
    return RunContext(pipeline_name="synthetic-pipeline", source_id="county-42")
