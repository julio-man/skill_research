"""Default selector-state builder from skill, benchmark, and patch features."""

from __future__ import annotations

from skill_research.core.types import BenchmarkSummary, SkillRef
from skill_research.patches.types import PatchPool
from skill_research.skills.summary import summarize_skill
from skill_research.state.types import EvaluationSummary, PatchFeature, SelectorState


class DefaultStateBuilder:
    schema_version = "0.1"

    def build(self, skill: SkillRef, benchmark: BenchmarkSummary, patch_pool: PatchPool, history: list) -> SelectorState:
        _ = history
        histogram = benchmark.failure_histogram
        known_total = sum(histogram.get(name, 0) for name in ["wrong_answer", "format_fail", "tool_fail", "timeout", "none"])
        n_other = max(sum(histogram.values()) - known_total, 0)
        return SelectorState(
            schema_version=self.schema_version,
            skill=summarize_skill(skill),
            evaluation=EvaluationSummary(
                avg_score=benchmark.avg_score,
                pass_rate=benchmark.pass_rate,
                n_wrong_answer=histogram.get("wrong_answer", 0),
                n_format_fail=histogram.get("format_fail", 0),
                n_tool_fail=histogram.get("tool_fail", 0),
                n_timeout=histogram.get("timeout", 0),
                n_other=n_other,
            ),
            patches=[
                PatchFeature(
                    patch_id=patch.patch_id,
                    patch_type=patch.patch_type,
                    delta_tokens=patch.delta_tokens,
                    target_file=patch.target_file,
                    target_section=patch.target_section,
                    support_count=patch.support_count,
                )
                for patch in patch_pool.patches
            ],
        )
