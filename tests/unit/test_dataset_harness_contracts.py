from __future__ import annotations

from pathlib import Path

import pytest

from skill_research.core.types import Task
from skill_research.datasets import build_dataset_provider
from skill_research.datasets.base import DatasetInfo, DatasetProviderBase, DatasetSplit, InMemoryDatasetProvider
from skill_research.datasets.spreadsheetbench_verified import SpreadsheetBenchVerifiedDatasetProvider, load_spreadsheetbench_verified


class ToyDatasetProvider(DatasetProviderBase):
    name = "toy"

    def __init__(self) -> None:
        super().__init__(DatasetInfo(name=self.name, domain="toy", root=None, metadata={"source": "unit"}))
        self._splits = {"val": [Task("toy-1", "solve toy task", metadata={"kind": "toy"})]}

    def load_split(self, split: str) -> DatasetSplit:
        return self.make_split(split, self._splits[split])


def test_dataset_provider_base_is_domain_agnostic() -> None:
    provider = ToyDatasetProvider()
    split = provider.load_split("val")

    assert split.name == "val"
    assert split.dataset.name == "toy"
    assert split.dataset.domain == "toy"
    assert split.tasks[0].metadata["kind"] == "toy"
    assert len(split) == 1


def test_in_memory_dataset_provider_returns_dataset_split_not_bare_list() -> None:
    task = Task("t1", "Do it")
    provider = InMemoryDatasetProvider({"val": [task]}, dataset=DatasetInfo(name="memory", domain="generic"))

    split = provider.load_split("val")

    assert split == DatasetSplit(name="val", tasks=[task], dataset=DatasetInfo(name="memory", domain="generic"))


def test_in_memory_dataset_provider_rejects_unknown_split() -> None:
    provider = InMemoryDatasetProvider({"val": []})

    with pytest.raises(KeyError, match="Unknown split"):
        provider.load_split("test")


def test_spreadsheetbench_provider_is_a_dataset_component() -> None:
    root = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")
    provider = SpreadsheetBenchVerifiedDatasetProvider(root=root, limit=1)
    split = provider.load_split("val")

    assert provider.info.name == "spreadsheetbench_verified"
    assert provider.info.domain == "spreadsheet"
    assert split.name == "val"
    assert split.dataset == provider.info


def test_dataset_registry_builds_spreadsheetbench_provider() -> None:
    root = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")
    provider = build_dataset_provider("spreadsheetbench_verified", root=root, limit=1)
    assert isinstance(provider, SpreadsheetBenchVerifiedDatasetProvider)
    assert load_spreadsheetbench_verified(root).info == provider.info
