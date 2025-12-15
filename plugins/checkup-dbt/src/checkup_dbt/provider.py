"""dbt manifest provider for checkup."""

import json
import logging
import os
from pathlib import Path

from dbt.cli.main import dbtRunner
from dbt.contracts.graph.manifest import Manifest

from checkup.types import Context

logger = logging.getLogger(__name__)


def dbt_manifest_provider(context: Context) -> Context:
    """Load dbt manifest from file or by parsing project.

    Supports two modes:
    1. Pre-generated manifest: Pass 'manifest_path' in context
    2. Live parsing: Pass 'dbt_project_dir' in context (runs dbt deps + parse)

    Args:
        context: Context dict containing either 'manifest_path' or 'dbt_project_dir'

    Returns:
        Context enriched with 'dbt_manifest' (Manifest object)

    Raises:
        ValueError: If neither 'manifest_path' nor 'dbt_project_dir' is provided
    """
    # Option 1: Pre-generated manifest file
    if "manifest_path" in context:
        manifest_path = Path(context["manifest_path"])
        logger.info(f"Loading manifest from {manifest_path}")

        with open(manifest_path) as f:
            manifest_dict = json.load(f)

        manifest = Manifest.from_dict(manifest_dict)
        return {**context, "dbt_manifest": manifest}

    # Option 2: Parse dbt project live
    if "dbt_project_dir" in context:
        project_dir = Path(context["dbt_project_dir"])
        logger.info(f"Parsing dbt project at {project_dir}")

        # Store current working directory (dbt changes it)
        cwd = Path.cwd()

        try:
            # Build common args
            common_args = ["--project-dir", str(project_dir)]

            # Add profiles-dir if provided
            if "profiles_dir" in context:
                common_args.extend(["--profiles-dir", str(context["profiles_dir"])])
            else:
                # Default to project dir for profiles
                common_args.extend(["--profiles-dir", str(project_dir)])

            # Run dbt deps to install dependencies
            logger.info("Running dbt deps...")
            deps_result = dbtRunner().invoke(["deps", *common_args])
            if not deps_result.success:
                raise RuntimeError(f"dbt deps failed: {deps_result.exception}")

            # Run dbt parse to generate manifest
            logger.info("Running dbt parse...")
            parse_result = dbtRunner().invoke(["parse", *common_args])
            if not parse_result.success:
                raise RuntimeError(f"dbt parse failed: {parse_result.exception}")

            manifest = parse_result.result
            return {**context, "dbt_manifest": manifest}

        finally:
            # Restore working directory
            os.chdir(cwd)

    raise ValueError(
        "Context must contain either 'manifest_path' (path to manifest.json) "
        "or 'dbt_project_dir' (path to dbt project for live parsing)"
    )
