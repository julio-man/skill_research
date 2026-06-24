from __future__ import annotations

from pathlib import Path

from skill_research.datasets.spreadsheetbench_verified import SpreadsheetBenchVerifiedDatasetProvider, discover_workbooks

DATA_ROOT = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")


def test_discover_workbooks_supports_dataset_naming_patterns() -> None:
    initial, golden = discover_workbooks(DATA_ROOT / "spreadsheet" / "13-1")

    assert initial.name == "1_13-1_init.xlsx"
    assert golden.name == "1_13-1_golden.xlsx"


def test_verified_provider_loads_real_tasks_with_metadata() -> None:
    provider = SpreadsheetBenchVerifiedDatasetProvider(DATA_ROOT, include_excluded=False, limit=3)

    split = provider.load_split("val")

    assert split.dataset.name == "spreadsheetbench_verified"
    assert split.dataset.metadata["total_records"] == 400
    assert split.dataset.metadata["eligible_records"] == 398
    assert len(split.tasks) == 3
    task = split.tasks[0]
    assert task.input_path is not None
    assert task.input_path.exists()
    assert Path(task.metadata["golden_workbook_path"]).exists()
    assert task.metadata["answer_position"]
    assert task.metadata["instruction_type"] in {"Cell-Level Manipulation", "Sheet-Level Manipulation"}
    assert task.metadata["is_excluded"] is False


def test_verified_provider_can_include_excluded_records() -> None:
    provider = SpreadsheetBenchVerifiedDatasetProvider(DATA_ROOT, include_excluded=True)

    split = provider.load_split("val")

    assert len(split.tasks) == provider.info.metadata["valid_records"]
    assert any(task.metadata["is_excluded"] for task in split.tasks)
