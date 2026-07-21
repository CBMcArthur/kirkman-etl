"""Shared fixtures for transformer tests."""

import pandas as pd
import pytest

from kirkman_etl.core.models import RunContext


@pytest.fixture
def context() -> RunContext:
    return RunContext(pipeline_name="synthetic-pipeline", source_id="county-42")


@pytest.fixture
def input_df() -> pd.DataFrame:
    return pd.DataFrame({"a": ["1", "2", "3"]})
