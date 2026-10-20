#!/usr/bin/env python3
"""Compatibility entry point for archive.repairs.soylent_system.migrate_surface_soylent_v212_slot1_to_v213."""
from importlib import import_module
from pathlib import Path
import sys
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_implementation = import_module('archive.repairs.soylent_system.migrate_surface_soylent_v212_slot1_to_v213')
globals().update({key: value for key, value in vars(_implementation).items() if not key.startswith("__")})
if __name__ == "__main__":
    if hasattr(_implementation, "main"):
        raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
