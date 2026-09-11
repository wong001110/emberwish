"""Source-export regression tests. No private task state or native app is needed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workspace_evidence", ROOT / "tools/workspace_evidence.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SourceExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Source export fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.autocrlf", "false")
        (self.root / ".gitignore").write_text("ignored.txt\n.reports/\n", encoding="utf-8")
        (self.root / "source.txt").write_bytes(b"source-v1\n")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "fixture")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root).decode().strip()

    def test_clean_export_hashes_match_zip_bytes(self):
        report = module.export_workspace(self.root)
        self.assertFalse(report["working_tree_dirty"])
        self.assertEqual(report["commit"], self.git("rev-parse", "HEAD"))
        self.assertNotIn("scope_hash", report)
        digest = hashlib.sha256()
        archive_path = self.root / ".reports/workspace.zip"
        self.assertEqual(report["archive_sha256"], hashlib.sha256(archive_path.read_bytes()).hexdigest())
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(set(archive.namelist()), set(report["files"]))
            for name in sorted(archive.namelist()):
                data = archive.read(name)
                self.assertEqual(report["files"][name], hashlib.sha256(data).hexdigest())
                digest.update(name.encode() + b"\0" + data + b"\0")
        self.assertEqual(report["source_sha256"], digest.hexdigest())
        self.assertEqual(report, json.loads((self.root / ".reports/workspace.json").read_text()))

    def test_dirty_bytes_change_identity_without_fabricating_commit(self):
        before = module.export_workspace(self.root)
        (self.root / "source.txt").write_bytes(b"changed\n")
        after = module.export_workspace(self.root)
        self.assertTrue(after["working_tree_dirty"])
        self.assertEqual(before["commit"], after["commit"])
        self.assertNotEqual(before["source_sha256"], after["source_sha256"])

    def test_ignored_and_untracked_files_are_not_exported(self):
        (self.root / "ignored.txt").write_text("private")
        (self.root / "untracked.txt").write_text("private")
        report = module.export_workspace(self.root)
        self.assertEqual(set(report["files"]), {".gitignore", "source.txt"})
        self.assertFalse(report["working_tree_dirty"])

    def test_tracked_environment_file_is_rejected(self):
        (self.root / ".env.local").write_text("EXAMPLE=value")
        self.git("add", ".env.local")
        with self.assertRaisesRegex(RuntimeError, "Environment"):
            module.export_workspace(self.root)
        self.assertFalse((self.root / ".reports/workspace.zip").exists())

    def test_symlink_is_rejected(self):
        link = self.root / "link.txt"
        try:
            link.symlink_to("source.txt")
        except OSError:
            self.skipTest("Host does not permit fixture symlinks")
        self.git("add", "link.txt")
        with self.assertRaisesRegex(RuntimeError, "Unexpected tracked source path"):
            module.export_workspace(self.root)

    def test_missing_tracked_file_is_rejected(self):
        (self.root / "source.txt").unlink()
        with self.assertRaisesRegex(RuntimeError, "Unexpected tracked source path"):
            module.export_workspace(self.root)

    def test_tracked_output_cannot_be_included_recursively(self):
        (self.root / ".reports").mkdir()
        (self.root / ".reports/old.txt").write_text("stale")
        self.git("add", "--force", ".reports/old.txt")
        with self.assertRaisesRegex(RuntimeError, "Evidence output must not be tracked"):
            module.export_workspace(self.root)

    def test_non_ascii_filename_survives_export(self):
        name = "願望 notes.txt"
        (self.root / name).write_text("fixture", encoding="utf-8")
        self.git("add", name)
        report = module.export_workspace(self.root)
        self.assertIn(name, report["files"])
        with zipfile.ZipFile(self.root / ".reports/workspace.zip") as archive:
            self.assertEqual(archive.read(name), b"fixture")


if __name__ == "__main__":
    unittest.main()
