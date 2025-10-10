import unittest
import os
from organizing_files import unique_name

class TestOrganizingFiles(unittest.TestCase):
    def test_unique_name(self):
        # Setup: create a temp directory and file
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = "test.txt"
            path = os.path.join(tmpdir, fname)
            with open(path, "w") as f:
                f.write("x")
            # Should return a new name since test.txt exists
            result = unique_name(tmpdir, "test", ".txt")
            self.assertTrue(result.startswith("test_"))
            self.assertTrue(result.endswith(".txt"))

if __name__ == "__main__":
    unittest.main()