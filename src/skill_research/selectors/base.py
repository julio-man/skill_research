from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from skill_research.patches.types import Patch, PatchPool


@dataclass(frozen=True)
class SelectorDecision:
    action_index: int | None
    patch_id: str
    patch: Patch | None
    reason: str
    scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseSelector:
    name = "base"

    def observe(self, transition: Any) -> None:
        return None

    def save_state(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"name": self.name}, indent=2), encoding="utf-8")

    def load_state(self, path: Path) -> None:
        if path.exists():
            path.read_text(encoding="utf-8")

    def _decision(self, patch_pool: PatchPool, patch: Patch, reason: str) -> SelectorDecision:
        return SelectorDecision(
            action_index=patch_pool.patches.index(patch),
            patch_id=patch.patch_id,
            patch=patch,
            reason=reason,
        )
