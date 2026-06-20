from __future__ import annotations

from collections import Counter
import datetime
from pathlib import Path
import json

from skill_research.data.types import SpreadsheetTask
from skill_research.evaluation.base import EvaluationResult
from skill_research.runner.agent import run_agent_once
from skill_research.traces import TraceRecord, save_trace_record, save_trace_summary


class BenchmarkRunError(RuntimeError):
    pass



def make_json_safe(value):
    if isinstance(value, dict):
        return {key: make_json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [make_json_safe(inner) for inner in value]
    if isinstance(value, tuple):
        return [make_json_safe(inner) for inner in value]
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, datetime.time):
        return value.isoformat()
    return value



def summarize_results(results: list[EvaluationResult]) -> dict:
    num_tasks = len(results)
    pass_rate = sum(1 for result in results if result.passed) / num_tasks if num_tasks else 0.0
    avg_score = sum(result.score for result in results) / num_tasks if num_tasks else 0.0
    failure_histogram = dict(Counter(result.failure_type for result in results))
    return {
        "num_tasks": num_tasks,
        "pass_rate": pass_rate,
        "avg_score": avg_score,
        "failure_histogram": failure_histogram,
    }



def run_benchmark(
    tasks: list[SpreadsheetTask],
    skill_path: Path,
    output_dir: Path,
    llm_client,
    evaluator,
    temperature: float,
    max_tokens: int,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    task_results = []
    trace_records = []

    for task in tasks:
        task_output_dir = output_dir / task.task_id
        task_output_dir.mkdir(parents=True, exist_ok=True)

        agent_run = run_agent_once(
            task=task,
            skill_path=skill_path,
            output_dir=task_output_dir,
            llm_client=llm_client,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        evaluation = evaluator.evaluate(task, Path(agent_run.candidate_workbook_path))

        task_result = {
            "task_id": task.task_id,
            "instruction_type": task.instruction_type,
            "candidate_workbook_path": agent_run.candidate_workbook_path,
            "code_path": agent_run.code_path,
            "raw_model_output": agent_run.raw_model_output,
            "execution_stdout": agent_run.execution_stdout,
            "execution_stderr": agent_run.execution_stderr,
            "execution_returncode": agent_run.execution_returncode,
            "evaluation": {
                "passed": evaluation.passed,
                "score": evaluation.score,
                "failure_type": evaluation.failure_type,
                "checks": [
                    {
                        "kind": check.kind,
                        "passed": check.passed,
                        "message": check.message,
                        "details": make_json_safe(check.details),
                    }
                    for check in evaluation.checks
                ],
                "metadata": make_json_safe(evaluation.metadata),
            },
        }
        (task_output_dir / "result.json").write_text(json.dumps(task_result, indent=2), encoding="utf-8")
        trace_record = TraceRecord(
            task_id=task.task_id,
            task_instruction=task.instruction,
            skill_path=str(skill_path),
            model=llm_client.model,
            provider=llm_client.provider,
            candidate_workbook_path=agent_run.candidate_workbook_path,
            code_path=agent_run.code_path,
            raw_model_output=agent_run.raw_model_output,
            execution_stdout=agent_run.execution_stdout,
            execution_stderr=agent_run.execution_stderr,
            execution_returncode=agent_run.execution_returncode,
            evaluation=task_result["evaluation"],
        )
        save_trace_record(trace_record, task_output_dir / "trace.json")
        trace_records.append(trace_record)
        task_results.append((task_result, evaluation))

    evaluations = [evaluation for _, evaluation in task_results]
    summary = summarize_results(evaluations)
    payload = {
        "summary": summary,
        "results": [task_result for task_result, _ in task_results],
    }
    (output_dir / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    save_trace_summary(trace_records, output_dir / "traces.json")
    return payload
