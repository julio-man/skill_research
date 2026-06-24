from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import random
from typing import Any, Protocol

from skill_research.core.types import Task


@dataclass(frozen=True)
class DatasetInfo:
    name: str
    domain: str
    root: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetSplit:
    name: str
    tasks: list[Task]
    dataset: DatasetInfo
    metadata: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.tasks)


class DatasetProvider(Protocol):
    name: str
    info: DatasetInfo

    def load_split(self, split: str) -> DatasetSplit:
        ...


class DatasetProviderBase:
    name = "base"

    def __init__(self, info: DatasetInfo):
        self.info = info

    def make_split(self, name: str, tasks: list[Task], metadata: dict[str, Any] | None = None) -> DatasetSplit:
        return DatasetSplit(name=name, tasks=tasks, dataset=self.info, metadata=metadata or {})


class InMemoryDatasetProvider(DatasetProviderBase):
    name = "memory"

    def __init__(self, splits: dict[str, list[Task]], dataset: DatasetInfo | None = None):
        super().__init__(dataset or DatasetInfo(name=self.name, domain="generic"))
        self.splits = splits

    def load_split(self, split: str) -> DatasetSplit:
        if split not in self.splits:
            known = ", ".join(sorted(self.splits)) or "none"
            raise KeyError(f"Unknown split '{split}'. Known splits: {known}")
        return self.make_split(split, self.splits[split])


def _category(task: Task, stratify_by: str) -> str:
    return str(task.metadata.get(stratify_by, "__missing__"))


def _allocate_counts(category_count: int, total_count: int, split_sizes: dict[str, int]) -> dict[str, int]:
    raw = {name: category_count * size / total_count for name, size in split_sizes.items()}
    counts = {name: int(value) for name, value in raw.items()}
    target = round(sum(raw.values()))
    remainder = target - sum(counts.values())
    order = sorted(raw, key=lambda name: (raw[name] - counts[name], split_sizes[name]), reverse=True)
    for name in order[:remainder]:
        counts[name] += 1
    return counts


def build_stratified_splits(tasks: list[Task], split_sizes: dict[str, int], stratify_by: str, seed: int) -> dict[str, list[Task]]:
    requested = sum(split_sizes.values())
    if requested > len(tasks):
        raise ValueError("Requested split sizes exceed available tasks")
    groups: dict[str, list[Task]] = defaultdict(list)
    for task in tasks:
        groups[_category(task, stratify_by)].append(task)
    rng = random.Random(seed)
    splits = {name: [] for name in split_sizes}
    reserve = []
    for category in sorted(groups):
        group = list(groups[category])
        rng.shuffle(group)
        counts = _allocate_counts(len(group), len(tasks), split_sizes)
        start = 0
        for split_name, count in counts.items():
            splits[split_name].extend(group[start : start + count])
            start += count
        reserve.extend(group[start:])
    for split_name, target_size in split_sizes.items():
        while len(splits[split_name]) < target_size and reserve:
            splits[split_name].append(reserve.pop(0))
        while len(splits[split_name]) > target_size:
            reserve.append(splits[split_name].pop())
    for split_tasks in splits.values():
        split_tasks.sort(key=lambda task: task.task_id)
    reserve.sort(key=lambda task: task.task_id)
    splits["reserve"] = reserve
    return splits
