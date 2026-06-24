from __future__ import annotations

from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.types import Patch, PatchApplicationResult, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.noop import NoOpSelector
from skill_research.selectors.random_selector import RandomSelector
from skill_research.traces.types import TraceRecord


class Benchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0), [TraceRecord("t1", False, "wrong_answer")])


class Proposer:
    def propose(self, skill, traces, config):
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule")])


class Applier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        return PatchApplicationResult(SkillRef(output_dir / patch.patch_id, patch.patch_id), patch)


def test_shared_round_still_writes_before_artifacts_for_each_selector(tmp_path: Path) -> None:
    def noop_factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), NoOpSelector(), Applier(), ScoreDeltaReward(), store)

    def random_factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), RandomSelector(seed=1), Applier(), ScoreDeltaReward(), store)

    run_comparison({"noop": noop_factory, "random": random_factory}, SkillRef(tmp_path / "skill", "seed"), tmp_path / "runs", rounds=1, seeds=[1])

    for selector in ["noop", "random"]:
        assert (tmp_path / "runs" / "selectors" / selector / "seed_001" / "round_000" / "current_skill_eval" / "evaluation_summary.json").exists()
        assert (tmp_path / "runs" / "selectors" / selector / "seed_001" / "round_000" / "current_skill_eval" / "task_traces.json").exists()
