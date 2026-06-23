from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from skill_research.patches.types import Patch
from skill_research.runner.improvement import (
    ImprovementResult,
    MultiRoundImprovementResult,
    MultiSeedSelectorComparisonResult,
    MultiSelectorImprovementResult,
    SelectorAggregateRoundStats,
    SelectorRunResult,
    compute_score_delta_reward,
    ensure_noop_patch,
    run_multi_round_improvement,
    run_multi_seed_multi_selector_multi_round_improvement,
    run_multi_selector_multi_round_improvement,
    run_single_round_improvement,
)
from skill_research.traces import TraceRecord


@dataclass
class _FakeBenchmarkRunner:
    calls: list[tuple[str, str]]

    def __call__(self, *, skill_path: Path, output_dir: Path):
        self.calls.append((str(skill_path), str(output_dir)))
        if str(skill_path).endswith("skill"):
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
        self.calls: list[str] = []

    def generate(self, skill_path: Path, traces: list[TraceRecord], k: int, llm_client=None):
        self.last_llm_client = llm_client
        self.last_k = k
        self.calls.append(str(skill_path))
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
            ),
            Patch(
                patch_id="p2",
                patch_type="add_example",
                target_file="SKILL.md",
                target_section=None,
                operation="append_document",
                content="## Added example\n",
                delta_tokens=8,
                support_count=1,
            ),
        ]


class _FakeSelector:
    def select(self, state: dict, patches: list[Patch]) -> Patch:
        return patches[0]


class _PickSecondSelector:
    def select(self, state: dict, patches: list[Patch]) -> Patch:
        return patches[1]


class _FakeApplier:
    def __init__(self):
        self.calls: list[tuple[str, str, str | None]] = []

    def apply_patch(self, skill_dir: str | Path, patch: Patch, label: str | None = None) -> str:
        self.calls.append((str(skill_dir), patch.patch_id, label))
        return str(Path(skill_dir).parent / f"{label}_{patch.patch_id}")


class _SeededBenchmarkRunner:
    def __init__(self, seed: int):
        self.seed = seed
        self.calls: list[tuple[str, str]] = []

    def __call__(self, *, skill_path: Path, output_dir: Path):
        self.calls.append((str(skill_path), str(output_dir)))
        if str(skill_path).endswith("skill"):
            return {
                "summary": {
                    "avg_score": self.seed / 100,
                    "pass_rate": self.seed / 200,
                    "failure_histogram": {"wrong_answer": 1},
                },
                "traces": {"num_traces": 1, "traces": []},
            }
        return {
            "summary": {
                "avg_score": self.seed / 100 + 0.2,
                "pass_rate": self.seed / 200 + 0.1,
                "failure_histogram": {"none": 1},
            },
            "traces": {"num_traces": 1, "traces": []},
        }



def test_compute_score_delta_reward_uses_avg_score_delta() -> None:
    reward = compute_score_delta_reward(
        before_summary={"avg_score": 0.2},
        after_summary={"avg_score": 0.6},
    )

    assert reward == 0.4



def test_ensure_noop_patch_appends_noop_when_missing() -> None:
    patches = ensure_noop_patch(
        [
            Patch("p1", "add_rule", "SKILL.md", None, "append_document", "x", 3, 1),
        ]
    )

    assert [patch.patch_id for patch in patches] == ["p1", "noop"]
    assert patches[-1].operation == "no_op"



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
    assert [patch.patch_id for patch in result.patch_pool] == ["p1", "p2", "noop"]



def test_run_multi_round_improvement_returns_history_and_final_skill(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    result = run_multi_round_improvement(
        skill_dir=skill_dir,
        workspace_dir=tmp_path / "workspace",
        benchmark_runner=_FakeBenchmarkRunner(calls=[]),
        proposer=_FakeProposer(),
        selector=_FakeSelector(),
        applier=_FakeApplier(),
        reward_fn=compute_score_delta_reward,
        rounds=2,
    )

    assert isinstance(result, MultiRoundImprovementResult)
    assert len(result.history) == 2
    assert result.final_skill_dir.endswith("round1_p1")



def test_run_multi_selector_multi_round_improvement_branches_from_shared_round_zero(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    benchmark_runner = _FakeBenchmarkRunner(calls=[])
    proposer = _FakeProposer()
    applier = _FakeApplier()

    result = run_multi_selector_multi_round_improvement(
        skill_dir=skill_dir,
        workspace_dir=tmp_path / "workspace",
        benchmark_runner=benchmark_runner,
        proposer=proposer,
        selectors={
            "support_like": _FakeSelector(),
            "random_like": _PickSecondSelector(),
        },
        applier=applier,
        reward_fn=compute_score_delta_reward,
        rounds=2,
        patch_count=2,
    )

    assert isinstance(result, MultiSelectorImprovementResult)
    assert set(result.selector_runs) == {"support_like", "random_like"}
    assert all(isinstance(run, SelectorRunResult) for run in result.selector_runs.values())
    assert len(result.selector_runs["support_like"].history) == 2
    assert len(result.selector_runs["random_like"].history) == 2
    assert result.selector_runs["support_like"].history[0].selected_patch.patch_id == "p1"
    assert result.selector_runs["random_like"].history[0].selected_patch.patch_id == "p2"
    assert proposer.calls.count(str(skill_dir)) == 1
    assert len(benchmark_runner.calls) == 7



def test_run_multi_seed_multi_selector_multi_round_improvement_aggregates_round_stats(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    result = run_multi_seed_multi_selector_multi_round_improvement(
        skill_dir=skill_dir,
        workspace_dir=tmp_path / "workspace",
        benchmark_runner_factory=lambda seed: _SeededBenchmarkRunner(seed),
        proposer=_FakeProposer(),
        selectors={
            "support_like": _FakeSelector(),
            "random_like": _PickSecondSelector(),
        },
        applier=_FakeApplier(),
        reward_fn=compute_score_delta_reward,
        seeds=[41, 42, 43],
        rounds=2,
        patch_count=2,
    )

    assert isinstance(result, MultiSeedSelectorComparisonResult)
    assert set(result.per_seed_runs) == {41, 42, 43}
    assert set(result.aggregate_by_selector) == {"support_like", "random_like"}

    support_round_zero = result.aggregate_by_selector["support_like"][0]
    assert isinstance(support_round_zero, SelectorAggregateRoundStats)
    assert support_round_zero.reward_mean == 0.2
    assert round(support_round_zero.reward_std, 10) == 0.0
    assert support_round_zero.before_avg_score_mean == 0.42
    assert support_round_zero.after_avg_score_mean == 0.62
    assert support_round_zero.seeds == [41, 42, 43]

    random_round_one = result.aggregate_by_selector["random_like"][1]
    assert random_round_one.selected_patch_ids == {41: "p2", 42: "p2", 43: "p2"}
    assert random_round_one.reward_mean == 0.0
