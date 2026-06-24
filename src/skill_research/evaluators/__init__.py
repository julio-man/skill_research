from skill_research.core.registry import ComponentRegistry
from skill_research.evaluators.base import CheckResult, EvaluationResult
from skill_research.evaluators.spreadsheet import SpreadsheetEvaluator


evaluator_registry = ComponentRegistry()
evaluator_registry.register("spreadsheet", lambda **kwargs: SpreadsheetEvaluator())


def build_evaluator(name: str, **kwargs):
    return evaluator_registry.build(name, **kwargs)


__all__ = ["CheckResult", "EvaluationResult", "SpreadsheetEvaluator", "build_evaluator", "evaluator_registry"]
