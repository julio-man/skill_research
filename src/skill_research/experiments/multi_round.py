from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from skill_research.artifacts.store import JsonArtifactStore


@dataclass(frozen=True)
class MultiRoundResult:
    episodes: list
    cumulative_reward: list[float]


def run_multi_round(*, skill, episode_factory, output_dir: Path, rounds: int) -> MultiRoundResult:
    episodes = []
    cumulative = []
    total = 0.0
    current_skill = skill
    for round_index in range(rounds):
        store = JsonArtifactStore(output_dir / f"round_{round_index:03d}")
        episode = episode_factory(store)
        result = episode.run(current_skill, output_dir / f"round_{round_index:03d}", {})
        episodes.append(result)
        current_skill = result.skill_after
        total = round(total + result.reward.value, 10)
        cumulative.append(total)
    run = MultiRoundResult(episodes, cumulative)
    JsonArtifactStore(output_dir).write_run(run)
    return run
