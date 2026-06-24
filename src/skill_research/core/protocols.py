"""Shared structural protocols for swappable harness components."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DatasetProvider(Protocol):
    name: str

    def load_split(self, split: str) -> Any:
        ...


@runtime_checkable
class Executor(Protocol):
    name: str

    def run(self, task: Any, skill: Any, output_dir: Path, config: Any) -> Any:
        ...


@runtime_checkable
class Evaluator(Protocol):
    name: str

    def evaluate(self, task: Any, execution: Any) -> Any:
        ...


@runtime_checkable
class PatchProposer(Protocol):
    name: str

    def propose(self, skill: Any, traces: list[Any], config: Any) -> Any:
        ...


@runtime_checkable
class PatchApplier(Protocol):
    name: str

    def apply(self, skill: Any, patch: Any, output_dir: Path) -> Any:
        ...


@runtime_checkable
class StateBuilder(Protocol):
    schema_version: str

    def build(self, skill: Any, benchmark: Any, patch_pool: Any, history: Any) -> Any:
        ...


@runtime_checkable
class Selector(Protocol):
    name: str

    def select(self, state: Any, patch_pool: Any) -> Any:
        ...

    def observe(self, transition: Any) -> None:
        ...

    def save_state(self, path: Path) -> None:
        ...

    def load_state(self, path: Path) -> None:
        ...


@runtime_checkable
class RewardFunction(Protocol):
    name: str

    def compute(self, before: Any, after: Any, context: Any) -> Any:
        ...


@runtime_checkable
class ArtifactStore(Protocol):
    def write_episode(self, episode: Any) -> None:
        ...

    def write_run(self, run: Any) -> None:
        ...

    def write_comparison(self, comparison: Any) -> None:
        ...
