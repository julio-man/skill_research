from __future__ import annotations

from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.types import Patch, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.noop import NoOpSelector


class Benchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0), [])


class Proposer:
    def propose(self, skill, traces, config):
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule")])


class ApplierShouldNotRun:
    def apply(self, skill, patch, output_dir):
        raise AssertionError("noop must not apply a patch")


class Store:
    def write_episode(self, episode):
        self.episode = episode


def test_episode_noop_keeps_original_skill_and_skips_applier(tmp_path: Path) -> None:
    skill = SkillRef(tmp_path / "skill", "seed")
    episode = PatchSelectionEpisode(Benchmark(), Proposer(), NoOpSelector(), ApplierShouldNotRun(), ScoreDeltaReward(), Store())

    result = episode.run(skill, tmp_path / "episode", {})

    assert result.selected_patch is None
    assert result.skill_after == skill
