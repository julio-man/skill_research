from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass
class TraceRecord:
    task_id: str
    task_instruction: str
    skill_path: str
    model: str
    provider: str
    candidate_workbook_path: str
    code_path: str
    raw_model_output: str
    execution_stdout: str
    execution_stderr: str
    execution_returncode: int
    evaluation: dict



def save_trace_record(record: TraceRecord, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")



def save_trace_summary(records: list[TraceRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "num_traces": len(records),
        "traces": [asdict(record) for record in records],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
