from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from contextlib import redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v228_slot1_to_v229 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = migration.SOURCE_FIXTURE
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v229_from_cd84f8b5_field549_seal.sav"
)
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = PROJECT_ROOT / "output" / migration.OLD_CUE_NAME.replace(".cue", ".bin")
NEW_DISC = PROJECT_ROOT / "output" / migration.NEW_CUE_NAME.replace(".cue", ".bin")
OLD_STAGE = PROJECT_ROOT / "work" / "surface_soylent_campaign_v228_stage"
NEW_STAGE = PROJECT_ROOT / "work" / "surface_soylent_campaign_v229_stage"
OLD_FIELD = OLD_STAGE / "clones" / "field_549_disc1_donor"
NEW_FIELD = NEW_STAGE / "clones" / "field_549_disc1_donor"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV228Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_DISC.with_suffix(".cue"),
            NEW_DISC.with_suffix(".cue"),
            OLD_STAGE / "manifest.json",
            NEW_STAGE / "manifest.json",
            OLD_FIELD / "header.bin",
            NEW_FIELD / "header.bin",
            OLD_FIELD / "05_scripts.bin",
            NEW_FIELD / "05_scripts.bin",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V228/V229 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_manifest = (OLD_STAGE / "manifest.json").read_bytes()
        cls.new_manifest = (NEW_STAGE / "manifest.json").read_bytes()
        cls.old_header = (OLD_FIELD / "header.bin").read_bytes()
        cls.new_header = (NEW_FIELD / "header.bin").read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v228_slot1_to_v229(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_manifest=cls.old_manifest,
            new_manifest=cls.new_manifest,
            old_header=cls.old_header,
            new_header=cls.new_header,
            old_script=cls.old_script,
            new_script=cls.new_script,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.source_frame, cls.source_prefix = migration._unpack_state(
            cls.source, cls.zstd
        )
        cls.result_payload, cls.result_frame, cls.result_prefix = migration._unpack_state(
            cls.result, cls.zstd
        )
        _offset, cls.source_ram = migration._ram_from_payload(cls.source_payload)
        _offset, cls.result_ram = migration._ram_from_payload(cls.result_payload)

    def test_candidate_round_trip_report_and_exact_identities_are_frozen(self) -> None:
        self.assertEqual(
            (len(self.source), _sha256(self.source)),
            (migration.SOURCE_STATE_SIZE, migration.SOURCE_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result), _sha256(self.result)),
            (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result_payload), _sha256(self.result_payload)),
            (migration.SOURCE_PAYLOAD_SIZE, migration.OUTPUT_PAYLOAD_SHA256),
        )
        self.assertEqual(_sha256(self.result_ram), migration.OUTPUT_RAM_SHA256)
        self.assertEqual(self.source_frame, self.result_frame)
        self.assertEqual(len(self.result) - self.result_frame, migration.OUTPUT_COMPRESSED_SIZE)
        self.assertEqual(
            _sha256(self.result[self.result_frame :]),
            migration.OUTPUT_COMPRESSED_SHA256,
        )
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(
                self.source_prefix,
                compressed_size=migration.OUTPUT_COMPRESSED_SIZE,
            ),
        )
        self.assertEqual(_sha256(self.result_prefix), migration.OUTPUT_PREFIX_SHA256)
        self.assertEqual(
            len(migration._diff_offsets(self.source_prefix, self.result_prefix)),
            migration.EXPECTED_PREFIX_BYTES_CHANGED,
        )
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode("ascii")), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode("ascii")), 1)
        self.assertEqual(self.report["payload_bytes_changed"], 2)
        self.assertEqual(
            self.report["payload_changed_offsets"],
            ["0x10C74D", "0x11217C"],
        )
        self.assertEqual(self.report["archive_table_bytes_changed"], 0)
        self.assertEqual(self.report["resident_script_bytes_changed"], 1)
        self.assertEqual(self.report["runtime_e16_radius_bytes_changed"], 1)
        self.assertTrue(self.report["round_trip_verified"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)
        if CANDIDATE_REPORT.is_file():
            self.assertEqual(json.loads(CANDIDATE_REPORT.read_text(encoding="utf-8")), self.report)

    def test_media_manifests_field_bundle_and_decoded_atel_are_exact(self) -> None:
        self.assertEqual(
            (len(self.old_manifest), _sha256(self.old_manifest)),
            (migration.V228_STAGE_MANIFEST_SIZE, migration.V228_STAGE_MANIFEST_SHA256),
        )
        self.assertEqual(
            (len(self.new_manifest), _sha256(self.new_manifest)),
            (migration.V229_STAGE_MANIFEST_SIZE, migration.V229_STAGE_MANIFEST_SHA256),
        )
        old_inventory = migration._manifest_inventory(
            self.old_manifest,
            size=migration.V228_STAGE_MANIFEST_SIZE,
            sha256=migration.V228_STAGE_MANIFEST_SHA256,
            label="V228 stage manifest",
        )
        new_inventory = migration._manifest_inventory(
            self.new_manifest,
            size=migration.V229_STAGE_MANIFEST_SIZE,
            sha256=migration.V229_STAGE_MANIFEST_SHA256,
            label="V229 stage manifest",
        )
        changed = tuple(
            sorted(
                canonical_id
                for canonical_id in old_inventory.keys() | new_inventory.keys()
                if old_inventory.get(canonical_id) != new_inventory.get(canonical_id)
            )
        )
        self.assertEqual(changed, migration.CHANGED_RESOURCE_IDS)
        self.assertEqual(old_inventory[1704], migration.OLD_MANIFEST_RESOURCES[1704])
        self.assertEqual(new_inventory[1704], migration.NEW_MANIFEST_RESOURCES[1704])
        self.assertEqual(old_inventory[1705], new_inventory[1705])

        old_bundle, old_field = migration._disc_field549(
            OLD_DISC,
            size=migration.OLD_FIELD_BUNDLE_SIZE,
            sha256=migration.OLD_FIELD_BUNDLE_SHA256,
            label="V228 field-549 bundle",
        )
        new_bundle, new_field = migration._disc_field549(
            NEW_DISC,
            size=migration.NEW_FIELD_BUNDLE_SIZE,
            sha256=migration.NEW_FIELD_BUNDLE_SHA256,
            label="V229 field-549 bundle",
        )
        self.assertEqual(migration._diff_triplets(old_bundle, new_bundle), migration.BUNDLE_DIFFS)
        self.assertEqual(
            migration._triplet_digest(migration.BUNDLE_DIFFS),
            migration.BUNDLE_DIFF_SHA256,
        )
        self.assertEqual(old_field.header, new_field.header)
        self.assertEqual(old_field.parts[5].data, self.old_script)
        self.assertEqual(new_field.parts[5].data, self.new_script)
        self.assertEqual(
            migration._diff_triplets(self.old_script, self.new_script),
            migration.SCRIPT_DIFFS,
        )
        self.assertEqual(
            migration._triplet_digest(migration.SCRIPT_DIFFS),
            migration.SCRIPT_DIFF_SHA256,
        )
        old_atel, new_atel = AtelScript(self.old_script), AtelScript(self.new_script)
        self.assertEqual(old_atel.get_script_pointer(16, 0), migration.SEAL_INIT_PC)
        self.assertEqual(new_atel.get_script_pointer(16, 0), migration.SEAL_INIT_PC)
        self.assertEqual(
            old_atel.bytecode[
                migration.SEAL_VOLUME_PC : migration.SEAL_VOLUME_PC + 5
            ],
            migration.OLD_SEAL_VOLUME,
        )
        self.assertEqual(
            new_atel.bytecode[
                migration.SEAL_VOLUME_PC : migration.SEAL_VOLUME_PC + 5
            ],
            migration.NEW_SEAL_VOLUME,
        )

    def test_archive_table_is_rebuilt_against_v229_with_volatile_tail_preserved(self) -> None:
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(old_table, new_table)
        self.assertEqual(_sha256(old_table), migration.OLD_ARCHIVE_TABLE_SHA256)
        self.assertEqual(migration._diff_triplets(old_table, new_table), ())
        table_offset = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        source_table = self.source_payload[
            table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE
        ]
        result_table = self.result_payload[
            table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE
        ]
        self.assertEqual(
            migration._diff_triplets(source_table, old_table),
            migration.RESIDENT_VS_MEDIA_DIFFS,
        )
        self.assertEqual(
            migration._diff_triplets(result_table, new_table),
            migration.RESIDENT_VS_MEDIA_DIFFS,
        )
        self.assertEqual(result_table, source_table)
        self.assertEqual(result_table[0x7FFF], 0xE0)
        self.assertEqual(_sha256(result_table), migration.OUTPUT_RESIDENT_TABLE_SHA256)
        self.assertEqual(
            migration._rebuild_resident_table(source_table, new_table),
            result_table,
        )

    def test_exact_payload_whitelist_changes_atel_and_runtime_radius_only(self) -> None:
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        self.assertEqual(actual, migration.EXPECTED_PAYLOAD_CHANGED_OFFSETS)
        self.assertEqual(
            migration._diff_triplets(self.source_payload, self.result_payload),
            (
                (migration.EXPECTED_SCRIPT_PATCH_PAYLOAD_OFFSET, 0x0E, 0x08),
                (migration.EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET, 0x1C, 0x10),
            ),
        )
        script_start = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        self.assertEqual(
            self.source_payload[script_start : script_start + migration.SCRIPT_SIZE],
            self.old_script,
        )
        self.assertEqual(
            self.result_payload[script_start : script_start + migration.SCRIPT_SIZE],
            self.new_script,
        )
        runtime = migration.EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET
        self.assertEqual(self.source_payload[runtime : runtime + 2], migration.OLD_RUNTIME_RADIUS)
        self.assertEqual(self.result_payload[runtime : runtime + 2], migration.NEW_RUNTIME_RADIUS)

    def test_fei_party_camera_and_all_unrelated_actor_runtime_are_preserved(self) -> None:
        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        self.assertEqual(
            self.result_ram[
                actor_base : actor_base + migration.ACTOR_ARRAY_SIZE
            ],
            self.source_ram[
                actor_base : actor_base + migration.ACTOR_ARRAY_SIZE
            ],
        )
        for entity in range(migration.SCRIPT_ACTOR_COUNT):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            data = struct.unpack_from(
                "<I", self.source_ram, record + FIELD_ACTOR_DATA_POINTER
            )[0] & 0x1FFFFFFF
            self.assertEqual(
                self.result_ram[record : record + FIELD_ACTOR_STRIDE],
                self.source_ram[record : record + FIELD_ACTOR_STRIDE],
            )
            before = self.source_ram[data : data + migration.ACTOR_DATA_SIZE]
            after = self.result_ram[data : data + migration.ACTOR_DATA_SIZE]
            if entity == migration.SEAL_ENTITY:
                self.assertEqual(
                    migration._diff_offsets(before, after),
                    (migration.ACTOR_COLLISION_RADIUS_OFFSET,),
                )
                self.assertEqual(_sha256(before), migration.SOURCE_SEAL_DATA_SHA256)
                self.assertEqual(_sha256(after), migration.OUTPUT_SEAL_DATA_SHA256)
                self.assertEqual(
                    after[
                        migration.ACTOR_COLLISION_VOLUME_OFFSET :
                        migration.ACTOR_COLLISION_VOLUME_OFFSET + 8
                    ],
                    migration.NEW_RUNTIME_COLLISION_VOLUME,
                )
            else:
                self.assertEqual(after, before)

        fei = migration.EXPECTED_FEI_DATA_OFFSET
        self.assertEqual(
            self.result_ram[fei : fei + migration.ACTOR_DATA_SIZE],
            self.source_ram[fei : fei + migration.ACTOR_DATA_SIZE],
        )
        for offset, size in (
            (GAME_STATE, GAMESTATE_SIZE),
            (FIELD_SCRIPT_MEMORY, migration.FIELD_VARIABLE_BANK_SIZE),
            (
                GAME_STATE + migration.FIELD_VARIABLE_BACKUP_OFFSET,
                migration.FIELD_VARIABLE_BANK_SIZE,
            ),
            (migration.DIALOG_WINDOWS, migration.DIALOG_WINDOWS_SIZE),
        ):
            self.assertEqual(
                self.result_ram[offset : offset + size],
                self.source_ram[offset : offset + size],
            )
        for address in CAMERA_VECTORS.values():
            self.assertEqual(
                self.result_ram[address : address + 16],
                self.source_ram[address : address + 16],
            )

    def test_wrong_source_artifacts_archive_tail_and_live_paths_fail_closed(self) -> None:
        wrong_source = bytearray(self.source)
        wrong_source[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v228_slot1_to_v229(
                bytes(wrong_source),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_manifest=self.old_manifest,
                new_manifest=self.new_manifest,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=self.zstd,
            )
        wrong_manifest = bytearray(self.new_manifest)
        wrong_manifest[-2] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V229 stage manifest identity"):
            migration.migrate_v228_slot1_to_v229(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_manifest=self.old_manifest,
                new_manifest=bytes(wrong_manifest),
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=self.zstd,
            )
        wrong_script = bytearray(self.new_script)
        wrong_script[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "V229 field-549 script identity",
        ):
            migration.migrate_v228_slot1_to_v229(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_manifest=self.old_manifest,
                new_manifest=self.new_manifest,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=bytes(wrong_script),
                zstd=self.zstd,
            )
        source_table = self.source_payload[
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + migration.ARCHIVE_TABLE_SIZE
        ]
        wrong_table = bytearray(source_table)
        wrong_table[0] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "archive-table source drifted"):
            migration._rebuild_resident_table(
                bytes(wrong_table),
                media_migration._archive_table(NEW_DISC),
            )

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (
                    str(SOURCE_STATE),
                    "--output",
                    str(migration.LIVE_SLOT1),
                    "--report",
                    str(CANDIDATE_REPORT),
                )
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (
                    str(SOURCE_STATE),
                    "--output",
                    str(CANDIDATE_STATE),
                    "--report",
                    str(migration.LIVE_SLOT1),
                )
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (
                    str(SOURCE_STATE),
                    "--output",
                    str(SOURCE_STATE),
                    "--report",
                    str(CANDIDATE_REPORT),
                )
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("may not replace the source state", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
