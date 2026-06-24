from skill_research.core.registry import ComponentRegistry
from skill_research.datasets.base import DatasetInfo, DatasetProvider, DatasetProviderBase, DatasetSplit, InMemoryDatasetProvider, build_stratified_splits
from skill_research.datasets.spreadsheetbench_verified import SpreadsheetBenchVerifiedDatasetProvider


dataset_registry = ComponentRegistry()
dataset_registry.register("memory", lambda splits, dataset=None, **kwargs: InMemoryDatasetProvider(splits, dataset=dataset))
dataset_registry.register("spreadsheetbench_verified", lambda root, **kwargs: SpreadsheetBenchVerifiedDatasetProvider(root, **kwargs))


def build_dataset_provider(name: str, **kwargs):
    return dataset_registry.build(name, **kwargs)


__all__ = [
    "DatasetInfo",
    "DatasetProvider",
    "DatasetProviderBase",
    "DatasetSplit",
    "InMemoryDatasetProvider",
    "SpreadsheetBenchVerifiedDatasetProvider",
    "build_dataset_provider",
    "build_stratified_splits",
    "dataset_registry",
]
