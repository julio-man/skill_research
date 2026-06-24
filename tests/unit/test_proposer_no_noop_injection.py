from __future__ import annotations

from pathlib import Path

from skill_research.core.types import SkillRef
from skill_research.llms.replay import ReplayLLMBackend
from skill_research.patches.proposers.openai_trace import OpenAITracePatchProposer
from skill_research.traces.types import TraceRecord


def test_openai_trace_proposer_does_not_inject_noop_patch(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    response = '{"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "Rule", "supported_trace_ids": ["t1"]}]}'
    backend = ReplayLLMBackend([response])

    pool = OpenAITracePatchProposer(backend).propose(SkillRef(skill), [TraceRecord("t1", False, "wrong_answer")], {})

    assert [patch.patch_id for patch in pool.patches] == ["p1"]
