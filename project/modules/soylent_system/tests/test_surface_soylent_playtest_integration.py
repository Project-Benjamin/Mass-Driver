"""Exercise standalone test-mode dispatch and its real output manifest."""

from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

from modules.soylent_system import base, build as campaign


class PlaytestOptionsTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="soylent_playtest_options_")
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "playtest.json"

    def write_options(self, value: object) -> None:
        self.path.write_text(json.dumps(value), encoding="utf-8")

    def test_loader_accepts_only_explicit_boolean_values(self) -> None:
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                self.write_options({
                    "format": "soylent-playtest-options-v1",
                    "one_hit_kills": enabled,
                })
                self.assertIs(campaign.load_playtest_options(self.path), enabled)

    def test_loader_rejects_truthy_values_and_misspelled_schema(self) -> None:
        valid = {"format": "soylent-playtest-options-v1", "one_hit_kills": False}
        invalid = [
            {**valid, "one_hit_kills": value}
            for value in (0, 1, None, "true", "false", [], {})
        ] + [
            [], None, True,
            {},
            {"format": "soylent-playtest-options-v1"},
            {"one_hit_kills": True},
            {**valid, "format": "soylent-playtest-options-v2"},
            {**valid, "one_hit_kill": True},
        ]
        for value in invalid:
            with self.subTest(value=value):
                self.write_options(value)
                with self.assertRaisesRegex(
                    campaign.SurfaceCampaignBuildError, "Invalid Soylent playtest options"
                ):
                    campaign.load_playtest_options(self.path)

    def test_loader_rejects_malformed_json(self) -> None:
        self.path.write_text('{"one_hit_kills": true,}', encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            campaign.load_playtest_options(self.path)

    def test_main_uses_source_options_when_no_cli_override_is_given(self) -> None:
        args = ["--source-disc", "source.bin", "--donor-disc", "donor.bin",
                "--output", str(self.path.parent / "stage")]
        for enabled in (False, True):
            with self.subTest(enabled=enabled), \
                    patch.object(campaign, "load_playtest_options", return_value=enabled) as load, \
                    patch.object(campaign, "build_campaign", return_value=((), (), ())) as build, \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(campaign.main(args), 0)
                load.assert_called_once_with()
                self.assertIs(build.call_args.kwargs["one_hit_kills"], enabled)

    def test_main_cli_overrides_do_not_read_source_options(self) -> None:
        args = ["--source-disc", "source.bin", "--donor-disc", "donor.bin",
                "--output", str(self.path.parent / "stage")]
        for flag, enabled in (("--one-hit-kills", True), ("--no-one-hit-kills", False)):
            with self.subTest(flag=flag), \
                    patch.object(campaign, "load_playtest_options") as load, \
                    patch.object(campaign, "build_campaign", return_value=((), (), ())) as build, \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(campaign.main([*args, flag]), 0)
                load.assert_not_called()
                self.assertIs(build.call_args.kwargs["one_hit_kills"], enabled)


class PlaytestBuildIntegrationTests(unittest.TestCase):
    """Replace disc preparation, retaining real emission and manifest hashing."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="soylent_playtest_build_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "normalized-source.bin"
        self.donor = self.root / "retail-donor.bin"
        self.title = self.resource(2595, "2595_title.bin", b"normal title bytes")
        self.normal_field_id = 1863
        self.normal_field_data = b"normal field bytes"
        self.playtest_resources = (
            self.resource(2684, "2684_playtest.bin", b"first enemy stats"),
            self.resource(2706, "2706_playtest.bin", b"second enemy stats"),
        )
        self.metadata = {
            "one_hit_kills": True,
            "scope": "standalone_soylent_encounters",
            "mode": "one_hit_kills",
            "resources": [{"canonical_id": item.canonical_id}
                          for item in self.playtest_resources],
        }
        self.prepare = self.start_patch(patch.object(
            campaign, "prepare_campaign", return_value=((), (), (self.title,))
        ))
        self.materialize = self.start_patch(patch.object(
            campaign.base, "materialize", side_effect=self.materialize_fixture
        ))
        # The helper's own tests verify native stat records. Here its narrow
        # return contract lets emission tests run without donor binaries.
        helper_name = "modules.soylent_system.tools.surface_soylent_playtest"
        helper = ModuleType(helper_name)
        self.prepare_playtest = Mock(return_value=(self.playtest_resources, self.metadata))
        helper.prepare_one_hit_resources = self.prepare_playtest
        self.start_patch(patch.dict(sys.modules, {helper_name: helper}))

    def start_patch(self, patcher):
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    @staticmethod
    def resource(canonical_id: int, filename: str, data: bytes) -> base.PreparedTitleResource:
        return base.PreparedTitleResource(
            canonical_id=canonical_id,
            name=filename,
            filename=filename,
            source_sha256=hashlib.sha256(data).hexdigest(),
            data=data,
        )

    def materialize_fixture(
        self, fields, output_root, source_disc, *, donor_fields, donor_disc,
        title_resources, complete_dungeon, force,
    ):
        self.assertEqual((fields, donor_fields), ((), ()))
        self.assertEqual((source_disc, donor_disc), (self.source, self.donor))
        self.assertEqual(title_resources, (self.title,))
        self.assertTrue(complete_dungeon)
        self.assertFalse(force)
        output = Path(output_root)
        replacement_dir = output / "replacements"
        replacement_dir.mkdir(parents=True)
        for item in self.playtest_resources:
            self.assertFalse((replacement_dir / item.filename).exists())
        field_path = replacement_dir / "1863_field.bin"
        field_path.write_bytes(self.normal_field_data)
        title_path = replacement_dir / self.title.filename
        title_path.write_bytes(self.title.data)
        (output / "manifest.json").write_text(json.dumps({
            "format": "fixture-normal-materialization",
            "jobs": [{"scene": 623}],
            "donor_jobs": [],
        }), encoding="utf-8")
        return ((self.normal_field_id, field_path), (self.title.canonical_id, title_path))

    def stage(self, name: str, **options):
        output = self.root / name
        result = campaign.build_campaign(self.source, self.donor, output, **options)
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        return output, result, manifest

    def test_api_defaults_to_normal_output_independently_of_source_test_setting(self) -> None:
        with patch.object(campaign, "load_playtest_options", return_value=True) as load:
            default_output, default_result, default_manifest = self.stage("default")
            _, normal_result, normal_manifest = self.stage("explicit-off", one_hit_kills=False)
        load.assert_not_called()
        self.prepare_playtest.assert_not_called()
        self.assertEqual(default_manifest, normal_manifest)
        self.assertEqual(default_result[:2], normal_result[:2])
        self.assertEqual([item[0] for item in default_result[2]], [1863, 2595])
        self.assertEqual(default_manifest["playtest"], {"one_hit_kills": False})
        self.assertEqual(default_manifest["materialization"]["replacement_resources"], 2)
        self.assertEqual(len(list((default_output / "replacements").iterdir())), 2)

    def test_api_rejects_non_boolean_options_before_preparing_disc_data(self) -> None:
        for value in (None, 0, 1, "true", "false", [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(
                campaign.SurfaceCampaignBuildError, "one_hit_kills must be a boolean"
            ):
                campaign.build_campaign(self.source, self.donor, self.root / "invalid",
                                        one_hit_kills=value)
        self.prepare.assert_not_called()
        self.materialize.assert_not_called()
        self.prepare_playtest.assert_not_called()

    def test_enabled_mode_emits_verified_inventory_without_counting_stats_as_title(self) -> None:
        output, result, manifest = self.stage("enabled", one_hit_kills=True)
        self.prepare_playtest.assert_called_once_with(self.source)
        self.assertEqual([item[0] for item in result[2]], [1863, 2595, 2684, 2706])
        self.assertEqual(manifest["playtest"], self.metadata)
        self.assertEqual(manifest["materialization"]["replacement_resources"], 4)
        self.assertEqual(manifest["materialization"]["title_resources"], 1)
        self.assertEqual([item["canonical_id"] for item in manifest["title_resources"]], [2595])
        inventory = {item["canonical_id"]: item for item in manifest["replacement_inventory"]}
        self.assertEqual(len(inventory), 4)
        for canonical_id, path in result[2]:
            with self.subTest(canonical_id=canonical_id):
                row = inventory[canonical_id]
                self.assertEqual(output / row["path"], path)
                self.assertEqual(row["size"], len(path.read_bytes()))
                self.assertEqual(row["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        for resource in self.playtest_resources:
            self.assertEqual((output / inventory[resource.canonical_id]["path"]).read_bytes(),
                             resource.data)
        self.assertEqual((output / inventory[1863]["path"]).read_bytes(), self.normal_field_data)
        self.assertEqual((output / inventory[2595]["path"]).read_bytes(), self.title.data)

    def test_overlapping_playtest_resource_cannot_overwrite_normal_replacement(self) -> None:
        collision = self.resource(self.normal_field_id, "1863_field.bin", b"bad overlap")
        self.prepare_playtest.return_value = ((collision,), self.metadata)
        output = self.root / "collision"
        with self.assertRaisesRegex(campaign.SurfaceCampaignBuildError, "overlaps campaign replacement"):
            campaign.build_campaign(self.source, self.donor, output, one_hit_kills=True)
        self.assertEqual((output / "replacements" / collision.filename).read_bytes(),
                         self.normal_field_data)


if __name__ == "__main__":
    unittest.main()
