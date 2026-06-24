from __future__ import annotations

from pathlib import Path

from skill_research.core.types import SkillRef, Task
from skill_research.datasets.base import DatasetInfo, DatasetSplit
from skill_research.evaluators.base import EvaluationResult
from skill_research.executors.base import ExecutionResult
from skill_research.experiments.benchmark import BenchmarkRunResult, ComponentBenchmarkRunner


class FakeExecutor:
    name = "fake_executor"

    def run(self, task, skill, output_dir, config):
        return ExecutionResult(str(output_dir / f"{task.task_id}.out"), None, "raw", "", "", 0)


class FakeEvaluator:
    name = "fake_evaluator"

    def evaluate(self, task, execution):
        passed = task.task_id == "pass"
        return EvaluationResult(passed=passed, score=1.0 if passed else 0.0, failure_type="none" if passed else "wrong_answer")


def test_component_benchmark_runner_returns_summary_and_traces(tmp_path: Path) -> None:
    split = DatasetSplit("val", [Task("pass", "ok"), Task("fail", "bad")], DatasetInfo("toy", "generic"))
    runner = ComponentBenchmarkRunner(split, FakeExecutor(), FakeEvaluator(), executor_config={"temperature": 0.0})

    result = runner.run(SkillRef(tmp_path / "skill", "seed"), tmp_path / "benchmark")

    assert isinstance(result, BenchmarkRunResult)
    assert result.summary.num_tasks == 2
    assert result.summary.avg_score == 0.5
    assert result.summary.pass_rate == 0.5
    assert result.summary.failure_histogram == {"none": 1, "wrong_answer": 1}
    assert len(result.traces) == 2
    assert (tmp_path / "benchmark" / "task_traces.json").exists()
    assert (tmp_path / "benchmark" / "evaluation_summary.json").exists()
