from __future__ import annotations

import argparse
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO_ZIP_URL = "https://github.com/Qwen-Applications/Trace2Skill/archive/refs/heads/main.zip"
DATASET_RELATIVE_PATH = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")
EXPECTED_FILE = DATASET_RELATIVE_PATH / "dataset.json"
REPO_PREFIX = "Trace2Skill-main"


def fetch_spreadsheetbench_verified_400(project_root: Path, force: bool) -> Path:
    destination = project_root / DATASET_RELATIVE_PATH
    expected_file = project_root / EXPECTED_FILE

    if expected_file.exists() and not force:
        return destination

    if destination.exists() and force:
        shutil.rmtree(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "trace2skill.zip"

        urllib.request.urlretrieve(REPO_ZIP_URL, zip_path)

        with zipfile.ZipFile(zip_path) as archive:
            members = archive.namelist()
            dataset_prefix = f"{REPO_PREFIX}/data/spreadsheetbench_verified/spreadsheetbench_verified_400/"
            dataset_members = [member for member in members if member.startswith(dataset_prefix)]

            if not dataset_members:
                raise RuntimeError("Could not find SpreadsheetBench Verified 400 in the source archive.")

            archive.extractall(tmp_path, members=dataset_members)

        extracted_root = tmp_path / REPO_PREFIX / "data" / "spreadsheetbench_verified" / "spreadsheetbench_verified_400"
        if not extracted_root.exists():
            raise RuntimeError("Dataset extraction failed: expected extracted directory is missing.")

        shutil.copytree(extracted_root, destination, dirs_exist_ok=True)

    if not expected_file.exists():
        raise RuntimeError("Dataset fetch completed but dataset.json is missing.")

    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download SpreadsheetBench Verified 400 into the local data directory.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root where the data directory should be created.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite an existing local copy.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dataset_path = fetch_spreadsheetbench_verified_400(
        project_root=args.project_root.resolve(),
        force=args.force,
    )
    print(dataset_path)


if __name__ == "__main__":
    main()
