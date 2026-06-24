from __future__ import annotations

from collections import Counter
from pathlib import Path

from skill_research.core.types import Task
from skill_research.datasets.base import build_stratified_splits
from skill_research.datasets.spreadsheetbench_verified import SpreadsheetBenchVerifiedDatasetProvider

DATA_ROOT = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")


def _tasks() -> list[Task]:
    tasks = []
    for index in range(12):
        category = "A" if index < 8 else "B"
        tasks.append(Task(str(index), "x", metadata={"category": category}))
    return tasks


def test_build_stratified_splits_has_exact_sizes_and_no_overlap() -> None:
    splits = build_stratified_splits(
        _tasks(),
        split_sizes={"trace": 6, "val": 3, "test": 2},
        stratify_by="category",
        seed=7,
    )

    assert {name: len(tasks) for name, tasks in splits.items()} == {"trace": 6, "val": 3, "test": 2, "reserve": 1}
    all_ids = [task.task_id for tasks in splits.values() for task in tasks]
    assert len(all_ids) == len(set(all_ids))
    assert Counter(task.metadata["category"] for task in splits["trace"])["B"] > 0
    assert Counter(task.metadata["category"] for task in splits["val"])["B"] > 0


def test_spreadsheetbench_provider_exposes_stratified_trace_val_test_splits() -> None:
    provider = SpreadsheetBenchVerifiedDatasetProvider(
        DATA_ROOT,
        split_strategy="stratified",
        split_seed=41,
        split_sizes={"trace": 128, "val": 32, "test": 128},
        stratify_by="instruction_type",
    )

    trace = provider.load_split("trace")
    val = provider.load_split("val")
    test = provider.load_split("test")
    reserve = provider.load_split("reserve")

    assert len(trace) == 128
    assert len(val) == 32
    assert len(test) == 128
    assert len(reserve) == provider.info.metadata["valid_records"] - 128 - 32 - 128
    assert set(task.task_id for task in trace.tasks).isdisjoint(task.task_id for task in val.tasks)
    assert set(task.task_id for task in trace.tasks).isdisjoint(task.task_id for task in test.tasks)
    assert trace.metadata["split_strategy"] == "stratified"
    assert trace.metadata["stratify_by"] == "instruction_type"
    assert sum(trace.metadata["category_counts"].values()) == 128
