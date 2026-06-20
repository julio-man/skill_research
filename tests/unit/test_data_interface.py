from pathlib import Path

from skill_research.datasets.spreadsheetbench_verified import discover_workbooks, load_dataset, parse_region_spec


DATASET_ROOT = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")


def test_load_dataset_skips_unusable_tasks() -> None:
    tasks = load_dataset(DATASET_ROOT)

    assert len(tasks) == 395
    assert all(not task.is_excluded for task in tasks)


def test_load_dataset_preserves_sheet_level_metadata() -> None:
    tasks = load_dataset(DATASET_ROOT)
    task = next(task for task in tasks if task.task_id == "13-1")

    assert task.answer_sheet == "LISTS"
    assert task.data_spec is not None
    assert task.data_spec.raw_text == "A1:E56"


def test_discover_workbooks_supports_standard_naming() -> None:
    pair = discover_workbooks(DATASET_ROOT / "spreadsheet" / "13-1")

    assert pair.initial_workbook_path.name == "1_13-1_init.xlsx"
    assert pair.golden_workbook_path.name == "1_13-1_golden.xlsx"


def test_discover_workbooks_supports_alternate_naming() -> None:
    pair = discover_workbooks(DATASET_ROOT / "spreadsheet" / "13284")

    assert pair.initial_workbook_path.name == "initial.xlsx"
    assert pair.golden_workbook_path.name == "golden.xlsx"


def test_parse_region_spec_supports_plain_range() -> None:
    spec = parse_region_spec("A3:D32")

    assert spec.raw_text == "A3:D32"
    assert len(spec.regions) == 1
    assert spec.regions[0].sheet_name is None
    assert spec.regions[0].start_cell == "A3"
    assert spec.regions[0].end_cell == "D32"


def test_parse_region_spec_supports_sheet_qualified_cell() -> None:
    spec = parse_region_spec("'data'!O3")

    assert len(spec.regions) == 1
    assert spec.regions[0].sheet_name == "data"
    assert spec.regions[0].start_cell == "O3"
    assert spec.regions[0].end_cell is None


def test_parse_region_spec_supports_multi_region_with_sheets() -> None:
    spec = parse_region_spec("'SHEET1'!B2:B8,'SHEET2'!B2:B7")

    assert len(spec.regions) == 2
    assert spec.regions[0].sheet_name == "SHEET1"
    assert spec.regions[0].start_cell == "B2"
    assert spec.regions[0].end_cell == "B8"
    assert spec.regions[1].sheet_name == "SHEET2"
    assert spec.regions[1].start_cell == "B2"
    assert spec.regions[1].end_cell == "B7"


def test_parse_region_spec_supports_discrete_cells() -> None:
    spec = parse_region_spec("D1,D5,D9")

    assert len(spec.regions) == 3
    assert [region.start_cell for region in spec.regions] == ["D1", "D5", "D9"]
    assert all(region.end_cell is None for region in spec.regions)
