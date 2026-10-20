from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from tools import xgguardian


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PEDESTAL_STATS = (
    PROJECT_ROOT / "work" / "normal_combat_resources" / "2748.bin"
)
PEDESTAL_MODEL = PROJECT_ROOT / "work" / "guardian_resources" / "2749.bin"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _synthetic_sources() -> tuple[bytes, bytes, bytes]:
    stats = bytearray(xgguardian.ENEMY_NAME_OFFSET + 32)
    native_hp = struct.pack("<I", xgguardian.PEDESTAL_HP)
    stats[
        xgguardian.GEAR_CURRENT_HP_OFFSET :
        xgguardian.GEAR_CURRENT_HP_OFFSET + 4
    ] = native_hp
    stats[
        xgguardian.GEAR_MAXIMUM_HP_OFFSET :
        xgguardian.GEAR_MAXIMUM_HP_OFFSET + 4
    ] = native_hp
    stats[
        xgguardian.ENEMY_NAME_OFFSET :
        xgguardian.ENEMY_NAME_OFFSET + len(xgguardian.PEDESTAL_NAME)
    ] = xgguardian.PEDESTAL_NAME
    model = b"checked-pedestal-model"

    expected = bytearray(stats)
    guardian_hp = struct.pack("<I", xgguardian.GUARDIAN_HP)
    expected[
        xgguardian.GEAR_CURRENT_HP_OFFSET :
        xgguardian.GEAR_CURRENT_HP_OFFSET + 4
    ] = guardian_hp
    expected[
        xgguardian.GEAR_MAXIMUM_HP_OFFSET :
        xgguardian.GEAR_MAXIMUM_HP_OFFSET + 4
    ] = guardian_hp
    expected[
        xgguardian.ENEMY_NAME_OFFSET :
        xgguardian.ENEMY_NAME_OFFSET + len(xgguardian.GUARDIAN_NAME)
    ] = xgguardian.GUARDIAN_NAME
    return bytes(stats), model, bytes(expected)


class IsolatedGuardianTests(unittest.TestCase):
    def test_resource_contract_uses_unused_set_10(self) -> None:
        self.assertEqual(xgguardian.GUARDIAN_RESOURCE_SET_ID, 0x10)
        self.assertEqual(xgguardian.GUARDIAN_STATS_CANONICAL_ID, 2650)
        self.assertEqual(xgguardian.GUARDIAN_MODEL_CANONICAL_ID, 2651)
        self.assertEqual(xgguardian.PEDESTAL_STATS_CANONICAL_ID, 2748)
        self.assertEqual(xgguardian.PEDESTAL_MODEL_CANONICAL_ID, 2749)
        self.assertEqual(xgguardian.GUARDIAN_HP, 36000)
        self.assertEqual(len(xgguardian.PEDESTAL_NAME), 8)
        self.assertEqual(len(xgguardian.GUARDIAN_NAME), 8)

    def test_transform_changes_only_name_and_hp_and_labels_destinations(
        self,
    ) -> None:
        stats, model, expected = _synthetic_sources()
        with (
            patch.object(xgguardian, "PEDESTAL_STATS_SIZE", len(stats)),
            patch.object(xgguardian, "PEDESTAL_MODEL_SIZE", len(model)),
            patch.object(
                xgguardian,
                "PEDESTAL_STATS_SHA256",
                _sha256(stats),
            ),
            patch.object(
                xgguardian,
                "PEDESTAL_MODEL_SHA256",
                _sha256(model),
            ),
            patch.object(
                xgguardian,
                "GUARDIAN_STATS_SHA256",
                _sha256(expected),
            ),
            patch.object(
                xgguardian,
                "GUARDIAN_MODEL_SHA256",
                _sha256(model),
            ),
        ):
            resources = xgguardian.build_isolated_guardian_resources(
                stats,
                model,
            )

        self.assertEqual(resources.stats.data, expected)
        self.assertEqual(resources.model.data, model)
        self.assertEqual(resources.stats.canonical_id, 2650)
        self.assertEqual(resources.stats.source_canonical_id, 2748)
        self.assertEqual(resources.model.canonical_id, 2651)
        self.assertEqual(resources.model.source_canonical_id, 2749)
        self.assertEqual(
            resources.canonical_payloads(),
            ((2650, expected), (2651, model)),
        )

        allowed = set(
            range(
                xgguardian.GEAR_CURRENT_HP_OFFSET,
                xgguardian.GEAR_CURRENT_HP_OFFSET + 4,
            )
        )
        allowed.update(
            range(
                xgguardian.GEAR_MAXIMUM_HP_OFFSET,
                xgguardian.GEAR_MAXIMUM_HP_OFFSET + 4,
            )
        )
        allowed.update(
            range(
                xgguardian.ENEMY_NAME_OFFSET,
                xgguardian.ENEMY_NAME_OFFSET
                + len(xgguardian.GUARDIAN_NAME),
            )
        )
        self.assertTrue(
            all(
                stats[index] == expected[index] or index in allowed
                for index in range(len(stats))
            )
        )

    def test_wrong_stats_hash_is_rejected(self) -> None:
        stats, _, _ = _synthetic_sources()
        with (
            patch.object(xgguardian, "PEDESTAL_STATS_SIZE", len(stats)),
            self.assertRaisesRegex(
                xgguardian.GuardianResourceError,
                "Pedestal stats canonical 2748 SHA-256",
            ),
        ):
            xgguardian.patch_guardian_stats(stats)

    def test_wrong_model_hash_is_rejected_before_cloning(self) -> None:
        stats, model, _ = _synthetic_sources()
        with (
            patch.object(xgguardian, "PEDESTAL_MODEL_SIZE", len(model)),
            self.assertRaisesRegex(
                xgguardian.GuardianResourceError,
                "Pedestal model canonical 2749 SHA-256",
            ),
        ):
            xgguardian.build_isolated_guardian_resources(stats, model)

    @unittest.skipUnless(
        PEDESTAL_STATS.is_file(),
        "normal Pedestal stats resource is absent",
    )
    def test_real_pedestal_stats_match_deterministic_output(self) -> None:
        source = PEDESTAL_STATS.read_bytes()
        output = xgguardian.patch_guardian_stats(source)

        self.assertEqual(
            _sha256(source),
            xgguardian.PEDESTAL_STATS_SHA256,
        )
        self.assertEqual(
            _sha256(output),
            xgguardian.GUARDIAN_STATS_SHA256,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I",
                output,
                xgguardian.GEAR_CURRENT_HP_OFFSET,
            )[0],
            36000,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I",
                output,
                xgguardian.GEAR_MAXIMUM_HP_OFFSET,
            )[0],
            36000,
        )
        self.assertEqual(
            output[
                xgguardian.ENEMY_NAME_OFFSET :
                xgguardian.ENEMY_NAME_OFFSET
                + len(xgguardian.GUARDIAN_NAME)
            ],
            xgguardian.GUARDIAN_NAME,
        )

    @unittest.skipUnless(
        PEDESTAL_STATS.is_file() and PEDESTAL_MODEL.is_file(),
        "checked Pedestal stats/model extraction is absent",
    )
    def test_real_pair_builds_for_isolated_canonical_ids(self) -> None:
        resources = xgguardian.build_isolated_guardian_resources(
            PEDESTAL_STATS.read_bytes(),
            PEDESTAL_MODEL.read_bytes(),
        )
        self.assertEqual(
            tuple(canonical_id for canonical_id, _ in resources.canonical_payloads()),
            (2650, 2651),
        )
        self.assertEqual(
            _sha256(resources.model.data),
            xgguardian.GUARDIAN_MODEL_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
