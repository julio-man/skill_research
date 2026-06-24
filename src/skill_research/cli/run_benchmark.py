"""CLI entrypoint for evaluating one skill on a configured benchmark split."""

from __future__ import annotations

import argparse
from pathlib import Path

from skill_research.cli.run_experiment import _build_dataset_split, _build_executor
from skill_research.config.loader import load_experiment_spec
from skill_research.core.types import SkillRef
from skill_research.evaluators import build_evaluator
from skill_research.experiments.benchmark import ComponentBenchmarkRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a benchmark with a configured executor and evaluator")
    parser.add_argument("--config", required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    spec = load_experiment_spec(args.config)
    dataset_split = _build_dataset_split(spec)
    executor, executor_config = _build_executor(spec)
    evaluator = build_evaluator(spec.evaluator.name, **spec.evaluator.params)
    runner = ComponentBenchmarkRunner(dataset_split, executor, evaluator, executor_config=executor_config)
    runner.run(SkillRef(Path(spec.skill.path), Path(spec.skill.path).name), Path(spec.run.output_dir))


if __name__ == "__main__":
    main()
