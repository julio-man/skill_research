"""Single patch-selection episode logic and proposer-failure handling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from skill_research.core.types import SkillRef
from skill_research.patches.types import Patch, PatchPool
from skill_research.traces.events import HarnessEvent


@dataclass(frozen=True)
class EpisodeResult:
    before_summary: object
    after_summary: object
    selected_patch: object
    reward: object
    skill_before: SkillRef
    skill_after: SkillRef
    patch_pool: object


def _summary(result):
    return result["summary"] if isinstance(result, dict) else result.summary


def _traces(result):
    return result.get("traces", []) if isinstance(result, dict) else result.traces


def _failure_type(exc: Exception) -> str:
    name = exc.__class__.__name__
    if name == "PatchSchemaError":
        return "patch_schema_error"
    if name == "JSONDecodeError":
        return "patch_json_error"
    return "patch_proposer_error"


def _fallback_patch_pool(failure_type: str) -> PatchPool:
    return PatchPool(
        [Patch("noop", "noop", "SKILL.md", None, "no_op", "")],
        metadata={"proposer_failed": True, "failure_type": failure_type},
    )


def _harness_event(exc: Exception) -> HarnessEvent:
    failure_type = _failure_type(exc)
    return HarnessEvent(
        event_type=failure_type,
        component="openai_trace",
        severity="error",
        message=str(exc),
        payload={"exception_type": exc.__class__.__name__},
    )


class PatchSelectionEpisode:
    def __init__(self, benchmark, proposer, selector, applier, reward, artifact_store, trace_benchmark=None, test_benchmark=None, validation_benchmark=None):
        self.benchmark = benchmark
        self.trace_benchmark = trace_benchmark or benchmark
        self.test_benchmark = test_benchmark
        self.validation_benchmark = validation_benchmark
        self.proposer = proposer
        self.selector = selector
        self.applier = applier
        self.reward = reward
        self.artifact_store = artifact_store

    def run(self, skill: SkillRef, output_dir: Path, config: dict) -> EpisodeResult:
        before = self.benchmark.run(skill, output_dir / "current_skill_eval")
        harness_events = []
        try:
            patch_pool = self.proposer.propose(skill, _traces(before), config)
        except Exception as exc:
            failure_type = _failure_type(exc)
            patch_pool = _fallback_patch_pool(failure_type)
            harness_events.append(_harness_event(exc))
        decision = self.selector.select({}, patch_pool)
        if decision.patch is None:
            skill_after = skill
        else:
            application = self.applier.apply(skill, decision.patch, output_dir / "skill_after")
            skill_after = application.skill
        after = self.benchmark.run(skill_after, output_dir / "selected_skill_eval")
        reward = self.reward.compute(_summary(before), _summary(after), context={})
        result = EpisodeResult(_summary(before), _summary(after), decision.patch, reward, skill, skill_after, patch_pool)
        self.artifact_store.write_episode(result)
        if harness_events and hasattr(self.artifact_store, "write_harness_events"):
            self.artifact_store.write_harness_events(harness_events)
        self.selector.observe(result)
        return result
