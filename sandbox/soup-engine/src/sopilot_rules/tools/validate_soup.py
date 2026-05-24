"""Validate a SOUP package file."""

from __future__ import annotations

import argparse
import sys

from sopilot_rules.loader import load_soup


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate a .soup.json package")
    parser.add_argument("path", help="Path to .soup.json")
    args = parser.parse_args(argv)

    try:
        package = load_soup(args.path)
    except Exception as exc:
        print("INVALID: %s" % exc, file=sys.stderr)
        return 1

    print("OK: %s %s" % (package.package.id, package.package.version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
