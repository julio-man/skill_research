from __future__ import annotations

from pathlib import Path

from skill_research.artifacts.store import JsonArtifactStore
from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.types import Patch, PatchApplicationResult, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.noop import NoOpSelector
from skill_research.selectors.random_selector import RandomSelector


class Benchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0), [])


class CountingProposer:
    def __init__(self):
        self.calls = 0

    def propose(self, skill, traces, config):
        self.calls += 1
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule")])


class Applier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        return PatchApplicationResult(SkillRef(output_dir / patch.patch_id, patch.patch_id), patch)


def test_comparison_shares_patch_pool_for_round_when_selector_skills_are_same(tmp_path: Path) -> None:
    proposer = CountingProposer()

    def noop_factory(store):
        return PatchSelectionEpisode(Benchmark(), proposer, NoOpSelector(), Applier(), ScoreDeltaReward(), store)

    def random_factory(store):
        return PatchSelectionEpisode(Benchmark(), proposer, RandomSelector(seed=1), Applier(), ScoreDeltaReward(), store)

    run_comparison({"noop": noop_factory, "random": random_factory}, SkillRef(tmp_path / "skill", "seed"), tmp_path / "runs", rounds=1, seeds=[1])

    assert proposer.calls == 1
    noop_episode = (tmp_path / "runs" / "selectors" / "noop" / "seed_001" / "round_000" / "episode.json").read_text(encoding="utf-8")
    random_episode = (tmp_path / "runs" / "selectors" / "random" / "seed_001" / "round_000" / "episode.json").read_text(encoding="utf-8")
    assert '"selected_patch": null' in noop_episode
    assert '"patch_id": "p1"' in random_episode
