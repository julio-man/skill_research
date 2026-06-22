from __future__ import annotations

from pathlib import Path
import shutil
import uuid

from skill_research.patches.types import Patch


class SkillPatchApplier:
    def __init__(self, versions_root: str | Path):
        self.versions_root = Path(versions_root)
        self.versions_root.mkdir(parents=True, exist_ok=True)

    def apply_patch(self, skill_dir: str | Path, patch: Patch, label: str | None = None) -> str:
        skill_dir = Path(skill_dir)
        slug = label or uuid.uuid4().hex[:8]
        new_dir = self.versions_root / f"skill_{slug}"
        if new_dir.exists():
            shutil.rmtree(new_dir)
        shutil.copytree(skill_dir, new_dir)

        if patch.operation == "no_op":
            return str(new_dir)

        target_path = new_dir / patch.target_file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if not target_path.exists():
            target_path.write_text("", encoding="utf-8")

        text = target_path.read_text(encoding="utf-8")
        if patch.operation == "append_document":
            updated = text + ("\n" if text and not text.endswith("\n") else "") + patch.content
        elif patch.operation == "prepend_document":
            updated = patch.content + ("\n" if patch.content and not patch.content.endswith("\n") else "") + text
        elif patch.operation == "append_under_section":
            updated = self._append_under_section(text, patch.target_section or "", patch.content)
        elif patch.operation == "replace_section":
            updated = self._replace_section(text, patch.target_section or "", patch.content)
        else:
            raise ValueError(f"Unsupported patch operation: {patch.operation}")

        target_path.write_text(updated, encoding="utf-8")
        return str(new_dir)

    def _append_under_section(self, text: str, section_name: str, content: str) -> str:
        lines = text.splitlines()
        target = section_name.lstrip("#").strip()
        header_idx = None
        header_level = None
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                if title == target:
                    header_idx = idx
                    header_level = len(stripped) - len(stripped.lstrip("#"))
                    break
        if header_idx is None:
            if text and not text.endswith("\n"):
                text += "\n"
            return text + f"## {target}\n" + content + ("\n" if not content.endswith("\n") else "")
        insert_idx = len(lines)
        for idx in range(header_idx + 1, len(lines)):
            stripped = lines[idx].strip()
            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                if level <= header_level:
                    insert_idx = idx
                    break
        new_lines = lines[:insert_idx] + content.splitlines() + lines[insert_idx:]
        return "\n".join(new_lines) + "\n"

    def _replace_section(self, text: str, section_name: str, content: str) -> str:
        lines = text.splitlines()
        target = section_name.lstrip("#").strip()
        header_idx = None
        header_level = None
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                if title == target:
                    header_idx = idx
                    header_level = len(stripped) - len(stripped.lstrip("#"))
                    break
        if header_idx is None:
            return self._append_under_section(text, target, content)
        end_idx = len(lines)
        for idx in range(header_idx + 1, len(lines)):
            stripped = lines[idx].strip()
            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                if level <= header_level:
                    end_idx = idx
                    break
        new_lines = lines[: header_idx + 1] + content.splitlines() + lines[end_idx:]
        return "\n".join(new_lines) + "\n"
