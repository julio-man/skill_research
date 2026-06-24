"""Patch proposer that replays a saved patch pool."""

from __future__ import annotations

from pathlib import Path

from skill_research.patches.types import PatchPool


class ReplayPatchProposer:
    name = "replay"

    def __init__(self, patch_pool_path: str | Path):
        self.patch_pool_path = Path(patch_pool_path)

    def propose(self, skill, traces: list, config) -> PatchPool:
        return PatchPool.load(self.patch_pool_path)
