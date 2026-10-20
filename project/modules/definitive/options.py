"""Strict patch selections; unfinished features cannot silently do nothing."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path


PENDING = {
    "hd_portraits": "HD pack can be exported separately; installation needs emulator validation.",
    "retranslation": "Fan script imported; ROM block mapping and layout review are incomplete.",
    "story_mode": "One-hit kills require testing against scripted battles and invulnerable phases.",
    "max_gold": "Persistent money patch has not been audited against spending and save/load.",
    "weight_fix": "The proven Bulimy cap correction is included in bug_fixes; a new body-weight combat formula would be a balance change.",
}


@dataclass(frozen=True)
class Options:
    bug_fixes: bool = True
    yellow_names: bool = False
    double_xp: bool = False
    encounters: str = "normal"
    hd_portraits: bool = False
    retranslation: bool = False
    story_mode: bool = False
    max_gold: bool = False
    weight_fix: bool = False

    def validate(self):
        for key, value in asdict(self).items():
            if key == "encounters":
                if value not in ("normal", "half", "none"):
                    raise ValueError("encounters must be normal, half, or none")
                if value == "half":
                    raise ValueError("Half encounters needs complete field and world-map scheduling analysis")
            elif type(value) is not bool:
                raise ValueError(f"{key} must be true or false")
            elif value and key in PENDING:
                raise ValueError(f"{key}: {PENDING[key]}")
        return self

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) - cls.__dataclass_fields__.keys():
            raise ValueError("Unknown patch option or invalid options object")
        return cls(**value).validate()

    @classmethod
    def load(cls, path: Path):
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8-sig")))

    def save(self, path: Path):
        self.validate()
        path.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
