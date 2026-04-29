import logging

import yaml

from checkup.measurement import Measurement, Measurements
from checkup.types import Context
from checkup_dbt.metrics.base import DbtMetric

logger = logging.getLogger(__name__)


class DbtProfileHostMetric(DbtMetric):
    """
    Extracts the host value from profiles.yml.

    Searches for a host configuration in the specified profile and target.
    If profile is not specified, searches all profiles.
    The target must be configured.

    Example:
        DbtProfileHostMetric(
            name="dbt_profile_host_dev",
            target="dev"
        )

        DbtProfileHostMetric(
            name="dbt_profile_host_prod",
            profile="my_project",
            target="prod"
        )
    """

    name: str = "dbt_profile_host"
    description: str = "The host configured in profiles.yml"
    unit: str = "url"

    profile: str | None = None
    target: str

    def calculate(self, context: Context, measurements: Measurements) -> Measurement:
        project_dir = self.get_project_dir(context)
        profiles_path = project_dir / "profiles.yml"

        if not profiles_path.exists():
            logger.warning(f"profiles.yml not found at {profiles_path}")
            return self.measure(value=None, diagnostic="profiles.yml not found")

        with open(profiles_path) as f:
            profiles = yaml.safe_load(f)

        if not profiles:
            return self.measure(value=None, diagnostic="profiles.yml is empty")

        host = self._find_host(profiles)
        if host:
            diagnostic = f"Host: {host}"
        else:
            diagnostic = f"No host found for target '{self.target}'"
        return self.measure(value=host, diagnostic=diagnostic)

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
