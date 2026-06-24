"""Dataclasses that describe a configurable selector experiment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NamedConfig:
    name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    split: str
    root: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillConfig:
    path: str


@dataclass(frozen=True)
class RunConfig:
    rounds: int
    seeds: list[int]
    output_dir: str


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    dataset: DatasetConfig
    skill: SkillConfig
    executor: NamedConfig
    evaluator: NamedConfig
    proposer: NamedConfig
    applier: NamedConfig
    reward: NamedConfig
    selectors: list[NamedConfig]
    run: RunConfig
