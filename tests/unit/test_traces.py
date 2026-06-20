from __future__ import annotations

import json
from pathlib import Path
import shutil

from skill_research.datasets.spreadsheetbench_verified import load_dataset
from skill_research.evaluation.spreadsheet import SpreadsheetTaskEvaluator
from skill_research.llm.client import LLMClient
from skill_research.runner.benchmark import run_benchmark
from skill_research.traces import TraceRecord, save_trace_record, save_trace_summary


DATASET_ROOT = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")


class _FakeSDKClient:
    def __init__(self, text: str):
        self.text = text


class _FakeLLMClient(LLMClient):
    def __init__(self, text: str):
        super().__init__(provider="openai", model="fake-model", sdk_client=_FakeSDKClient(text))

    def complete(self, messages, temperature: float, max_tokens: int) -> str:
        return self.sdk_client.text



def test_save_trace_record_writes_json(tmp_path: Path) -> None:
    record = TraceRecord(
        task_id="task-1",
        task_instruction="do something",
        skill_path="skills/minimal_seed/SKILL.md",
        model="fake-model",
        provider="openai",
        candidate_workbook_path="candidate.xlsx",
        code_path="code.py",
        raw_model_output="print('hi')",
        execution_stdout="",
        execution_stderr="",
        execution_returncode=0,
        evaluation={"passed": True, "score": 1.0},
    )
    output_path = tmp_path / "trace.json"

    save_trace_record(record, output_path)

    payload = json.loads(output_path.read_text())
    assert payload["task_id"] == "task-1"
    assert payload["skill_path"] == "skills/minimal_seed/SKILL.md"



def test_save_trace_summary_writes_trace_list(tmp_path: Path) -> None:
    records = [
        TraceRecord(
            task_id="task-1",
            task_instruction="a",
            skill_path="skills/minimal_seed/SKILL.md",
            model="fake-model",
            provider="openai",
            candidate_workbook_path="candidate.xlsx",
            code_path="code.py",
            raw_model_output="print('hi')",
            execution_stdout="",
            execution_stderr="",
            execution_returncode=0,
            evaluation={"passed": True, "score": 1.0},
        )
    ]
    output_path = tmp_path / "traces.json"

    save_trace_summary(records, output_path)

    payload = json.loads(output_path.read_text())
    assert payload["num_traces"] == 1
    assert payload["traces"][0]["task_id"] == "task-1"



def test_run_benchmark_emits_per_task_and_benchmark_traces(tmp_path: Path) -> None:
    task = next(task for task in load_dataset(DATASET_ROOT) if task.task_id == "379-36")
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text("Use Python to modify the workbook.")

    llm_client = _FakeLLMClient(
        """
```python
from pathlib import Path
Path(OUTPUT_WORKBOOK).write_text('not a real workbook')
```
""".strip()
    )

    payload = run_benchmark(
        tasks=[task],
        skill_path=skill_path,
        output_dir=tmp_path / "run",
        llm_client=llm_client,
        evaluator=SpreadsheetTaskEvaluator(),
        temperature=0.0,
        max_tokens=200,
    )

    assert payload["summary"]["num_tasks"] == 1
    assert (tmp_path / "run" / task.task_id / "trace.json").exists()
    assert (tmp_path / "run" / "traces.json").exists()
