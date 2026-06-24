from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReportRows:
    per_round_rewards: list[dict[str, Any]]
    selected_patches: list[dict[str, Any]]
    failure_modes: list[dict[str, Any]]
    task_score_flips: list[dict[str, Any]]
    final_test_scores: list[dict[str, Any]]


def _load(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _trace_scores(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    for trace in _load(path, []):
        evaluation = trace.get("payload", {}).get("evaluation", {})
        rows[trace["task_id"]] = {
            "score": float(evaluation.get("score", 0.0)),
            "failure_type": evaluation.get("failure_type", trace.get("failure_type")),
            "passed": bool(evaluation.get("passed", trace.get("success", False))),
        }
    return rows


def _failure_row(selector: str, seed: str, round_index: int, eval_name: str, summary: dict[str, Any]) -> dict[str, Any]:
    row = {"selector": selector, "seed": seed, "round": round_index, "eval": eval_name}
    row.update(summary.get("failure_histogram", {}))
    row["avg_score"] = summary.get("avg_score", 0.0)
    row["pass_rate"] = summary.get("pass_rate", 0.0)
    row["num_tasks"] = summary.get("num_tasks", 0)
    return row


def load_report_rows(run_root: Path) -> ReportRows:
    run_root = Path(run_root)
    comparison = _load(run_root / "selector_comparison.json", {"selectors": {}})
    per_round_rewards = []
    selected_patches = []
    failure_modes = []
    task_score_flips = []
    final_test_scores = []
    for selector, selector_payload in comparison.get("selectors", {}).items():
        for seed, seed_payload in selector_payload.get("seeds", {}).items():
            round_rewards = seed_payload.get("round_rewards", [])
            cumulative = seed_payload.get("cumulative_reward", [])
            seed_dir = run_root / "selectors" / selector / f"seed_{int(seed):03d}"
            for round_index, reward in enumerate(round_rewards):
                per_round_rewards.append({
                    "selector": selector,
                    "seed": seed,
                    "round": round_index,
                    "round_reward": reward,
                    "cumulative_reward": cumulative[round_index] if round_index < len(cumulative) else None,
                })
                round_dir = seed_dir / f"round_{round_index:03d}"
                decision = _load(round_dir / "selection" / "decision.json", {})
                pool = _load(round_dir / "patch_proposal" / "patch_pool.json", {"patches": [], "metadata": {}})
                patch = next((item for item in pool.get("patches", []) if item.get("patch_id") == decision.get("patch_id")), None)
                selected_patches.append({
                    "selector": selector,
                    "seed": seed,
                    "round": round_index,
                    "patch_id": decision.get("patch_id"),
                    "action_index": decision.get("action_index"),
                    "reason": decision.get("reason"),
                    "patch_type": patch.get("patch_type") if patch else None,
                    "delta_tokens": patch.get("delta_tokens") if patch else None,
                    "support_count": patch.get("support_count") if patch else None,
                    "target_file": patch.get("target_file") if patch else None,
                    "proposer": pool.get("metadata", {}).get("proposer"),
                })
                current_summary = _load(round_dir / "current_skill_eval" / "evaluation_summary.json", {})
                selected_summary = _load(round_dir / "selected_skill_eval" / "evaluation_summary.json", {})
                failure_modes.append(_failure_row(selector, seed, round_index, "current_skill_eval", current_summary))
                failure_modes.append(_failure_row(selector, seed, round_index, "selected_skill_eval", selected_summary))
                current_scores = _trace_scores(round_dir / "current_skill_eval" / "task_traces.json")
                selected_scores = _trace_scores(round_dir / "selected_skill_eval" / "task_traces.json")
                for task_id in sorted(set(current_scores) | set(selected_scores)):
                    current = current_scores.get(task_id, {"score": 0.0, "failure_type": "missing", "passed": False})
                    selected = selected_scores.get(task_id, {"score": 0.0, "failure_type": "missing", "passed": False})
                    task_score_flips.append({
                        "selector": selector,
                        "seed": seed,
                        "round": round_index,
                        "task_id": task_id,
                        "current_score": current["score"],
                        "selected_score": selected["score"],
                        "score_delta": selected["score"] - current["score"],
                        "current_failure_type": current["failure_type"],
                        "selected_failure_type": selected["failure_type"],
                        "current_passed": current["passed"],
                        "selected_passed": selected["passed"],
                    })
            final_summary = _load(seed_dir / "final_test_eval" / "evaluation_summary.json", None)
            if final_summary is not None:
                row = {"selector": selector, "seed": seed}
                row.update(final_summary)
                final_test_scores.append(row)
    return ReportRows(per_round_rewards, selected_patches, failure_modes, task_score_flips, final_test_scores)
