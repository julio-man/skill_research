from __future__ import annotations

from pathlib import Path

from skill_research.data.types import SpreadsheetTask, RegionSpec, RegionSpecSet
from skill_research.evaluation.base import EvaluationResult, CheckResult
from skill_research.llm.client import LLMClient
from skill_research.runner.benchmark import run_benchmark


class _FakeSDKClient:
    def __init__(self, text: str):
        self.text = text


class _FakeLLMClient(LLMClient):
    def __init__(self, text: str):
        super().__init__(provider="openai", model="fake-model", sdk_client=_FakeSDKClient(text))

    def complete(self, messages, temperature: float, max_tokens: int) -> str:
        return self.sdk_client.text


class _FakeEvaluator:
    def evaluate(self, task: SpreadsheetTask, candidate_workbook_path: Path) -> EvaluationResult:
        return EvaluationResult(
            passed=True,
            score=1.0,
            failure_type="none",
            checks=[CheckResult(kind="ok", passed=True, message="ok", details={})],
            metadata={"task_id": task.task_id, "expected_region_values": {}, "actual_region_values": {}},
        )


def _make_task(tmp_path: Path) -> SpreadsheetTask:
    spreadsheet_dir = tmp_path / "task"
    spreadsheet_dir.mkdir()
    init_path = spreadsheet_dir / "initial.xlsx"
    golden_path = spreadsheet_dir / "golden.xlsx"
    init_path.write_text("placeholder workbook")
    golden_path.write_text("placeholder workbook")
    return SpreadsheetTask(
        task_id="task-001",
        instruction="Update workbook.",
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


def test_run_benchmark_returns_traces_payload(tmp_path: Path) -> None:
    task = _make_task(tmp_path)
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text("Use Python.")
    llm_client = _FakeLLMClient("```python\nfrom pathlib import Path\nPath(OUTPUT_WORKBOOK).write_text('generated workbook')\n```")

    payload = run_benchmark(
        tasks=[task],
        skill_path=skill_path,
        output_dir=tmp_path / "run",
        llm_client=llm_client,
        evaluator=_FakeEvaluator(),
        temperature=0.0,
        max_tokens=100,
    )

    assert "traces" in payload
    assert payload["traces"]["num_traces"] == 1
    assert payload["traces"]["traces"][0]["task_id"] == "task-001"
