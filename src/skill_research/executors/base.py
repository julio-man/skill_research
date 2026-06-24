from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExecutionResult:
    artifact_path: str
    code_path: str | None
    raw_output: str
    stdout: str
    stderr: str
    returncode: int
    metadata: dict[str, Any] = field(default_factory=dict)
