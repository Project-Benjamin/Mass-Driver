"""Legacy discovery wrapper for modules.rico.tests.test_migrate_rico_arc_faraway_fire_slot1."""

from importlib import import_module as _import_module

_implementation = _import_module("modules.rico.tests.test_migrate_rico_arc_faraway_fire_slot1")
# Keep this wrapper's __file__ for unittest discover's location check.
# Export private buddy-test helpers as well as the canonical test classes.
globals().update({
    name: value for name, value in vars(_implementation).items()
    if not name.startswith("__")
})
