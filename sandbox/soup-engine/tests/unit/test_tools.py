from __future__ import annotations

import unittest
from pathlib import Path

from sopilot_rules.tools.validate_soup import main as validate_main

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bp"


class ToolTests(unittest.TestCase):
    def test_validate_soup_cli_accepts_bp_package(self):
        self.assertEqual(validate_main([str(FIXTURE_DIR / "bp_monitor.soup.json")]), 0)


if __name__ == "__main__":
    unittest.main()
