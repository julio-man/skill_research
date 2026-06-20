from __future__ import annotations

import argparse
from pathlib import Path

from skill_research.datasets.spreadsheetbench_verified import build_splits, load_dataset
from skill_research.evaluation.spreadsheet import SpreadsheetTaskEvaluator
from skill_research.llm.client import build_llm_client, resolve_llm_config
from skill_research.runner.benchmark import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SpreadsheetBench Verified benchmark with the current 0.2.0 harness.")
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--split", choices=["train", "val", "test"], default="test")
    parser.add_argument("--train-size", type=int, default=200)
    parser.add_argument("--val-size", type=int, default=100)
    parser.add_argument("--test-size", type=int, default=95)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2500)
    args = parser.parse_args()

    tasks = load_dataset(Path(args.dataset_root))
    splits = build_splits(tasks, train_size=args.train_size, val_size=args.val_size, test_size=args.test_size, seed=args.seed)
    selected_tasks = getattr(splits, args.split)

    config = resolve_llm_config(provider=args.provider, model=args.model, api_key=args.api_key, base_url=args.base_url)
    llm_client = build_llm_client(config)
    evaluator = SpreadsheetTaskEvaluator()

    payload = run_benchmark(
        tasks=selected_tasks,
        skill_path=Path(args.skill_path),
        output_dir=Path(args.output_dir),
        llm_client=llm_client,
        evaluator=evaluator,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    print(payload["summary"])


if __name__ == "__main__":
    main()
