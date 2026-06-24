"""Benchmark runner that evaluates one skill over a dataset split."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any

from skill_research.core.serialization import to_json_file
from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.datasets.base import DatasetSplit
from skill_research.traces.store import save_traces
from skill_research.traces.types import TraceRecord


@dataclass(frozen=True)
class BenchmarkRunResult:
    summary: BenchmarkSummary
    traces: list[TraceRecord]


def _relative_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return os.path.relpath(Path(path).resolve(), Path.cwd().resolve())


class ComponentBenchmarkRunner:
    def __init__(self, dataset_split: DatasetSplit, executor, evaluator, executor_config: dict[str, Any] | None = None):
        self.dataset_split = dataset_split
        self.executor = executor
        self.evaluator = evaluator
        self.executor_config = executor_config or {}

    def run(self, skill: SkillRef, output_dir: Path) -> BenchmarkRunResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        traces: list[TraceRecord] = []
        scores = []
        failure_histogram: dict[str, int] = {}
        for task in self.dataset_split.tasks:
            task_dir = output_dir / "tasks" / task.task_id
            execution = self.executor.run(task, skill, task_dir, self.executor_config)
            evaluation = self.evaluator.evaluate(task, execution)
            scores.append(evaluation.score)
            failure_histogram[evaluation.failure_type] = failure_histogram.get(evaluation.failure_type, 0) + 1
            traces.append(
                TraceRecord(
                    task_id=task.task_id,
                    success=evaluation.passed,
                    failure_type=evaluation.failure_type,
                    payload={
                        "instruction": task.instruction,
                        "input_path": _relative_path(task.input_path),
                        "execution": execution,
                        "evaluation": evaluation,
                    },
                )
            )
        num_tasks = len(self.dataset_split.tasks)
        avg_score = sum(scores) / num_tasks if num_tasks else 0.0
        pass_rate = failure_histogram.get("none", 0) / num_tasks if num_tasks else 0.0
        summary = BenchmarkSummary(num_tasks=num_tasks, avg_score=avg_score, pass_rate=pass_rate, failure_histogram=failure_histogram)
        save_traces(traces, output_dir / "task_traces.json")
        to_json_file(summary, output_dir / "evaluation_summary.json")
        return BenchmarkRunResult(summary=summary, traces=traces)
