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


class BenchmarkWithTaskTrace:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0, {"wrong_answer": 1}), [TraceRecord("task-1", False, "wrong_answer")])


def test_proposer_failure_is_harness_event_not_task_trace(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    episode = PatchSelectionEpisode(
        BenchmarkWithTaskTrace(),
        OpenAITracePatchProposer(ReplayLLMBackend(['{"patches": [{"id": "bad", "content": "Rule"}]}'])),
        NoOpSelector(),
        SkillDirectoryPatchApplier(),
        ScoreDeltaReward(),
        JsonArtifactStore(tmp_path / "artifacts"),
    )

    result = episode.run(SkillRef(skill_dir, "seed"), tmp_path / "episode", {})

    assert result.patch_pool.metadata["proposer_failed"] is True
    assert "failure_trace" not in result.patch_pool.metadata
    event_payload = json.loads((tmp_path / "artifacts" / "harness_events.json").read_text(encoding="utf-8"))
    assert event_payload[0]["event_type"] == "patch_schema_error"
    assert event_payload[0]["component"] == "openai_trace"
    episode_payload = json.loads((tmp_path / "artifacts" / "episode.json").read_text(encoding="utf-8"))
    assert "failure_trace" not in episode_payload["patch_pool"]["metadata"]
