from __future__ import annotations

from collections import Counter
import datetime
import hashlib
import json
import shutil
from pathlib import Path

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


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _hash_skill(skill_path: Path) -> str:
    resolved = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
    if resolved.is_file() and not skill_path.is_dir():
        return _hash_file(resolved)

    digest = hashlib.sha256()
    for path in sorted(path for path in skill_path.rglob('*') if path.is_file()):
        digest.update(str(path.relative_to(skill_path)).encode('utf-8'))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _cache_key(*, task: SpreadsheetTask, skill_hash: str, llm_client, temperature: float, max_tokens: int) -> str:
    payload = {
        "task_id": task.task_id,
        "instruction": task.instruction,
        "skill_hash": skill_hash,
        "provider": llm_client.provider,
        "model": llm_client.model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    encoded = json.dumps(payload, sort_keys=True).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _restore_cached_result(*, cache_task_dir: Path, task_output_dir: Path) -> dict:
    task_output_dir.mkdir(parents=True, exist_ok=True)
    candidate_source = cache_task_dir / 'candidate.xlsx'
    code_source = cache_task_dir / 'agent_code.py'
    candidate_target = task_output_dir / f"{cache_task_dir.name.split('__', 1)[0]}_candidate.xlsx"
    code_target = task_output_dir / f"{cache_task_dir.name.split('__', 1)[0]}_agent_code.py"
    shutil.copy2(candidate_source, candidate_target)
    shutil.copy2(code_source, code_target)
    task_result = json.loads((cache_task_dir / 'task_result.json').read_text(encoding='utf-8'))
    task_result['candidate_workbook_path'] = str(candidate_target)
    task_result['code_path'] = str(code_target)
    return task_result


def _store_cached_result(*, cache_task_dir: Path, task_result: dict) -> None:
    cache_task_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(task_result['candidate_workbook_path'], cache_task_dir / 'candidate.xlsx')
    shutil.copy2(task_result['code_path'], cache_task_dir / 'agent_code.py')
    cached_task_result = dict(task_result)
    cached_task_result['candidate_workbook_path'] = 'candidate.xlsx'
    cached_task_result['code_path'] = 'agent_code.py'
    (cache_task_dir / 'task_result.json').write_text(json.dumps(cached_task_result, indent=2), encoding='utf-8')


def _task_result_to_trace_record(*, task: SpreadsheetTask, task_result: dict, llm_client, skill_path: Path) -> TraceRecord:
    return TraceRecord(
        task_id=task.task_id,
        task_instruction=task.instruction,
        skill_path=str(skill_path),
        model=llm_client.model,
        provider=llm_client.provider,
        candidate_workbook_path=task_result['candidate_workbook_path'],
        code_path=task_result['code_path'],
        raw_model_output=task_result['raw_model_output'],
        execution_stdout=task_result['execution_stdout'],
        execution_stderr=task_result['execution_stderr'],
        execution_returncode=task_result['execution_returncode'],
        evaluation=task_result['evaluation'],
    )


def run_benchmark(
    tasks: list[SpreadsheetTask],
    skill_path: Path,
    output_dir: Path,
    llm_client,
    evaluator,
    temperature: float,
    max_tokens: int,
    cache_dir: Path | None = None,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    task_results = []
    trace_records = []
    skill_hash = _hash_skill(skill_path) if cache_dir is not None else None

    for task in tasks:
        task_output_dir = output_dir / task.task_id
        task_output_dir.mkdir(parents=True, exist_ok=True)
        cache_task_dir = None
        task_result = None

        if cache_dir is not None and skill_hash is not None:
            key = _cache_key(
                task=task,
                skill_hash=skill_hash,
                llm_client=llm_client,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            cache_task_dir = cache_dir / f"{task.task_id}__{key}"
            if cache_task_dir.exists():
                task_result = _restore_cached_result(cache_task_dir=cache_task_dir, task_output_dir=task_output_dir)

        if task_result is None:
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
            if cache_task_dir is not None:
                _store_cached_result(cache_task_dir=cache_task_dir, task_result=task_result)

        (task_output_dir / 'result.json').write_text(json.dumps(task_result, indent=2), encoding='utf-8')
        trace_record = _task_result_to_trace_record(
            task=task,
            task_result=task_result,
            llm_client=llm_client,
            skill_path=skill_path,
        )
        save_trace_record(trace_record, task_output_dir / 'trace.json')
        trace_records.append(trace_record)

        evaluation = EvaluationResult(
            passed=task_result['evaluation']['passed'],
            score=task_result['evaluation']['score'],
            failure_type=task_result['evaluation']['failure_type'],
            checks=[],
            metadata=task_result['evaluation']['metadata'],
        )
        task_results.append((task_result, evaluation))

    evaluations = [evaluation for _, evaluation in task_results]
    summary = summarize_results(evaluations)
    traces_payload = {
        'num_traces': len(trace_records),
        'traces': [
            {
                'task_id': record.task_id,
                'task_instruction': record.task_instruction,
                'skill_path': record.skill_path,
                'model': record.model,
                'provider': record.provider,
                'candidate_workbook_path': record.candidate_workbook_path,
                'code_path': record.code_path,
                'raw_model_output': record.raw_model_output,
                'execution_stdout': record.execution_stdout,
                'execution_stderr': record.execution_stderr,
                'execution_returncode': record.execution_returncode,
                'evaluation': record.evaluation,
            }
            for record in trace_records
        ],
    }
    payload = {
        'summary': summary,
        'results': [task_result for task_result, _ in task_results],
        'traces': traces_payload,
    }
    (output_dir / 'summary.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    save_trace_summary(trace_records, output_dir / 'traces.json')
    return payload
