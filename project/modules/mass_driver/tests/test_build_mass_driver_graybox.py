from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.build_mass_driver_graybox import (
    BytePatch,
    GrayboxBuildError,
    apply_byte_patches,
    build_graybox,
    load_recipe,
    xenoiso_wrapper_command,
)
from tools.xgatel import AtelScript, scan_raw_transitions
from tools.xgfield import FIELD_HEADER_MINIMUM, STREAM_NAMES, parse_field


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _script(field: int, parameter: int, trailer: bytes = b"") -> bytes:
    data = bytearray(0x84 + 0x40)
    struct.pack_into("<I", data, 0x80, 1)
    data.extend(
        bytes((0x98,))
        + struct.pack("<H", field | 0x8000)
        + struct.pack("<H", parameter | 0x8000)
        + bytes((0x00,))
        + trailer
    )
    return bytes(data)


def _write_unpacked(directory: Path, script: bytes) -> None:
    directory.mkdir(parents=True)
    (directory / "header.bin").write_bytes(bytes(FIELD_HEADER_MINIMUM))
    for index, name in enumerate(STREAM_NAMES):
        data = script if index == 5 else bytes((index,)) * index
        (directory / f"{index:02d}_{name}.bin").write_bytes(data)
    (directory / "provenance.txt").write_text("source copy\n", encoding="ascii")


class TrackedRecipeTests(unittest.TestCase):
    def test_recipe_encodes_the_audited_foot_only_route(self) -> None:
        project = REPOSITORY_ROOT
        recipe = load_recipe(project / "recipes" / "mass_driver_graybox.json")

        self.assertEqual(
            [
                (
                    clone.source_field,
                    clone.target_field,
                    clone.source_bundle_id,
                    clone.source_graphics_id,
                    clone.target_bundle_id,
                    clone.target_graphics_id,
                )
                for clone in recipe.clones
            ],
            [
                (633, 724, 1872, 1873, 2054, 2055),
                (634, 721, 1874, 1875, 2048, 2049),
                (631, 726, 1868, 1869, 2058, 2059),
            ],
        )
        self.assertEqual(
            [
                (
                    recipe.hook.patches[0].pc,
                    recipe.hook.patches[0].expected_field,
                    recipe.hook.patches[0].expected_parameter,
                    recipe.hook.patches[0].new_field,
                    recipe.hook.patches[0].new_parameter,
                )
            ],
            [(0x07F1, 618, 0, 724, 0)],
        )
        self.assertEqual(
            [(patch.pc, patch.expected, patch.replacement) for patch in recipe.hook.byte_patches],
            [
                (0x07D9, bytes.fromhex("09 1f 2b"), bytes.fromhex("01 dc 07")),
                (0x0837, bytes.fromhex("09 1f 2a"), bytes.fromhex("01 3a 08")),
                (
                    0x0848,
                    bytes.fromhex("3a 48 02 02 00 40"),
                    bytes.fromhex("3b 48 02 02 00 40"),
                ),
                (
                    0x084F,
                    bytes.fromhex("56 00 04 ff 0f ff ff 11 00 f0"),
                    bytes.fromhex("98 d4 82 00 80 14 14 14 14 14"),
                ),
            ],
        )
        self.assertEqual(
            [patch.new_parameter for patch in recipe.clones[0].patches],
            [0, 0, 0],
        )
        self.assertEqual(
            [(patch.pc, patch.expected, patch.replacement) for patch in recipe.clones[0].byte_patches],
            [
                (0x0017, bytes.fromhex("f7 2c 81 00 80"), bytes.fromhex("14 14 14 14 14")),
                (0x0160, bytes.fromhex("0b 00 04"), bytes.fromhex("29 fb 00")),
            ],
        )
        self.assertEqual(
            [patch.pc for patch in recipe.clones[1].byte_patches],
            [0x0035, 0x0624, 0x0819],
        )
        self.assertEqual(
            [patch.pc for patch in recipe.clones[2].byte_patches],
            [0x0093, 0x00BE],
        )
        self.assertEqual(
            recipe.clones[2].dialogue_spec.name,
            "mass_driver_control_dialogue.json",
        )


class BytePatchTests(unittest.TestCase):
    def test_applies_at_bytecode_pc_without_changing_size(self) -> None:
        source = _script(2, 0, b"\xAA\xBB")
        patched = apply_byte_patches(
            source,
            (BytePatch(pc=6, expected=b"\xAA\xBB", replacement=b"\xCC\xDD"),),
        )

        self.assertEqual(len(patched), len(source))
        offset = AtelScript(source).bytecode_offset
        self.assertEqual(patched[offset + 6 : offset + 8], b"\xCC\xDD")

    def test_rejects_unexpected_bytes(self) -> None:
        with self.assertRaisesRegex(GrayboxBuildError, "expected aa bb"):
            apply_byte_patches(
                _script(2, 0, b"\x10\x20"),
                (
                    BytePatch(
                        pc=6,
                        expected=b"\xAA\xBB",
                        replacement=b"\xCC\xDD",
                    ),
                ),
            )


class GrayboxBuilderTests(unittest.TestCase):
    def _fixture(self, root: Path, wrong_expected: bool = False) -> tuple[Path, Path]:
        inputs = root / "inputs"
        hook_script = _script(618, 0)
        donor_script = _script(10, 2, b"\xAA\xBB")
        _write_unpacked(inputs / "hook", hook_script)
        _write_unpacked(inputs / "donor", donor_script)
        graphics = b"GRAPHICS-COPY"
        (inputs / "graphics.bin").write_bytes(graphics)

        recipe = {
            "format": "xenogears-mass-driver-graybox-v1",
            "name": "unit-test graybox",
            "notes": ["synthetic fixture"],
            "hook": {
                "source_field": 617,
                "canonical_bundle_id": 100,
                "bundle_directory": "hook",
                "script_sha256": _sha256(hook_script),
                "patches": [
                    {
                        "pc": 0,
                        "expected_field": 999 if wrong_expected else 618,
                        "expected_parameter": 0,
                        "new_field": 7,
                        "new_parameter": 0,
                    }
                ],
            },
            "clones": [
                {
                    "role": "test room",
                    "source_field": 1,
                    "target_field": 7,
                    "source_bundle_id": 10,
                    "source_graphics_id": 11,
                    "target_bundle_id": 200,
                    "target_graphics_id": 201,
                    "bundle_directory": "donor",
                    "graphics_file": "graphics.bin",
                    "script_sha256": _sha256(donor_script),
                    "graphics_sha256": _sha256(graphics),
                    "patches": [
                        {
                            "pc": 0,
                            "expected_field": 10,
                            "expected_parameter": 2,
                            "new_field": 8,
                            "new_parameter": 1,
                        }
                    ],
                    "byte_patches": [
                        {
                            "pc": 6,
                            "expected": "aa bb",
                            "replacement": "cc dd",
                        }
                    ],
                }
            ],
        }
        recipe_path = root / "recipe.json"
        recipe_path.write_text(json.dumps(recipe), encoding="utf-8")
        return inputs, recipe_path

    def test_builds_clones_and_replacements_without_mutating_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs, recipe_path = self._fixture(root)
            output = root / "result"
            source_script = (inputs / "donor" / "05_scripts.bin").read_bytes()
            source_graphics = (inputs / "graphics.bin").read_bytes()

            _, replacements = build_graybox(recipe_path, inputs, output)

            self.assertEqual([item[0] for item in replacements], [100, 200, 201])
            self.assertEqual(
                (inputs / "donor" / "05_scripts.bin").read_bytes(), source_script
            )
            self.assertEqual((inputs / "graphics.bin").read_bytes(), source_graphics)
            self.assertEqual(
                (output / "clones" / "field_7" / "provenance.txt").read_text(
                    encoding="ascii"
                ),
                "source copy\n",
            )

            clone_script = (
                output / "clones" / "field_7" / "05_scripts.bin"
            ).read_bytes()
            transitions = scan_raw_transitions(AtelScript(clone_script))
            self.assertEqual(
                [(item.field, item.parameter) for item in transitions], [(8, 1)]
            )
            bytecode_offset = AtelScript(clone_script).bytecode_offset
            self.assertEqual(
                clone_script[bytecode_offset + 6 : bytecode_offset + 8], b"\xCC\xDD"
            )

            packed_clone = parse_field(dict(replacements)[200].read_bytes())
            self.assertEqual(packed_clone.parts[5].data, clone_script)
            self.assertEqual(dict(replacements)[201].read_bytes(), source_graphics)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [
                    replacement["canonical_id"]
                    for job in manifest["jobs"]
                    for replacement in job["replacements"]
                ],
                [100, 200, 201],
            )

    def test_rejects_existing_output_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs, recipe_path = self._fixture(root)
            output = root / "result"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("mine", encoding="ascii")

            with self.assertRaisesRegex(GrayboxBuildError, "Refusing to overwrite"):
                build_graybox(recipe_path, inputs, output)
            self.assertEqual(marker.read_text(encoding="ascii"), "mine")

    def test_failed_validation_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs, recipe_path = self._fixture(root, wrong_expected=True)
            output = root / "result"

            with self.assertRaisesRegex(Exception, "expected 999/0"):
                build_graybox(recipe_path, inputs, output)
            self.assertFalse(output.exists())

    def test_xenoiso_command_uses_wrapper_and_refuses_source_overwrite(self) -> None:
        command = xenoiso_wrapper_command(
            "Xenoiso.exe",
            "source.bin",
            "patched.bin",
            [(100, Path("field.bin")), (200, Path("room.bin"))],
        )

        self.assertTrue(command[1].endswith("xenoiso_build.py"))
        self.assertIn("100=", " ".join(command))
        self.assertIn("200=", " ".join(command))
        with self.assertRaisesRegex(GrayboxBuildError, "must not overwrite"):
            xenoiso_wrapper_command(
                "Xenoiso.exe", "same.bin", "same.bin", [(100, Path("field.bin"))]
            )


if __name__ == "__main__":
    unittest.main()
