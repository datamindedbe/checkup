import logging
from typing import ClassVar

import yaml

from checkup.metric import Metric
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtProfileHostMetric(DbtMetric):
    """Extracts the host value from profiles.yml.

    Searches for a host configuration in the specified profile and target.
    If profile is not specified, searches all profiles.
    The target must be configured.

    Example:
        class DevHostMetric(DbtProfileHostMetric):
            target: str = "dev"

        class ProdHostMetric(DbtProfileHostMetric):
            profile: str = "my_project"
            target: str = "prod"
    """

    name: ClassVar[str] = "dbt_profile_host"
    description: ClassVar[str] = "The host configured in profiles.yml"
    unit: ClassVar[str] = "url"

    profile: str | None = None
    target: str

    def calculate(self, context: Context, metrics: dict[type[Metric], Metric]) -> None:
        project_dir = self.get_project_dir(context)
        profiles_path = project_dir / "profiles.yml"

        if not profiles_path.exists():
            logger.warning(f"profiles.yml not found at {profiles_path}")
            self.value = None
            self.diagnostic = "profiles.yml not found"
            return

        with open(profiles_path) as f:
            profiles = yaml.safe_load(f)

        if not profiles:
            self.value = None
            self.diagnostic = "profiles.yml is empty"
            return

        host = self._find_host(profiles)
        self.value = host
        if host:
            self.diagnostic = f"Host: {host}"
        else:
            self.diagnostic = f"No host found for target '{self.target}'"

    def _find_host(self, profiles: dict) -> str | None:
        """Find host in profiles matching the configuration."""
        if self.profile:
            # Look in specific profile
            profile_data = profiles.get(self.profile, {})
            return profile_data.get("outputs", {}).get(self.target, {}).get("host")

        # Search all profiles
        for profile_name, profile_data in profiles.items():
            if not isinstance(profile_data, dict):
                continue
            host = profile_data.get("outputs", {}).get(self.target, {}).get("host")
            if host:
                logger.info(f"Found host in profile '{profile_name}': {host}")
                return host

        return None
