"""Feature extraction helpers for linear patch selectors."""

from __future__ import annotations

from typing import Any

from skill_research.patches.types import Patch

FEATURE_NAMES = [
    "bias",
    "support_count",
    "delta_tokens",
    "target_file_is_skill_md",
    "operation_append_document",
    "patch_type_guidance",
    "patch_type_noop",
    "round_index",
    "current_avg_score",
    "current_pass_rate",
    "n_wrong_answer",
    "n_artifact_missing",
    "n_format_fail",
    "n_tool_fail",
    "n_timeout",
    "n_other",
    "supported_wrong_answer",
    "supported_artifact_missing",
    "supported_format_fail",
    "supported_tool_fail",
    "supported_timeout",
    "supported_other",
]


def _summary_value(state: dict[str, Any], key: str, default: float = 0.0) -> float:
    summary = state.get("current_summary", {}) if isinstance(state, dict) else {}
    if isinstance(summary, dict):
        return float(summary.get(key, default))
    return float(getattr(summary, key, default))


def _failure_histogram(state: dict[str, Any]) -> dict[str, float]:
    summary = state.get("current_summary", {}) if isinstance(state, dict) else {}
    histogram = summary.get("failure_histogram", {}) if isinstance(summary, dict) else getattr(summary, "failure_histogram", {})
    return {str(key): float(value) for key, value in histogram.items()}


def _supported_failure_counts(patch: Patch, state: dict[str, Any]) -> dict[str, float]:
    supported_ids = set(patch.metadata.get("supported_trace_ids", []))
    counts: dict[str, float] = {}
    for trace in state.get("current_traces", []) if isinstance(state, dict) else []:
        if getattr(trace, "task_id", None) in supported_ids:
            failure_type = getattr(trace, "failure_type", "other") or "other"
            counts[failure_type] = counts.get(failure_type, 0.0) + 1.0
    return counts


def _bucket(counts: dict[str, float], name: str) -> float:
    return float(counts.get(name, 0.0))


def _other(counts: dict[str, float]) -> float:
    known = {"wrong_answer", "artifact_missing", "format_fail", "tool_fail", "timeout"}
    return sum(value for key, value in counts.items() if key not in known)


def patch_features(patch: Patch, state: dict[str, Any] | None = None) -> list[float]:
    """Return numeric patch/context features for linear selector scoring."""
    state = state or {}
    histogram = _failure_histogram(state)
    supported = _supported_failure_counts(patch, state)
    return [
        1.0,
        float(patch.support_count),
        float(patch.delta_tokens),
        1.0 if patch.target_file == "SKILL.md" else 0.0,
        1.0 if patch.operation == "append_document" else 0.0,
        1.0 if patch.patch_type == "guidance" else 0.0,
        1.0 if patch.patch_type == "noop" or patch.operation == "no_op" else 0.0,
        float(state.get("round", 0.0)) if isinstance(state, dict) else 0.0,
        _summary_value(state, "avg_score"),
        _summary_value(state, "pass_rate"),
        _bucket(histogram, "wrong_answer"),
        _bucket(histogram, "artifact_missing"),
        _bucket(histogram, "format_fail"),
        _bucket(histogram, "tool_fail"),
        _bucket(histogram, "timeout"),
        _other(histogram),
        _bucket(supported, "wrong_answer"),
        _bucket(supported, "artifact_missing"),
        _bucket(supported, "format_fail"),
        _bucket(supported, "tool_fail"),
        _bucket(supported, "timeout"),
        _other(supported),
    ]


def dot(left: list[float], right: list[float]) -> float:
    """Compute a dot product for equal-length vectors."""
    return sum(a * b for a, b in zip(left, right))
