from __future__ import annotations

from pathlib import Path

from skill_research.patches.applier import SkillPatchApplier
from skill_research.patches.types import Patch



def _seed_skill(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "# Minimal Seed Skill\n\n## Workflow\n\nUse Python to modify the workbook.\n",
        encoding="utf-8",
    )
    return skill_dir



def test_apply_patch_creates_new_version_directory(tmp_path: Path) -> None:
    skill_dir = _seed_skill(tmp_path)
    applier = SkillPatchApplier(tmp_path / "versions")
    patch = Patch(
        patch_id="p1",
        patch_type="add_rule",
        target_file="SKILL.md",
        target_section=None,
        operation="append_document",
        content="## Extra\n\nAlways inspect sheet names first.\n",
        delta_tokens=7,
        support_count=1,
    )

    new_dir = applier.apply_patch(skill_dir, patch, label="round0")

    assert Path(new_dir).exists()
    assert (Path(new_dir) / "SKILL.md").exists()
    assert Path(new_dir).name == "skill_round0"



def test_apply_patch_append_document_updates_skill_md(tmp_path: Path) -> None:
    skill_dir = _seed_skill(tmp_path)
    applier = SkillPatchApplier(tmp_path / "versions")
    patch = Patch(
        patch_id="p2",
        patch_type="add_checklist",
        target_file="SKILL.md",
        target_section=None,
        operation="append_document",
        content="## Checklist\n\n- Check real sheet names\n",
        delta_tokens=8,
        support_count=2,
    )

    new_dir = Path(applier.apply_patch(skill_dir, patch, label="round1"))
    text = (new_dir / "SKILL.md").read_text(encoding="utf-8")

    assert "## Checklist" in text
    assert "- Check real sheet names" in text



def test_apply_patch_append_under_section_inserts_under_target_section(tmp_path: Path) -> None:
    skill_dir = _seed_skill(tmp_path)
    applier = SkillPatchApplier(tmp_path / "versions")
    patch = Patch(
        patch_id="p3",
        patch_type="add_example",
        target_file="SKILL.md",
        target_section="Workflow",
        operation="append_under_section",
        content="- Example: write into the existing target range, not a new column.\n",
        delta_tokens=12,
        support_count=1,
    )

    new_dir = Path(applier.apply_patch(skill_dir, patch, label="round2"))
    text = (new_dir / "SKILL.md").read_text(encoding="utf-8")

    assert "## Workflow" in text
    assert "- Example: write into the existing target range, not a new column." in text
    assert text.index("## Workflow") < text.index("- Example: write into the existing target range, not a new column.")



def test_apply_patch_no_op_preserves_skill_contents(tmp_path: Path) -> None:
    skill_dir = _seed_skill(tmp_path)
    original = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    applier = SkillPatchApplier(tmp_path / "versions")
    patch = Patch(
        patch_id="noop",
        patch_type="noop",
        target_file="SKILL.md",
        target_section=None,
        operation="no_op",
        content="",
        delta_tokens=0,
        support_count=0,
    )

    new_dir = Path(applier.apply_patch(skill_dir, patch, label="round3"))
    text = (new_dir / "SKILL.md").read_text(encoding="utf-8")

    assert text == original
