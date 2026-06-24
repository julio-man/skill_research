from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
import json
from pathlib import Path
from typing import Any


def to_json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return to_json_safe(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): to_json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [to_json_safe(inner) for inner in value]
    if isinstance(value, tuple):
        return [to_json_safe(inner) for inner in value]
    return value


def to_json_file(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_json_safe(value), indent=2), encoding="utf-8")


def from_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
