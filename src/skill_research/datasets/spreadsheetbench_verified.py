from __future__ import annotations

import json
import random
import re
from pathlib import Path

from skill_research.data.types import BenchmarkSplits, RegionSpec, RegionSpecSet, SpreadsheetTask, WorkbookPair


CELL_RE = re.compile(r"^[A-Za-z]+\d+$")
RANGE_RE = re.compile(r"^([A-Za-z]+\d+):([A-Za-z]+\d+)$")
COLUMN_RANGE_RE = re.compile(r"^([A-Za-z]+):([A-Za-z]+)$")
ROW_EXTENDED_RANGE_RE = re.compile(r"^([A-Za-z]+)(\d+):(\d+)$")
SHEET_SPLIT_RE = re.compile(r"^(?P<sheet>.+)!?(?P<cell>[A-Za-z]+\d+(?::[A-Za-z]+\d+)?)$")


def discover_workbooks(task_dir: Path) -> WorkbookPair:
    init_files = sorted(task_dir.glob("*_init.xlsx"))
    if not init_files:
        init_files = sorted(task_dir.glob("initial.xlsx"))

    golden_files = sorted(task_dir.glob("*_golden.xlsx"))
    if not golden_files:
        golden_files = sorted(task_dir.glob("golden.xlsx"))

    if len(init_files) != 1 or len(golden_files) != 1:
        raise ValueError(f"Could not resolve unique workbook pair in {task_dir}")

    return WorkbookPair(
        initial_workbook_path=init_files[0],
        golden_workbook_path=golden_files[0],
    )


def parse_region_spec(raw: str) -> RegionSpecSet:
    normalized = raw.strip()
    if "!'," in normalized:
        normalized = normalized.replace("!',", "',")

    raw_parts = _split_region_list(normalized)
    parts = [part for part in raw_parts if part.strip().strip("'").strip()]
    regions = [_parse_single_region(part) for part in parts]
    return RegionSpecSet(regions=regions, raw_text=raw)



def _split_region_list(raw: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    in_quote = False

    for char in raw:
        if char == "'":
            in_quote = not in_quote
            current.append(char)
            continue
        if char == "," and not in_quote:
            piece = "".join(current).strip()
            if piece:
                parts.append(piece)
            current = []
            continue
        current.append(char)

    piece = "".join(current).strip()
    if piece:
        parts.append(piece)
    return parts



def _parse_single_region(raw: str) -> RegionSpec:
    token = raw.strip().strip(",").strip().strip("'").strip()

    if "!" in token:
        sheet_name, cell_part = token.rsplit("!", 1)
        sheet_name = sheet_name.strip("'").strip()
    else:
        match = SHEET_SPLIT_RE.match(token)
        if match and not CELL_RE.match(token) and not RANGE_RE.match(token):
            sheet_name = match.group("sheet").strip("'").strip()
            cell_part = match.group("cell")
        else:
            sheet_name = None
            cell_part = token

    cell_part = cell_part.strip(",").strip().strip("'").strip()
    range_match = RANGE_RE.match(cell_part)
    if range_match:
        start_cell, end_cell = range_match.groups()
        return RegionSpec(
            sheet_name=sheet_name,
            start_cell=start_cell.upper(),
            end_cell=end_cell.upper(),
            raw_text=raw,
        )

    row_extended_range_match = ROW_EXTENDED_RANGE_RE.match(cell_part)
    if row_extended_range_match:
        column, start_row, end_row = row_extended_range_match.groups()
        return RegionSpec(
            sheet_name=sheet_name,
            start_cell=f"{column.upper()}{start_row}",
            end_cell=f"{column.upper()}{end_row}",
            raw_text=raw,
        )

    column_range_match = COLUMN_RANGE_RE.match(cell_part)
    if column_range_match:
        start_cell, end_cell = column_range_match.groups()
        return RegionSpec(
            sheet_name=sheet_name,
            start_cell=start_cell.upper(),
            end_cell=end_cell.upper(),
            raw_text=raw,
        )

    if CELL_RE.match(cell_part):
        return RegionSpec(
            sheet_name=sheet_name,
            start_cell=cell_part.upper(),
            end_cell=None,
            raw_text=raw,
        )

    raise ValueError(f"Unsupported region spec: {raw}")



def load_dataset(dataset_root: Path) -> list[SpreadsheetTask]:
    raw_items = json.loads((dataset_root / "dataset.json").read_text())
    tasks: list[SpreadsheetTask] = []

    for raw_item in raw_items:
        exclude_reason = raw_item.get("exclude")
        if exclude_reason:
            continue

        spreadsheet_dir = dataset_root / raw_item["spreadsheet_path"]

        try:
            workbooks = discover_workbooks(spreadsheet_dir)
            answer_spec = parse_region_spec(raw_item["answer_position"])
            data_spec = parse_region_spec(raw_item["data_position"]) if "data_position" in raw_item else None
        except ValueError:
            continue

        tasks.append(
            SpreadsheetTask(
                task_id=str(raw_item["id"]),
                instruction=raw_item["instruction"],
                instruction_type=raw_item["instruction_type"],
                spreadsheet_dir=spreadsheet_dir,
                initial_workbook_path=workbooks.initial_workbook_path,
                golden_workbook_path=workbooks.golden_workbook_path,
                answer_spec=answer_spec,
                answer_sheet=raw_item.get("answer_sheet"),
                data_spec=data_spec,
                is_excluded=False,
                exclude_reason=None,
                raw_record=raw_item,
            )
        )

    return tasks



def build_splits(
    tasks: list[SpreadsheetTask],
    train_size: int,
    val_size: int,
    test_size: int,
    seed: int,
) -> BenchmarkSplits:
    requested = train_size + val_size + test_size
    if requested > len(tasks):
        raise ValueError("Requested split sizes exceed available tasks")

    ordered_tasks = sorted(tasks, key=lambda task: task.task_id)
    shuffled_tasks = ordered_tasks[:]
    random.Random(seed).shuffle(shuffled_tasks)

    train_end = train_size
    val_end = train_end + val_size
    test_end = val_end + test_size

    return BenchmarkSplits(
        train=shuffled_tasks[:train_end],
        val=shuffled_tasks[train_end:val_end],
        test=shuffled_tasks[val_end:test_end],
    )
