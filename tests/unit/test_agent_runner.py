from __future__ import annotations

from pathlib import Path

from skill_research.data.types import RegionSpec, RegionSpecSet, SpreadsheetTask
from skill_research.llm.client import ChatMessage, LLMClient
from skill_research.runner.agent import AgentRunResult, build_agent_messages, extract_python, run_agent_once


class _FakeSDKClient:
    def __init__(self, text: str):
        self.text = text
        self.seen_messages = None


class _FakeLLMClient(LLMClient):
    def __init__(self, text: str):
        super().__init__(provider="openai", model="fake-model", sdk_client=_FakeSDKClient(text))

    def complete(self, messages: list[ChatMessage], temperature: float, max_tokens: int) -> str:
        self.sdk_client.seen_messages = messages
        return self.sdk_client.text


def _make_task(tmp_path: Path) -> SpreadsheetTask:
    spreadsheet_dir = tmp_path / "task"
    spreadsheet_dir.mkdir()
    init_path = spreadsheet_dir / "initial.xlsx"
    golden_path = spreadsheet_dir / "golden.xlsx"
    init_path.write_text("placeholder workbook")
    golden_path.write_text("placeholder workbook")
    return SpreadsheetTask(
        task_id="task-001",
        instruction="Update the workbook according to the task.",
        instruction_type="Sheet-Level Manipulation",
        spreadsheet_dir=spreadsheet_dir,
        initial_workbook_path=init_path,
        golden_workbook_path=golden_path,
        answer_spec=RegionSpecSet(regions=[RegionSpec(sheet_name=None, start_cell="A1", end_cell="A2", raw_text="A1:A2")], raw_text="A1:A2"),
        answer_sheet=None,
        data_spec=None,
        is_excluded=False,
        exclude_reason=None,
        raw_record={},
    )


def test_extract_python_strips_markdown_fences() -> None:
    raw = "```python\nprint('hi')\n```"

    assert extract_python(raw) == "print('hi')"


def test_build_agent_messages_contains_skill_task_and_paths(tmp_path: Path) -> None:
    task = _make_task(tmp_path)
    messages = build_agent_messages(
        task=task,
        skill_text="Always preserve unrelated cells.",
        output_workbook_path=tmp_path / "candidate.xlsx",
    )

    assert messages[0].role == "system"
    assert "produce ONLY Python code" in messages[0].content
    assert "Always preserve unrelated cells." in messages[1].content
    assert task.instruction in messages[1].content
    assert str(task.initial_workbook_path) in messages[1].content
    assert str(tmp_path / "candidate.xlsx") in messages[1].content


def test_run_agent_once_writes_code_and_candidate_artifact(tmp_path: Path) -> None:
    task = _make_task(tmp_path)
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text("Use openpyxl.")
    output_dir = tmp_path / "run"
    llm_client = _FakeLLMClient(
        """
```python
from pathlib import Path
Path(OUTPUT_WORKBOOK).write_text('generated workbook')
print('done')
```
""".strip()
    )

    result = run_agent_once(
        task=task,
        skill_path=skill_dir,
        output_dir=output_dir,
        llm_client=llm_client,
        temperature=0.0,
        max_tokens=400,
    )

    assert isinstance(result, AgentRunResult)
    assert Path(result.code_path).exists()
    assert Path(result.candidate_workbook_path).exists()
    assert Path(result.candidate_workbook_path).read_text() == "generated workbook"
    assert result.execution_returncode == 0
    assert "done" in result.execution_stdout
