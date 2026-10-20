"""Resolve active test discs through the same local registry as project builds."""

from pathlib import Path

from shared.paths import PROJECT_ROOT
from shared.project_registry import configured_path, load_registry


def source_disc_path(source_id: str) -> Path:
    """Use the declared donor without falling back to another disc or release.

    Historical byte fixtures and save migrations retain their own identities.
    Current campaign tests request ``mass_driver_base`` for the normalized V166
    source; raw donor-allocation tests request ``pw_disc2`` explicitly.
    """
    registry = load_registry(PROJECT_ROOT)
    return configured_path(
        PROJECT_ROOT,
        registry["sources"][source_id].get("path"),
        f"sources.{source_id}.path",
    )
