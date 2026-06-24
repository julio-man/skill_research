"""Loads JSON, TOML, or YAML experiment specs into typed config objects."""

from __future__ import annotations

import json
from pathlib import Path
import tomllib
from typing import Any

from skill_research.config.experiment import DatasetConfig, ExperimentSpec, NamedConfig, RunConfig, SkillConfig


def _named(payload: dict[str, Any]) -> NamedConfig:
    params = {key: value for key, value in payload.items() if key != "name"}
    return NamedConfig(name=payload["name"], params=params)


def _load_payload(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise ValueError("YAML experiment specs require PyYAML to be installed") from exc
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported experiment spec format: {path.suffix}")


def load_experiment_spec(path: str | Path) -> ExperimentSpec:
    path = Path(path)
    payload = _load_payload(path)
    dataset_payload = payload["dataset"]
    dataset_params = {key: value for key, value in dataset_payload.items() if key not in {"name", "split", "root"}}
    return ExperimentSpec(
        experiment_id=payload["experiment_id"],
        dataset=DatasetConfig(
            name=dataset_payload["name"],
            split=dataset_payload["split"],
            root=dataset_payload.get("root"),
            params=dataset_params,
        ),
        skill=SkillConfig(**payload["skill"]),
        executor=_named(payload["executor"]),
        evaluator=_named(payload["evaluator"]),
        proposer=_named(payload["proposer"]),
        applier=_named(payload["applier"]),
        reward=_named(payload["reward"]),
        selectors=[_named(selector) for selector in payload["selectors"]],
        run=RunConfig(**payload["run"]),
    )
