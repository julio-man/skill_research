from __future__ import annotations

from pathlib import Path

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.patches.types import Patch, PatchPool
from skill_research.rewards.bloat_regression import BloatRegressionReward
from skill_research.rewards.score_delta import ScoreDeltaReward
from skill_research.skills.summary import summarize_skill
from skill_research.state.builders.default import DefaultStateBuilder
from skill_research.state.types import SelectorState


def test_score_delta_reward_returns_components() -> None:
    reward = ScoreDeltaReward().compute(
        BenchmarkSummary(2, 0.2, 0.0),
        BenchmarkSummary(2, 0.7, 0.5),
        context={},
    )
    assert reward.value == 0.5
    assert reward.score_delta == 0.5
    assert reward.pass_rate_delta == 0.5


def test_bloat_regression_reward_penalizes_growth_and_regressions() -> None:
    reward = BloatRegressionReward(lambda_token_growth=0.1, mu_anchor_regression=0.25).compute(
        BenchmarkSummary(2, 0.2, 0.0),
        BenchmarkSummary(2, 0.7, 0.5),
        context={"token_growth": 1, "anchor_regressions": 1},
    )
    assert reward.value == 0.15


def test_summarize_skill_counts_directory_structure(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    refs = skill_dir / "references"
    scripts = skill_dir / "scripts"
    refs.mkdir(parents=True)
    scripts.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\nUse openpyxl.\n", encoding="utf-8")
    (refs / "note.md").write_text("Reference text\n", encoding="utf-8")
    (scripts / "helper.py").write_text("print('x')\n", encoding="utf-8")

    summary = summarize_skill(SkillRef(skill_dir, "seed"))

    assert summary.skill_tokens_main == 3
    assert summary.num_files == 3
    assert summary.num_references == 1
    assert summary.num_scripts == 1


def test_default_state_builder_combines_skill_eval_and_patch_features(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    patch_pool = PatchPool([Patch("p1", "add_rule", "SKILL.md", None, "append_document", "Rule", 4, 2)])

    state = DefaultStateBuilder().build(
        SkillRef(skill_dir, "seed"),
        BenchmarkSummary(1, 0.5, 0.0, {"wrong_answer": 1}),
        patch_pool,
        history=[],
    )

    assert isinstance(state, SelectorState)
    assert state.schema_version == "0.1"
    assert state.evaluation.n_wrong_answer == 1
    assert state.patches[0].patch_id == "p1"
