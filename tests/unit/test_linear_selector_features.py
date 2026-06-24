from __future__ import annotations

from skill_research.patches.types import Patch
from skill_research.selectors.linear_features import FEATURE_NAMES, patch_features
from skill_research.traces.types import TraceRecord


def test_patch_features_include_current_eval_round_and_supported_failure_types() -> None:
    patch = Patch(
        "p1",
        "guidance",
        "SKILL.md",
        None,
        "append_document",
        "Rule",
        delta_tokens=10,
        support_count=2,
        metadata={"supported_trace_ids": ["t1", "t2"]},
    )
    state = {
        "round": 3,
        "current_summary": {"avg_score": 0.25, "pass_rate": 0.1, "failure_histogram": {"wrong_answer": 2, "artifact_missing": 1}},
        "current_traces": [TraceRecord("t1", False, "wrong_answer"), TraceRecord("t2", False, "artifact_missing"), TraceRecord("t3", False, "wrong_answer")],
    }

    features = dict(zip(FEATURE_NAMES, patch_features(patch, state)))

    assert features["round_index"] == 3.0
    assert features["current_avg_score"] == 0.25
    assert features["current_pass_rate"] == 0.1
    assert features["n_wrong_answer"] == 2.0
    assert features["n_artifact_missing"] == 1.0
    assert features["supported_wrong_answer"] == 1.0
    assert features["supported_artifact_missing"] == 1.0
    assert features["patch_type_guidance"] == 1.0
