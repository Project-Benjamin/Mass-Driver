"""Compatibility discovery wrapper for shared.tests.test_migrate_duckstation_disc_state."""
from importlib import import_module
_implementation = import_module('shared.tests.test_migrate_duckstation_disc_state')
globals().update({key:value for key,value in vars(_implementation).items() if not key.startswith("__")})
