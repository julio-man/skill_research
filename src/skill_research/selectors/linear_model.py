"""Small ridge-regression utilities for online selector models."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

import numpy as np


@dataclass
class OnlineRidgeModel:
    """Maintain A and b for online ridge regression over patch features."""

    dimension: int
    l2: float = 1.0
    matrix: list[list[float]] = field(init=False)
    target: list[float] = field(init=False)

    def __post_init__(self) -> None:
        self.matrix = (np.eye(self.dimension) * self.l2).tolist()
        self.target = [0.0] * self.dimension

    def update(self, features: list[float], reward: float) -> None:
        vector = np.array(features, dtype=float)
        matrix = np.array(self.matrix, dtype=float)
        target = np.array(self.target, dtype=float)
        matrix += np.outer(vector, vector)
        target += reward * vector
        self.matrix = matrix.tolist()
        self.target = target.tolist()

    def weights(self) -> list[float]:
        return np.linalg.solve(np.array(self.matrix, dtype=float), np.array(self.target, dtype=float)).tolist()

    def variance(self, features: list[float]) -> float:
        vector = np.array(features, dtype=float)
        inverse = np.linalg.inv(np.array(self.matrix, dtype=float))
        return float(vector @ inverse @ vector)

    def to_dict(self) -> dict:
        return {"dimension": self.dimension, "l2": self.l2, "matrix": self.matrix, "target": self.target}

    @classmethod
    def from_dict(cls, payload: dict) -> "OnlineRidgeModel":
        model = cls(int(payload["dimension"]), float(payload.get("l2", 1.0)))
        model.matrix = payload["matrix"]
        model.target = payload["target"]
        return model

    def save(self, path: Path, selector_name: str, extra: dict | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"name": selector_name, "model": self.to_dict()}
        if extra:
            payload.update(extra)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_model(path: Path) -> tuple[OnlineRidgeModel, dict]:
    """Load an online ridge model and return extra selector metadata."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    model = OnlineRidgeModel.from_dict(payload["model"])
    return model, payload
