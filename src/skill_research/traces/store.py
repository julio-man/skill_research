"""JSON persistence helpers for task traces."""

from __future__ import annotations

import json
from pathlib import Path

from skill_research.core.serialization import to_json_safe
from skill_research.traces.types import TraceRecord


def save_traces(traces: list[TraceRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_json_safe(traces), indent=2), encoding="utf-8")


def load_traces(path: Path) -> list[TraceRecord]:
    return [TraceRecord(**row) for row in json.loads(path.read_text(encoding="utf-8"))]
