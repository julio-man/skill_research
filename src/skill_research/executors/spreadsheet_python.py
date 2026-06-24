"""Spreadsheet executor that asks an LLM for Python and runs it on a workbook."""

from __future__ import annotations

from pathlib import Path
import os
import re
import subprocess
import sys

from skill_research.core.types import SkillRef, Task
from skill_research.executors.base import ExecutionResult
from skill_research.llms.base import ChatMessage, CompletionRequest, CompletionResponse


def extract_python(raw: str) -> str:
    match = re.search(r"```python\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    generic = re.search(r"```\s*(.*?)```", raw, re.DOTALL)
    if generic:
        return generic.group(1).strip()
    return raw.strip()


def sanitize_generated_python(code: str) -> str:
    reserved_assignment = re.compile(r"^\s*(INPUT_WORKBOOK|OUTPUT_WORKBOOK)\s*=.*$")
    sanitized = "\n".join(line for line in code.splitlines() if not reserved_assignment.match(line)).strip()
    return sanitized + "\n" if sanitized else ""


def _relative_path(path: Path, start: Path | None = None) -> str:
    start = start or Path.cwd()
    return os.path.relpath(path.resolve(), start.resolve())


class SpreadsheetPythonExecutor:
    name = "spreadsheet_python"

    def __init__(self, backend):
        self.backend = backend

    def run(self, task: Task, skill: SkillRef, output_dir: Path, config: dict) -> ExecutionResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir = output_dir.resolve()
        skill_path = skill.path / "SKILL.md" if skill.path.is_dir() else skill.path
        skill_text = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
        artifact_path = output_dir / f"{task.task_id}_candidate.xlsx"
        code_path = output_dir / f"{task.task_id}_agent_code.py"
        request = CompletionRequest(
            messages=[
                ChatMessage("system", "Return only Python code that uses existing INPUT_WORKBOOK and OUTPUT_WORKBOOK variables. Do not assign INPUT_WORKBOOK or OUTPUT_WORKBOOK."),
                ChatMessage("user", f"SKILL:\n{skill_text}\nTASK:\n{task.instruction}"),
            ],
            temperature=float(config.get("temperature", 0.0)),
            max_tokens=int(config.get("max_tokens", 2500)),
            seed=config.get("seed"),
        )
        response = self.backend.complete(request)
        raw = response.content if isinstance(response, CompletionResponse) else str(response)
        code = sanitize_generated_python(extract_python(raw))
        input_path = Path(task.input_path).resolve() if task.input_path is not None else None
        input_for_code = _relative_path(input_path, output_dir) if input_path is not None else ""
        output_for_code = artifact_path.name
        prelude = f"INPUT_WORKBOOK = {input_for_code!r}\nOUTPUT_WORKBOOK = {output_for_code!r}\n"
        code_path.write_text(prelude + code, encoding="utf-8")
        proc = subprocess.run([sys.executable, str(code_path)], cwd=str(output_dir), capture_output=True, text=True)
        return ExecutionResult(
            artifact_path=_relative_path(artifact_path),
            code_path=_relative_path(code_path),
            raw_output=raw,
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )
