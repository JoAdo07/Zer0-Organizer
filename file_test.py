import unittest
import json
import os
import subprocess
import sys
import tempfile
from organizing_files import unique_name


def run_cli(*argv, cwd):
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "organizing_files.py")
    return subprocess.run(
        [sys.executable, script, *argv],
        cwd=cwd,
        capture_output=True,
        text=True,
        input="yes\n",
    )


class TestOrganizingFiles(unittest.TestCase):
    def test_unique_name(self):
        # Setup: create a temp directory and file
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = "test.txt"
            path = os.path.join(tmpdir, fname)
            with open(path, "w") as f:
                f.write("x")
            # Should return a new name since test.txt exists
            result = unique_name(tmpdir, "test", ".txt")
            self.assertTrue(result.startswith("test_"))
            self.assertTrue(result.endswith(".txt"))

    def test_sort_commit_undo_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ("a.jpg", "b.pdf", "c.txt"):
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write("x")
            journal = os.path.join(tmpdir, "journal.json")

            sort = run_cli("sort", "--dir", tmpdir, "--commit", "--journal", journal, cwd=tmpdir)
            self.assertEqual(sort.returncode, 0, sort.stderr)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "Images", "a.jpg")))
            self.assertTrue(os.path.isfile(journal))
            with open(journal, encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)), 3)

            preview = run_cli("undo", "--journal", journal, cwd=tmpdir)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertIn("Preview", preview.stdout)
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "Images", "a.jpg")))

            undo = run_cli("undo", "--journal", journal, "--commit", cwd=tmpdir)
            self.assertEqual(undo.returncode, 0, undo.stderr)
            for name in ("a.jpg", "b.pdf", "c.txt"):
                self.assertTrue(os.path.isfile(os.path.join(tmpdir, name)), name)
            self.assertFalse(os.path.exists(os.path.join(tmpdir, "Images", "a.jpg")))

    def test_dry_run_writes_no_journal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "a.jpg"), "w") as f:
                f.write("x")
            journal = os.path.join(tmpdir, "journal.json")
            sort = run_cli("sort", "--dir", tmpdir, "--journal", journal, cwd=tmpdir)
            self.assertEqual(sort.returncode, 0, sort.stderr)
            self.assertFalse(os.path.exists(journal))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "a.jpg")))

    def test_undo_skips_missing_and_occupied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "a.jpg"), "w") as f:
                f.write("x")
            journal = os.path.join(tmpdir, "journal.json")
            with open(journal, "w", encoding="utf-8") as f:
                json.dump([
                    {"src": os.path.join(tmpdir, "a.jpg"), "dst": os.path.join(tmpdir, "gone.jpg")},
                    {"src": os.path.join(tmpdir, "b.jpg"), "dst": os.path.join(tmpdir, "Images", "b.jpg")},
                ], f)
            os.makedirs(os.path.join(tmpdir, "Images"))
            with open(os.path.join(tmpdir, "Images", "b.jpg"), "w") as f:
                f.write("y")
            with open(os.path.join(tmpdir, "b.jpg"), "w") as f:
                f.write("occupant")
            undo = run_cli("undo", "--journal", journal, "--commit", cwd=tmpdir)
            self.assertEqual(undo.returncode, 0, undo.stderr)
            self.assertIn("skipped 2", undo.stdout)
            # Occupant untouched, moved file left in place.
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "b.jpg")))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "Images", "b.jpg")))


if __name__ == "__main__":
    unittest.main()