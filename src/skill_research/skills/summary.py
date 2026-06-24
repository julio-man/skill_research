"""Skill directory summarization for selector state features."""

from __future__ import annotations

from dataclasses import dataclass
import re

from skill_research.core.types import SkillRef


@dataclass(frozen=True)
class SkillSummary:
    skill_tokens_main: int
    skill_tokens_total: int
    num_files: int
    num_scripts: int
    num_references: int


def _count_tokens(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_']+", text))


def summarize_skill(skill: SkillRef) -> SkillSummary:
    root = skill.path
    files = sorted(path for path in root.rglob("*") if path.is_file()) if root.is_dir() else ([root] if root.is_file() else [])
    skill_md = root / "SKILL.md" if root.is_dir() else root
    main_text = skill_md.read_text(encoding="utf-8") if skill_md.exists() else ""
    total_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files)
    return SkillSummary(
        skill_tokens_main=_count_tokens(main_text),
        skill_tokens_total=_count_tokens(total_text),
        num_files=len(files),
        num_scripts=sum(1 for path in files if path.suffix == ".py" or "scripts" in path.parts),
        num_references=sum(1 for path in files if "references" in path.parts),
    )
