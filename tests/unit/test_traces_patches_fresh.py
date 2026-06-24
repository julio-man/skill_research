from __future__ import annotations

from pathlib import Path

from skill_research.core.types import SkillRef
from skill_research.patches.appliers.skill_directory import SkillDirectoryPatchApplier
from skill_research.patches.proposers.replay import ReplayPatchProposer
from skill_research.patches.types import Patch, PatchPool
from skill_research.traces.store import load_traces, save_traces
from skill_research.traces.types import TraceRecord


def test_trace_store_round_trips_records(tmp_path: Path) -> None:
    traces = [TraceRecord(task_id="t1", success=False, failure_type="wrong_answer", payload={"x": 1})]
    path = tmp_path / "task_traces.json"
    save_traces(traces, path)
    assert load_traces(path) == traces


def test_replay_patch_proposer_returns_saved_patch_pool(tmp_path: Path) -> None:
    patch = Patch("p1", "add_rule", "SKILL.md", None, "append_document", "Rule", 4, 2)
    path = tmp_path / "pool.json"
    PatchPool([patch]).save(path)
    proposer = ReplayPatchProposer(path)
    assert proposer.propose(SkillRef(tmp_path), [], config={}).patches == [patch]


def test_skill_directory_patch_applier_creates_new_version(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    patch = Patch("p1", "add_rule", "SKILL.md", None, "append_document", "Rule", 4, 2)
    applier = SkillDirectoryPatchApplier()

    result = applier.apply(SkillRef(skill_dir), patch, tmp_path / "versions")

    assert result.skill.path.exists()
    assert (result.skill.path / "SKILL.md").read_text(encoding="utf-8").endswith("Rule")
    assert result.patch == patch
