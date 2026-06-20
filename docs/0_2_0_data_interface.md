# `0.2.0` Data Interface Spec

## Purpose
This document translates the real `SpreadsheetBench Verified 400` dataset into concrete `0.2.0` code-facing interface requirements.

The goal is to answer:
- what the dataset actually contains,
- what abstractions the harness should expose,
- what edge cases must be supported,
- and what should be validated at load time.

This is based on direct inspection of:

- `data/spreadsheetbench_verified/spreadsheetbench_verified_400/dataset.json`
- per-task workbook directories under `spreadsheet/`

---

## Canonical dataset path
The canonical local dataset root is:

- `data/spreadsheetbench_verified/spreadsheetbench_verified_400/`

This is the path used by the current fetch script and matches the public `Trace2Skill` repo layout.

---

## Dataset format overview

### Top-level format
`dataset.json` is:
- a JSON **list**
- length **400**

So the first loader assumption for `0.2.0` should be:
- dataset root contains one JSON file
- that file deserializes into a list of task records

---

## Actual record schemas found in the dataset
There are **3 distinct key patterns** in the inspected dataset.

### Schema A — minimal cell-level-like schema
Present in **273** tasks.

Fields:
- `id`
- `instruction`
- `spreadsheet_path`
- `instruction_type`
- `answer_position`

### Schema B — richer sheet-level schema
Present in **125** tasks.

Fields:
- `id`
- `instruction`
- `spreadsheet_path`
- `instruction_type`
- `answer_position`
- `answer_sheet`
- `data_position`

### Schema C — special-case excluded tasks
Present in **2** tasks.

Fields:
- `id`
- `instruction`
- `spreadsheet_path`
- `instruction_type`
- `answer_position`
- `exclude`

The two observed `exclude` values were:
- `ignore, initial file already passes verification`
- `golden has data validation dropdown set to a completely different value`

---

## Immediate design implication
The `0.2.0` loader **must not assume a single uniform record schema**.

Instead, it should:
- parse a common core record,
- preserve optional fields,
- and explicitly track task eligibility.

---

## Recommended internal task model
The harness should normalize each dataset item into a structured task object.

Recommended normalized object:

- `task_id: str`
- `instruction: str`
- `instruction_type: str`
- `spreadsheet_rel_path: str`
- `spreadsheet_dir: Path`
- `initial_workbook_path: Path`
- `golden_workbook_path: Path`
- `prompt_path: Path | None`
- `answer_spec: RegionSpecSet`
- `answer_sheet: str | None`
- `data_spec: RegionSpecSet | None`
- `exclude_reason: str | None`
- `is_excluded: bool`
- `raw_record: dict`

### Why normalize this way
This gives us:
- a stable in-memory representation for all tasks
- a place to preserve raw dataset information without lossy conversion
- a way to filter excluded tasks cleanly
- a path to benchmark split construction and validation

---

## Workbook directory layout
Each task points to a relative directory under:

- `spreadsheet/<task_id>/`

Typical directory contents:
- one initial workbook
- one golden workbook
- `prompt.txt`

### Common naming pattern
For most tasks:
- `1_<task_id>_init.xlsx`
- `1_<task_id>_golden.xlsx`
- `prompt.txt`

### Alternate naming pattern
For 5 tasks, files are named:
- `initial.xlsx`
- `golden.xlsx`
- `prompt.txt`

The 5 observed task IDs were:
- `13284`
- `32023`
- `32789`
- `56274`
- `58109`

---

## Immediate workbook discovery requirement
The `0.2.0` loader **must support both workbook naming schemes**.

Recommended discovery logic:
1. check for `*init.xlsx`
2. if none found, check for `initial.xlsx`
3. check for `*golden.xlsx`
4. if none found, check for `golden.xlsx`
5. require exactly one initial workbook and one golden workbook after resolution

If not exactly one of each exists:
- treat as load error
- unless future dataset-specific rules are introduced explicitly

---

## Prompt file handling
Each inspected task directory contains `prompt.txt`.

Recommended behavior:
- load it if present
- preserve it as an auxiliary artifact
- do not require it to be the sole instruction source

Why:
- `dataset.json` already includes `instruction`
- `prompt.txt` may be useful as a source-aligned copy, debugging artifact, or alternate field
- but the harness should not break if the two differ slightly in formatting in future versions

---

## Instruction type distribution
Observed values:
- `Cell-Level Manipulation`: **275** tasks
- `Sheet-Level Manipulation`: **125** tasks

---

## Immediate design implication for `instruction_type`
The task loader should preserve `instruction_type` as a first-class field.

It should likely be used for:
- split stratification
- selector state metadata
- error analysis
- later compatibility features

At minimum, `0.2.0` should avoid discarding it.

---

## Region field complexity
One of the most important findings is that `answer_position` and `data_position` are not simple uniform Excel ranges.

### `answer_position` type counts
Across all 400 tasks:
- `plain_range`: **243**
- `sheet_qualified`: **148**
- `multi_region`: **9**

### `data_position` type counts
Across the 125 tasks that contain `data_position`:
- `plain_range`: **81**
- `sheet_qualified`: **2**
- `multi_region`: **42**

So `0.2.0` must support:
- plain ranges
- sheet-qualified ranges
- multiple ranges in a single string

---

## Examples of region complexity
Examples found in `answer_position`:
- `A3:D32`
- `'data'!O3`
- `D9:D12`
- `OUT CAS'!A2:C1529,'OUT CAS'!E2:G586,'OUT CAS'!I2:K13,'OUT CAS'!L2:O8`
- `G4:G6, G11:G13, G20:G22`
- `D1,D5,D9`

Examples found in `data_position`:
- `A1:E56`
- `sheet1!A1:j24',',ورق1!B1:B11'`
- `'Consolidated Tracker!A1:E11','Existing Task!A2:E9','Additions!A2:E6','Retired!A2:E4'`
- `Source!A1:B8','Source2!A1:B8','Result!A1:B8'`

These examples show that:
- quoting is inconsistent
- some sheet names include spaces
- some fields contain multiple sheet-qualified regions
- some comma-separated values are separate cells, not contiguous ranges
- some strings appear malformed but still encode multiple valid region references

---

## Critical parser requirement
The harness should **not** treat region fields as plain strings or simple Excel A1 ranges.

Instead, `0.2.0` should introduce a dedicated normalization/parsing layer.

Recommended abstraction:

### `RegionSpec`
A normalized single region reference, e.g.:
- `sheet_name: str | None`
- `start_cell: str`
- `end_cell: str | None`
- `raw_text: str`

### `RegionSpecSet`
A collection of one or more `RegionSpec` objects, preserving original order.

This should support:
- single-cell references
- contiguous ranges
- multiple ranges
- sheet-qualified references
- malformed-but-recoverable input strings after normalization

---

## Strong recommendation on parsing strategy
Use a **two-stage parse**.

### Stage 1: raw normalization
Normalize common formatting noise, such as:
- inconsistent quoting
- stray unmatched apostrophes
- case normalization of columns if helpful
- comma-separated region splitting while preserving sheet-qualified tokens
- trimming whitespace

### Stage 2: structured parsing
Convert normalized pieces into `RegionSpec` objects.

### Important rule
The loader should preserve the original raw string even after normalization.

Why:
- for debugging
- for error reporting
- for future parser refinement

---

## Treatment of excluded tasks
Two tasks currently include an `exclude` field.

This means `0.2.0` should support exclusion metadata in the dataset layer.

Recommended behavior:
- parse `exclude` into `exclude_reason`
- set `is_excluded = True`
- default benchmark split builders should exclude such tasks unless explicitly requested otherwise

This is better than deleting or silently skipping them because:
- the exclusion is part of the dataset truth
- we may later want to analyze exclusion reasons
- reproducibility is improved if exclusions are explicit

---

## Recommended loader validation checks
When loading tasks, validate the following:

### Required field checks
- `id` exists
- `instruction` exists
- `spreadsheet_path` exists
- `instruction_type` exists
- `answer_position` exists

### Path checks
- spreadsheet directory exists
- initial workbook resolves uniquely
- golden workbook resolves uniquely
- `prompt.txt` exists or is explicitly marked missing

### Region parse checks
- `answer_position` can be parsed into one or more `RegionSpec`
- if present, `data_position` can be parsed into one or more `RegionSpec`

### Exclusion checks
- if `exclude` exists, preserve it
- do not silently treat excluded tasks as normal tasks

### Metadata checks
- preserve any unknown fields rather than dropping them

---

## Recommended split construction policy
`0.2.0` should support explicit split files eventually, but until those exist, the loader layer should be compatible with deterministic split generation.

### Split builder inputs should be able to use:
- `instruction_type`
- task ID
- exclusion flag
- optional hash of task ID for deterministic partitioning

### Strong recommendation
Do not hard-code positional splits like `0:200` in the core dataset layer.

That behavior belongs in:
- an experiment config
- or a split-generation module

This is important because `0.2.0` should support:
- `train`
- `val`
- `anchor`
- `test`

with more explicit split semantics than `v1_env`.

---

## What the evaluator should assume about the data
At the dataset-interface layer, the evaluator should assume:
- it receives a normalized task object
- it receives a candidate workbook path
- it receives the golden workbook path
- it receives a parsed answer region set
- it may optionally receive parsed data-region metadata

It should **not** have to know:
- how workbook file discovery worked
- how raw region strings were normalized
- how exclusions were decided

That separation will keep the evaluator cleaner and easier to test.

---

## What the executor should assume about the data
At the dataset-interface layer, the executor/agent should assume:
- it receives a task object with instruction text
- it receives an initial workbook path
- it receives enough metadata to know the intended target region and task type if needed

The executor should not need to parse `dataset.json` directly.

---

## Suggested code-facing interface boundary
Recommended `0.2.0` dataset-layer interfaces:

### `load_dataset(root: Path) -> list[SpreadsheetTask]`
Loads and validates the dataset root.

### `load_task(root: Path, raw_record: dict) -> SpreadsheetTask`
Normalizes one raw dataset record.

### `discover_workbooks(task_dir: Path) -> WorkbookPair`
Resolves initial/golden workbook files.

### `parse_region_spec(raw: str) -> RegionSpecSet`
Parses `answer_position` or `data_position`.

### `build_splits(tasks: list[SpreadsheetTask], split_config: ...) -> BenchmarkSplits`
Builds deterministic train/val/anchor/test sets.

---

## Suggested first internal data classes

### `SpreadsheetTask`
Fields:
- `task_id: str`
- `instruction: str`
- `instruction_type: str`
- `spreadsheet_dir: Path`
- `initial_workbook_path: Path`
- `golden_workbook_path: Path`
- `prompt_path: Path | None`
- `answer_spec: RegionSpecSet`
- `answer_sheet: str | None`
- `data_spec: RegionSpecSet | None`
- `exclude_reason: str | None`
- `is_excluded: bool`
- `raw_record: dict`

### `WorkbookPair`
Fields:
- `initial_workbook_path: Path`
- `golden_workbook_path: Path`

### `RegionSpec`
Fields:
- `sheet_name: str | None`
- `start_cell: str`
- `end_cell: str | None`
- `raw_text: str`

### `RegionSpecSet`
Fields:
- `regions: list[RegionSpec]`
- `raw_text: str`

### `BenchmarkSplits`
Fields:
- `train: list[SpreadsheetTask]`
- `val: list[SpreadsheetTask]`
- `anchor: list[SpreadsheetTask]`
- `test: list[SpreadsheetTask]`

---

## Immediate implications for TDD
Since we are under strict TDD, the first data-layer tests should target behavior, not missing names.

That means the first Red tests should likely check things like:
- loading `dataset.json` returns 400 tasks
- workbook discovery resolves both standard and alternate naming patterns
- excluded tasks are recognized and marked excluded
- plain, sheet-qualified, and multi-region strings parse into normalized region specs
- malformed-but-observed strings are normalized into parseable forms

These are good Red tests because:
- the target functionality clearly exists conceptually
- the code can be scaffolded enough to run
- failures will be about incorrect behavior, not missing symbols

---

## Practical recommendation for the next build step
The first `0.2.0` implementation slice should be:

1. dataset root abstraction
2. `SpreadsheetTask` normalization
3. workbook discovery
4. region parsing
5. split construction
6. tests covering all observed schema variants and region edge cases

This is the cleanest next step because every later system component depends on it:
- evaluator
- executor
- trace layer
- proposer
- selector state
- reward computation

---

## Summary
The real dataset is more irregular than the earlier prototype data.

The main takeaways are:
- schema is mostly regular, but not uniform
- workbook naming has two patterns
- exclusion metadata exists
- region strings are a serious parsing problem and need a dedicated abstraction
- task typing is useful and should be preserved

So `0.2.0` should begin with a robust data layer, not direct ad hoc access to raw JSON and workbook folders.

That will give the rest of the harness a stable foundation.
