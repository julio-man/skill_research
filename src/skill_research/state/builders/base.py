"""Protocol for turning experiment context into selector state."""

from __future__ import annotations

from typing import Protocol

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.patches.types import PatchPool
from skill_research.state.types import SelectorState


class StateBuilder(Protocol):
    schema_version: str

    def build(self, skill: SkillRef, benchmark: BenchmarkSummary, patch_pool: PatchPool, history: list) -> SelectorState:
        ...
