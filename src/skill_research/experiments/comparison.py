"""Multi-selector experiment loop and artifact writer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import inspect
import shutil

from skill_research.artifacts.store import JsonArtifactStore
from skill_research.core.serialization import to_json_file, to_json_safe
from skill_research.experiments.episode import EpisodeResult
from skill_research.experiments.multi_round import MultiRoundResult
from skill_research.traces.store import save_traces


@dataclass(frozen=True)
class ComparisonResult:
    selector_runs: dict[str, dict[str, MultiRoundResult]]


def _summary(result):
    return result["summary"] if isinstance(result, dict) else result.summary


def _traces(result):
    return result.get("traces", []) if isinstance(result, dict) else result.traces


def _copy_skill(skill, target_dir: Path) -> None:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    if skill.path.is_dir():
        shutil.copytree(skill.path, target_dir)
    elif skill.path.is_file():
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill.path, target_dir / skill.path.name)
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "SKILL.md").write_text("", encoding="utf-8")


def _write_eval_artifacts(result, target_dir: Path) -> None:
    to_json_file(_summary(result), target_dir / "evaluation_summary.json")
    save_traces(_traces(result), target_dir / "task_traces.json")


def _copy_eval_artifacts(source_dir: Path, target_dir: Path, result) -> None:
    if source_dir.resolve() != target_dir.resolve():
        if target_dir.exists():
            shutil.rmtree(target_dir)
        if source_dir.exists():
            shutil.copytree(source_dir, target_dir)
    _write_eval_artifacts(result, target_dir)


def _clean_patch_pool_metadata(patch_pool):
    metadata = dict(patch_pool.metadata)
    metadata.pop("raw_response", None)
    return type(patch_pool)(patch_pool.patches, metadata=metadata, schema_version=patch_pool.schema_version)


def _write_episode_artifact(round_dir: Path, selector_name: str, seed: int, round_index: int, result: EpisodeResult) -> None:
    selected_patch = None
    if result.selected_patch is not None:
        selected_patch = to_json_safe(result.selected_patch)
        selected_patch["selector"] = selector_name
    reward = to_json_safe(result.reward)
    reward["function"] = getattr(result.reward, "metadata", {}).get("function", "score_delta")
    payload = {
        "selector": selector_name,
        "seed": seed,
        "round": round_index,
        "input_skill": "input_skill",
        "current_skill_eval": {
            "summary_path": "current_skill_eval/evaluation_summary.json",
            "traces_path": "current_skill_eval/task_traces.json",
        },
        "patch_proposal": {"patch_pool_path": "patch_proposal/patch_pool.json"},
        "selection": {"decision_path": "selection/decision.json"},
        "selected_patch": selected_patch,
        "selected_skill": "selected_skill",
        "selected_skill_eval": {
            "summary_path": "selected_skill_eval/evaluation_summary.json",
            "traces_path": "selected_skill_eval/task_traces.json",
        },
        "reward": reward,
    }
    to_json_file(payload, round_dir / "episode.json")


def _run_selector_episode_from_shared(selector_name: str, seed: int, round_index: int, episode, skill, current_eval, current_eval_dir: Path, patch_pool, output_dir: Path) -> EpisodeResult:
    round_dir = output_dir / "selectors" / selector_name / f"seed_{seed:03d}" / f"round_{round_index:03d}"
    round_dir.mkdir(parents=True, exist_ok=True)
    _copy_skill(skill, round_dir / "input_skill")
    _copy_eval_artifacts(current_eval_dir, round_dir / "current_skill_eval", current_eval)
    clean_patch_pool = _clean_patch_pool_metadata(patch_pool)
    to_json_file(clean_patch_pool, round_dir / "patch_proposal" / "patch_pool.json")
    selector_state = {"round": round_index, "current_summary": _summary(current_eval), "current_traces": _traces(current_eval)}
    if getattr(episode, "validation_benchmark", None) is not None:
        validation_scores = {}
        for patch in clean_patch_pool.patches:
            validation_skill_dir = round_dir / "selector_validation" / patch.patch_id / "skill"
            application = episode.applier.apply(skill, patch, validation_skill_dir)
            validation_eval = episode.validation_benchmark.run(application.skill, round_dir / "selector_validation" / patch.patch_id)
            _write_eval_artifacts(validation_eval, round_dir / "selector_validation" / patch.patch_id)
            validation_scores[patch.patch_id] = _summary(validation_eval).avg_score
        selector_state["validation_scores"] = validation_scores
    decision = episode.selector.select(selector_state, clean_patch_pool)
    to_json_file(
        {
            "selector": selector_name,
            "action_index": decision.action_index,
            "patch_id": decision.patch_id if decision.patch is not None else None,
            "reason": decision.reason,
            "scores": decision.scores,
            "metadata": decision.metadata,
        },
        round_dir / "selection" / "decision.json",
    )
    if decision.patch is None:
        skill_after = skill
        _copy_skill(skill, round_dir / "selected_skill")
    else:
        selected_skill_dir = round_dir / "selected_skill"
        temp_skill_dir = round_dir / "_selected_skill_tmp"
        application = episode.applier.apply(skill, decision.patch, temp_skill_dir)
        _copy_skill(application.skill, selected_skill_dir)
        if temp_skill_dir.exists():
            shutil.rmtree(temp_skill_dir)
        skill_after = type(application.skill)(selected_skill_dir, selected_skill_dir.name)
    selected_eval = episode.benchmark.run(skill_after, round_dir / "selected_skill_eval")
    _write_eval_artifacts(selected_eval, round_dir / "selected_skill_eval")
    reward = episode.reward.compute(_summary(current_eval), _summary(selected_eval), context={})
    result = EpisodeResult(_summary(current_eval), _summary(selected_eval), decision.patch, reward, skill, skill_after, clean_patch_pool)
    _write_episode_artifact(round_dir, selector_name, seed, round_index, result)
    episode.selector.observe(result)
    return result


def _write_curve(output_dir: Path, selector_name: str, seed: int, episodes: list[EpisodeResult], cumulative_reward: list[float]) -> MultiRoundResult:
    run = MultiRoundResult(episodes, cumulative_reward)
    seed_dir = output_dir / "selectors" / selector_name / f"seed_{seed:03d}"
    round_rewards = [episode.reward.value for episode in episodes]
    to_json_file(
        {
            "selector": selector_name,
            "seed": seed,
            "round_rewards": round_rewards,
            "cumulative_reward": cumulative_reward,
            "rounds": [f"round_{index:03d}" for index in range(len(episodes))],
        },
        seed_dir / "selector_curve.json",
    )
    return run


def _make_episode(factory, store, seed: int):
    if "seed" in inspect.signature(factory).parameters:
        return factory(store, seed=seed)
    return factory(store)


def run_comparison(selector_episode_factories: dict[str, object], skill, output_dir: Path, rounds: int, seeds: list[int]) -> ComparisonResult:
    selector_runs: dict[str, dict[str, MultiRoundResult]] = {name: {} for name in selector_episode_factories}
    comparison_payload = {"selectors": {name: {"seeds": {}} for name in selector_episode_factories}}
    for seed in seeds:
        skills = {name: skill for name in selector_episode_factories}
        episodes_by_selector = {name: [] for name in selector_episode_factories}
        cumulative_by_selector = {name: [] for name in selector_episode_factories}
        totals = {name: 0.0 for name in selector_episode_factories}
        for round_index in range(rounds):
            current_skill_groups: dict[object, list[str]] = {}
            for selector_name, current_skill in skills.items():
                current_skill_groups.setdefault(current_skill, []).append(selector_name)
            for current_skill, selector_names in current_skill_groups.items():
                first_name = selector_names[0]
                first_round_dir = output_dir / "selectors" / first_name / f"seed_{seed:03d}" / f"round_{round_index:03d}"
                first_episode = _make_episode(selector_episode_factories[first_name], JsonArtifactStore(first_round_dir), seed)
                current_eval_dir = first_round_dir / "current_skill_eval"
                current_eval = first_episode.benchmark.run(current_skill, current_eval_dir)
                patch_pool = first_episode.proposer.propose(current_skill, _traces(current_eval), {})
                for selector_name in selector_names:
                    round_dir = output_dir / "selectors" / selector_name / f"seed_{seed:03d}" / f"round_{round_index:03d}"
                    episode = first_episode if selector_name == first_name else _make_episode(selector_episode_factories[selector_name], JsonArtifactStore(round_dir), seed)
                    result = _run_selector_episode_from_shared(selector_name, seed, round_index, episode, current_skill, current_eval, current_eval_dir, patch_pool, output_dir)
                    episodes_by_selector[selector_name].append(result)
                    skills[selector_name] = result.skill_after
                    totals[selector_name] = round(totals[selector_name] + result.reward.value, 10)
                    cumulative_by_selector[selector_name].append(totals[selector_name])
        for selector_name in selector_episode_factories:
            final_episode = _make_episode(selector_episode_factories[selector_name], JsonArtifactStore(output_dir / "selectors" / selector_name / f"seed_{seed:03d}"), seed)
            if getattr(final_episode, "test_benchmark", None) is not None:
                final_eval = final_episode.test_benchmark.run(skills[selector_name], output_dir / "selectors" / selector_name / f"seed_{seed:03d}" / "final_test_eval")
                _write_eval_artifacts(final_eval, output_dir / "selectors" / selector_name / f"seed_{seed:03d}" / "final_test_eval")
            run = _write_curve(output_dir, selector_name, seed, episodes_by_selector[selector_name], cumulative_by_selector[selector_name])
            selector_runs[selector_name][str(seed)] = run
            comparison_payload["selectors"][selector_name]["seeds"][str(seed)] = {
                "round_rewards": [episode.reward.value for episode in episodes_by_selector[selector_name]],
                "cumulative_reward": run.cumulative_reward,
            }
    JsonArtifactStore(output_dir).write("selector_comparison.json", comparison_payload)
    return ComparisonResult(selector_runs)
