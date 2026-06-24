"""SpreadsheetBench Verified dataset provider and workbook discovery logic."""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from skill_research.core.types import Task
from skill_research.datasets.base import DatasetInfo, DatasetProviderBase, DatasetSplit, build_stratified_splits


class SpreadsheetBenchDataError(ValueError):
    pass


def discover_workbooks(task_dir: Path) -> tuple[Path, Path]:
    initial_candidates = sorted(task_dir.glob("*init.xlsx")) or sorted(task_dir.glob("initial.xlsx"))
    golden_candidates = sorted(task_dir.glob("*golden.xlsx")) or sorted(task_dir.glob("golden.xlsx"))
    if len(initial_candidates) != 1 or len(golden_candidates) != 1:
        raise SpreadsheetBenchDataError(f"Expected one initial and one golden workbook in {task_dir}")
    return initial_candidates[0], golden_candidates[0]


class SpreadsheetBenchVerifiedDatasetProvider(DatasetProviderBase):
    name = "spreadsheetbench_verified"

    def __init__(
        self,
        root: str | Path,
        include_excluded: bool = False,
        limit: int | None = None,
        seed: int | None = None,
        split_strategy: str = "full_copy",
        split_seed: int = 41,
        split_sizes: dict[str, int] | None = None,
        stratify_by: str = "instruction_type",
    ):
        root = Path(root)
        self.root = root
        self.include_excluded = include_excluded
        self.limit = limit
        self.seed = seed
        self.split_strategy = split_strategy
        self.split_seed = split_seed
        self.split_sizes = split_sizes or {"trace": 128, "val": 32, "test": 128}
        self.stratify_by = stratify_by
        records = self._load_records()
        eligible_count = sum(1 for record in records if "exclude" not in record)
        super().__init__(
            DatasetInfo(
                name=self.name,
                domain="spreadsheet",
                root=root,
                metadata={"total_records": len(records), "eligible_records": eligible_count},
            )
        )
        self._tasks = self._build_tasks(records)
        self._splits = self._build_splits()

    def _load_records(self) -> list[dict[str, Any]]:
        dataset_path = self.root / "dataset.json"
        records = json.loads(dataset_path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise SpreadsheetBenchDataError("dataset.json must contain a list")
        return records

    def _build_tasks(self, records: list[dict[str, Any]]) -> list[Task]:
        tasks = []
        for record in records:
            exclude_reason = record.get("exclude")
            if exclude_reason and not self.include_excluded:
                continue
            spreadsheet_dir = self.root / record["spreadsheet_path"]
            initial_path, golden_path = discover_workbooks(spreadsheet_dir)
            prompt_path = spreadsheet_dir / "prompt.txt"
            task = Task(
                task_id=str(record["id"]),
                instruction=str(record["instruction"]),
                input_path=initial_path,
                metadata={
                    "dataset": self.name,
                    "spreadsheet_rel_path": record["spreadsheet_path"],
                    "spreadsheet_dir": str(spreadsheet_dir),
                    "golden_workbook_path": str(golden_path),
                    "prompt_path": str(prompt_path) if prompt_path.exists() else None,
                    "instruction_type": record.get("instruction_type"),
                    "answer_position": record.get("answer_position"),
                    "answer_sheet": record.get("answer_sheet"),
                    "data_position": record.get("data_position"),
                    "exclude_reason": exclude_reason,
                    "is_excluded": bool(exclude_reason),
                    "raw_record": record,
                },
            )
            tasks.append(task)
        if self.seed is not None and self.split_strategy == "full_copy":
            rng = random.Random(self.seed)
            rng.shuffle(tasks)
        if self.limit is not None and self.split_strategy == "full_copy":
            tasks = tasks[: self.limit]
        return tasks

    def _build_splits(self) -> dict[str, list[Task]]:
        if self.split_strategy == "full_copy":
            return {"train": list(self._tasks), "val": list(self._tasks), "test": list(self._tasks), "all": list(self._tasks)}
        if self.split_strategy == "stratified":
            splits = build_stratified_splits(self._tasks, self.split_sizes, self.stratify_by, self.split_seed)
            splits["all"] = list(self._tasks)
            return splits
        raise ValueError(f"Unknown split strategy: {self.split_strategy}")

    def _split_metadata(self, split: str, tasks: list[Task]) -> dict[str, Any]:
        return {
            "split_strategy": self.split_strategy,
            "split_seed": self.split_seed,
            "stratify_by": self.stratify_by if self.split_strategy == "stratified" else None,
            "split_sizes": self.split_sizes if self.split_strategy == "stratified" else None,
            "task_ids": [task.task_id for task in tasks],
            "category_counts": dict(Counter(str(task.metadata.get(self.stratify_by, "__missing__")) for task in tasks)),
        }

    def load_split(self, split: str) -> DatasetSplit:
        if split not in self._splits:
            known = ", ".join(sorted(self._splits))
            raise KeyError(f"Unknown split '{split}'. Known splits: {known}")
        tasks = list(self._splits[split])
        if self.limit is not None and self.split_strategy != "full_copy":
            tasks = tasks[: self.limit]
        return self.make_split(split, tasks, metadata=self._split_metadata(split, tasks))


def load_spreadsheetbench_verified(root: Path) -> SpreadsheetBenchVerifiedDatasetProvider:
    return SpreadsheetBenchVerifiedDatasetProvider(root)


__all__ = ["SpreadsheetBenchDataError", "SpreadsheetBenchVerifiedDatasetProvider", "Task", "discover_workbooks", "load_spreadsheetbench_verified"]
