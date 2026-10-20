from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from shared.tools.xenoiso_build import BuildError, command_build, command_list_bytes, parse_replacement


class XenoisoCommandListTests(unittest.TestCase):
    def test_command_list_has_crlf_but_no_final_newline(self) -> None:
        content = command_list_bytes(
            Path("source.bin"),
            Path("output.bin"),
            [(1840, Path("replacement.bin"))],
        )

        self.assertEqual(
            content,
            b"cd2fix\r\nsource.bin\r\noutput.bin\r\n1840,replacement.bin",
        )
        self.assertFalse(content.endswith((b"\r", b"\n")))

    def test_disc_one_uses_cd1_with_the_same_canonical_ids(self) -> None:
        content = command_list_bytes(
            Path("disc1.bin"),
            Path("rico-disc1.bin"),
            [(1586, Path("title.bin")), (2595, Path("state.bin"))],
            disc=1,
        )

        self.assertEqual(
            content,
            b"cd1\r\ndisc1.bin\r\nrico-disc1.bin\r\n"
            b"1586,title.bin\r\n2595,state.bin",
        )

    def test_rejects_unknown_disc_number(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Disc must be 1 or 2"):
            command_list_bytes(
                Path("source.bin"),
                Path("output.bin"),
                [(1, Path("replacement.bin"))],
                disc=3,
            )

    def test_parses_replacement(self) -> None:
        number, path = parse_replacement("0x730=field.bin")

        self.assertEqual(number, 1840)
        self.assertEqual(path, Path("field.bin"))

    def test_force_preserves_stale_output_until_successful_xenoiso_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "xenoiso.exe"
            source = root / "source.bin"
            replacement = root / "replacement.bin"
            output = root / "output.bin"
            for path in (executable, source, replacement):
                path.write_bytes(b"input")
            output.write_bytes(b"stale")
            output.with_suffix(".cue").write_bytes(b"stale cue")

            def fake_run(*_args: object, **kwargs: object) -> SimpleNamespace:
                self.assertEqual(output.read_bytes(), b"stale")
                self.assertEqual(output.with_suffix(".cue").read_bytes(), b"stale cue")
                (Path(kwargs["cwd"]) / "output.bin").write_bytes(b"rebuilt")
                return SimpleNamespace(stdout=b"Operations successfully completed", returncode=0)

            arguments = SimpleNamespace(
                xenoiso=executable,
                source=source,
                output=output,
                replacement=[(1840, replacement)],
                force=True,
                disc=2,
            )
            with patch("shared.tools.xenoiso_build.subprocess.run", side_effect=fake_run):
                self.assertEqual(command_build(arguments), 0)

            self.assertEqual(output.read_bytes(), b"rebuilt")
            self.assertIn(
                'FILE "output.bin" BINARY',
                output.with_suffix(".cue").read_text(encoding="ascii"),
            )

    def test_deep_and_whitespace_paths_only_reach_xenoiso_as_short_ascii_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "tool directory with spaces" / "xenoiso.exe"
            source = root / "disc source with spaces.bin"
            replacement = root / ("long_replacement_" * 4 + ".bin")
            output = root / "deep output with spaces" / ("release_" * 7) / ("chapter_output_" * 4 + ".bin")
            executable.parent.mkdir()
            for path in (executable, source, replacement):
                path.write_bytes(path.name.encode())
            originals = {path: path.read_bytes() for path in (executable, source, replacement)}
            observed_workspaces = []

            def fake_run(command, **kwargs):
                workspace = Path(kwargs["cwd"])
                observed_workspaces.append(workspace)
                self.assertEqual(command, [str(executable), "build.txt"])
                data = (workspace / command[1]).read_bytes()
                self.assertEqual(data, b"cd2fix\r\nsource.bin\r\noutput.bin\r\n1840,r00000.bin")
                self.assertEqual((workspace / "source.bin").read_bytes(), originals[source])
                self.assertEqual((workspace / "r00000.bin").read_bytes(), originals[replacement])
                (workspace / "output.bin").write_bytes(b"valid output")
                return SimpleNamespace(returncode=0, stdout=b"Done")

            args = SimpleNamespace(xenoiso=executable, source=source, output=output,
                                   replacement=[(1840, replacement)], force=False, disc=2)
            with patch("shared.tools.xenoiso_build.subprocess.run", side_effect=fake_run):
                self.assertEqual(command_build(args), 0)
            self.assertEqual(output.read_bytes(), b"valid output")
            self.assertTrue(all(not path.exists() for path in observed_workspaces))
            for path, content in originals.items():
                self.assertEqual(path.read_bytes(), content)

    def test_process_errors_and_empty_output_preserve_previous_image_and_cue(self) -> None:
        for returncode, stdout, payload, expected in (
            (-1073741819, b"Writing file 4146...Don", b"partial", "0xC0000005"),
            (0, b"error opening file", b"partial", "reported an error"),
            (0, b"Done", b"", "non-empty output"),
            (0, b"Done", None, "non-empty output"),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                executable, source, replacement, output = [root / name for name in
                    ("xenoiso.exe", "source.bin", "replacement.bin", "output.bin")]
                for path in (executable, source, replacement):
                    path.write_bytes(b"input")
                output.write_bytes(b"previous image")
                cue = output.with_suffix(".cue")
                cue.write_bytes(b"previous cue")
                def fake_run(*_args, **kwargs):
                    if payload is not None:
                        (Path(kwargs["cwd"]) / "output.bin").write_bytes(payload)
                    return SimpleNamespace(returncode=returncode, stdout=stdout)
                args = SimpleNamespace(xenoiso=executable, source=source, output=output,
                                       replacement=[(1840, replacement)], force=True, disc=2)
                with patch("shared.tools.xenoiso_build.subprocess.run", side_effect=fake_run):
                    with self.assertRaisesRegex(BuildError, expected):
                        command_build(args)
                self.assertEqual(output.read_bytes(), b"previous image")
                self.assertEqual(cue.read_bytes(), b"previous cue")
                self.assertEqual(list(root.glob("xgi_*")), [])

    def test_copy_fallback_and_exclusive_publish_preserve_inputs_and_racing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable, source, replacement, output = [root / name for name in
                ("xenoiso.exe", "source.bin", "replacement.bin", "output.bin")]
            for path in (executable, source, replacement):
                path.write_bytes(b"input")
            def fake_run(*_args, **kwargs):
                workspace = Path(kwargs["cwd"])
                self.assertEqual((workspace / "source.bin").read_bytes(), b"input")
                (workspace / "output.bin").write_bytes(b"new image")
                return SimpleNamespace(returncode=0, stdout=b"Done")
            args = SimpleNamespace(xenoiso=executable, source=source, output=output,
                                   replacement=[(1840, replacement)], force=False, disc=2)
            with patch("shared.tools.xenoiso_build.os.link", side_effect=OSError("not supported")):
                with patch("shared.tools.xenoiso_build.subprocess.run", side_effect=fake_run):
                    self.assertEqual(command_build(args), 0)
            self.assertEqual(output.read_bytes(), b"new image")
            self.assertEqual(source.read_bytes(), b"input")
            output.unlink()
            output.with_suffix(".cue").unlink()
            def racing_run(*positional, **kwargs):
                result = fake_run(*positional, **kwargs)
                output.write_bytes(b"another process")
                return result
            with patch("shared.tools.xenoiso_build.subprocess.run", side_effect=racing_run):
                with self.assertRaisesRegex(BuildError, "Refusing to overwrite"):
                    command_build(args)
            self.assertEqual(output.read_bytes(), b"another process")

    def test_output_must_not_overwrite_any_input_or_existing_cue_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable, source, replacement, output = [root / name for name in
                ("xenoiso.exe", "source.bin", "replacement.bin", "output.bin")]
            for path in (executable, source, replacement):
                path.write_bytes(b"input")
            args = SimpleNamespace(xenoiso=executable, source=source, output=replacement,
                                   replacement=[(1840, replacement)], force=True, disc=2)
            with self.assertRaisesRegex(BuildError, "must not overwrite"):
                command_build(args)
            args.output = output
            args.force = False
            output.with_suffix(".cue").write_bytes(b"existing cue")
            with patch("shared.tools.xenoiso_build.subprocess.run") as runner:
                with self.assertRaisesRegex(BuildError, "Refusing to overwrite"):
                    command_build(args)
                runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
