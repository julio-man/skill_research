from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Task:
    task_id: str
    instruction: str
    input_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskSplit:
    name: str
    tasks: list[Task]


@dataclass(frozen=True)
class SkillRef:
    path: Path
    skill_id: str | None = None


@dataclass(frozen=True)
class BenchmarkSummary:
    num_tasks: int
    avg_score: float
    pass_rate: float
    failure_histogram: dict[str, int] = field(default_factory=dict)
