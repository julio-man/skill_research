from pathlib import Path

from skill_research.datasets.spreadsheetbench_verified import BenchmarkSplits, build_splits, load_dataset


DATASET_ROOT = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")


def test_build_splits_returns_requested_sizes() -> None:
    tasks = load_dataset(DATASET_ROOT)

    splits = build_splits(tasks, train_size=200, val_size=100, test_size=95, seed=7)

    assert isinstance(splits, BenchmarkSplits)
    assert len(splits.train) == 200
    assert len(splits.val) == 100
    assert len(splits.test) == 95


def test_build_splits_is_deterministic_for_same_seed() -> None:
    tasks = load_dataset(DATASET_ROOT)

    first = build_splits(tasks, train_size=200, val_size=100, test_size=95, seed=11)
    second = build_splits(tasks, train_size=200, val_size=100, test_size=95, seed=11)

    assert [task.task_id for task in first.train] == [task.task_id for task in second.train]
    assert [task.task_id for task in first.val] == [task.task_id for task in second.val]
    assert [task.task_id for task in first.test] == [task.task_id for task in second.test]


def test_build_splits_changes_when_seed_changes() -> None:
    tasks = load_dataset(DATASET_ROOT)

    first = build_splits(tasks, train_size=200, val_size=100, test_size=95, seed=3)
    second = build_splits(tasks, train_size=200, val_size=100, test_size=95, seed=17)

    assert [task.task_id for task in first.train] != [task.task_id for task in second.train]


def test_build_splits_are_disjoint_and_cover_selected_budget() -> None:
    tasks = load_dataset(DATASET_ROOT)

    splits = build_splits(tasks, train_size=200, val_size=100, test_size=95, seed=5)
    selected_ids = {task.task_id for task in splits.train + splits.val + splits.test}

    assert len(selected_ids) == 395
    assert selected_ids == {task.task_id for task in tasks}


def test_build_splits_raises_if_requested_budget_exceeds_dataset() -> None:
    tasks = load_dataset(DATASET_ROOT)

    try:
        build_splits(tasks, train_size=300, val_size=100, test_size=100, seed=0)
    except ValueError as exc:
        assert "Requested split sizes exceed available tasks" in str(exc)
    else:
        raise AssertionError("Expected ValueError when split sizes exceed task count")
