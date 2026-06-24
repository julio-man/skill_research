from __future__ import annotations

import argparse
from pathlib import Path

from skill_research.reports.generator import generate_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate human-readable reports from run artifacts")
    parser.add_argument("--run-root", required=True, help="Path to run artifacts directory")
    parser.add_argument("--output-dir", required=True, help="Directory where report files will be written")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    generate_report(Path(args.run_root), Path(args.output_dir))


if __name__ == "__main__":
    main()
