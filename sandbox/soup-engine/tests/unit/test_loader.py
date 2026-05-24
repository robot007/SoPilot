from __future__ import annotations

import unittest
from pathlib import Path

from sopilot_rules import load_soup

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bp"


class LoaderTests(unittest.TestCase):
    def test_load_soup_returns_package(self):
        package = load_soup(FIXTURE_DIR / "bp_monitor.soup.json")
        self.assertEqual(package.package.name, "Blood Pressure Monitor SOP Checker")


if __name__ == "__main__":
    unittest.main()
