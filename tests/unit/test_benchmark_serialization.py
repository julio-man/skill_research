from __future__ import annotations

import datetime

from skill_research.runner.benchmark import make_json_safe


def test_make_json_safe_converts_datetime_values() -> None:
    payload = {
        "when": datetime.datetime(2024, 1, 2, 3, 4, 5),
        "nested": {"date": datetime.date(2024, 1, 2)},
        "items": [datetime.time(3, 4), 1, "x"],
    }

    safe = make_json_safe(payload)

    assert safe == {
        "when": "2024-01-02T03:04:05",
        "nested": {"date": "2024-01-02"},
        "items": ["03:04:00", 1, "x"],
    }
