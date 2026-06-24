from __future__ import annotations

from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.experiments.benchmark import BenchmarkRunResult
from skill_research.experiments.comparison import run_comparison
from skill_research.experiments.episode import PatchSelectionEpisode
from skill_research.patches.types import Patch, PatchApplicationResult, PatchPool
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.selectors.random_selector import RandomSelector
from skill_research.selectors.smallest_patch import SmallestPatchSelector
from skill_research.traces.types import TraceRecord


class Benchmark:
    def run(self, skill: SkillRef, output_dir: Path):
        task_dir = output_dir / "tasks" / "task_a"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "generated_code.py").write_text("print('x')\n", encoding="utf-8")
        return BenchmarkRunResult(BenchmarkSummary(1, 0.0, 0.0, {"wrong_answer": 1}), [TraceRecord("task_a", False, "wrong_answer")])


class Proposer:
    def propose(self, skill, traces, config):
        return PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule", 1, 1)])


class Applier:
    def apply(self, skill, patch, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "SKILL.md").write_text("# Skill\nRule\n", encoding="utf-8")
        return PatchApplicationResult(SkillRef(output_dir, output_dir.name), patch)


def test_shared_current_skill_eval_copies_task_artifacts_to_every_selector(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    def random_factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), RandomSelector(seed=1), Applier(), ScoreDeltaReward(), store)

    def smallest_factory(store):
        return PatchSelectionEpisode(Benchmark(), Proposer(), SmallestPatchSelector(), Applier(), ScoreDeltaReward(), store)

    run_comparison({"random": random_factory, "smallest_patch": smallest_factory}, SkillRef(skill, "seed"), tmp_path / "run", rounds=1, seeds=[1])

    for selector in ["random", "smallest_patch"]:
        assert (tmp_path / "run" / "selectors" / selector / "seed_001" / "round_000" / "current_skill_eval" / "tasks" / "task_a" / "generated_code.py").exists()
