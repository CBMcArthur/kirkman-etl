"""Abstract base class for the Load stage of the ETL pipeline.

BaseLoader defines the load() template method: a fixed
pre-load -> load -> post-load sequence that every concrete loader subclass
builds on. Subclasses implement the required _load() hook and may
optionally override _pre_load() / _post_load(). The template method itself
is never overridden.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

import pandas as pd

from kirkman_etl.core.models import RunContext, StageRecord, StageStatus


class BaseLoader(ABC):
    """Template for the Load stage: write validated data to its destination.

    load() is the one public template method and must not be overridden.
    It runs, in order, inside a single try block:
      1. _pre_load(context, df) -- identity hook.
      2. _load(context, df) -- abstract; required. Writes df to its
         destination and returns the number of rows written.
      3. _post_load(context, df) -- identity hook. Its returned DataFrame
         is not used for anything downstream (Load is terminal); it exists
         purely for structural consistency with the other three stages'
         hook signatures.

    If any step raises, the exception is caught, recorded as a FAILURE
    StageRecord, and re-raised; no later step in the sequence runs.

    rows_out, both in the StageRecord and in load()'s own return value,
    comes from _load()'s return, not from len(df). They will normally
    match, but _load()'s count is authoritative.
    """

    def load(self, context: RunContext, df: pd.DataFrame) -> int:
        """Run the Load stage and record its outcome on context.

        Args:
            context: Execution metadata for the current run. Not bound at
                construction -- passed fresh on each call so loader
                instances remain stateless and reusable across runs.
            df: The DataFrame produced by the Validate stage.

        Returns:
            The number of rows written, as returned by _load().

        Raises:
            Exception: Whatever _pre_load, _load, or _post_load raises,
                after recording a FAILURE StageRecord on context.
        """
        rows_in = len(df)
        started_at = datetime.now(UTC)
        try:
            df = self._pre_load(context, df)
            rows_out = self._load(context, df)
            self._post_load(context, df)
        except Exception as e:
            context.add_stage_record(
                StageRecord(
                    stage_name="load",
                    status=StageStatus.FAILURE,
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                    rows_in=rows_in,
                    rows_out=None,
                    error_message=str(e),
                )
            )
            raise

        context.add_stage_record(
            StageRecord(
                stage_name="load",
                status=StageStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                rows_in=rows_in,
                rows_out=rows_out,
            )
        )
        return rows_out

    def _pre_load(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Identity by default. Override for pre-load preparation."""
        return df

    @abstractmethod
    def _load(self, context: RunContext, df: pd.DataFrame) -> int:
        """Write df to its destination.

        Required. Returns the number of rows written -- never None or
        Optional. Failure signals only through raising, never a sentinel
        return; 0 is a valid, meaningful success (an empty input
        legitimately produced nothing to write). Do not judge what counts
        as "validated" here -- that is Validate's job.

        Args:
            context: Execution metadata for the current run.
            df: The DataFrame produced by the Validate stage (post
                _pre_load).

        Returns:
            The number of rows written.
        """
        raise NotImplementedError

    def _post_load(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Identity by default. Its return value is unused (Load is terminal)."""
        return df
