"""Compatibility discovery wrapper for modules.mass_driver.tests.test_xgzeboim_missiles."""
from importlib import import_module
_implementation = import_module('modules.mass_driver.tests.test_xgzeboim_missiles')
globals().update({key:value for key,value in vars(_implementation).items() if not key.startswith("__")})
