"""Selection composition and disc-integrity regressions without a disc rebuild."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from modules.definitive import build
from modules.definitive.options import Options
from shared.tools.xgdisc import DirectoryEntry, IndexEntry


class CompositionTests(unittest.TestCase):
    def source(self):
        return SimpleNamespace(disc=1, image=SimpleNamespace(path=Path("retail.bin")),
                               read=Mock(return_value=b"original executable"))

    def test_all_options_off_produces_no_replacements(self):
        source = self.source()
        with patch.object(build, "build_restoration_replacements") as mechanics, \
                patch.object(build, "patch_rewards") as rewards, \
                patch.object(build, "build_encounter_replacements") as encounters, \
                patch.object(build, "patch_executable") as renderer, \
                patch.object(build, "patch_disc_dialogue", return_value=({}, {"runtime_status": "untested"})) as dialogue:
            replacements, audit = build.prepare_disc(source, Options(bug_fixes=False))
        self.assertEqual(replacements, {})
        self.assertEqual(set(audit), {"dialogue"})
        for operation in (mechanics, rewards, encounters, renderer):
            operation.assert_not_called()
        source.read.assert_not_called()
        dialogue.assert_called_once_with(source.image.path, 1, yellow_names=False, replacements={})

    def test_selected_patches_compose_without_losing_prior_resources(self):
        source = self.source()
        seen = {}

        def rewards(_reader, replacements):
            seen["rewards_input"] = dict(replacements)
            return {**replacements, 2618: b"double XP"}, {"applied": True}

        def dialogue(_path, _disc, *, yellow_names, replacements):
            seen["dialogue_input"] = dict(replacements)
            self.assertTrue(yellow_names)
            return {**replacements, 634: b"yellow name dialogue"}, {"applied": True}

        with patch.object(build, "build_restoration_replacements", return_value=({38: b"battle fix"}, {"applied": True})), \
                patch.object(build, "patch_rewards", side_effect=rewards), \
                patch.object(build, "build_encounter_replacements", return_value=({7: b"field encounters", 95: b"world encounters"}, {"applied": True})) as encounters, \
                patch.object(build, "patch_disc_dialogue", side_effect=dialogue), \
                patch.object(build, "patch_executable", return_value=b"yellow name renderer") as renderer:
            replacements, audit = build.prepare_disc(source, Options(yellow_names=True, double_xp=True, encounters="none"))
        self.assertEqual(seen["rewards_input"], {38: b"battle fix"})
        self.assertEqual(seen["dialogue_input"], {38: b"battle fix", 2618: b"double XP", 7: b"field encounters", 95: b"world encounters"})
        self.assertEqual(replacements, {**seen["dialogue_input"], 634: b"yellow name dialogue", 22: b"yellow name renderer"})
        self.assertEqual(set(audit), {"bug_fixes", "double_xp", "encounters", "dialogue"})
        encounters.assert_called_once_with(source.read, mode="none")
        source.read.assert_called_once_with(22)
        renderer.assert_called_once_with(b"original executable")

    def test_overlap_rejects_before_dialogue_or_executable_can_be_published(self):
        source = self.source()
        with patch.object(build, "build_restoration_replacements", return_value=({38: b"battle fix"}, {})), \
                patch.object(build, "build_encounter_replacements", return_value=({38: b"conflicting change"}, {})), \
                patch.object(build, "patch_disc_dialogue") as dialogue, \
                patch.object(build, "patch_executable") as renderer:
            with self.assertRaisesRegex(ValueError, "overlap"):
                build.prepare_disc(source, Options(yellow_names=True, encounters="none"))
        dialogue.assert_not_called()
        renderer.assert_not_called()

    def test_unfinished_retranslation_cannot_trigger_partial_build(self):
        source = self.source()
        with patch.object(build, "build_restoration_replacements") as mechanics, \
                patch.object(build, "patch_disc_dialogue") as dialogue:
            with self.assertRaisesRegex(ValueError, "retranslation"):
                build.prepare_disc(source, Options(retranslation=True))
        mechanics.assert_not_called()
        dialogue.assert_not_called()
        source.read.assert_not_called()


def fake_disc(disc=1):
    """Minimal FAT with one data resource, one boot file, and native metadata."""
    shift = 5 if disc == 2 else 0
    boot = 22 - shift
    entries = [IndexEntry(index, 0, 0, "empty") for index in range(23)]
    entries[0] = IndexEntry(0, 50, 8, "file")
    entries[1] = IndexEntry(1, 0xFFFFFE, 0xFF000000, "metadata")
    entries[boot] = IndexEntry(boot, 60, 4, "file")
    payloads = {0: b"original", boot: b"boot"}
    image = SimpleNamespace(path=Path(f"disc{disc}.bin"),
        read_directories=Mock(return_value=[DirectoryEntry(0, 22 - shift), DirectoryEntry(4, 424 - shift)]),
        extract_entry=lambda entry: payloads[entry.index])
    return SimpleNamespace(disc=disc, entries=entries, image=image, payloads=payloads,
        read=lambda canonical: payloads[canonical - shift])


class ResourceVerificationTests(unittest.TestCase):
    def verify(self, source, actual, replacements=None):
        with patch.object(build, "RetailDisc", return_value=actual), \
                patch.object(build, "verify_executable_image", return_value={"verified": True}) as boot:
            report = build.verify_resources(source, Path("rebuilt.bin"), replacements or {})
        return report, boot

    def test_relocated_files_and_selected_patches_pass_on_both_disc_namespaces(self):
        for disc in (1, 2):
            with self.subTest(disc=disc):
                source, actual = fake_disc(disc), fake_disc(disc)
                canonical = 5 if disc == 2 else 0
                actual.entries[0] = replace(actual.entries[0], sector=900, size=7)
                actual.payloads[0] = b"patched"
                report, boot = self.verify(source, actual, {canonical: b"patched", 22: b"patched boot"})
                self.assertEqual(report["resource_files_verified"], 1)
                self.assertEqual(report["runtime_status"], "untested")
                boot.assert_called_once_with(Path("rebuilt.bin"), disc, b"patched boot")

    def test_corrupted_native_directory_table_is_rejected_with_intact_files(self):
        source, actual = fake_disc(), fake_disc()
        actual.image.read_directories.return_value[1] = DirectoryEntry(4, 425)
        with self.assertRaisesRegex(ValueError, "directory lookup"):
            self.verify(source, actual)

    def test_changed_nonfile_metadata_is_rejected_even_with_same_kind(self):
        source, actual = fake_disc(), fake_disc()
        actual.entries[1] = replace(actual.entries[1], size=0xFF000001)
        with self.assertRaisesRegex(ValueError, "Nonfile FAT metadata"):
            self.verify(source, actual)

    def test_metadata_group_start_tracks_its_relocated_following_file(self):
        source, actual = fake_disc(), fake_disc()
        # A group marker and its first file share a start sector. The legacy
        # rebuild may move the group, but may not change its count/size value.
        source.entries[1] = IndexEntry(1, 70, 0xFFFFFFFD, "metadata")
        actual.entries[1] = replace(source.entries[1], sector=700)
        source.entries[2] = IndexEntry(2, 70, 5, "file")
        actual.entries[2] = replace(source.entries[2], sector=700)
        source.payloads[2] = actual.payloads[2] = b"group"
        report, _ = self.verify(source, actual)
        self.assertEqual(report["resource_files_verified"], 2)
        actual.entries[1] = replace(actual.entries[1], sector=701)
        with self.assertRaisesRegex(ValueError, "Nonfile FAT metadata"):
            self.verify(source, actual)

    def test_empty_and_terminator_metadata_cannot_move(self):
        for index, before in [(2, IndexEntry(2, 0, 0, "empty")),
                              (21, IndexEntry(21, 0xFFFFFF, 0, "metadata"))]:
            with self.subTest(index=index):
                source, actual = fake_disc(), fake_disc()
                source.entries[index] = before
                actual.entries[index] = replace(before, sector=before.sector + 1)
                with self.assertRaisesRegex(ValueError, "Nonfile FAT metadata"):
                    self.verify(source, actual)

    def test_xa_movies_use_raw_sector_hashes_and_reject_stream_corruption(self):
        source, actual = fake_disc(), fake_disc()
        for disc in (source, actual):
            disc.entries[0] = IndexEntry(0, 41, 0xFFFFFFFF, "metadata")
            disc.entries[1] = IndexEntry(1, 41, 2336, "file")
            disc.entries[2] = IndexEntry(2, 42, 0, "metadata")
            disc.entries[3] = IndexEntry(3, 42, 5, "file")
            disc.payloads[3] = b"after"
            disc.image.raw_sector_sha256 = Mock(return_value="movie-sector-hash")
            # No logical payload is provided for movie 1; a mistaken 2048-byte
            # extraction would fail instead of being silently accepted here.
        report, _ = self.verify(source, actual)
        self.assertEqual(report["raw_xa_movies_verified"], 1)
        source.image.raw_sector_sha256.assert_called_once_with(41, 1)
        actual.image.raw_sector_sha256.assert_called_once_with(41, 1)
        actual.image.raw_sector_sha256.return_value = "corrupted-video-or-audio"
        with self.assertRaisesRegex(ValueError, "Raw XA movie sectors"):
            self.verify(source, actual)
        actual.image.raw_sector_sha256.return_value = "movie-sector-hash"
        with self.assertRaisesRegex(ValueError, "Unselected movie extent"):
            self.verify(source, actual, {1: b"unauthorized movie replacement"})

    def test_rebuilt_file_corruption_and_discarded_patch_are_rejected(self):
        for replacements, payload in [({}, b"corrupt!"), ({0: b"patched"}, b"original")]:
            with self.subTest(replacements=replacements):
                source, actual = fake_disc(), fake_disc()
                actual.payloads[0] = payload
                with self.assertRaisesRegex(ValueError, "differs from expected bytes"):
                    self.verify(source, actual, replacements)

    def test_file_record_kind_and_fat_length_changes_are_rejected(self):
        source, actual = fake_disc(), fake_disc()
        actual.entries[0] = replace(actual.entries[0], kind="empty")
        with self.assertRaisesRegex(ValueError, "record kind"):
            self.verify(source, actual)
        actual = fake_disc()
        actual.entries.pop()
        with self.assertRaisesRegex(ValueError, "entry count"):
            self.verify(source, actual)


class DefinitivePlaylistTests(unittest.TestCase):
    def test_definitive_selects_two_disc_playlist_and_rejects_duplicate_disc(self):
        # Reuse the current registry fixture so this exercises real receipt,
        # descriptor, hash, and source-freshness checks rather than mocking them.
        from tests.test_project_releases import ProjectReleaseTests
        from shared import project_registry, project_releases

        fixture = ProjectReleaseTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        directory, receipt = fixture.build(profile="definitive")
        (directory / "disc2.bin").write_bytes(b"second retail disc fixture")
        (directory / "disc2.cue").write_text(
            'FILE "disc2.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n', encoding="utf-8")
        (directory / "game.m3u").write_text("disc.cue\ndisc2.cue\n", encoding="utf-8")
        receipt["outputs"] = [
            {"path": path.name, **project_registry.fingerprint_file(path)}
            for path in sorted(directory.iterdir()) if path.name != "project-build.json"]
        fixture.write_receipt(directory, receipt)
        plan = project_releases.play_plan(fixture.root, fixture.registry, "definitive", "reviewed")
        self.assertEqual(Path(plan["media"]), directory / "game.m3u")
        self.assertEqual(plan["runtime_status"], "untested")
        self.assertFalse((fixture.root / "builds/current.json").exists())
        # Re-sign the broken descriptor in the fixture receipt: the semantic
        # distinct-disc guard must reject it, independently of the hash check.
        fixture.update_output(directory, receipt, "game.m3u", "disc.cue\ndisc.cue\n")
        with self.assertRaisesRegex(project_registry.ProjectError, "two distinct"):
            project_releases.play_plan(fixture.root, fixture.registry, "definitive", "reviewed")


if __name__ == "__main__":
    unittest.main()
