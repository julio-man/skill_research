from __future__ import annotations

from pathlib import Path

from skill_research.patches.proposer import PATCH_SYSTEM_PROMPT, build_patch_messages
from skill_research.traces import TraceRecord



def _trace() -> TraceRecord:
    return TraceRecord(
        task_id="379-36",
        task_instruction="Rewrite Georgia Its Tax rows.",
        skill_path="skills/minimal_seed/SKILL.md",
        model="gpt-5.4",
        provider="openai",
        candidate_workbook_path="candidate.xlsx",
        code_path="code.py",
        raw_model_output="print('hello')",
        execution_stdout="",
        execution_stderr="",
        execution_returncode=0,
        evaluation={
            "passed": False,
            "score": 0.0,
            "failure_type": "wrong_answer",
            "checks": [],
            "metadata": {
                "expected_region_values": {"Sheet1!E10": "Georgia WH Tax"},
                "actual_region_values": {"Sheet1!E10": "Georgia Its Tax/ga Tx *****0"},
            },
        },
    )


def test_build_patch_messages_includes_skill_text_trace_summary_and_k(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text("Use Python. Inspect real sheet names.")

    messages = build_patch_messages(skill_path=skill_dir, traces=[_trace()], k=3)

    assert messages[0].role == "system"
    assert PATCH_SYSTEM_PROMPT in messages[0].content
    assert "Current skill file (`SKILL.md`):" in messages[1].content
    assert "Use Python. Inspect real sheet names." in messages[1].content
    assert "task_id: 379-36" in messages[1].content
    assert "expected_region_values" in messages[1].content
    assert "Generate up to 3 candidate patches." in messages[1].content
