"""Abstract base class for the Extract stage of the ETL pipeline.

BaseExtractor defines the extract() template method: a fixed
pre-extract -> extract -> post-extract -> raw-write sequence that every
concrete extractor subclass builds on. Subclasses implement the required
_extract() hook and may optionally override _pre_extract() / _post_extract().
The template method itself is never overridden.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Protocol

import pandas as pd

from kirkman_etl.core.models import RunContext, StageRecord, StageStatus


class RawStorageWriter(Protocol):
    """Writes a DataFrame to the standardized raw-preservation store.

    This is an interface only. A concrete implementation (e.g. a Parquet-backed
    writer) is out of scope for this module and is defined separately.
    """

    def write(self, df: pd.DataFrame, context: RunContext) -> None:
        """Persist df as the raw-preservation snapshot for this run."""
        ...


class BaseExtractor(ABC):
    """Template for the Extract stage: pull source data into a DataFrame.

    extract() is the one public template method and must not be overridden.
    It runs, in order, inside a single try block:
      1. _pre_extract(context) -- no-op hook, override for e.g. opening a
         source connection.
      2. _extract(context) -- abstract; required. Pulls and structurally
         parses the source into a DataFrame.
      3. _post_extract(context, df) -- identity hook, override for
         extractor-specific structural cleanup.
      4. raw_writer.write(df, context) -- fixed call, not a hook. No
         subclass can see, override, or skip this; the raw snapshot of
         every extracted DataFrame is always written.

    If any step raises, the exception is caught, recorded as a FAILURE
    StageRecord, and re-raised; no later step in the sequence runs.
    """

    def __init__(self, raw_writer: RawStorageWriter):
        """Initialize the extractor.

        Args:
            raw_writer: Collaborator responsible for writing this stage's
                output to the raw-preservation store. Required -- there is
                no code path that constructs a BaseExtractor subclass
                without one.
        """
        self._raw_writer = raw_writer

    def extract(self, context: RunContext) -> pd.DataFrame:
        """Run the Extract stage and record its outcome on context.

        Args:
            context: Execution metadata for the current run. Not bound at
                construction -- passed fresh on each call so extractor
                instances remain stateless and reusable across runs.

        Returns:
            The extracted, structurally-cleaned DataFrame (post _post_extract).

        Raises:
            Exception: Whatever _pre_extract, _extract, _post_extract, or
                raw_writer.write raises, after recording a FAILURE
                StageRecord on context.
        """
        started_at = datetime.now(UTC)
        try:
            self._pre_extract(context)
            df = self._extract(context)
            df = self._post_extract(context, df)
            self._raw_writer.write(df, context)
        except Exception as e:
            context.add_stage_record(
                StageRecord(
                    stage_name="extract",
                    status=StageStatus.FAILURE,
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                    rows_in=None,
                    rows_out=None,
                    error_message=str(e),
                )
            )
            raise

        context.add_stage_record(
            StageRecord(
                stage_name="extract",
                status=StageStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                rows_in=None,
                rows_out=len(df),
            )
        )
        return df

    def _pre_extract(self, context: RunContext) -> None:
        """No-op by default. Override for e.g. opening a source connection."""

    @abstractmethod
    def _extract(self, context: RunContext) -> pd.DataFrame:
        """Pull data from the source and parse it into a DataFrame.

        Required. Conceptually responsible for structural cleanup only --
        stripping noise rows, normalizing character encoding, assigning row
        lineage (sequential 0-based row position plus run_id), and
        normalizing column casing. These responsibilities require a real
        source to parse against and are left to concrete subclasses; do not
        establish real dtypes or interpret what values mean here, that is
        Transform's job.

        Args:
            context: Execution metadata for the current run.

        Returns:
            The raw, structurally-parsed DataFrame.
        """
        raise NotImplementedError

    def _post_extract(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Identity by default. Override for extractor-specific cleanup."""
        return df
