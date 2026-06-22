from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Patch:
    patch_id: str
    patch_type: str
    target_file: str
    target_section: str | None
    operation: str
    content: str
    delta_tokens: int
    support_count: int
