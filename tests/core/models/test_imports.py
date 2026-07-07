"""Confirms the core models package exposes its public API cleanly."""


def test_models_import_from_package():
    from kirkman_etl.core.models import (
        PipelineConfig,
        RunContext,
        RunResult,
        RunStatus,
        SourceConfig,
        StageName,
        StageRecord,
        StageStatus,
    )

    assert PipelineConfig is not None
    assert RunContext is not None
    assert RunResult is not None
    assert RunStatus is not None
    assert SourceConfig is not None
    assert StageName is not None
    assert StageRecord is not None
    assert StageStatus is not None
