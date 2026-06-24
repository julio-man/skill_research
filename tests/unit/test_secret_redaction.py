from __future__ import annotations

import json
from pathlib import Path

from skill_research.cli.run_experiment import main, redact_secrets
from skill_research.llms.openai_backend import OpenAIBackendConfig, OpenAIChatBackend


class FakeClient:
    chat = None


def test_redact_secrets_removes_base_url_and_api_key() -> None:
    payload = {"llm": {"base_url": "https://secret.example", "api_key": "secret", "model": "gpt"}}

    redacted = redact_secrets(payload)

    assert redacted["llm"]["base_url"] == "<redacted>"
    assert redacted["llm"]["api_key"] == "<redacted>"
    assert redacted["llm"]["model"] == "gpt"


def test_run_experiment_resolved_config_redacts_base_url(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    out = tmp_path / "out"
    spec_path.write_text(json.dumps({"experiment_id": "x", "dataset": {"name": "memory", "split": "val"}, "skill": {"path": "skill"}, "executor": {"name": "spreadsheet_python", "llm": {"name": "openai", "model": "gpt", "base_url": "https://secret.example", "api_key": "secret"}}, "evaluator": {"name": "spreadsheet"}, "proposer": {"name": "openai_trace"}, "applier": {"name": "skill_directory"}, "reward": {"name": "score_delta"}, "selectors": [{"name": "noop"}], "run": {"rounds": 1, "seeds": [1], "output_dir": str(out)}}), encoding="utf-8")

    main(["--config", str(spec_path), "--dry-run"])

    resolved = json.loads((out / "experiment_config.resolved.json").read_text(encoding="utf-8"))
    assert resolved["executor"]["params"]["llm"]["base_url"] == "<redacted>"
    assert resolved["executor"]["params"]["llm"]["api_key"] == "<redacted>"


def test_openai_backend_info_does_not_store_base_url() -> None:
    backend = OpenAIChatBackend(OpenAIBackendConfig(model="gpt", api_key="x", base_url="https://secret.example"), client=FakeClient())

    assert "base_url" not in backend.info.metadata
