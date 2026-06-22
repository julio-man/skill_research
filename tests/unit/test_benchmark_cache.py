from __future__ import annotations

from pathlib import Path

from skill_research.data.types import RegionSpec, RegionSpecSet, SpreadsheetTask
from skill_research.evaluation.base import CheckResult, EvaluationResult
from skill_research.llm.client import LLMClient
from skill_research.runner.benchmark import run_benchmark


class _CountingSDKClient:
    def __init__(self, texts: list[str]):
        self.texts = texts
        self.calls = 0


class _CountingLLMClient(LLMClient):
    def __init__(self, texts: list[str]):
        super().__init__(provider="openai", model="fake-model", sdk_client=_CountingSDKClient(texts))

    def complete(self, messages, temperature: float, max_tokens: int) -> str:
        text = self.sdk_client.texts[self.sdk_client.calls]
        self.sdk_client.calls += 1
        return text


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
    init_path.write_text("placeholder workbook", encoding="utf-8")
    golden_path.write_text("placeholder workbook", encoding="utf-8")
    return SpreadsheetTask(
        task_id="task-001",
        instruction="Update workbook.",
        instruction_type="Sheet-Level Manipulation",
        spreadsheet_dir=spreadsheet_dir,
        initial_workbook_path=init_path,
        golden_workbook_path=golden_path,
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



def test_run_benchmark_cache_reuses_result_for_same_skill_contents(tmp_path: Path) -> None:
    task = _make_task(tmp_path)
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("Use Python.\n", encoding="utf-8")

    llm_client = _CountingLLMClient(
        [
            "```python\nfrom pathlib import Path\nPath(OUTPUT_WORKBOOK).write_text('first workbook')\n```",
            "```python\nfrom pathlib import Path\nPath(OUTPUT_WORKBOOK).write_text('second workbook')\n```",
        ]
    )
    evaluator = _FakeEvaluator()
    cache_dir = tmp_path / "cache"

    first_payload = run_benchmark(
        tasks=[task],
        skill_path=skill_dir,
        output_dir=tmp_path / "run1",
        llm_client=llm_client,
        evaluator=evaluator,
        temperature=0.0,
        max_tokens=100,
        cache_dir=cache_dir,
    )
    copied_skill_dir = tmp_path / "skill_copy"
    copied_skill_dir.mkdir()
    (copied_skill_dir / "SKILL.md").write_text("Use Python.\n", encoding="utf-8")
    second_payload = run_benchmark(
        tasks=[task],
        skill_path=copied_skill_dir,
        output_dir=tmp_path / "run2",
        llm_client=llm_client,
        evaluator=evaluator,
        temperature=0.0,
        max_tokens=100,
        cache_dir=cache_dir,
    )

    assert llm_client.sdk_client.calls == 1
    assert first_payload["results"][0]["raw_model_output"] == second_payload["results"][0]["raw_model_output"]
    second_candidate = Path(second_payload["results"][0]["candidate_workbook_path"])
    assert second_candidate.read_text(encoding="utf-8") == "first workbook"
