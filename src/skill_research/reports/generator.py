"""Generates report tables and figures from run artifacts."""

from __future__ import annotations

from collections import defaultdict
import csv
from pathlib import Path
from textwrap import fill
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from skill_research.reports.loader import ReportRows, load_report_rows

TABLE_NAMES = ["selector_final_summary"]
FIGURE_NAMES = ["cumulative_reward_curve", "round_reward_curve", "final_test_failure_modes"]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    extra = sorted({key for row in rows for key in row} - set(fields))
    fields.extend(extra)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _final_reward_by_selector(rows: ReportRows) -> dict[str, list[float]]:
    latest = {}
    for row in rows.per_round_rewards:
        latest[(row["selector"], row["seed"])] = float(row["cumulative_reward"])
    grouped: dict[str, list[float]] = defaultdict(list)
    for (selector, _seed), value in latest.items():
        grouped[str(selector)].append(value)
    return grouped


def _histogram(row: dict[str, Any]) -> dict[str, float]:
    histogram = row.get("failure_histogram", {})
    return histogram if isinstance(histogram, dict) else {}


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    mean = sum(values) / len(values)
    return (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5


def _reward_series(rows: ReportRows) -> dict[str, dict[str, list[float]]]:
    series: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows.per_round_rewards:
        series[str(row["selector"])][str(row["seed"])].append(float(row["cumulative_reward"]))
    return series


def _selector_final_summary_rows(rows: ReportRows) -> list[dict[str, Any]]:
    reward_series = _reward_series(rows)
    rewards = {selector: [values[-1] for values in by_seed.values() if values] for selector, by_seed in reward_series.items()}
    aucs = {selector: [sum(values) for values in by_seed.values() if values] for selector, by_seed in reward_series.items()}
    test_by_selector: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows.final_test_scores:
        test_by_selector[str(row["selector"])].append(row)
    noop_by_seed = {seed: values[-1] for seed, values in reward_series.get("noop", {}).items() if values}
    random_by_seed = {seed: values[-1] for seed, values in reward_series.get("random", {}).items() if values}
    output = []
    for selector in sorted(set(rewards) | set(test_by_selector)):
        reward_values = rewards.get(selector, [])
        auc_values = aucs.get(selector, [])
        by_seed = reward_series.get(selector, {})
        test_rows = test_by_selector.get(selector, [])
        test_scores = [float(row.get("avg_score", 0.0)) for row in test_rows]
        pass_rates = [float(row.get("pass_rate", 0.0)) for row in test_rows]
        failure_totals: dict[str, int] = defaultdict(int)
        for row in test_rows:
            for failure_type, count in _histogram(row).items():
                failure_totals[f"{failure_type}_total"] += int(count)
        delta_noop = [values[-1] - noop_by_seed[seed] for seed, values in by_seed.items() if values and seed in noop_by_seed]
        delta_random = [values[-1] - random_by_seed[seed] for seed, values in by_seed.items() if values and seed in random_by_seed]
        summary = {
            "selector": selector,
            "seeds": len(set(str(row.get("seed")) for row in test_rows)) or len(reward_values),
            "final_cumulative_reward_mean": _mean(reward_values),
            "final_cumulative_reward_std": _std(reward_values),
            "final_cumulative_reward_min": min(reward_values) if reward_values else None,
            "final_cumulative_reward_max": max(reward_values) if reward_values else None,
            "cumulative_reward_auc_mean": _mean(auc_values),
            "cumulative_reward_auc_std": _std(auc_values),
            "delta_vs_noop_final_reward_mean": _mean(delta_noop),
            "delta_vs_noop_final_reward_std": _std(delta_noop),
            "delta_vs_random_final_reward_mean": _mean(delta_random),
            "delta_vs_random_final_reward_std": _std(delta_random),
            "final_test_avg_score_mean": _mean(test_scores),
            "final_test_avg_score_std": _std(test_scores),
            "final_test_pass_rate_mean": _mean(pass_rates),
            "final_test_pass_rate_std": _std(pass_rates),
        }
        summary.update(dict(sorted(failure_totals.items())))
        output.append(summary)
    return output


def _selector_summary(rows: ReportRows) -> list[str]:
    lines = ["# Experiment Report", ""]
    summary_rows = _selector_final_summary_rows(rows)
    lines.append("## Final Selector Summary")
    lines.append("")
    lines.append("| selector | seeds | final reward mean±std | AUC mean±std | final test avg score mean±std | final test pass rate mean±std |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for row in summary_rows:
        lines.append(
            f"| {row['selector']} | {row['seeds']} | "
            f"{_format_number(row['final_cumulative_reward_mean'])}±{_format_number(row['final_cumulative_reward_std'])} | "
            f"{_format_number(row['cumulative_reward_auc_mean'])}±{_format_number(row['cumulative_reward_auc_std'])} | "
            f"{_format_number(row['final_test_avg_score_mean'])}±{_format_number(row['final_test_avg_score_std'])} | "
            f"{_format_number(row['final_test_pass_rate_mean'])}±{_format_number(row['final_test_pass_rate_std'])} |"
        )
    lines.append("")
    lines.append("## Generated Final-Test Table")
    lines.append("")
    for name in TABLE_NAMES:
        lines.append(f"- `tables/{name}.csv`")
    lines.append("")
    lines.append("## Generated Final-Test Table Image")
    lines.append("")
    for name in TABLE_NAMES:
        lines.append(f"- `table_pngs/{name}.png`")
    lines.append("")
    lines.append("## Generated Figures")
    lines.append("")
    for name in FIGURE_NAMES:
        lines.append(f"- `figures/{name}.png`")
    lines.append("")
    return lines


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _format_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _plot_reward_curve(rows: list[dict[str, Any]], value_key: str, ylabel: str, path: Path) -> None:
    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row["selector"])][int(row["round"])].append(float(row[value_key]))
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5.5))
    for selector, by_round in sorted(grouped.items()):
        rounds = sorted(by_round)
        means = [sum(by_round[round_index]) / len(by_round[round_index]) for round_index in rounds]
        stds = [_std(by_round[round_index]) or 0.0 for round_index in rounds]
        lows = [mean - std for mean, std in zip(means, stds)]
        highs = [mean + std for mean, std in zip(means, stds)]
        plt.plot(rounds, means, marker="o", linewidth=2, label=selector)
        if any(std > 0 for std in stds):
            plt.fill_between(rounds, lows, highs, alpha=0.18)
    plt.axhline(0, color="#666666", linewidth=0.8, linestyle="--")
    plt.xlabel("Round")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} (mean ± std across seeds)")
    if grouped:
        plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def _plot_final_test_failure_modes(summary_rows: list[dict[str, Any]], path: Path) -> None:
    modes = sorted({key.removesuffix("_total") for row in summary_rows for key in row if key.endswith("_total")})
    labels = [str(row["selector"]) for row in summary_rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(max(8, len(labels) * 1.2), 5))
    bottoms = [0.0] * len(labels)
    for mode in modes:
        values = [float(row.get(f"{mode}_total", 0.0)) for row in summary_rows]
        plt.bar(labels, values, bottom=bottoms, label=mode)
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
    plt.ylabel("Final Test Count")
    plt.title("Final Test Failure Modes")
    if modes:
        plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def _write_figures(rows: ReportRows, output_dir: Path, summary_rows: list[dict[str, Any]]) -> None:
    figure_dir = output_dir / "figures"
    _plot_reward_curve(rows.per_round_rewards, "cumulative_reward", "Cumulative Reward", figure_dir / "cumulative_reward_curve.png")
    _plot_reward_curve(rows.per_round_rewards, "round_reward", "Round Reward", figure_dir / "round_reward_curve.png")
    _plot_final_test_failure_modes(summary_rows, figure_dir / "final_test_failure_modes.png")


def _format_cell(value: Any, wrap_width: int = 32) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return fill(str(value), width=wrap_width, break_long_words=False, break_on_hyphens=False)


def _column_widths(fields: list[str], rows: list[dict[str, Any]]) -> list[float]:
    widths = []
    for field in fields:
        max_len = len(field)
        for row in rows:
            max_len = max(max_len, min(40, len(str(row.get(field, "")))))
        widths.append(max(1.2, min(4.5, max_len * 0.13)))
    return widths


def _render_table_png(rows: list[dict[str, Any]], title: str, path: Path, max_rows: int = 35) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.axis("off")
        ax.set_title(title, fontsize=14, weight="bold")
        ax.text(0.5, 0.5, "No final test rows", ha="center", va="center", fontsize=12)
        fig.tight_layout()
        fig.savefig(path, dpi=220)
        plt.close(fig)
        return
    fields = list(rows[0].keys())
    extra = sorted({key for row in rows for key in row} - set(fields))
    fields.extend(extra)
    display_rows = rows[:max_rows]
    table_data = [[_format_cell(row.get(field)) for field in fields] for row in display_rows]
    col_widths = _column_widths(fields, display_rows)
    width = max(12, sum(col_widths) + 1.5)
    height = max(3, (len(display_rows) + 2.5) * 0.55)
    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis("off")
    ax.set_title(title, fontsize=16, weight="bold", pad=18)
    table = ax.table(cellText=table_data, colLabels=fields, colWidths=[width / sum(col_widths) for width in col_widths], loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.55)
    for (row_index, _col_index), cell in table.get_celld().items():
        cell.set_edgecolor("#d0d0d0")
        if row_index == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#345995")
        elif row_index % 2 == 0:
            cell.set_facecolor("#f5f7fb")
        else:
            cell.set_facecolor("white")
    if len(rows) > max_rows:
        ax.text(0.5, 0.01, f"Showing first {max_rows} of {len(rows)} rows", ha="center", va="bottom", transform=ax.transAxes, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _write_table_pngs(output_dir: Path, summary_rows: list[dict[str, Any]]) -> None:
    _render_table_png(summary_rows, "Selector Final Summary", output_dir / "table_pngs" / "selector_final_summary.png")


def generate_report(run_root: Path, output_dir: Path) -> ReportRows:
    rows = load_report_rows(run_root)
    summary_rows = _selector_final_summary_rows(rows)
    table_dir = output_dir / "tables"
    _write_csv(table_dir / "selector_final_summary.csv", summary_rows)
    _write_figures(rows, output_dir, summary_rows)
    _write_table_pngs(output_dir, summary_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.md").write_text("\n".join(_selector_summary(rows)), encoding="utf-8")
    return rows
