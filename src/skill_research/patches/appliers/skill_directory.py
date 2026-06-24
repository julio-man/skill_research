"""Patch applier for directory-based skills."""

from __future__ import annotations

from pathlib import Path
import shutil

from skill_research.core.types import SkillRef
from skill_research.patches.types import Patch, PatchApplicationResult


class SkillDirectoryPatchApplier:
    name = "skill_directory"

    def apply(self, skill: SkillRef, patch: Patch, output_dir: Path) -> PatchApplicationResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        target_skill_dir = output_dir / f"skill_{patch.patch_id}"
        if target_skill_dir.exists():
            shutil.rmtree(target_skill_dir)
        shutil.copytree(skill.path, target_skill_dir)
        if patch.operation != "no_op":
            target_file = target_skill_dir / patch.target_file
            target_file.parent.mkdir(parents=True, exist_ok=True)
            existing = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
            if patch.operation == "append_document":
                updated = existing + ("\n" if existing and not existing.endswith("\n") else "") + patch.content
            elif patch.operation == "prepend_document":
                updated = patch.content + ("\n" if patch.content and not patch.content.endswith("\n") else "") + existing
            else:
                updated = patch.content
            target_file.write_text(updated, encoding="utf-8")
        return PatchApplicationResult(skill=SkillRef(target_skill_dir, target_skill_dir.name), patch=patch)
