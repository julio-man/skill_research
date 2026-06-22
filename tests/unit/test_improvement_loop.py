from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from skill_research.patches.types import Patch
from skill_research.runner.improvement import ImprovementResult, compute_score_delta_reward, run_single_round_improvement
from skill_research.traces import TraceRecord


@dataclass
class _FakeBenchmarkRunner:
    calls: list[tuple[str, str]]

    def __call__(self, *, skill_path: Path, output_dir: Path):
        self.calls.append((str(skill_path), str(output_dir)))
        if len(self.calls) == 1:
            return {
                "summary": {
                    "avg_score": 0.2,
                    "pass_rate": 0.1,
                    "failure_histogram": {"wrong_answer": 1},
                },
                "traces": {"num_traces": 1, "traces": []},
            }
        return {
            "summary": {
                "avg_score": 0.6,
                "pass_rate": 0.3,
                "failure_histogram": {"none": 1},
            },
            "traces": {"num_traces": 1, "traces": []},
        }


class _FakeProposer:
    def __init__(self):
        self.last_llm_client = None
        self.last_k = None

    def generate(self, skill_path: Path, traces: list[TraceRecord], k: int, llm_client=None):
        self.last_llm_client = llm_client
        self.last_k = k
        return [
            Patch(
                patch_id="p1",
                patch_type="add_rule",
                target_file="SKILL.md",
                target_section=None,
                operation="append_document",
                content="## Added rule\n",
                delta_tokens=5,
                support_count=2,
            )
        ]


class _FakeSelector:
    def select(self, state: dict, patches: list[Patch]) -> Patch:
        return patches[0]


class _FakeApplier:
    def apply_patch(self, skill_dir: str | Path, patch: Patch, label: str | None = None) -> str:
        return str(Path(skill_dir).parent / "skill_after")



def test_compute_score_delta_reward_uses_avg_score_delta() -> None:
    reward = compute_score_delta_reward(
        before_summary={"avg_score": 0.2},
        after_summary={"avg_score": 0.6},
    )

    assert reward == 0.4



def test_run_single_round_improvement_orchestrates_components(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    benchmark_runner = _FakeBenchmarkRunner(calls=[])
    proposer = _FakeProposer()
    selector = _FakeSelector()
    applier = _FakeApplier()
    proposer_llm_client = object()

    result = run_single_round_improvement(
        skill_dir=skill_dir,
        workspace_dir=tmp_path / "workspace",
        benchmark_runner=benchmark_runner,
        proposer=proposer,
        selector=selector,
        applier=applier,
        reward_fn=compute_score_delta_reward,
        proposer_llm_client=proposer_llm_client,
        patch_count=3,
    )

    assert isinstance(result, ImprovementResult)
    assert result.reward == 0.4
    assert result.selected_patch.patch_id == "p1"
    assert result.before_summary["avg_score"] == 0.2
    assert result.after_summary["avg_score"] == 0.6
    assert len(benchmark_runner.calls) == 2
    assert proposer.last_llm_client is proposer_llm_client
    assert proposer.last_k == 3
