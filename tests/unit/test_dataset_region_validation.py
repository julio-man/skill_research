from __future__ import annotations

from pathlib import Path

from skill_research.core.types import Task
from skill_research.datasets.spreadsheetbench_verified import SpreadsheetBenchVerifiedDatasetProvider, normalize_cell_range
from skill_research.evaluators.spreadsheet import answer_cell_refs

DATA_ROOT = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")


def test_normalize_cell_range_repairs_missing_end_column() -> None:
    assert normalize_cell_range("BD2:308") == "BD2:BD308"


def test_answer_cell_refs_handles_repaired_range() -> None:
    task = Task("t", "x", metadata={"answer_position": "BD2:308", "answer_sheet": "Sheet1"})

    refs = answer_cell_refs(task)

    assert refs[0] == "Sheet1!BD2"
    assert refs[-1] == "Sheet1!BD308"


def test_stratified_splits_are_built_after_region_validation() -> None:
    provider = SpreadsheetBenchVerifiedDatasetProvider(
        DATA_ROOT,
        split_strategy="stratified",
        split_seed=42,
        split_sizes={"trace": 32, "val": 16, "test": 32},
        stratify_by="instruction_type",
    )

    assert len(provider.load_split("trace")) == 32
    assert len(provider.load_split("val")) == 16
    assert len(provider.load_split("test")) == 32
    assert provider.info.metadata["valid_records"] <= provider.info.metadata["eligible_records"]
    assert provider.info.metadata["invalid_region_records"] >= 0
