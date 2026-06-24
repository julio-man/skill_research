from __future__ import annotations

import json
from pathlib import Path

from skill_research.cli.run_experiment import build_selectors, main
from skill_research.config.loader import load_experiment_spec
from skill_research.patches.proposers.openai_trace import OpenAITracePatchProposer, build_patch_messages
from skill_research.traces.types import TraceRecord


def test_openai_trace_patch_proposer_builds_failed_trace_prompt(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    traces = [TraceRecord("t1", False, "wrong_answer", {"expected": 2, "actual": 1})]

    messages = build_patch_messages(skill_dir, traces, k=2)

    assert messages[0].role == "system"
    assert "skill patch generator" in messages[0].content
    assert "wrong_answer" in messages[1].content
    assert "expected" in messages[1].content


def test_openai_trace_patch_proposer_parses_json_response() -> None:
    proposer = OpenAITracePatchProposer()
    patches = proposer.parse_response('{"patches": [{"patch_id": "p1", "patch_type": "add_rule", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "Rule", "supported_trace_ids": ["t1"]}]}')
    assert patches[0].patch_id == "p1"


def test_run_experiment_dry_run_writes_resolved_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    output_dir = tmp_path / "out"
    spec_path.write_text(json.dumps({"experiment_id": "x", "dataset": {"name": "memory", "split": "val"}, "skill": {"path": "skill"}, "executor": {"name": "exec"}, "evaluator": {"name": "eval"}, "proposer": {"name": "prop"}, "applier": {"name": "apply"}, "reward": {"name": "score_delta"}, "selectors": [{"name": "noop"}], "run": {"rounds": 1, "seeds": [1], "output_dir": str(output_dir)}}), encoding="utf-8")
    main(["--config", str(spec_path), "--dry-run"])
    assert (output_dir / "experiment_config.resolved.json").exists()
    spec = load_experiment_spec(spec_path)
    assert list(build_selectors(spec)) == ["noop"]
