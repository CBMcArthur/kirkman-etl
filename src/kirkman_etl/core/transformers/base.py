"""Abstract base class for the Transform stage of the ETL pipeline.

BaseTransformer defines the transform() template method: a fixed
pre-transform -> transform -> post-transform sequence that every concrete
transformer subclass builds on. Subclasses implement the required
_transform() hook and may optionally override _pre_transform() /
_post_transform(). The template method itself is never overridden.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

import pandas as pd

from kirkman_etl.core.models import RunContext, StageRecord, StageStatus


class BaseTransformer(ABC):
    """Template for the Transform stage: establish canonical, typed data.

    transform() is the one public template method and must not be
    overridden. It runs, in order, inside a single try block:
      1. _pre_transform(context, df) -- identity hook.
      2. _transform(context, df) -- abstract; required. The first and only
         place real dtypes are established -- Extract hands off an
         all-string DataFrame. Also responsible for unit/format conversion
         and mapping to canonical field names.
      3. _post_transform(context, df) -- identity hook.

    If any step raises, the exception is caught, recorded as a FAILURE
    StageRecord, and re-raised; no later step in the sequence runs.
    """

    def transform(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Run the Transform stage and record its outcome on context.

        Args:
            context: Execution metadata for the current run. Not bound at
                construction -- passed fresh on each call so transformer
                instances remain stateless and reusable across runs.
            df: The DataFrame produced by the Extract stage.

        Returns:
            The canonical, typed DataFrame (post _post_transform).

        Raises:
            Exception: Whatever _pre_transform, _transform, or
                _post_transform raises, after recording a FAILURE
                StageRecord on context.
        """
        rows_in = len(df)
        started_at = datetime.now(UTC)
        try:
            df = self._pre_transform(context, df)
            df = self._transform(context, df)
            df = self._post_transform(context, df)
        except Exception as e:
            context.add_stage_record(
                StageRecord(
                    stage_name="transform",
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
                stage_name="transform",
                status=StageStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                rows_in=rows_in,
                rows_out=len(df),
            )
        )
        return df

    def _pre_transform(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Identity by default. Override for pre-transform preparation."""
        return df

    @abstractmethod
    def _transform(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Establish real dtypes and map to the canonical schema.

        Required. The first and only place in the pipeline where real
        dtypes are established, alongside unit/format conversion and
        renaming to canonical field names. Do not judge whether a value is
        plausible here -- that is Validate's job.

        Args:
            context: Execution metadata for the current run.
            df: The DataFrame produced by the Extract stage (post
                _pre_transform).

        Returns:
            The canonical, typed DataFrame.
        """
        raise NotImplementedError

    def _post_transform(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Identity by default. Override for post-transform cleanup."""
        return df
