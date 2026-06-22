from __future__ import annotations

import random


class RandomSelector:
    def __init__(self, seed: int = 42):
        self._random = random.Random(seed)

    def select(self, state: dict, patches: list):
        if not patches:
            raise ValueError("No patches available")
        return self._random.choice(patches)
