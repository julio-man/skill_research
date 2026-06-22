from __future__ import annotations

from skill_research.patches.proposer import OpenAIPatchProposer
from skill_research.traces import TraceRecord


def _trace(task_id: str, failure_type: str, expected: str, actual: str) -> TraceRecord:
    return TraceRecord(
        task_id=task_id,
        task_instruction="Rewrite a workbook region.",
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
            "failure_type": failure_type,
            "checks": [
                {
                    "kind": "cell_value",
                    "passed": False,
                    "message": f"Mismatch at Sheet1!E10",
                    "details": {
                        "sheet_name": "Sheet1",
                        "cell": "E10",
                        "expected": expected,
                        "actual": actual,
                    },
                }
            ],
            "metadata": {
                "task_id": task_id,
                "answer_region_raw": "'Sheet1'!E2:E17",
                "answer_sheet": "Sheet1",
                "expected_region_values": {"Sheet1!E10": expected},
                "actual_region_values": {"Sheet1!E10": actual},
            },
        },
    )


def test_build_trace_summary_includes_failure_and_region_values() -> None:
    proposer = OpenAIPatchProposer(model="gpt-5.4")
    summary = proposer.build_trace_summary([
        _trace("379-36", "wrong_answer", "Georgia WH Tax", "Georgia Its Tax/ga Tx *****0")
    ])

    assert "task_id: 379-36" in summary
    assert "failure_type: wrong_answer" in summary
    assert "expected_region_values" in summary
    assert "actual_region_values" in summary
    assert "Georgia WH Tax" in summary


def test_parse_patch_response_returns_patch_objects() -> None:
    proposer = OpenAIPatchProposer(model="gpt-5.4")
    patches = proposer.parse_patch_response(
        '{"patches": ['
        '{"patch_id": "p1", "patch_type": "add_rule", "target_file": "SKILL.md", '
        '"target_section": "workflow", "operation": "append_under_section", '
        '"content": "Always inspect real sheet names before indexing.", '
        '"delta_tokens": 8, "support_count": 3}'
        ']}'
    )

    assert len(patches) == 1
    patch = patches[0]
    assert patch.patch_id == "p1"
    assert patch.patch_type == "add_rule"
    assert patch.target_file == "SKILL.md"
    assert patch.target_section == "workflow"
    assert patch.operation == "append_under_section"
    assert patch.delta_tokens == 8
    assert patch.support_count == 3
