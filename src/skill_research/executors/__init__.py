from skill_research.core.registry import ComponentRegistry
from skill_research.executors.base import ExecutionResult
from skill_research.executors.spreadsheet_python import SpreadsheetPythonExecutor, extract_python


executor_registry = ComponentRegistry()
executor_registry.register("spreadsheet_python", lambda backend, **kwargs: SpreadsheetPythonExecutor(backend))


def build_executor(name: str, **kwargs):
    return executor_registry.build(name, **kwargs)


__all__ = ["ExecutionResult", "SpreadsheetPythonExecutor", "build_executor", "executor_registry", "extract_python"]
