from __future__ import annotations

import json
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
        return BenchmarkRunResult(BenchmarkSummary(1, 0.5, 0.0, {"wrong_answer": 1}), [TraceRecord("task_001", False, "wrong_answer")])


class Proposer:
    def propose(self, skill, traces, config):
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule", 1, 1)])


class Applier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        skill_dir = output_dir
        (skill_dir / "SKILL.md").write_text("# Skill\nRule\n", encoding="utf-8")
        return PatchApplicationResult(SkillRef(skill_dir, skill_dir.name), patch)


def test_comparison_writes_complete_selector_seed_round_artifact_contract(tmp_path: Path) -> None:
    initial_skill = tmp_path / "skill"
    initial_skill.mkdir()
    (initial_skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    def noop_factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), NoOpSelector(), Applier(), ScoreDeltaReward(), store)

    def random_factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), RandomSelector(seed=1), Applier(), ScoreDeltaReward(), store)

    run_comparison({"noop": noop_factory, "random": random_factory}, SkillRef(initial_skill, "seed"), tmp_path / "run", rounds=1, seeds=[1])

    assert not (tmp_path / "run" / "shared").exists()
    assert (tmp_path / "run" / "selector_comparison.json").exists()
    for selector in ["noop", "random"]:
        seed_dir = tmp_path / "run" / "selectors" / selector / "seed_001"
        round_dir = seed_dir / "round_000"
        assert (seed_dir / "selector_curve.json").exists()
        for rel in [
            "input_skill/SKILL.md",
            "current_skill_eval/evaluation_summary.json",
            "current_skill_eval/task_traces.json",
            "patch_proposal/patch_pool.json",
            "selection/decision.json",
            "selected_skill/SKILL.md",
            "selected_skill_eval/evaluation_summary.json",
            "selected_skill_eval/task_traces.json",
                        "episode.json",
        ]:
            assert (round_dir / rel).exists(), rel
    noop_decision = json.loads((tmp_path / "run" / "selectors" / "noop" / "seed_001" / "round_000" / "selection" / "decision.json").read_text())
    random_decision = json.loads((tmp_path / "run" / "selectors" / "random" / "seed_001" / "round_000" / "selection" / "decision.json").read_text())
    assert noop_decision["patch_id"] is None
    assert random_decision["patch_id"] == "p1"
