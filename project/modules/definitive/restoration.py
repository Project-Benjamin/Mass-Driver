"""Compose the verified retail corrections behind the patcher's bug-fix option."""
from modules.definitive.mechanics import build_mechanics_replacements
from modules.definitive.deus_fix import build_deus_replacements
from modules.definitive.description_fixes import build_description_replacements
from modules.definitive.weight_fix import build_weight_replacements


def build_restoration_replacements(read):
    replacements, mechanics = build_mechanics_replacements(read)
    # These two patches deliberately share battle resource 38. The Deus helper
    # validates the exact preceding mechanics edits before composing them.
    replacements, deus = build_deus_replacements(read, replacements)
    reports = {"mechanics": mechanics, "deus": deus}
    for name, builder in (("descriptions", build_description_replacements),
                          ("body_weight_gain", build_weight_replacements)):
        changes, report = builder(read)
        if replacements.keys() & changes.keys():
            raise ValueError(f"{name} overlaps another repair; explicit composition is required")
        replacements.update(changes)
        reports[name] = report
    return replacements, {
        "repairs": reports,
        "coverage": "Specific documented corrections; not an all-bugs or all-items/spells certification",
        "body_weight": "Native gain-item cap corrected; no new body-weight combat formula",
        "runtime_validation": "not tested in emulator",
    }
