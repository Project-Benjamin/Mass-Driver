from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from tools.xgfield import STREAM_NAMES, build_field, parse_field
from tools.xgmissiles import MissileModelError, _model_spans
from tools.xgzeboim_missiles import (
    PATCHED_FIELD_385_MODELS_SHA256,
    RACK_PLACEMENTS,
    TARGET_MODEL_INDEX,
    _audit_model11,
    build_zeboim_missile_rack_geometry,
    patch_zeboim_missile_racks,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DONOR = PROJECT_ROOT / "work" / "audit_zeboim_cd1" / "field_385"


class ZeboimMissileRackTests(unittest.TestCase):
    def test_horizontal_rack_geometry_counts_and_safe_envelope(self) -> None:
        geometry = build_zeboim_missile_rack_geometry()

        self.assertEqual(len(RACK_PLACEMENTS), 8)
        self.assertEqual(len(geometry.vertices), 352)
        self.assertEqual(len(geometry.triangles), 480)
        self.assertEqual(
            (
                min(vertex[0] for vertex in geometry.vertices),
                min(vertex[1] for vertex in geometry.vertices),
                min(vertex[2] for vertex in geometry.vertices),
            ),
            (-175, -172, -1067),
        )
        self.assertEqual(
            (
                max(vertex[0] for vertex in geometry.vertices),
                max(vertex[1] for vertex in geometry.vertices),
                max(vertex[2] for vertex in geometry.vertices),
            ),
            (175, -87, -29),
        )

        # Everything is mounted well above field 385's y=0 walkmesh and
        # remains inside model 11's audited static-room envelope.
        self.assertTrue(all(-176 <= vertex[0] <= 176 for vertex in geometry.vertices))
        self.assertTrue(all(-235 <= vertex[1] <= -80 for vertex in geometry.vertices))
        self.assertTrue(all(-1411 <= vertex[2] <= 176 for vertex in geometry.vertices))
        for triangle in geometry.triangles:
            self.assertTrue(
                all(
                    0 <= index < len(geometry.vertices)
                    for index in triangle.indices[:3]
                )
            )
            self.assertEqual(triangle.indices[3], 0)

    def test_wrong_model_archive_is_rejected(self) -> None:
        with self.assertRaises(MissileModelError):
            patch_zeboim_missile_racks(bytes(256))

    @unittest.skipUnless(DONOR.is_dir(), "retail field-385 extraction is absent")
    def test_retail_patch_is_narrow_deterministic_and_field_safe(self) -> None:
        models = (DONOR / "02_models.bin").read_bytes()
        patched = patch_zeboim_missile_racks(models)
        source_entries = [
            models[start:end] for start, end in _model_spans(models)
        ]
        patched_entries = [
            patched[start:end] for start, end in _model_spans(patched)
        ]

        self.assertEqual(len(source_entries), 13)
        self.assertEqual(len(patched_entries), 13)
        for index, (source, result) in enumerate(
            zip(source_entries, patched_entries, strict=True)
        ):
            if index == TARGET_MODEL_INDEX:
                self.assertNotEqual(result, source)
            else:
                self.assertEqual(result, source)

        before = _audit_model11(source_entries[TARGET_MODEL_INDEX])
        after = _audit_model11(patched_entries[TARGET_MODEL_INDEX])
        self.assertEqual(after.vertex_count - before.vertex_count, 352)
        self.assertEqual(after.primitive_count - before.primitive_count, 480)
        self.assertEqual(after.f3_count - before.f3_count, 480)
        self.assertEqual(after.instance_buffer_size - before.instance_buffer_size, 480 * 0x14)
        self.assertEqual(after.minimum, before.minimum)
        self.assertEqual(after.maximum, before.maximum)
        self.assertEqual(patch_zeboim_missile_racks(models), patched)
        self.assertEqual(
            hashlib.sha256(patched).hexdigest(),
            PATCHED_FIELD_385_MODELS_SHA256,
        )

        header = (DONOR / "header.bin").read_bytes()
        components = [
            (DONOR / f"{index:02d}_{name}.bin").read_bytes()
            for index, name in enumerate(STREAM_NAMES)
        ]
        components[2] = patched
        bundle = build_field(header, components, compact=True)
        self.assertLess(len(bundle), 0x40000)
        reparsed = parse_field(bundle)
        self.assertEqual(reparsed.parts[2].data, patched)
        self.assertEqual(
            [part.data for part in reparsed.parts],
            components,
        )

        # Header/model-only work: the source field's other eight decoded
        # components are byte-identical in the round trip.
        self.assertEqual(
            [part.data for index, part in enumerate(reparsed.parts) if index != 2],
            [component for index, component in enumerate(components) if index != 2],
        )


if __name__ == "__main__":
    unittest.main()
