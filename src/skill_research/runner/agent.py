from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import subprocess
import sys

from skill_research.data.types import SpreadsheetTask
from skill_research.llm.client import ChatMessage, LLMClient


SYSTEM_PROMPT = """You are a spreadsheet task agent.
You will be given:
1. A skill document.
2. A spreadsheet task.
3. The input workbook path.
4. The output workbook path.

You must produce ONLY Python code.
Requirements:
- Use Python to create a candidate workbook artifact.
- Read the workbook from INPUT_WORKBOOK when needed.
- Write the result to OUTPUT_WORKBOOK.
- Do not print explanations.
- Do not use markdown fences unless unavoidable.
"""


@dataclass
class AgentRunResult:
    candidate_workbook_path: str
    code_path: str
    raw_model_output: str
    execution_stdout: str
    execution_stderr: str
    execution_returncode: int



def extract_python(raw: str) -> str:
    fence = re.search(r"```python\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    generic_fence = re.search(r"```\s*(.*?)```", raw, re.DOTALL)
    if generic_fence:
        return generic_fence.group(1).strip()
    return raw.strip()



def build_agent_messages(task: SpreadsheetTask, skill_text: str, output_workbook_path: Path) -> list[ChatMessage]:
    input_workbook_path = task.initial_workbook_path.resolve()
    output_workbook_path = output_workbook_path.resolve()
    user_prompt = f"""SKILL DOCUMENT:
{skill_text}

TASK:
{task.instruction}

INPUT_WORKBOOK={input_workbook_path}
OUTPUT_WORKBOOK={output_workbook_path}

Return only runnable Python code.
"""
    return [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]



def run_agent_once(
    task: SpreadsheetTask,
    skill_path: Path,
    output_dir: Path,
    llm_client: LLMClient,
    temperature: float,
    max_tokens: int,
) -> AgentRunResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_skill_path = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
    skill_text = resolved_skill_path.read_text(encoding="utf-8")
    candidate_workbook_path = (output_dir / f"{task.task_id}_candidate.xlsx").resolve()
    code_path = (output_dir / f"{task.task_id}_agent_code.py").resolve()

    messages = build_agent_messages(task=task, skill_text=skill_text, output_workbook_path=candidate_workbook_path)
    raw_model_output = llm_client.complete(messages, temperature=temperature, max_tokens=max_tokens)
    code = extract_python(raw_model_output)
    prelude = (
        f"INPUT_WORKBOOK = {str(task.initial_workbook_path.resolve())!r}\n"
        f"OUTPUT_WORKBOOK = {str(candidate_workbook_path)!r}\n"
    )
    code_path.write_text(prelude + code, encoding="utf-8")

    process = subprocess.run(
        [sys.executable, str(code_path)],
        cwd=str(output_dir),
        env={
            **os.environ,
            "INPUT_WORKBOOK": str(task.initial_workbook_path),
            "OUTPUT_WORKBOOK": str(candidate_workbook_path),
        },
        capture_output=True,
        text=True,
    )

    return AgentRunResult(
        candidate_workbook_path=str(candidate_workbook_path),
        code_path=str(code_path),
        raw_model_output=raw_model_output,
        execution_stdout=process.stdout,
        execution_stderr=process.stderr,
        execution_returncode=process.returncode,
    )
