"""Compatibility discovery wrapper for shared.tests.test_xgdeathblows."""
from importlib import import_module
_implementation = import_module('shared.tests.test_xgdeathblows')
globals().update({key:value for key,value in vars(_implementation).items() if not key.startswith("__")})
