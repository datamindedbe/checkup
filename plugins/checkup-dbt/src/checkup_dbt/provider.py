"""dbt manifest provider for checkup."""

import json
import logging
import os
from pathlib import Path
from typing import Any, ClassVar

from dbt.cli.main import dbtRunner
from dbt.contracts.graph.manifest import Manifest

from checkup.provider import Provider

logger = logging.getLogger(__name__)


class DbtManifestProvider(Provider):
    """Provides dbt manifest from file or by parsing project.

    Supports two modes:
    1. manifest_path: Load from pre-generated manifest.json
    2. dbt_project_dir: Run dbt parse to generate manifest

    Example:
        # From file
        DbtManifestProvider(manifest_path="./target/manifest.json")

        # From project
        DbtManifestProvider(dbt_project_dir="./my_dbt_project")
    """

    name: ClassVar[str] = "dbt"

    def __init__(
        self,
        manifest_path: str | Path | None = None,
        dbt_project_dir: str | Path | None = None,
        profiles_dir: str | Path | None = None,
    ):
        """Initialize DbtManifestProvider.

        Args:
            manifest_path: Path to pre-generated manifest.json
            dbt_project_dir: Path to dbt project (runs dbt parse)
            profiles_dir: Optional profiles directory (defaults to project dir)

        Raises:
            ValueError: If neither manifest_path nor dbt_project_dir provided
        """
        if manifest_path is None and dbt_project_dir is None:
            raise ValueError("Must provide either 'manifest_path' or 'dbt_project_dir'")

        self.manifest_path = Path(manifest_path) if manifest_path else None
        self.dbt_project_dir = Path(dbt_project_dir) if dbt_project_dir else None
        self.profiles_dir = Path(profiles_dir) if profiles_dir else None

    def provide(self) -> dict[str, Any]:
        """Load dbt manifest from file or by parsing project.

        Returns:
            Dict with 'manifest' key containing Manifest object
        """
        if self.manifest_path:
            return self._load_from_file()
        return self._parse_project()

    def _load_from_file(self) -> dict[str, Any]:
        """Load manifest from pre-generated file."""
        logger.info(f"Loading manifest from {self.manifest_path}")

        with open(self.manifest_path) as f:
            manifest_dict = json.load(f)

        manifest = Manifest.from_dict(manifest_dict)
        return {"manifest": manifest}

    def _parse_project(self) -> dict[str, Any]:
        """Parse dbt project to generate manifest."""
        logger.info(f"Parsing dbt project at {self.dbt_project_dir}")

        cwd = Path.cwd()

        try:
            common_args = ["--project-dir", str(self.dbt_project_dir)]

            profiles_dir = self.profiles_dir or self.dbt_project_dir
            common_args.extend(["--profiles-dir", str(profiles_dir)])

            logger.info("Running dbt deps...")
            deps_result = dbtRunner().invoke(["deps", *common_args])
            if not deps_result.success:
                raise RuntimeError(f"dbt deps failed: {deps_result.exception}")

            logger.info("Running dbt parse...")
            parse_result = dbtRunner().invoke(["parse", *common_args])
            if not parse_result.success:
                raise RuntimeError(f"dbt parse failed: {parse_result.exception}")

            manifest = parse_result.result
            return {"manifest": manifest}

        finally:
            os.chdir(cwd)
