from __future__ import annotations

import json
from pathlib import Path

from skill_research.artifacts.store import JsonArtifactStore
from skill_research.core.types import BenchmarkSummary, SkillRef, Task
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.experiments.multi_round import run_multi_round
from skill_research.patches.types import Patch, PatchApplicationResult, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.noop import NoOpSelector


class FakeBenchmark:
    def __init__(self):
        self.calls = 0

    def run(self, skill: SkillRef, output_dir: Path):
        self.calls += 1
        score = 0.0 if self.calls == 1 else 1.0
        return {"summary": BenchmarkSummary(1, score, score), "traces": []}


class FakeProposer:
    def propose(self, skill, traces, config):
        return PatchPool([Patch("noop", "noop", "SKILL.md", None, "no_op", "")])


class FakeApplier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        return PatchApplicationResult(SkillRef(output_dir / "skill", "next"), patch)


def test_patch_selection_episode_runs_and_writes_artifacts(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path / "artifacts")
    episode = PatchSelectionEpisode(FakeBenchmark(), FakeProposer(), NoOpSelector(), FakeApplier(), ScoreDeltaReward(), store)

    result = episode.run(SkillRef(tmp_path / "skill", "seed"), tmp_path / "episode", {})

    assert result.reward.value == 1.0
    assert (tmp_path / "artifacts" / "episode.json").exists()


def test_multi_round_and_comparison_return_curves(tmp_path: Path) -> None:
    selector = NoOpSelector()
    result = run_multi_round(
        skill=SkillRef(tmp_path / "skill", "seed"),
        episode_factory=lambda store: PatchSelectionEpisode(FakeBenchmark(), FakeProposer(), selector, FakeApplier(), ScoreDeltaReward(), store),
        output_dir=tmp_path / "run",
        rounds=2,
    )
    assert len(result.episodes) == 2
    comparison = run_comparison({"noop": lambda store: PatchSelectionEpisode(FakeBenchmark(), FakeProposer(), selector, FakeApplier(), ScoreDeltaReward(), store)}, SkillRef(tmp_path / "skill", "seed"), tmp_path / "cmp", rounds=1, seeds=[1])
    assert comparison.selector_runs["noop"]["1"].episodes[0].reward.value == 1.0
    payload = json.loads((tmp_path / "cmp" / "selector_comparison.json").read_text(encoding="utf-8"))
    assert payload["selectors"]["noop"]["seeds"]["1"]["cumulative_reward"] == [1.0]
