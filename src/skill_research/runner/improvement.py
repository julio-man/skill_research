from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from skill_research.patches.types import Patch
from skill_research.traces import TraceRecord


@dataclass
class ImprovementResult:
    before_summary: dict
    after_summary: dict
    selected_patch: Patch
    reward: float
    skill_before: str
    skill_after: str
    patch_pool: list[Patch]



def compute_score_delta_reward(before_summary: dict, after_summary: dict) -> float:
    return round(after_summary["avg_score"] - before_summary["avg_score"], 10)



def run_single_round_improvement(
    *,
    skill_dir: Path,
    workspace_dir: Path,
    benchmark_runner,
    proposer,
    selector,
    applier,
    reward_fn,
    proposer_llm_client=None,
    patch_count: int = 8,
):
    workspace_dir.mkdir(parents=True, exist_ok=True)

    baseline_dir = workspace_dir / "baseline"
    baseline_payload = benchmark_runner(skill_path=skill_dir, output_dir=baseline_dir)
    before_summary = baseline_payload["summary"]

    traces_payload = baseline_payload.get("traces", {})
    raw_traces = traces_payload.get("traces", [])
    trace_records = [trace if isinstance(trace, TraceRecord) else TraceRecord(**trace) for trace in raw_traces]
    patch_pool = proposer.generate(
        skill_path=skill_dir,
        traces=trace_records,
        k=patch_count,
        llm_client=proposer_llm_client,
    )

    selector_state = {
        "skill_path": str(skill_dir),
        "before_summary": before_summary,
    }
    selected_patch = selector.select(selector_state, patch_pool)

    improved_skill_dir = Path(applier.apply_patch(skill_dir, selected_patch, label="round0"))
    improved_dir = workspace_dir / "after"
    improved_payload = benchmark_runner(skill_path=improved_skill_dir, output_dir=improved_dir)
    after_summary = improved_payload["summary"]

    reward = reward_fn(before_summary=before_summary, after_summary=after_summary)

    return ImprovementResult(
        before_summary=before_summary,
        after_summary=after_summary,
        selected_patch=selected_patch,
        reward=reward,
        skill_before=str(skill_dir),
        skill_after=str(improved_skill_dir),
        patch_pool=patch_pool,
    )
