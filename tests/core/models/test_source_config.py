"""Tests for kirkman_etl.core.models.SourceConfig."""

import pytest
from pydantic import ValidationError

from kirkman_etl.core.models import SourceConfig


def test_constructs_with_valid_input():
    source = SourceConfig(source_id="county-42", name="Synthetic County")

    assert source.source_id == "county-42"
    assert source.name == "Synthetic County"


def test_missing_required_fields_raises():
    with pytest.raises(ValidationError):
        SourceConfig()


def test_empty_source_id_raises():
    with pytest.raises(ValidationError):
        SourceConfig(source_id="", name="Synthetic County")


def test_empty_name_raises():
    with pytest.raises(ValidationError):
        SourceConfig(source_id="county-42", name="")
