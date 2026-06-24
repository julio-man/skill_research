from __future__ import annotations

from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.llms.replay import ReplayLLMBackend
from skill_research.patches.appliers.skill_directory import SkillDirectoryPatchApplier
from skill_research.patches.proposers.openai_trace import OpenAITracePatchProposer
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.noop import NoOpSelector
from skill_research.traces.types import TraceRecord


class FailingBenchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0, {"wrong_answer": 1}), [TraceRecord("t1", False, "wrong_answer", {"detail": "bad"})])


class Store:
    def write_episode(self, episode):
        self.episode = episode

    def write_harness_events(self, events):
        self.events = events


def test_episode_captures_patch_schema_failure_as_harness_event_and_falls_back_to_noop(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    proposer = OpenAITracePatchProposer(ReplayLLMBackend(['{"patches": [{"id": "bad", "content": "Rule"}]}']))
    store = Store()
    episode = PatchSelectionEpisode(FailingBenchmark(), proposer, NoOpSelector(), SkillDirectoryPatchApplier(), ScoreDeltaReward(), store)

    result = episode.run(SkillRef(skill_dir, "seed"), tmp_path / "episode", {})

    assert result.selected_patch is None
    assert result.patch_pool.metadata["proposer_failed"] is True
    assert result.patch_pool.metadata["failure_type"] == "patch_schema_error"
    assert store.events[0].event_type == "patch_schema_error"
    assert store.events[0].component == "openai_trace"
