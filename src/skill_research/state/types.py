"""Typed selector-state feature schemas."""

from __future__ import annotations

from dataclasses import dataclass

from skill_research.skills.summary import SkillSummary


@dataclass(frozen=True)
class EvaluationSummary:
    avg_score: float
    pass_rate: float
    n_wrong_answer: int
    n_format_fail: int
    n_tool_fail: int
    n_timeout: int
    n_other: int


@dataclass(frozen=True)
class PatchFeature:
    patch_id: str
    patch_type: str
    delta_tokens: int
    target_file: str
    target_section: str | None
    support_count: int


@dataclass(frozen=True)
class SelectorState:
    schema_version: str
    skill: SkillSummary
    evaluation: EvaluationSummary
    patches: list[PatchFeature]
