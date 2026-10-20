import struct
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from modules.rico import build as core
from modules.rico.release_presentation import apply_release_presentation, speaker_portraits
from modules.rico.dialogue_presentation import SPEAKER_LABELS
from modules.rico.tests.test_dialogue_portraits import field, run
from shared.tools.xgfield import parse_field
from shared.tools.xgscript import AtelScript


class ReleasePresentationTests(unittest.TestCase):
    def test_every_authored_speaker_has_a_native_slot(self):
        self.assertLessEqual(set(SPEAKER_LABELS.values()), speaker_portraits().keys())
        self.assertEqual(speaker_portraits()["Hammer"], 46)
        self.assertEqual(speaker_portraits(young_rico=True)["Rico"], 32)
        self.assertEqual(speaker_portraits()["Rico"], 5)

    def test_combined_targets_only_owned_fields_and_uses_actual_disc_executable(self):
        source = field(bytes.fromhex("F5 00 00 01 9C FE 53 00"), "<Rico>\nHello.<Close>")
        owned = set(range(230, 237)) | set(range(64, 80))
        items = [core.Replacement(606 + 2*f, "field", source) for f in owned]
        items += [core.Replacement(1586, "title", b"preserve title"),
                  core.Replacement(1344, "protected external field", b"preserve scene")]
        asset = SimpleNamespace(canonical_id=493, slug="young_rico", data=b"TIM",
                                portrait_id=32, sha256="test", png_sha256="test")
        with patch("modules.rico.release_presentation.prepare_portrait_assets", return_value=[asset]), \
             patch("modules.rico.dialogue_name_color.patch_executable", return_value=b"patched disc2") as exe:
            output, report = apply_release_presentation(
                SimpleNamespace(canonical=lambda _: b"donor"), {2: items},
                executable_sources={2: b"actual disc2"}, combined=True)
        exe.assert_called_once_with(b"actual disc2")
        resources = {item.canonical_id: item.data for item in output[2]}
        self.assertEqual(resources[22], b"patched disc2")
        self.assertEqual(resources[1586], b"preserve title")
        self.assertEqual(resources[1344], b"preserve scene")
        for number in owned:
            script = AtelScript(parse_field(resources[606+2*number]).parts[5].data)
            windows, unlocked, _, stack = run(script.bytecode)
            self.assertEqual(windows[0][1], 32 if number in {64,65,66,230} else 5)
            self.assertTrue(unlocked)
            self.assertEqual(stack, [])
        self.assertEqual(len(report["discs"]["2"]["fields"]), len(owned))

    def test_missing_executable_fails_before_asset_work(self):
        with self.assertRaisesRegex(ValueError, "own source executable"):
            apply_release_presentation(None, {1: []}, executable_sources={})


if __name__ == "__main__":
    unittest.main()
