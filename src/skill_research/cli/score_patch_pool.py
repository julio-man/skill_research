"""CLI entrypoint for scoring a saved patch pool against a configured benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from skill_research.cli.run_experiment import _build_dataset_split, _build_executor
from skill_research.config.loader import load_experiment_spec
from skill_research.core.serialization import to_json_safe
from skill_research.core.types import SkillRef
from skill_research.evaluators import build_evaluator
from skill_research.experiments.benchmark import ComponentBenchmarkRunner
from skill_research.patches.appliers import build_applier
from skill_research.patches.types import PatchPool
from skill_research.rewards import build_reward


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score a saved patch pool against a configured benchmark")
    parser.add_argument("--config", required=True)
    parser.add_argument("--patch-pool", required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    spec = load_experiment_spec(args.config)
    output_dir = Path(spec.run.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    skill = SkillRef(Path(spec.skill.path), Path(spec.skill.path).name)
    dataset_split = _build_dataset_split(spec)
    executor, executor_config = _build_executor(spec)
    evaluator = build_evaluator(spec.evaluator.name, **spec.evaluator.params)
    applier = build_applier(spec.applier.name, **spec.applier.params)
    reward = build_reward(spec.reward.name, **spec.reward.params)
    patch_pool = PatchPool.load(Path(args.patch_pool))
    baseline_runner = ComponentBenchmarkRunner(dataset_split, executor, evaluator, executor_config=executor_config)
    baseline = baseline_runner.run(skill, output_dir / "baseline")
    scores = []
    for patch in patch_pool.patches:
        application = applier.apply(skill, patch, output_dir / "skills" / patch.patch_id)
        runner = ComponentBenchmarkRunner(dataset_split, executor, evaluator, executor_config=executor_config)
        after = runner.run(application.skill, output_dir / "patches" / patch.patch_id)
        reward_result = reward.compute(baseline.summary, after.summary, context={})
        scores.append({"patch_id": patch.patch_id, "reward": reward_result.value, "before": baseline.summary, "after": after.summary})
    (output_dir / "patch_scores.json").write_text(json.dumps(to_json_safe(scores), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
