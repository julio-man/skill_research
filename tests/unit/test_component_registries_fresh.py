from __future__ import annotations

from pathlib import Path

from skill_research.datasets import build_dataset_provider, dataset_registry
from skill_research.evaluators import build_evaluator, evaluator_registry
from skill_research.executors import build_executor, executor_registry
from skill_research.patches.appliers import applier_registry, build_applier
from skill_research.patches.proposers import build_proposer, proposer_registry
from skill_research.rewards import build_reward, reward_registry
from skill_research.selectors import build_selector, selector_registry


class Backend:
    def complete(self, messages, temperature: float, max_tokens: int) -> str:
        return ""


def test_all_swappable_component_registries_have_default_entries(tmp_path: Path) -> None:
    assert "memory" in dataset_registry.names()
    assert "spreadsheet_python" in executor_registry.names()
    assert "spreadsheet" in evaluator_registry.names()
    assert "openai_trace" in proposer_registry.names()
    assert "replay" in proposer_registry.names()
    assert "skill_directory" in applier_registry.names()
    assert "score_delta" in reward_registry.names()
    assert "noop" in selector_registry.names()

    assert build_dataset_provider("memory", splits={}).name == "memory"
    assert build_executor("spreadsheet_python", backend=Backend()).name == "spreadsheet_python"
    assert build_evaluator("spreadsheet").name == "spreadsheet"
    assert build_proposer("openai_trace").name == "openai_trace"
    assert build_applier("skill_directory").name == "skill_directory"
    assert build_reward("score_delta").name == "score_delta"
    assert build_selector("noop").name == "noop"
