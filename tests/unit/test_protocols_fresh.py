from __future__ import annotations

from skill_research.core.protocols import ArtifactStore, DatasetProvider, Evaluator, Executor, PatchApplier, PatchProposer, RewardFunction, Selector, StateBuilder


def test_component_protocols_exist_and_are_named() -> None:
    assert Executor.__name__ == "Executor"
    assert Evaluator.__name__ == "Evaluator"
    assert DatasetProvider.__name__ == "DatasetProvider"
    assert PatchProposer.__name__ == "PatchProposer"
    assert PatchApplier.__name__ == "PatchApplier"
    assert StateBuilder.__name__ == "StateBuilder"
    assert Selector.__name__ == "Selector"
    assert RewardFunction.__name__ == "RewardFunction"
    assert ArtifactStore.__name__ == "ArtifactStore"
