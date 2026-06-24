from __future__ import annotations

from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.types import Patch, PatchApplicationResult, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.support_count import SupportCountSelector
from skill_research.traces.types import TraceRecord


class BenchmarkObject:
    def __init__(self):
        self.calls = 0

    def run(self, skill: SkillRef, output_dir: Path):
        self.calls += 1
        score = 0.0 if self.calls == 1 else 1.0
        return BenchmarkRunResult(BenchmarkSummary(1, score, score, {"wrong_answer" if score == 0 else "none": 1}), [TraceRecord("t1", score == 1.0, "none" if score == 1.0 else "wrong_answer")])


class Proposer:
    def propose(self, skill, traces, config):
        return PatchPool([Patch("p1", "add_rule", "SKILL.md", None, "append_document", "Rule", support_count=len(traces))])


class Applier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        return PatchApplicationResult(SkillRef(output_dir, "next"), patch)


class Store:
    def write_episode(self, episode):
        self.episode = episode


def test_episode_accepts_benchmark_run_result_objects(tmp_path: Path) -> None:
    store = Store()
    episode = PatchSelectionEpisode(BenchmarkObject(), Proposer(), SupportCountSelector(), Applier(), ScoreDeltaReward(), store)

    result = episode.run(SkillRef(tmp_path / "skill", "seed"), tmp_path / "episode", {})

    assert result.reward.value == 1.0
    assert result.selected_patch.patch_id == "p1"
    assert store.episode == result
