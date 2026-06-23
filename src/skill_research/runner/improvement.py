from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import statistics

from skill_research.patches.types import Patch
from skill_research.traces import TraceRecord


@dataclass
class ImprovementResult:
    before_summary: dict
    after_summary: dict
    selected_patch: Patch
    reward: float
    skill_before: str
    skill_after: str
    patch_pool: list[Patch]


@dataclass
class MultiRoundImprovementResult:
    history: list[ImprovementResult]
    final_skill_dir: str


@dataclass
class SelectorRunResult:
    selector_name: str
    history: list[ImprovementResult]
    final_skill_dir: str


@dataclass
class MultiSelectorImprovementResult:
    selector_runs: dict[str, SelectorRunResult]


@dataclass
class SelectorAggregateRoundStats:
    round_index: int
    seeds: list[int]
    reward_mean: float
    reward_std: float
    before_avg_score_mean: float
    before_avg_score_std: float
    after_avg_score_mean: float
    after_avg_score_std: float
    before_pass_rate_mean: float
    before_pass_rate_std: float
    after_pass_rate_mean: float
    after_pass_rate_std: float
    selected_patch_ids: dict[int, str]


@dataclass
class MultiSeedSelectorComparisonResult:
    per_seed_runs: dict[int, MultiSelectorImprovementResult]
    aggregate_by_selector: dict[str, list[SelectorAggregateRoundStats]]


def compute_score_delta_reward(before_summary: dict, after_summary: dict) -> float:
    return round(after_summary["avg_score"] - before_summary["avg_score"], 10)


def ensure_noop_patch(patches: list[Patch]) -> list[Patch]:
    if any(patch.operation == "no_op" or patch.patch_id == "noop" for patch in patches):
        return patches
    return patches + [
        Patch(
            patch_id="noop",
            patch_type="noop",
            target_file="SKILL.md",
            target_section=None,
            operation="no_op",
            content="",
            delta_tokens=0,
            support_count=0,
        )
    ]


def _coerce_trace_records(raw_traces: list[TraceRecord | dict]) -> list[TraceRecord]:
    return [trace if isinstance(trace, TraceRecord) else TraceRecord(**trace) for trace in raw_traces]


def _generate_patch_pool(*, skill_dir: Path, benchmark_payload: dict, proposer, proposer_llm_client, patch_count: int) -> tuple[dict, list[Patch]]:
    before_summary = benchmark_payload["summary"]
    traces_payload = benchmark_payload.get("traces", {})
    raw_traces = traces_payload.get("traces", [])
    trace_records = _coerce_trace_records(raw_traces)
    patch_pool = proposer.generate(
        skill_path=skill_dir,
        traces=trace_records,
        k=patch_count,
        llm_client=proposer_llm_client,
    )
    return before_summary, ensure_noop_patch(patch_pool)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 10)


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return round(statistics.stdev(values), 10)


def run_single_round_improvement(
    *,
    skill_dir: Path,
    workspace_dir: Path,
    benchmark_runner,
    proposer,
    selector,
    applier,
    reward_fn,
    proposer_llm_client=None,
    patch_count: int = 8,
    label: str = "round0",
):
    workspace_dir.mkdir(parents=True, exist_ok=True)

    baseline_dir = workspace_dir / "baseline"
    baseline_payload = benchmark_runner(skill_path=skill_dir, output_dir=baseline_dir)
    before_summary, patch_pool = _generate_patch_pool(
        skill_dir=skill_dir,
        benchmark_payload=baseline_payload,
        proposer=proposer,
        proposer_llm_client=proposer_llm_client,
        patch_count=patch_count,
    )

    selector_state = {
        "skill_path": str(skill_dir),
        "before_summary": before_summary,
    }
    selected_patch = selector.select(selector_state, patch_pool)

    improved_skill_dir = Path(applier.apply_patch(skill_dir, selected_patch, label=label))
    improved_dir = workspace_dir / "after"
    improved_payload = benchmark_runner(skill_path=improved_skill_dir, output_dir=improved_dir)
    after_summary = improved_payload["summary"]

    reward = reward_fn(before_summary=before_summary, after_summary=after_summary)

    return ImprovementResult(
        before_summary=before_summary,
        after_summary=after_summary,
        selected_patch=selected_patch,
        reward=reward,
        skill_before=str(skill_dir),
        skill_after=str(improved_skill_dir),
        patch_pool=patch_pool,
    )


def run_multi_round_improvement(
    *,
    skill_dir: Path,
    workspace_dir: Path,
    benchmark_runner,
    proposer,
    selector,
    applier,
    reward_fn,
    proposer_llm_client=None,
    patch_count: int = 8,
    rounds: int = 1,
):
    current_skill_dir = Path(skill_dir)
    history: list[ImprovementResult] = []

    for round_index in range(rounds):
        round_result = run_single_round_improvement(
            skill_dir=current_skill_dir,
            workspace_dir=workspace_dir / f"round_{round_index}",
            benchmark_runner=benchmark_runner,
            proposer=proposer,
            selector=selector,
            applier=applier,
            reward_fn=reward_fn,
            proposer_llm_client=proposer_llm_client,
            patch_count=patch_count,
            label=f"round{round_index}",
        )
        history.append(round_result)
        current_skill_dir = Path(round_result.skill_after)

    return MultiRoundImprovementResult(history=history, final_skill_dir=str(current_skill_dir))


def run_multi_selector_multi_round_improvement(
    *,
    skill_dir: Path,
    workspace_dir: Path,
    benchmark_runner,
    proposer,
    selectors: dict[str, object],
    applier,
    reward_fn,
    proposer_llm_client=None,
    patch_count: int = 8,
    rounds: int = 1,
):
    workspace_dir.mkdir(parents=True, exist_ok=True)

    current_skill_dirs = {selector_name: Path(skill_dir) for selector_name in selectors}
    histories: dict[str, list[ImprovementResult]] = {selector_name: [] for selector_name in selectors}

    for round_index in range(rounds):
        grouped_selector_names: dict[str, list[str]] = {}
        grouped_skill_dirs: dict[str, Path] = {}
        for selector_name, current_skill_dir in current_skill_dirs.items():
            skill_key = str(current_skill_dir)
            grouped_skill_dirs[skill_key] = current_skill_dir
            grouped_selector_names.setdefault(skill_key, []).append(selector_name)

        for group_index, (skill_key, selector_names) in enumerate(grouped_selector_names.items()):
            source_skill_dir = grouped_skill_dirs[skill_key]
            group_workspace_dir = workspace_dir / f"round_{round_index}" / f"source_{group_index}"
            baseline_payload = benchmark_runner(
                skill_path=source_skill_dir,
                output_dir=group_workspace_dir / "baseline",
            )
            before_summary, patch_pool = _generate_patch_pool(
                skill_dir=source_skill_dir,
                benchmark_payload=baseline_payload,
                proposer=proposer,
                proposer_llm_client=proposer_llm_client,
                patch_count=patch_count,
            )

            for selector_name in selector_names:
                selector = selectors[selector_name]
                selector_state = {
                    "skill_path": str(source_skill_dir),
                    "before_summary": before_summary,
                    "selector_name": selector_name,
                    "round_index": round_index,
                }
                selected_patch = selector.select(selector_state, patch_pool)
                improved_skill_dir = Path(
                    applier.apply_patch(
                        source_skill_dir,
                        selected_patch,
                        label=f"{selector_name}_round{round_index}",
                    )
                )
                improved_payload = benchmark_runner(
                    skill_path=improved_skill_dir,
                    output_dir=group_workspace_dir / selector_name / "after",
                )
                after_summary = improved_payload["summary"]
                reward = reward_fn(before_summary=before_summary, after_summary=after_summary)
                histories[selector_name].append(
                    ImprovementResult(
                        before_summary=before_summary,
                        after_summary=after_summary,
                        selected_patch=selected_patch,
                        reward=reward,
                        skill_before=str(source_skill_dir),
                        skill_after=str(improved_skill_dir),
                        patch_pool=patch_pool,
                    )
                )
                current_skill_dirs[selector_name] = improved_skill_dir

    selector_runs = {
        selector_name: SelectorRunResult(
            selector_name=selector_name,
            history=histories[selector_name],
            final_skill_dir=str(current_skill_dirs[selector_name]),
        )
        for selector_name in selectors
    }
    return MultiSelectorImprovementResult(selector_runs=selector_runs)


def _aggregate_selector_rounds(
    per_seed_runs: dict[int, MultiSelectorImprovementResult],
) -> dict[str, list[SelectorAggregateRoundStats]]:
    selector_names = next(iter(per_seed_runs.values())).selector_runs.keys() if per_seed_runs else []
    aggregate: dict[str, list[SelectorAggregateRoundStats]] = {}
    for selector_name in selector_names:
        round_count = len(next(iter(per_seed_runs.values())).selector_runs[selector_name].history)
        aggregate[selector_name] = []
        for round_index in range(round_count):
            seeds = sorted(per_seed_runs)
            round_results = [
                per_seed_runs[seed].selector_runs[selector_name].history[round_index]
                for seed in seeds
            ]
            aggregate[selector_name].append(
                SelectorAggregateRoundStats(
                    round_index=round_index,
                    seeds=seeds,
                    reward_mean=_mean([result.reward for result in round_results]),
                    reward_std=_std([result.reward for result in round_results]),
                    before_avg_score_mean=_mean([result.before_summary["avg_score"] for result in round_results]),
                    before_avg_score_std=_std([result.before_summary["avg_score"] for result in round_results]),
                    after_avg_score_mean=_mean([result.after_summary["avg_score"] for result in round_results]),
                    after_avg_score_std=_std([result.after_summary["avg_score"] for result in round_results]),
                    before_pass_rate_mean=_mean([result.before_summary["pass_rate"] for result in round_results]),
                    before_pass_rate_std=_std([result.before_summary["pass_rate"] for result in round_results]),
                    after_pass_rate_mean=_mean([result.after_summary["pass_rate"] for result in round_results]),
                    after_pass_rate_std=_std([result.after_summary["pass_rate"] for result in round_results]),
                    selected_patch_ids={seed: result.selected_patch.patch_id for seed, result in zip(seeds, round_results, strict=True)},
                )
            )
    return aggregate


def run_multi_seed_multi_selector_multi_round_improvement(
    *,
    skill_dir: Path,
    workspace_dir: Path,
    benchmark_runner_factory,
    proposer,
    selectors: dict[str, object],
    applier,
    reward_fn,
    seeds: list[int],
    proposer_llm_client=None,
    patch_count: int = 8,
    rounds: int = 1,
) -> MultiSeedSelectorComparisonResult:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    per_seed_runs: dict[int, MultiSelectorImprovementResult] = {}

    for seed in seeds:
        benchmark_runner = benchmark_runner_factory(seed)
        per_seed_runs[seed] = run_multi_selector_multi_round_improvement(
            skill_dir=skill_dir,
            workspace_dir=workspace_dir / f"seed_{seed}",
            benchmark_runner=benchmark_runner,
            proposer=proposer,
            selectors=selectors,
            applier=applier,
            reward_fn=reward_fn,
            proposer_llm_client=proposer_llm_client,
            patch_count=patch_count,
            rounds=rounds,
        )

    return MultiSeedSelectorComparisonResult(
        per_seed_runs=per_seed_runs,
        aggregate_by_selector=_aggregate_selector_rounds(per_seed_runs),
    )
