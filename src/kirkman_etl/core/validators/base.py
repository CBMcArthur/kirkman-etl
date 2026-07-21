"""Abstract base class for the Validate stage of the ETL pipeline.

BaseValidator defines the validate() template method: a fixed
pre-validate -> validate -> post-validate sequence that every concrete
validator subclass builds on. Subclasses implement the required
_validate() hook and may optionally override _pre_validate() /
_post_validate(). The template method itself is never overridden.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

import pandas as pd

from kirkman_etl.core.models import RunContext, StageRecord, StageStatus


class BaseValidator(ABC):
    """Template for the Validate stage: domain-plausibility checks.

    validate() is the one public template method and must not be
    overridden. It runs, in order, inside a single try block:
      1. _pre_validate(context, df) -- identity hook.
      2. _validate(context, df) -- abstract; required. Runs plausibility
         checks against typed, canonical data (Transform's output only --
         it never sees raw data).
      3. _post_validate(context, df) -- identity hook.

    If any step raises, the exception is caught, recorded as a FAILURE
    StageRecord, and re-raised; no later step in the sequence runs.

    _validate() has exactly two remediation actions available: null out a
    specific attribute value it doesn't trust, or drop the row entirely. It
    must never derive or compute a "corrected" replacement value -- that is
    Transform's job. Filtering rows and nulling attributes are handled
    inline in the returned DataFrame, without raising; validate() only
    raises for genuine execution failures (a bug, a missing expected
    column, something structurally wrong with the check itself), never
    because some rows failed a plausibility check. As a result, a future
    pipeline runner will never abort a run because of bad data -- only
    because of an actual bug in a stage.

    rows_out naturally reflects how many rows survived (rows_in - rows_out
    = rows dropped). There is no separate count of how many attributes were
    nulled in this pass -- that is a deliberate, deferred decision.
    """

    def validate(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Run the Validate stage and record its outcome on context.

        Args:
            context: Execution metadata for the current run. Not bound at
                construction -- passed fresh on each call so validator
                instances remain stateless and reusable across runs.
            df: The DataFrame produced by the Transform stage.

        Returns:
            The validated DataFrame (post _post_validate), with untrustworthy
            attribute values nulled and/or failing rows dropped.

        Raises:
            Exception: Whatever _pre_validate, _validate, or _post_validate
                raises, after recording a FAILURE StageRecord on context.
                Not raised merely because rows failed a plausibility check.
        """
        rows_in = len(df)
        started_at = datetime.now(UTC)
        try:
            df = self._pre_validate(context, df)
            df = self._validate(context, df)
            df = self._post_validate(context, df)
        except Exception as e:
            context.add_stage_record(
                StageRecord(
                    stage_name="validate",
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
                stage_name="validate",
                status=StageStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                rows_in=rows_in,
                rows_out=len(df),
            )
        )
        return df

    def _pre_validate(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Identity by default. Override for pre-validation preparation."""
        return df

    @abstractmethod
    def _validate(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Run domain-plausibility checks against typed, canonical data.

        Required. May null out untrustworthy attribute values or drop rows
        that fail a check. Must never compute a replacement value -- that
        belongs in Transform. Must not raise merely because rows fail a
        plausibility check; only raise for a genuine execution failure.

        Args:
            context: Execution metadata for the current run.
            df: The DataFrame produced by the Transform stage (post
                _pre_validate).

        Returns:
            The DataFrame with untrustworthy values nulled and/or failing
            rows dropped.
        """
        raise NotImplementedError

    def _post_validate(self, context: RunContext, df: pd.DataFrame) -> pd.DataFrame:
        """Identity by default. Override for post-validation cleanup."""
        return df
