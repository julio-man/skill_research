from skill_research.evaluation.base import CheckResult, EvaluationResult
from skill_research.runner.benchmark import summarize_results


def _result(task_id: str, passed: bool, score: float, failure_type: str) -> EvaluationResult:
    return EvaluationResult(
        passed=passed,
        score=score,
        failure_type=failure_type,
        checks=[CheckResult(kind="dummy", passed=passed, message="", details={})],
        metadata={"task_id": task_id},
    )


def test_summarize_results_computes_basic_metrics() -> None:
    results = [
        _result("t1", True, 1.0, "none"),
        _result("t2", False, 0.0, "wrong_answer"),
        _result("t3", False, 0.5, "artifact_missing"),
    ]

    summary = summarize_results(results)

    assert summary["num_tasks"] == 3
    assert summary["pass_rate"] == 1 / 3
    assert summary["avg_score"] == 0.5
    assert summary["failure_histogram"] == {
        "none": 1,
        "wrong_answer": 1,
        "artifact_missing": 1,
    }
