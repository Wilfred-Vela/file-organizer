"""Tests for organize.py. Every test runs inside a temporary folder."""

import ast
import io
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import organize  # noqa: E402


def touch(folder, *names):
    for name in names:
        path = Path(folder) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)


def run_main(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = organize.main(list(args))
    return code, out.getvalue(), err.getvalue()


class OrganizerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class TestR1OneCommand(OrganizerTestCase):
    def test_R1_runs_as_single_command_with_stdlib_only(self):
        touch(self.dir, "a.txt")
        result = subprocess.run(
            [sys.executable, str(ROOT / "organize.py"), str(self.dir)],
            capture_output=True, text=True, timeout=30,
            env={"PATH": os.environ.get("PATH", "")},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.dir / "Documents" / "a.txt").is_file())

    def test_R1_imports_only_standard_library(self):
        stdlib = sys.stdlib_module_names
        source = (ROOT / "organize.py").read_text()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                self.assertIn(name.split(".")[0], stdlib)


class TestR2FolderArgument(OrganizerTestCase):
    def test_R2_accepts_folder_path_argument(self):
        touch(self.dir, "a.png")
        code, out, _ = run_main(str(self.dir))
        self.assertEqual(code, 0)
        self.assertTrue((self.dir / "Images" / "a.png").is_file())

    def test_R2_missing_argument_is_usage_error(self):
        code, _, err = run_main()
        self.assertEqual(code, 2)
        self.assertIn("usage", err.lower())

    def test_R2_extra_arguments_are_usage_error(self):
        code, _, err = run_main(str(self.dir), str(self.dir))
        self.assertEqual(code, 2)
        self.assertIn("usage", err.lower())


class TestR3Scan(OrganizerTestCase):
    def test_R3_scans_all_regular_files_in_folder(self):
        touch(self.dir, "a.txt", "b.jpg", "c.mp3")
        planned = {src.name for src, _ in organize.plan_moves(self.dir)}
        self.assertEqual(planned, {"a.txt", "b.jpg", "c.mp3"})

    def test_R3_skips_hidden_files(self):
        touch(self.dir, ".DS_Store", "a.txt")
        organize.organize(self.dir)
        self.assertTrue((self.dir / ".DS_Store").is_file())

    def test_R3_skips_symlinks(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "real.txt"
        target.write_text("x")
        (self.dir / "link.txt").symlink_to(target)
        organize.organize(self.dir)
        self.assertTrue((self.dir / "link.txt").is_symlink())
        self.assertTrue(target.is_file())


class TestR4Extensions(unittest.TestCase):
    def test_R4_identifies_category_by_extension(self):
        self.assertEqual(organize.categorize("photo.jpg"), "Images")
        self.assertEqual(organize.categorize("report.pdf"), "Documents")
        self.assertEqual(organize.categorize("song.mp3"), "Audio")
        self.assertEqual(organize.categorize("clip.mp4"), "Videos")

    def test_R4_extension_match_is_case_insensitive(self):
        self.assertEqual(organize.categorize("PHOTO.JPG"), "Images")

    def test_R4_uses_last_extension(self):
        self.assertEqual(organize.categorize("backup.tar.gz"), "Archives")
        self.assertEqual(organize.categorize("my.report.pdf"), "Documents")


class TestR5Organize(OrganizerTestCase):
    def test_R5_moves_files_into_type_folders(self):
        touch(self.dir, "a.jpg", "b.pdf", "c.zip", "d.py")
        organize.organize(self.dir)
        self.assertTrue((self.dir / "Images" / "a.jpg").is_file())
        self.assertTrue((self.dir / "Documents" / "b.pdf").is_file())
        self.assertTrue((self.dir / "Archives" / "c.zip").is_file())
        self.assertTrue((self.dir / "Code" / "d.py").is_file())
        self.assertFalse((self.dir / "a.jpg").exists())

    def test_R5_unknown_extension_goes_to_other(self):
        touch(self.dir, "thing.xyz")
        organize.organize(self.dir)
        self.assertTrue((self.dir / "Other" / "thing.xyz").is_file())

    def test_R5_never_overwrites_existing_file(self):
        touch(self.dir, "Images/photo.jpg", "photo.jpg")
        (self.dir / "Images" / "photo.jpg").write_text("original")
        organize.organize(self.dir)
        self.assertEqual((self.dir / "Images" / "photo.jpg").read_text(), "original")
        self.assertEqual((self.dir / "Images" / "photo (1).jpg").read_text(), "photo.jpg")

    def test_R5_repeated_collisions_get_increasing_numbers(self):
        touch(self.dir, "Images/photo.jpg", "Images/photo (1).jpg", "photo.jpg")
        organize.organize(self.dir)
        self.assertTrue((self.dir / "Images" / "photo (2).jpg").is_file())

    def test_R5_contents_preserved_after_move(self):
        (self.dir / "a.txt").write_text("hello")
        organize.organize(self.dir)
        self.assertEqual((self.dir / "Documents" / "a.txt").read_text(), "hello")


class TestR6CreateFolders(OrganizerTestCase):
    def test_R6_creates_missing_category_folder(self):
        touch(self.dir, "a.mp4")
        self.assertFalse((self.dir / "Videos").exists())
        organize.organize(self.dir)
        self.assertTrue((self.dir / "Videos").is_dir())

    def test_R6_reuses_existing_folder(self):
        touch(self.dir, "Images/old.png", "new.png")
        organize.organize(self.dir)
        self.assertTrue((self.dir / "Images" / "old.png").is_file())
        self.assertTrue((self.dir / "Images" / "new.png").is_file())

    def test_R6_does_not_create_unused_folders(self):
        touch(self.dir, "a.png")
        organize.organize(self.dir)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["Images"])


class TestR7NoExtension(OrganizerTestCase):
    def test_R7_categorize_no_extension(self):
        self.assertEqual(organize.categorize("Makefile"), organize.NO_EXTENSION)
        self.assertEqual(organize.categorize("notes."), organize.NO_EXTENSION)

    def test_R7_files_without_extension_go_to_separate_folder(self):
        touch(self.dir, "README", "LICENSE")
        organize.organize(self.dir)
        self.assertTrue((self.dir / "No Extension" / "README").is_file())
        self.assertTrue((self.dir / "No Extension" / "LICENSE").is_file())


class TestR8Summary(OrganizerTestCase):
    def test_R8_summary_lists_counts_per_category_and_total(self):
        touch(self.dir, "a.jpg", "b.png", "c.pdf")
        result = organize.organize(self.dir)
        text = organize.format_summary(result)
        self.assertIn("Images: 2", text)
        self.assertIn("Documents: 1", text)
        self.assertIn("Total: 3", text)

    def test_R8_summary_printed_by_main(self):
        touch(self.dir, "a.jpg")
        code, out, _ = run_main(str(self.dir))
        self.assertEqual(code, 0)
        self.assertIn("Images: 1", out)
        self.assertIn("Total: 1", out)

    def test_R8_summary_when_nothing_to_organize(self):
        code, out, _ = run_main(str(self.dir))
        self.assertEqual(code, 0)
        self.assertIn("No files to organize", out)

    def test_R8_summary_reports_skipped_files(self):
        touch(self.dir, ".hidden", "a.txt")
        result = organize.organize(self.dir)
        self.assertIn("Skipped: 1", organize.format_summary(result))

    def test_R8_failed_move_is_reported_and_others_continue(self):
        touch(self.dir, "a.txt", "b.txt")
        real_rename = os.rename

        def flaky(src, dst):
            if os.path.basename(src) == "a.txt":
                raise PermissionError("denied")
            real_rename(src, dst)

        with unittest.mock.patch("organize.os.rename", side_effect=flaky):
            result = organize.organize(self.dir)
        self.assertTrue((self.dir / "a.txt").is_file())
        self.assertTrue((self.dir / "Documents" / "b.txt").is_file())
        self.assertEqual(len(result.failed), 1)
        self.assertIn("a.txt", organize.format_summary(result))


class TestR9InvalidPath(OrganizerTestCase):
    def test_R9_nonexistent_path_shows_helpful_error(self):
        missing = self.dir / "does-not-exist"
        code, out, err = run_main(str(missing))
        self.assertEqual(code, 2)
        self.assertIn(str(missing), err)
        self.assertIn("does not exist", err)

    def test_R9_file_path_instead_of_folder_shows_error(self):
        touch(self.dir, "a.txt")
        code, _, err = run_main(str(self.dir / "a.txt"))
        self.assertEqual(code, 2)
        self.assertIn("not a folder", err)
        self.assertTrue((self.dir / "a.txt").is_file())

    def test_R9_validate_folder_raises_for_invalid(self):
        with self.assertRaises(organize.InvalidFolderError):
            organize.validate_folder(self.dir / "nope")


class TestR10NoSubfolders(OrganizerTestCase):
    def test_R10_files_in_subfolders_are_not_moved(self):
        touch(self.dir, "sub/inner.jpg", "top.jpg")
        organize.organize(self.dir)
        self.assertTrue((self.dir / "sub" / "inner.jpg").is_file())
        self.assertFalse((self.dir / "Images" / "inner.jpg").exists())
        self.assertTrue((self.dir / "Images" / "top.jpg").is_file())

    def test_R10_subfolders_themselves_are_not_moved(self):
        (self.dir / "photos.jpg").mkdir()
        organize.organize(self.dir)
        self.assertTrue((self.dir / "photos.jpg").is_dir())
        self.assertFalse((self.dir / "Images").exists())


if __name__ == "__main__":
    unittest.main()
