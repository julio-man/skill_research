from __future__ import annotations

from pathlib import Path

from skill_research.core.serialization import to_json_file


class JsonArtifactStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, relative_path: str, payload) -> None:
        to_json_file(payload, self.root / relative_path)

    def write_episode(self, episode) -> None:
        self.write("episode.json", episode)

    def write_run(self, run) -> None:
        self.write("run.json", run)

    def write_harness_events(self, events) -> None:
        self.write("harness_events.json", events)

    def write_comparison(self, comparison) -> None:
        self.write("comparison.json", comparison)
