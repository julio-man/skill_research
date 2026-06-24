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


class Benchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.5, 0.0, {"wrong_answer": 1}), [TraceRecord("t1", False, "wrong_answer", {"path": str(Path.cwd() / "abs.txt")})])


class Proposer:
    name = "fake_proposer"

    def propose(self, skill, traces, config):
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule", 1, 1)], metadata={"proposer": self.name, "raw_response": "secret raw"})


class Applier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "SKILL.md").write_text("# Skill\nRule\n", encoding="utf-8")
        return PatchApplicationResult(SkillRef(output_dir, output_dir.name), patch)


def test_clean_artifact_contract_names_and_episode_schema(tmp_path: Path) -> None:
    initial_skill = tmp_path / "initial_skill"
    initial_skill.mkdir()
    (initial_skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    def factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), RandomSelector(seed=1), Applier(), ScoreDeltaReward(), store)

    run_comparison({"random": factory}, SkillRef(initial_skill, "seed"), tmp_path / "artifacts", rounds=1, seeds=[1])

    assert (tmp_path / "artifacts" / "selector_comparison.json").exists()
    assert not (tmp_path / "artifacts" / "comparison.json").exists()
    seed_dir = tmp_path / "artifacts" / "selectors" / "random" / "seed_001"
    assert (seed_dir / "selector_curve.json").exists()
    assert not (seed_dir / "run.json").exists()
    round_dir = seed_dir / "round_000"
    assert (round_dir / "current_skill_eval" / "evaluation_summary.json").exists()
    assert (round_dir / "current_skill_eval" / "task_traces.json").exists()
    assert not (round_dir / "current_skill_eval" / "summary.json").exists()
    assert not (round_dir / "current_skill_eval" / "traces.json").exists()
    assert not (round_dir / "reward.json").exists()
    assert not (round_dir / "round.json").exists()

    patch_pool = json.loads((round_dir / "patch_proposal" / "patch_pool.json").read_text(encoding="utf-8"))
    assert patch_pool["metadata"] == {"proposer": "fake_proposer"}

    episode = json.loads((round_dir / "episode.json").read_text(encoding="utf-8"))
    assert "before_summary" not in episode
    assert "after_summary" not in episode
    assert "skill_before" not in episode
    assert "skill_after" not in episode
    assert "patch_pool" not in episode
    assert episode["selected_patch"]["selector"] == "random"
    assert episode["reward"]["function"] == "score_delta"
    assert episode["current_skill_eval"]["summary_path"] == "current_skill_eval/evaluation_summary.json"
    assert episode["selected_skill_eval"]["summary_path"] == "selected_skill_eval/evaluation_summary.json"
