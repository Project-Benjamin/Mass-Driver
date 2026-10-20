from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from tools.xgfield import build_field, parse_field
from tools.xgmissiles import (
    MISSILE_POSITIONS,
    MissileModelError,
    _audit_model0,
    _model_spans,
    build_stockpile_geometry,
    patch_mass_driver_stockpile,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DONOR = PROJECT_ROOT / "work" / "donor_1870"


class MissileGeometryTests(unittest.TestCase):
    def test_stockpile_geometry_counts_and_bounds(self) -> None:
        geometry = build_stockpile_geometry()
        self.assertEqual(len(MISSILE_POSITIONS), 8)
        self.assertEqual(len(geometry.vertices), 304)
        self.assertEqual(len(geometry.triangles), 448)
        self.assertTrue(all(v[1] <= -174 for v in geometry.vertices))
        self.assertEqual(min(v[1] for v in geometry.vertices), -570)
        self.assertEqual(max(v[1] for v in geometry.vertices), -174)
        for triangle in geometry.triangles:
            self.assertTrue(all(0 <= i < len(geometry.vertices) for i in triangle.indices[:3]))
            self.assertEqual(triangle.indices[3], 0)

    def test_wrong_input_is_rejected(self) -> None:
        with self.assertRaises(MissileModelError):
            patch_mass_driver_stockpile(bytes(128))

    @unittest.skipUnless(DONOR.is_dir(), "retail donor extraction is not present")
    def test_retail_patch_and_field_round_trip(self) -> None:
        source = (DONOR / "02_models.bin").read_bytes()
        patched = patch_mass_driver_stockpile(source)
        source_spans = _model_spans(source)
        patched_spans = _model_spans(patched)
        source_models = [source[a:b] for a, b in source_spans]
        patched_models = [patched[a:b] for a, b in patched_spans]

        before = _audit_model0(source_models[0])
        after = _audit_model0(patched_models[0])
        self.assertEqual(after.vertex_count - before.vertex_count, 304)
        self.assertEqual(after.primitive_count - before.primitive_count, 448)
        self.assertEqual(after.triangle_count - before.triangle_count, 448)
        self.assertEqual(after.quad_count, before.quad_count)
        self.assertEqual(after.instance_buffer_size - before.instance_buffer_size, 448 * 0x14)
        self.assertEqual(patched_models[1:], source_models[1:])

        header = (DONOR / "header.bin").read_bytes()
        names = (
            "images",
            "walkmesh",
            "models",
            "actors",
            "sprites",
            "scripts",
            "encounters",
            "dialogue",
            "triggers",
        )
        components = [
            (DONOR / f"{index:02d}_{name}.bin").read_bytes()
            for index, name in enumerate(names)
        ]
        components[2] = patched
        bundle = build_field(header, components)
        reparsed = parse_field(bundle)
        self.assertEqual(reparsed.parts[2].data, patched)
        self.assertEqual([part.data for part in reparsed.parts], components)

        # Determinism is important because release hashes are documented.
        self.assertEqual(patch_mass_driver_stockpile(source), patched)
        self.assertEqual(
            hashlib.sha256(patched).hexdigest(),
            "2bd3ff9718866eec1b14133980abe5aaea902e8f3627fa14c007be318a248762",
        )


if __name__ == "__main__":
    unittest.main()
