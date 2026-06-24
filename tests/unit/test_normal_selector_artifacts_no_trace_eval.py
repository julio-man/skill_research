from __future__ import annotations

from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.types import Patch, PatchApplicationResult, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.random_selector import RandomSelector
from skill_research.traces.types import TraceRecord


class Benchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.5, 0.0, {"evolution": 1}), [TraceRecord("evolution-task", False, "wrong_answer")])


class TestBenchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 1.0, 1.0, {"none": 1}), [TraceRecord("test-task", True, "none")])


class Proposer:
    def propose(self, skill, traces, config):
        assert traces[0].task_id == "evolution-task"
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule", 1, 1)])


class Applier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "SKILL.md").write_text("# Skill\nRule\n", encoding="utf-8")
        return PatchApplicationResult(SkillRef(output_dir, output_dir.name), patch)


def test_normal_selector_round_has_no_trace_eval_and_uses_current_eval_for_proposer(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    def factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), RandomSelector(seed=1), Applier(), ScoreDeltaReward(), store, test_benchmark=TestBenchmark())

    run_comparison({"random": factory}, SkillRef(skill, "seed"), tmp_path / "run", rounds=1, seeds=[1])

    round_dir = tmp_path / "run" / "selectors" / "random" / "seed_001" / "round_000"
    assert not (round_dir / "trace_eval").exists()
    assert (round_dir / "current_skill_eval" / "task_traces.json").exists()
    assert (round_dir / "selected_skill_eval" / "task_traces.json").exists()
    assert (tmp_path / "run" / "selectors" / "random" / "seed_001" / "final_test_eval" / "evaluation_summary.json").exists()
