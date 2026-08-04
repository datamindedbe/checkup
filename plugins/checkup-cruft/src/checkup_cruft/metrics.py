from datetime import UTC, datetime

from checkup.measurement import Measurement, Measurements
from checkup.metric import Metric
from checkup.provider import Provider
from checkup.types import Context
from checkup_cruft.provider import CruftProvider


class CruftMetric(Metric):
    """
    Base class for cruft-related metrics.
    """

    @classmethod
    def providers(cls) -> list[type[Provider]]:
        return [CruftProvider]

    def get_context(self, context: Context) -> dict:
        return context.get(CruftProvider.name, {})


class CruftLinkedMetric(CruftMetric):
    """
    Whether the project is linked to a cruft template.
    """

    name: str = "cruft_linked"
    description: str = "Whether a .cruft.json template link is present"
    unit: str = "boolean"

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        cruft = self.get_context(context)
        return self.measure(value=1 if cruft.get("present") else 0)


class CruftDaysSinceUpdateMetric(CruftMetric):
    """Days since the cruft template link (.cruft.json) was last updated."""

    name: str = "cruft_days_since_update"
    description: str = "Days since the last cruft template update"
    unit: str = "days"

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        cruft = self.get_context(context)
        last_update = cruft.get("last_update_date")
        if not isinstance(last_update, datetime):
            return self.measure(value=None, diagnostic="No .cruft.json found")
        delta = datetime.now(UTC) - last_update
        return self.measure(
            value=delta.days,
            diagnostic=f"Last cruft update: {last_update.strftime('%Y-%m-%d')}",
        )


class CruftConflictCountMetric(CruftMetric):
    """Number of unresolved cruft template conflicts (*.rej files)."""

    name: str = "cruft_conflicts"
    description: str = "Number of unresolved cruft template conflicts (.rej files)"
    unit: str = "files"

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        cruft = self.get_context(context)
        conflicts = cruft.get("conflict_files", [])
        return self.measure(value=len(conflicts), diagnostic=", ".join(conflicts))


class CruftCommitsBehindMetric(CruftMetric):
    """Template commits between the pinned commit and the template head.

    Requires the provider to run with fetch_template=True; otherwise None.
    """

    name: str = "cruft_commits_behind"
    description: str = "Number of template commits the project is behind"
    unit: str = "commits"

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        cruft = self.get_context(context)
        behind = cruft.get("commits_behind")
        if behind is None:
            return self.measure(value=None, diagnostic="Template not fetched")
        return self.measure(value=behind)


class CruftUpToDateMetric(CruftMetric):
    """Whether the pinned template commit matches the template head.

    Requires the provider to run with fetch_template=True; otherwise None.
    """

    name: str = "cruft_up_to_date"
    description: str = "Whether the project matches the latest template commit"
    unit: str = "boolean"

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        cruft = self.get_context(context)
        behind = cruft.get("commits_behind")
        if behind is None:
            return self.measure(value=None, diagnostic="Template not fetched")
        return self.measure(value=1 if behind == 0 else 0)


class CruftDaysBehindTemplateMetric(CruftMetric):
    """Days between the pinned template commit and the latest template commit.

    Requires the provider to run with fetch_template=True; otherwise None.
    """

    name: str = "cruft_days_behind_template"
    description: str = "Days between the pinned commit and the template head"
    unit: str = "days"

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        cruft = self.get_context(context)
        pinned = cruft.get("pinned_date")
        head = cruft.get("head_date")
        if not isinstance(pinned, datetime) or not isinstance(head, datetime):
            return self.measure(value=None, diagnostic="Template not fetched")
        return self.measure(value=(head - pinned).days)
