from __future__ import annotations

from pathlib import Path

import pytest

from skill_research.core.types import SkillRef
from skill_research.llms.replay import ReplayLLMBackend
from skill_research.patches.proposers.openai_trace import OpenAITracePatchProposer, PatchSchemaError
from skill_research.traces.types import TraceRecord


def test_openai_trace_proposer_computes_delta_tokens_and_support_count(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    response = '{"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "one two three", "supported_trace_ids": ["t1", "t2"], "metadata": {}}]}'
    proposer = OpenAITracePatchProposer(ReplayLLMBackend([response]))

    pool = proposer.propose(SkillRef(skill), [TraceRecord("t1", False, "wrong_answer"), TraceRecord("t2", False, "wrong_answer")], {})

    assert pool.patches[0].delta_tokens == 3
    assert pool.patches[0].support_count == 2
    assert pool.patches[0].metadata["supported_trace_ids"] == ["t1", "t2"]


def test_openai_trace_proposer_rejects_unknown_supported_trace_ids(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    response = '{"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "one", "supported_trace_ids": ["missing"], "metadata": {}}]}'
    proposer = OpenAITracePatchProposer(ReplayLLMBackend([response]))

    with pytest.raises(PatchSchemaError, match="supported_trace_ids"):
        proposer.propose(SkillRef(skill), [TraceRecord("t1", False, "wrong_answer")], {})
