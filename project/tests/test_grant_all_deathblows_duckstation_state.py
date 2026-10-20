"""Compatibility discovery wrapper for shared.tests.test_grant_all_deathblows_duckstation_state."""
from importlib import import_module
_implementation = import_module('shared.tests.test_grant_all_deathblows_duckstation_state')
globals().update({key:value for key,value in vars(_implementation).items() if not key.startswith("__")})
