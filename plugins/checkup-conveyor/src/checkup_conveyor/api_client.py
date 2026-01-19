"""Conveyor API client for making authenticated HTTP requests."""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ConveyorApiClient:
    """Client for interacting with the Conveyor API.

    Handles authentication and common API operations.

    Example:
        client = ConveyorApiClient(api_key="my-key")
        project_id = client.get_project_id("my-project")
    """

    DEFAULT_BASE_URL = "https://app.conveyordata.com/api/v2"

    def __init__(self, api_key: str, base_url: str | None = None):
        """Initialize the API client.

        Args:
            api_key: Conveyor API key for authentication
            base_url: Optional base URL override (defaults to production)
        """
        self._api_key = api_key
        self._base_url = base_url or self.DEFAULT_BASE_URL

    def _get_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        return {"Authorization": f"Bearer {self._api_key}"}

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        """Make a GET request to the API.

        Args:
            endpoint: API endpoint (e.g., "/projects")
            params: Optional query parameters

        Returns:
            JSON response as dict
        """
        return requests.get(
            f"{self._base_url}{endpoint}", headers=self._get_headers(), params=params
        ).json()

    def get_project_id(self, project_name: str) -> str | None:
        """Get project ID by name.

        Args:
            project_name: Name of the project to find

        Returns:
            Project ID if found, None otherwise
        """
        projects = self._get("/projects", params={"name": project_name}).get("projects", [])

        if not projects:
            logger.warning("No Conveyor project found with name: %s", project_name)
            return None

        return projects[0]["id"]

    def get_environment_id(self, environment_name: str) -> str | None:
        """Get environment ID by name.

        Args:
            environment_name: Name of the environment to find

        Returns:
            Environment ID if found, None otherwise
        """
        environments = self._get(
            "/environments", params={"name": environment_name}
        ).get("environments", [])

        if not environments:
            logger.warning("No Conveyor environment found with name: %s", environment_name)
            return None

        return environments[0]["id"]
