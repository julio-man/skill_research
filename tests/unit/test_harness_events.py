from __future__ import annotations

import json
from pathlib import Path

from skill_research.traces.events import HarnessEvent, event_store_path, save_harness_events, load_harness_events


def test_harness_events_round_trip_separately_from_task_traces(tmp_path: Path) -> None:
    events = [HarnessEvent(event_type="patch_schema_error", component="openai_trace", severity="error", message="bad schema", payload={"raw": "{}"})]
    path = event_store_path(tmp_path)

    save_harness_events(events, path)

    assert path.name == "harness_events.json"
    assert json.loads(path.read_text(encoding="utf-8"))[0]["event_type"] == "patch_schema_error"
    assert load_harness_events(path) == events
