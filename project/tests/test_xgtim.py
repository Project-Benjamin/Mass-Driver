"""Legacy discovery wrapper for shared.tests.test_xgtim."""

from importlib import import_module as _import_module

_implementation = _import_module("shared.tests.test_xgtim")
# Keep this wrapper's __file__ for unittest discover's location check.
# Export private buddy-test helpers as well as the canonical test classes.
globals().update({
    name: value for name, value in vars(_implementation).items()
    if not name.startswith("__")
})
