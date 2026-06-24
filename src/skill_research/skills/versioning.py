"""Deterministic hashing and path helpers for skill versions."""

from __future__ import annotations

import hashlib
from pathlib import Path

from skill_research.core.types import SkillRef


def skill_hash(skill: SkillRef) -> str:
    root = skill.path
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file()) if root.is_dir() else ([root] if root.is_file() else [])
    for path in files:
        digest.update(str(path.relative_to(root) if root.is_dir() else path.name).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def versioned_skill_path(root: Path, label: str) -> Path:
    return root / f"skill_{label}"
