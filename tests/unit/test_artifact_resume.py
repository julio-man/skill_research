from __future__ import annotations

import json
from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.types import Patch, PatchApplicationResult, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.random_selector import RandomSelector
from skill_research.traces.types import TraceRecord


class CountingBenchmark:
    calls = 0

    def run(self, skill: SkillRef, output_dir: Path):
        CountingBenchmark.calls += 1
        return BenchmarkRunResult(BenchmarkSummary(1, 1.0, 1.0, {"none": 1}), [TraceRecord("t1", True, "none")])


class Proposer:
    calls = 0

    def propose(self, skill, traces, config):
        Proposer.calls += 1
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule", 1, 1)])


class Applier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "SKILL.md").write_text("# Skill\nRule\n", encoding="utf-8")
        return PatchApplicationResult(SkillRef(output_dir, output_dir.name), patch)


def test_run_comparison_resumes_partial_round_from_artifacts(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    round_dir = tmp_path / "run" / "selectors" / "random" / "seed_001" / "round_000"
    (round_dir / "current_skill_eval").mkdir(parents=True)
    (round_dir / "current_skill_eval" / "evaluation_summary.json").write_text(json.dumps({"num_tasks": 1, "avg_score": 0.0, "pass_rate": 0.0, "failure_histogram": {"wrong_answer": 1}}), encoding="utf-8")
    (round_dir / "current_skill_eval" / "task_traces.json").write_text(json.dumps([{"task_id": "t1", "success": False, "failure_type": "wrong_answer", "payload": {}}]), encoding="utf-8")
    (round_dir / "patch_proposal").mkdir()
    (round_dir / "patch_proposal" / "patch_pool.json").write_text(json.dumps({"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": None, "operation": "append_document", "content": "Rule", "delta_tokens": 1, "support_count": 1, "metadata": {}}], "metadata": {}}), encoding="utf-8")
    (round_dir / "selection").mkdir()
    (round_dir / "selection" / "decision.json").write_text(json.dumps({"selector": "random", "action_index": 0, "patch_id": "p1", "reason": "random", "scores": {}, "metadata": {}}), encoding="utf-8")
    CountingBenchmark.calls = 0
    Proposer.calls = 0

    def factory(store):
        return PatchSelectionEpisode(CountingBenchmark(), Proposer(), RandomSelector(seed=1), Applier(), ScoreDeltaReward(), store)

    run_comparison({"random": factory}, SkillRef(skill, "seed"), tmp_path / "run", rounds=1, seeds=[1])

    assert Proposer.calls == 0
    assert CountingBenchmark.calls == 1
    assert (round_dir / "selected_skill_eval" / "evaluation_summary.json").exists()
    assert (round_dir / "episode.json").exists()
