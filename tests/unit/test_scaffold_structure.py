from pathlib import Path

EXPECTED_FILES = [
    "src/skill_research/core/types.py",
    "src/skill_research/core/protocols.py",
    "src/skill_research/core/registry.py",
    "src/skill_research/core/serialization.py",
    "src/skill_research/config/experiment.py",
    "src/skill_research/config/loader.py",
    "src/skill_research/datasets/base.py",
    "src/skill_research/datasets/spreadsheetbench_verified.py",
    "src/skill_research/executors/base.py",
    "src/skill_research/executors/spreadsheet_python.py",
    "src/skill_research/evaluators/base.py",
    "src/skill_research/evaluators/spreadsheet.py",
    "src/skill_research/traces/types.py",
    "src/skill_research/traces/store.py",
    "src/skill_research/skills/summary.py",
    "src/skill_research/skills/versioning.py",
    "src/skill_research/patches/types.py",
    "src/skill_research/patches/proposers/base.py",
    "src/skill_research/patches/proposers/openai_trace.py",
    "src/skill_research/patches/proposers/replay.py",
    "src/skill_research/patches/appliers/base.py",
    "src/skill_research/patches/appliers/skill_directory.py",
    "src/skill_research/state/types.py",
    "src/skill_research/state/builders/base.py",
    "src/skill_research/state/builders/default.py",
    "src/skill_research/rewards/base.py",
    "src/skill_research/rewards/score_delta.py",
    "src/skill_research/rewards/bloat_regression.py",
    "src/skill_research/selectors/base.py",
    "src/skill_research/selectors/noop.py",
    "src/skill_research/selectors/random_selector.py",
    "src/skill_research/selectors/support_count.py",
    "src/skill_research/selectors/smallest_patch.py",
    "src/skill_research/artifacts/store.py",
    "src/skill_research/experiments/episode.py",
    "src/skill_research/experiments/multi_round.py",
    "src/skill_research/experiments/comparison.py",
    "src/skill_research/cli/run_benchmark.py",
    "src/skill_research/cli/run_experiment.py",
    "src/skill_research/cli/score_patch_pool.py",
]


def test_exact_harness_scaffold_files_exist():
    missing = [path for path in EXPECTED_FILES if not Path(path).is_file()]
    assert missing == []
