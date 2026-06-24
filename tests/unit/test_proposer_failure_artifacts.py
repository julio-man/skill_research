from __future__ import annotations

import json
from pathlib import Path

from skill_research.artifacts.store import JsonArtifactStore
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
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0, {"wrong_answer": 1}), [TraceRecord("t1", False, "wrong_answer")])


def test_proposer_failure_event_is_written_separately_from_episode_artifact(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    episode = PatchSelectionEpisode(
        FailingBenchmark(),
        OpenAITracePatchProposer(ReplayLLMBackend(['{"patches": [{"id": "bad", "content": "Rule"}]}'])),
        NoOpSelector(),
        SkillDirectoryPatchApplier(),
        ScoreDeltaReward(),
        JsonArtifactStore(tmp_path / "artifacts"),
    )

    episode.run(SkillRef(skill_dir, "seed"), tmp_path / "episode", {})

    episode_payload = json.loads((tmp_path / "artifacts" / "episode.json").read_text(encoding="utf-8"))
    events_payload = json.loads((tmp_path / "artifacts" / "harness_events.json").read_text(encoding="utf-8"))
    assert episode_payload["patch_pool"]["metadata"]["failure_type"] == "patch_schema_error"
    assert "failure_trace" not in episode_payload["patch_pool"]["metadata"]
    assert events_payload[0]["event_type"] == "patch_schema_error"
    assert events_payload[0]["message"]
