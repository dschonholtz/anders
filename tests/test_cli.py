import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from anders.cli import ensure_day


class CliTests(unittest.TestCase):
    def test_ensure_day_creates_expected_files(self):
        with TemporaryDirectory() as d:
            root = ensure_day(Path(d), date(2026, 5, 16))
            self.assertTrue((root / "goals.md").exists())
            self.assertTrue((root / "followups.md").exists())
            self.assertTrue((root / "raw").is_dir())


if __name__ == "__main__":
    unittest.main()
