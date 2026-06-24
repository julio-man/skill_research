"""Protocol for components that materialize a patch into a new skill."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from skill_research.core.types import SkillRef
from skill_research.patches.types import Patch, PatchApplicationResult


class PatchApplier(Protocol):
    name: str

    def apply(self, skill: SkillRef, patch: Patch, output_dir: Path) -> PatchApplicationResult:
        ...
