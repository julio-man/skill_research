from __future__ import annotations

from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.appliers.skill_directory import SkillDirectoryPatchApplier
from skill_research.patches.types import Patch, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.random_selector import RandomSelector


class Benchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0), [])


class Proposer:
    def propose(self, skill, traces, config):
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule")])


def test_selected_skill_artifact_is_skill_root_even_when_applier_versions_in_subdir(tmp_path: Path) -> None:
    initial_skill = tmp_path / "skill"
    initial_skill.mkdir()
    (initial_skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    def random_factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), RandomSelector(seed=1), SkillDirectoryPatchApplier(), ScoreDeltaReward(), store)

    run_comparison({"random": random_factory}, SkillRef(initial_skill, "seed"), tmp_path / "run", rounds=1, seeds=[1])

    selected_skill = tmp_path / "run" / "selectors" / "random" / "seed_001" / "round_000" / "selected_skill"
    assert (selected_skill / "SKILL.md").exists()
    assert not any(path.name.startswith("skill_") for path in selected_skill.iterdir() if path.is_dir())
