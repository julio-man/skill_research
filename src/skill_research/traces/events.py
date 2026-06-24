"""Harness-event records for infrastructure and proposer failures."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skill_research.core.serialization import from_json_file, to_json_file


@dataclass(frozen=True)
class HarnessEvent:
    event_type: str
    component: str
    severity: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


def event_store_path(root: Path) -> Path:
    return root / "harness_events.json"


def save_harness_events(events: list[HarnessEvent], path: Path) -> None:
    to_json_file(events, path)


def load_harness_events(path: Path) -> list[HarnessEvent]:
    return [HarnessEvent(**event) for event in from_json_file(path)]
