from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.xgdialog import (
    DialogueBlockSpec,
    DialogueFormatError,
    build_dialogue,
    dialogue_document,
    encode_dialogue,
    encode_text,
    main,
    parse_dialogue,
    rebuild_dialogue,
    replace_dialogue,
    replacements_document,
)


def _six_block_dialogue() -> bytes:
    return encode_dialogue(
        [
            DialogueBlockSpec(0, 32, 2, "System status\nprepared.<Close>"),
            DialogueBlockSpec(1, 36, 2, "Launch system\nactivated.<Close>"),
            DialogueBlockSpec(2, 42, 2, "Payload loaded.<Close>"),
            DialogueBlockSpec(3, 18, 1, "Ready!<Close>"),
            DialogueBlockSpec(
                4,
                54,
                4,
                "Zeboim facility.<New>Weapon systems offline.<Close>",
            ),
            DialogueBlockSpec(
                5,
                60,
                4,
                "Manual authorization\nrequired.<Close><Close>",
            ),
        ]
    )


class DialogueCodecTests(unittest.TestCase):
    def test_six_blocks_roundtrip_exactly(self) -> None:
        source = _six_block_dialogue()

        parsed = parse_dialogue(source)
        document = dialogue_document(source)
        rebuilt = build_dialogue(source, document)

        self.assertEqual(len(parsed.blocks), 6)
        self.assertEqual([block.block_id for block in parsed.blocks], list(range(6)))
        self.assertEqual(rebuilt, source)

    def test_controls_roundtrip_losslessly(self) -> None:
        text = (
            "<Elly>: Wait<Delay:8>.<Wait><New>"
            "<Name:200><Opcode:04:AA><Extra1:7F><Extra2:80>"
            "<Byte:90><Close><Close>"
        )

        encoded = encode_text(text)
        component = encode_dialogue([DialogueBlockSpec(0, 60, 4, text)])

        self.assertEqual(parse_dialogue(component).blocks[0].payload, encoded)
        self.assertEqual(parse_dialogue(component).blocks[0].text, text)

    def test_el_regulus_name_control_uses_runtime_name_slot_21(self) -> None:
        text = "<El-Regulus><Close>"

        encoded = encode_text(text)

        self.assertEqual(encoded, bytes.fromhex("0F 05 15 00"))
        self.assertEqual(
            parse_dialogue(
                encode_dialogue([DialogueBlockSpec(0, 20, 1, text)])
            ).blocks[0].text,
            text,
        )

    def test_replacements_change_lengths_without_changing_ids(self) -> None:
        source = _six_block_dialogue()
        document = replacements_document(source)
        document["replacements"] = [
            {
                "id": 0,
                "text": "Mass-driver status already prepared.<Close>",
            },
            {
                "id": 5,
                "width": 62,
                "height": 4,
                "text": (
                    "Atmospheric dispersion pod.<New>"
                    "Manual authorization required.<Close>"
                ),
            },
        ]

        rebuilt = replace_dialogue(source, document)
        parsed = parse_dialogue(rebuilt)

        self.assertNotEqual(len(rebuilt), len(source))
        self.assertEqual([block.block_id for block in parsed.blocks], list(range(6)))
        self.assertEqual((parsed.blocks[0].width, parsed.blocks[0].height), (32, 2))
        self.assertEqual((parsed.blocks[5].width, parsed.blocks[5].height), (62, 4))
        self.assertIn("Atmospheric dispersion", parsed.blocks[5].text)

    def test_auto_rebuild_accepts_both_json_formats(self) -> None:
        source = _six_block_dialogue()
        complete = dialogue_document(source)
        replacements = replacements_document(source)
        replacements["replacements"] = [
            {"id": 3, "text": "Complete.<Close>"}
        ]

        self.assertEqual(rebuild_dialogue(source, complete), source)
        self.assertEqual(
            parse_dialogue(rebuild_dialogue(source, replacements)).blocks[3].text,
            "Complete.<Close>",
        )

    def test_rejects_unsupported_character(self) -> None:
        with self.assertRaisesRegex(DialogueFormatError, "Unsupported character"):
            encode_text("Curly apostrophe: ’<Close>")

    def test_rejects_missing_or_nonterminal_close(self) -> None:
        with self.assertRaisesRegex(DialogueFormatError, "must end with <Close>"):
            encode_text("No terminator")
        with self.assertRaisesRegex(DialogueFormatError, "follow the first <Close>"):
            encode_text("Early<Close>late<Close>")

    def test_rejects_changed_block_id_or_count(self) -> None:
        source = _six_block_dialogue()
        document = dialogue_document(source)
        document["blocks"][1]["id"] = 4

        with self.assertRaisesRegex(DialogueFormatError, "IDs must be exactly"):
            build_dialogue(source, document)

        document = dialogue_document(source)
        document["blocks"].pop()
        with self.assertRaisesRegex(DialogueFormatError, "Expected 6 block entries"):
            build_dialogue(source, document)

    def test_rejects_template_hash_mismatch_and_duplicate_replacement(self) -> None:
        source = _six_block_dialogue()
        document = replacements_document(source)
        document["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(DialogueFormatError, "SHA-256"):
            replace_dialogue(source, document)

        document = replacements_document(source)
        document["replacements"] = [
            {"id": 0, "text": "A.<Close>"},
            {"id": 0, "text": "B.<Close>"},
        ]
        with self.assertRaisesRegex(DialogueFormatError, "Duplicate replacement"):
            replace_dialogue(source, document)

    def test_rejects_u16_section_overflow(self) -> None:
        with self.assertRaisesRegex(DialogueFormatError, "u16 safety limit"):
            encode_dialogue(
                [DialogueBlockSpec(0, 60, 4, " " * 65530 + "<Close>")]
            )

    def test_builder_facing_rebuild_command(self) -> None:
        source = _six_block_dialogue()
        document = replacements_document(source)
        document["replacements"] = [
            {"id": 2, "text": "Nanomachine payload loaded.<Close>"}
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            template = root / "07_dialogue.bin"
            spec = root / "mass_driver_dialogue.json"
            output = root / "rebuilt.bin"
            template.write_bytes(source)
            spec.write_text(json.dumps(document), encoding="utf-8")

            result = main(
                [
                    "rebuild",
                    str(template),
                    str(output),
                    "--spec",
                    str(spec),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(
                parse_dialogue(output.read_bytes()).blocks[2].text,
                "Nanomachine payload loaded.<Close>",
            )
            self.assertEqual(template.read_bytes(), source)


if __name__ == "__main__":
    unittest.main()
