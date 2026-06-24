from __future__ import annotations

import json
from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.types import Patch, PatchApplicationResult, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.greedy import GreedySelector
from skill_research.traces.types import TraceRecord


class EvolutionBenchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0, {"wrong_answer": 1}), [TraceRecord("evo", False, "wrong_answer")])


class ValidationBenchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        score = 1.0 if "p_good" in str(skill.path) else 0.0
        return BenchmarkRunResult(BenchmarkSummary(1, score, score, {"none" if score else "wrong_answer": 1}), [TraceRecord("val", score == 1.0, "none" if score else "wrong_answer")])


class Proposer:
    def propose(self, skill, traces, config):
        return PatchPool([
            Patch("p_bad", "guidance", "SKILL.md", None, "append_document", "bad", 1, 1),
            Patch("p_good", "guidance", "SKILL.md", None, "append_document", "good", 1, 1),
        ])


class Applier:
    def apply(self, skill, patch, output_dir):
        target = output_dir / f"skill_{patch.patch_id}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "SKILL.md").write_text(patch.content, encoding="utf-8")
        return PatchApplicationResult(SkillRef(target, target.name), patch)


def test_greedy_selector_validates_candidates_and_writes_artifacts(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    def factory(store):
        return PatchSelectionEpisode(EvolutionBenchmark(), Proposer(), GreedySelector(), Applier(), ScoreDeltaReward(), store, validation_benchmark=ValidationBenchmark())

    run_comparison({"greedy": factory}, SkillRef(skill, "seed"), tmp_path / "run", rounds=1, seeds=[1])

    round_dir = tmp_path / "run" / "selectors" / "greedy" / "seed_001" / "round_000"
    decision = json.loads((round_dir / "selection" / "decision.json").read_text(encoding="utf-8"))
    assert decision["patch_id"] == "p_good"
    assert (round_dir / "selector_validation" / "p_bad" / "evaluation_summary.json").exists()
    assert (round_dir / "selector_validation" / "p_good" / "evaluation_summary.json").exists()
