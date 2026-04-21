import logging
from typing import ClassVar

import yaml

from checkup.metric import Measurement, Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtFlaggedPackagesMetric(DbtMetric):
    """
    Metric that counts flagged packages in packages.yml.

    Checks packages.yml for packages matching the configured flagged_packages list.
    Useful for identifying deprecated, insecure, or non-approved packages.

    Example:
        class DeprecatedPackagesMetric(DbtFlaggedPackagesMetric):
            flagged_packages: list[str] = [
                "https://github.com/org/deprecated-package",
                "https://github.com/org/insecure-package",
            ]
    """

    name: ClassVar[str] = "dbt_flagged_packages"
    description: ClassVar[str] = "Number of flagged packages in packages.yml"
    unit: ClassVar[str] = "packages"

    flagged_packages: list[str]

    def calculate(
        self, context: Context, measurements: dict[type[Metric], Measurement]
    ) -> Measurement:
        project_dir = self.get_project_dir(context)
        packages_path = project_dir / "packages.yml"

        if not packages_path.exists():
            logger.warning(f"packages.yml not found at {packages_path}")
            return self.measurement(value=0, diagnostic="packages.yml not found")

        with open(packages_path) as f:
            packages_data = yaml.safe_load(f)

        if not packages_data or "packages" not in packages_data:
            return self.measurement(
                value=0, diagnostic="No packages defined in packages.yml"
            )

        flagged = []
        for package in packages_data["packages"]:
            if "git" in package:
                for flagged_package in self.flagged_packages:
                    if flagged_package in package["git"]:
                        flagged.append(package["git"])
                        break

        value = len(flagged)
        diagnostic = f"Flagged packages: {', '.join(flagged)}" if flagged else ""
        logger.info(f"Found {value} flagged packages")
        return self.measurement(value=value, diagnostic=diagnostic)
