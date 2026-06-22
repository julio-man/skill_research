from __future__ import annotations

from pathlib import Path

from skill_research.data.types import RegionSpec, RegionSpecSet, SpreadsheetTask
from skill_research.runner.agent import build_agent_messages, extract_python, run_agent_once


class _FakeLLMClient:
    provider = "openai"
    model = "fake-model"

    def __init__(self, response: str):
        self.response = response

    def complete(self, messages, temperature: float, max_tokens: int) -> str:
        return self.response



def _make_task(tmp_path: Path) -> SpreadsheetTask:
    spreadsheet_dir = tmp_path / "task"
    spreadsheet_dir.mkdir()
    initial = spreadsheet_dir / "initial.xlsx"
    golden = spreadsheet_dir / "golden.xlsx"
    initial.write_text("placeholder workbook", encoding="utf-8")
    golden.write_text("placeholder workbook", encoding="utf-8")
    return SpreadsheetTask(
        task_id="task-123",
        instruction="Fill the target range.",
        instruction_type="Sheet-Level Manipulation",
        spreadsheet_dir=spreadsheet_dir,
        initial_workbook_path=initial,
        golden_workbook_path=golden,
        answer_spec=RegionSpecSet(
            regions=[RegionSpec(sheet_name=None, start_cell="A1", end_cell="A2", raw_text="A1:A2")],
            raw_text="A1:A2",
        ),
        answer_sheet=None,
        data_spec=None,
        is_excluded=False,
        exclude_reason=None,
        raw_record={},
    )



def test_extract_python_strips_python_fence() -> None:
    raw = "```python\nprint('hello')\n```"

    extracted = extract_python(raw)

    assert extracted == "print('hello')"



def test_build_agent_messages_mentions_predefined_workbook_variables(tmp_path: Path) -> None:
    task = _make_task(tmp_path)

    messages = build_agent_messages(task=task, skill_text="Use Python.")

    assert len(messages) == 2
    assert "Fill the target range." in messages[1].content
    assert "INPUT_WORKBOOK is already defined" in messages[1].content
    assert "OUTPUT_WORKBOOK is already defined" in messages[1].content
    assert str(task.initial_workbook_path.resolve()) not in messages[1].content



def test_run_agent_once_writes_and_executes_generated_code(tmp_path: Path) -> None:
    task = _make_task(tmp_path)
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text("Use Python.", encoding="utf-8")
    llm_client = _FakeLLMClient(
        "```python\nfrom pathlib import Path\nPath(OUTPUT_WORKBOOK).write_text('generated workbook')\n```"
    )

    result = run_agent_once(
        task=task,
        skill_path=skill_path,
        output_dir=tmp_path / "run",
        llm_client=llm_client,
        temperature=0.0,
        max_tokens=100,
    )

    assert Path(result.code_path).exists()
    assert Path(result.candidate_workbook_path).read_text(encoding="utf-8") == "generated workbook"
    assert result.execution_returncode == 0
