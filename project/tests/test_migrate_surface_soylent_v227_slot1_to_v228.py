"""Legacy discovery wrapper for modules.soylent_system.tests.test_migrate_surface_soylent_v227_slot1_to_v228."""

from importlib import import_module as _import_module

_implementation = _import_module("modules.soylent_system.tests.test_migrate_surface_soylent_v227_slot1_to_v228")
# Keep this wrapper's __file__ for unittest discover's location check.
# Export private buddy-test helpers as well as the canonical test classes.
globals().update({
    name: value for name, value in vars(_implementation).items()
    if not name.startswith("__")
})
