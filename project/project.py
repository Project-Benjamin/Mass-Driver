#!/usr/bin/env python3
"""One entry point for module discovery, validation, and reproducible builds."""

from pathlib import Path

from shared.project_registry import main


if __name__ == "__main__":
    raise SystemExit(main(root=Path(__file__).resolve().parent))
