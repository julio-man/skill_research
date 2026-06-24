"""CLI entrypoint for running selector-based skill patch experiments."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from skill_research.config.loader import load_experiment_spec
from skill_research.core.types import SkillRef
from skill_research.datasets import build_dataset_provider
from skill_research.evaluators import build_evaluator
from skill_research.executors import build_executor
from skill_research.experiments.benchmark import ComponentBenchmarkRunner
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.llms import build_llm_backend
from skill_research.patches.appliers import build_applier
from skill_research.patches.proposers import build_proposer
from skill_research.rewards import build_reward
from skill_research.selectors import build_selector


SECRET_KEYS = {"api_key", "base_url", "endpoint", "azure_openai_endpoint", "openai_base_url"}


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("<redacted>" if str(key).lower() in SECRET_KEYS else redact_secrets(inner)) for key, inner in value.items()}
    if isinstance(value, list):
        return [redact_secrets(inner) for inner in value]
    return value


def _build_llm(config: dict[str, Any]):
    payload = dict(config)
    name = payload.pop("name")
    return build_llm_backend(name, **payload)


def build_selectors(spec) -> dict[str, object]:
    return {selector.name: build_selector(selector.name, **selector.params) for selector in spec.selectors}


def _component_params(named_config) -> dict[str, Any]:
    return dict(named_config.params)


def _build_executor(spec):
    params = _component_params(spec.executor)
    llm_config = params.pop("llm", None)
    if llm_config is not None:
        params["backend"] = _build_llm(llm_config)
    return build_executor(spec.executor.name, **params), params


def _build_proposer(spec):
    params = _component_params(spec.proposer)
    llm_config = params.pop("llm", None)
    if llm_config is not None:
        params["backend"] = _build_llm(llm_config)
    return build_proposer(spec.proposer.name, **params)


def _build_dataset_provider(spec):
    dataset_params = {key: value for key, value in spec.dataset.params.items() if key not in {"validation_split", "test_split"}}
    if spec.dataset.root is not None:
        dataset_params["root"] = spec.dataset.root
    return build_dataset_provider(spec.dataset.name, **dataset_params)


def _build_dataset_split(spec):
    return _build_dataset_provider(spec).load_split(spec.dataset.split)


def _build_optional_split(spec, key: str):
    split_name = spec.dataset.params.get(key)
    if not split_name:
        return None
    return _build_dataset_provider(spec).load_split(split_name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a skill patch-selection experiment")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    spec = load_experiment_spec(args.config)
    output_dir = Path(spec.run.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "experiment_config.resolved.json").write_text(json.dumps(redact_secrets(asdict(spec)), indent=2), encoding="utf-8")
    selectors = build_selectors(spec)
    if args.dry_run:
        return

    dataset_split = _build_dataset_split(spec)
    validation_split = _build_optional_split(spec, "validation_split")
    test_split = _build_optional_split(spec, "test_split")
    executor, executor_config = _build_executor(spec)
    evaluator = build_evaluator(spec.evaluator.name, **spec.evaluator.params)
    proposer = _build_proposer(spec)
    applier = build_applier(spec.applier.name, **spec.applier.params)
    reward = build_reward(spec.reward.name, **spec.reward.params)
    skill = SkillRef(Path(spec.skill.path), Path(spec.skill.path).name)

    factories = {}
    for selector_name, selector in selectors.items():
        def factory(store, selected=selector):
            benchmark = ComponentBenchmarkRunner(dataset_split, executor, evaluator, executor_config=executor_config)
            test_benchmark = ComponentBenchmarkRunner(test_split, executor, evaluator, executor_config=executor_config) if test_split is not None else None
            validation_benchmark = ComponentBenchmarkRunner(validation_split, executor, evaluator, executor_config=executor_config) if validation_split is not None and selector_name == "greedy" else None
            return PatchSelectionEpisode(benchmark, proposer, selected, applier, reward, store, test_benchmark=test_benchmark, validation_benchmark=validation_benchmark)

        factories[selector_name] = factory
    run_comparison(factories, skill, output_dir, spec.run.rounds, spec.run.seeds)


if __name__ == "__main__":
    main()
