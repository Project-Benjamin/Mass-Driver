"""Compatibility discovery wrapper for modules.mass_driver.tests.test_repair_guardian_v143_state."""
from importlib import import_module
_implementation = import_module('modules.mass_driver.tests.test_repair_guardian_v143_state')
globals().update({key:value for key,value in vars(_implementation).items() if not key.startswith("__")})
