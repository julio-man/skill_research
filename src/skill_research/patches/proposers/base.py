from __future__ import annotations

from typing import Protocol

from skill_research.core.types import SkillRef
from skill_research.patches.types import PatchPool
from skill_research.traces.types import TraceRecord


class PatchProposer(Protocol):
    name: str

    def propose(self, skill: SkillRef, traces: list[TraceRecord], config: dict) -> PatchPool:
        ...
