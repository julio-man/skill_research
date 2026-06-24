from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from skill_research.core.types import SkillRef, Task
from skill_research.evaluators.spreadsheet import SpreadsheetEvaluator
from skill_research.executors.spreadsheet_python import SpreadsheetPythonExecutor
from skill_research.llms.base import CompletionResponse, LLMBackendInfo
from skill_research.patches.proposers.openai_trace import OpenAITracePatchProposer
from skill_research.traces.types import TraceRecord


class ProviderError(Exception):
    code = "invalid_prompt"


class FailingBackend:
    def complete(self, request):
        raise ProviderError("policy blocked")


class RetryBackend:
    def __init__(self):
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        if self.calls == 1:
            raise ProviderError("policy blocked")
        return CompletionResponse('{"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "Rule", "supported_trace_ids": ["t1"]}]}', LLMBackendInfo("retry", "test", "retry"))


def test_executor_classifies_llm_provider_error(tmp_path: Path) -> None:
    workbook = tmp_path / "input.xlsx"
    Workbook().save(workbook)
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    result = SpreadsheetPythonExecutor(FailingBackend()).run(Task("t1", "copy", workbook), SkillRef(skill), tmp_path / "out", {})

    assert result.returncode == -3
    assert result.stderr == "llm_provider_error"
    assert result.metadata["provider_error_type"] == "ProviderError"
    assert result.metadata["provider_error_code"] == "invalid_prompt"


def test_evaluator_maps_llm_provider_error(tmp_path: Path) -> None:
    golden = tmp_path / "golden.xlsx"
    Workbook().save(golden)
    task = Task("t1", "copy", metadata={"golden_workbook_path": str(golden), "answer_cells": ["Sheet1!A1"]})
    result = SpreadsheetEvaluator().evaluate(task, {"artifact_path": str(tmp_path / "missing.xlsx"), "returncode": -3, "stderr": "llm_provider_error"})

    assert result.failure_type == "llm_provider_error"


def test_patch_proposer_retries_provider_error(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    backend = RetryBackend()

    pool = OpenAITracePatchProposer(backend, max_retries=1).propose(SkillRef(skill), [TraceRecord("t1", False, "wrong_answer")], {})

    assert backend.calls == 2
    assert pool.patches[0].patch_id == "p1"
    assert pool.metadata["retry_count"] == 1
