from pathlib import Path


def test_no_scaffold_module_is_empty():
    empty = [str(path) for path in Path("src/skill_research").rglob("*.py") if path.stat().st_size == 0]
    assert empty == []
