# Data Setup

## Benchmark data
The current benchmark data target is:

- `data/spreadsheetbench_verified/spreadsheetbench_verified_400/`

This is the `SpreadsheetBench Verified 400` subset shipped in the public `Trace2Skill` repository and used in that paper's spreadsheet reproduction flow.

## Why `data/` is ignored
Benchmark data is not committed to the repo by default.

Reasons:
- it keeps the repository lighter
- it avoids duplicating third-party benchmark files in git history
- it makes provenance clearer
- it allows the data source to be refreshed reproducibly

## How to fetch the dataset
From the project root:

```bash
uv run skill_research_fetch_data
```

This downloads the public `Trace2Skill` source archive, extracts only the `SpreadsheetBench Verified 400` dataset subtree, and installs it into the canonical local path under `data/`.

### Force a refresh
```bash
uv run skill_research_fetch_data --force
```

## Expected local files
At minimum, after a successful download, this file should exist:

- `data/spreadsheetbench_verified/spreadsheetbench_verified_400/dataset.json`

The dataset directory also contains:
- per-task spreadsheet folders
- `*_init.xlsx` workbooks
- `*_golden.xlsx` workbooks
- `prompt.txt`
