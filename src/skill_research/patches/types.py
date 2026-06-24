from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Patch:
    patch_id: str
    patch_type: str
    target_file: str
    target_section: str | None
    operation: str
    content: str
    delta_tokens: int = 0
    support_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PatchPool:
    patches: list[Patch]
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "0.1"

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "PatchPool":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            patches=[Patch(**patch) for patch in payload.get("patches", [])],
            metadata=payload.get("metadata", {}),
            schema_version=payload.get("schema_version", "0.1"),
        )


@dataclass(frozen=True)
class PatchApplicationResult:
    skill: Any
    patch: Patch
    metadata: dict[str, Any] = field(default_factory=dict)
