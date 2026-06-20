# `0.2.0` Alignment and Build Checklist

## Purpose
This document captures the current shared understanding of what `0.2.0` should be, based on:
- the paper review,
- the current Q1 research question,
- lessons from `legacy/v1_env`,
- and advisor feedback.

The goal is to prevent drift while we build.

This is a build-alignment document for the next implementation phase and is intended to keep implementation decisions pointed toward the final research system.

---

## The current research question

> Can we train an RL policy to select skill patches from execution traces, maximizing evaluation reward while avoiding regressions and bloat?

Important clarification:
- At this stage, we are committing to building the **environment/harness** needed to test RL, contextual bandits, and supervised alternatives.
- Whether RL, contextual bandits, or supervised selection is the strongest fit is an empirical question to be answered by experiments.
- The harness should therefore be designed so that all three can be compared cleanly under matched conditions.

---

## What `0.2.0` is

`0.2.0` should be a **clean, deterministic, modular patch-selection experiment harness**.

Its purpose is to support controlled experiments over the following loop, in a way that establishes a strong foundation for the final research system:
1. start from a current skill artifact,
2. evaluate that skill on a benchmark split,
3. generate a candidate patch pool,
4. let a selector choose one patch or `noop`,
5. apply the selected patch,
6. re-evaluate the resulting skill,
7. compute reward,
8. repeat for a fixed round budget,
9. compare selectors over repeated runs.

This is the minimum system that lets us answer the advisor’s immediate priority:
- build the environment,
- run experiments,
- compare selectors on full reward curves,
- then refine the formulation.

---

## What `0.2.0` is not

To stay aligned, `0.2.0` should avoid overreaching in ways that make the system harder to build, compare, and extend.

In particular, `0.2.0` should not begin by centering:
- a migration of `legacy/v1_env`
- a learned patch generator
- a combinatorial subset selector
- a broad multi-domain benchmark suite before the core harness is stable
- a maximally elaborate state/action/reward design before the basic loop is clean

Instead, `0.2.0` should be:
- a clean rebuild,
- informed by `v1_env` lessons,
- optimized for empirical clarity,
- and structured so later work can extend it cleanly toward the final research system.

---

## Why we are rebuilding instead of extending `v1_env`

`legacy/v1_env` was useful because it proved the end-to-end loop could exist.

It gave us evidence that the following capabilities are real and worth carrying forward conceptually:
- a real benchmark can be run,
- traces can be recorded,
- patches can be proposed,
- patches can be applied,
- reward can be computed,
- multi-round improvement can be run,
- selectors can be connected to the loop.

But it was still an earlier-stage reference implementation.

The point of `0.2.0` is to rebuild now that we know more clearly what the harness actually needs to support:
- deterministic execution,
- benchmark splits,
- selector comparison under matched conditions,
- replayable patch pools,
- better logging,
- richer reward options,
- and clearer module boundaries.

So `v1_env` should now be treated as:
- a source of ideas,
- a source of schemas and lessons,
- but **not** a codebase to lift directly.

---

## The core design principle

The main design principle for `0.2.0` is:

**Experimental usefulness over theoretical completeness.**

That means:
- we prefer a harness that is easy to compare methods in,
- over a more ambitious system with too many moving parts,
- especially if those moving parts make attribution harder.

In practice, this means:
- deterministic settings where possible,
- fixed selector comparison conditions,
- explicit artifact saving,
- and simple first versions of state/action/reward that can later be refined.

---

## The core unit of the environment

The atomic object in `0.2.0` should be a **patch-selection episode**.

A patch-selection episode should contain:
- a current skill `S_t`
- an evaluation snapshot of `S_t`
- a current candidate patch pool `P_t`
- a selector decision `a_t`
- an updated skill `S_{t+1}` after patch application
- an evaluation snapshot of `S_{t+1}`
- a computed reward `r_t`

This is the smallest unit that should be self-contained, saved, and analyzable.

Above that, the next unit is a **multi-round improvement run**:
- a sequence of patch-selection episodes over a fixed round budget.

Above that, the final experimental unit is a **selector comparison experiment**:
- multiple repeated multi-round runs across selectors and seeds.

---

## What `0.2.0` must do

At a minimum, `0.2.0` must support the following end-to-end procedure:

1. Load a benchmark/task split.
2. Load a seed skill directory.
3. Evaluate the current skill under deterministic executor settings.
4. Produce traces and a benchmark summary.
5. Generate a candidate patch pool from the current skill and traces.
6. Featurize the selector state from:
   - skill summary,
   - evaluation summary,
   - patch pool.
7. Run a selector over `P_t ∪ {noop}`.
8. Apply the selected patch deterministically.
9. Re-run evaluation under the exact same executor and benchmark conditions.
10. Compute reward.
11. Save all artifacts.
12. Repeat for the requested number of rounds.
13. Repeat for the requested number of run seeds.
14. Repeat for all requested selectors.
15. Aggregate results into selector-comparison outputs.

If the harness cannot do all of the above, then it is not yet meeting the `0.2.0` goal.

---

## Required inputs for `0.2.0`

Each experiment should be driven by a single explicit spec plus referenced assets.

### 1. Benchmark/task input
The harness should accept:
- task definitions
- deterministic verifiers
- benchmark split definitions
- optional task metadata and family labels

Required split conceptually:
- `train`
- `val`
- `anchor`
- `test`

We do not need every experiment to use every split immediately, but the harness should be designed with these splits in mind from the start.

### 2. Skill input
The harness should accept:
- a seed skill directory
- optionally a current skill version directory for resumed runs

### 3. Executor input
The harness should accept:
- task model / executor model name
- generation settings
- deterministic configuration
- tool/runtime limits

This must include:
- `temperature = 0`
- fixed seed if supported by the backend
- any additional settings needed to suppress unnecessary execution noise

### 4. Patch proposer input
The harness should accept:
- proposer type
- proposer model name/config
- patch pool size `K`
- proposer hyperparameters
- patch schema version

### 5. Selector input
The harness should accept:
- selector name
- selector hyperparameters
- selector seed

### 6. Reward input
The harness should accept:
- reward mode
- reward weights
- benchmark split used for reward
- whether anchor regressions are included
- whether bloat penalties are included

### 7. Experiment input
The harness should accept:
- number of rounds
- number of repeated runs
- list of seeds
- artifact output path
- run identifier / experiment identifier

---

## Required outputs for `0.2.0`

The harness must produce outputs at three levels:
- per-round
- per-run
- per-selector aggregate

### 1. Per-round outputs
For every round, save:
- `before_summary`
- `patch_pool`
- `selector_state`
- `selected_action`
- `selected_patch`
- `after_summary`
- `reward`
- `skill_version`
- traces
- verifier outputs
- executor stdout/stderr or equivalent
- metadata for reproducibility

At minimum the per-round outputs should make it possible to answer:
- what did the skill look like?
- how was it doing?
- what were the candidate patches?
- which one got selected?
- what happened after selection?
- what reward was assigned?

### 2. Per-run outputs
For every multi-round run, save:
- the ordered round history
- cumulative reward curve
- benchmark score curve
- pass-rate curve
- skill-size curve
- per-round selected patch IDs
- run config and run seed

### 3. Per-selector aggregate outputs
For every selector, save:
- mean cumulative reward over repeats
- standard deviation of cumulative reward
- mean final benchmark score
- standard deviation of final benchmark score
- mean reward per round
- optional area-under-curve summaries

### 4. Cross-selector comparison outputs
For a selector comparison experiment, save:
- one normalized summary table
- one reward-curve artifact across selectors
- one final-score comparison artifact across selectors
- enough metadata to prove conditions were matched

---

## Required benchmark split design

One of the clearest improvements over `v1_env` should be split design.

### The environment should support four conceptual splits

#### `train`
Used for:
- generating traces
- proposing patches
- optionally fitting supervised models
- optionally updating online bandit state

#### `val`
Used for:
- computing reward during improvement rounds
- comparing patches within runs
- driving selector learning/evaluation during development

This is the closest analogue to the draft’s `B_val`.

#### `anchor`
Used for:
- regression checks
- detecting whether patches break previously stable behavior

This is where regression penalties should come from when enabled.

#### `test`
Used for:
- held-out selector comparison
- final evaluation and reporting

### Why this matters
This split design lets us move beyond the `v1_env` simplification of “just evaluate on the full benchmark every round.”

It also directly supports the advisor’s point that questions like reward variance and selector value become concrete only once the environment is real.

---

## Determinism requirements

The advisor’s first concrete request was to turn off noise before comparing selectors.

So `0.2.0` must prioritize deterministic execution.

### Required deterministic behavior
- executor generation at `temperature = 0`
- fixed random seed where supported
- deterministic task ordering where applicable
- deterministic benchmark split loading
- deterministic patch application behavior
- deterministic result serialization

### Desired but optional if backend allows
- deterministic proposer behavior
- deterministic code execution environment
- reproducible tool ordering and file-system ordering

### Why this matters
Without determinism, variation may come from:
- executor sampling
- proposer randomness
- task ordering
- patch order instability
- file resolution nondeterminism

That makes selector comparisons weak and hard to interpret.

---

## Patch proposer requirements

At this stage, the patch proposer should be:
- fixed
- modular
- replaceable
- structured

### The proposer is not the experimental variable yet
The selector is the main object of comparison now.

So the proposer should be treated as infrastructure.

### The proposer should emit structured patch objects
Each patch should include at minimum:
- `patch_id`
- `patch_type`
- `target_file`
- `target_section`
- `operation`
- `content`
- `delta_tokens`
- `support_count`

Additional fields are acceptable if helpful, but these minimum fields should exist because they already connect naturally to the current research framing.

### Frozen/replayable patch pools
One of the most important improvements for `0.2.0` should be support for **replayable patch pools**.

That means the harness should support this workflow:
1. evaluate skill,
2. generate patch pool once,
3. save patch pool,
4. run multiple selectors against the same saved patch pool.

This matters because otherwise selector comparisons may be confounded by proposer variation.

### Strong recommendation
Patch-pool generation and selector replay should be separable stages in the harness.

---

## Required selector set for `0.2.0`

Per advisor feedback, `0.2.0` must compare all already implemented selector families conceptually, whether or not the implementation is fully new.

The required selector set is:
- `noop`
- `random`
- `support_count`
- `smallest_patch`
- `LinUCB`
- `supervised`

### Why each is required
#### `noop`
Tests whether patching at all helps.

#### `random`
Tests whether intelligent selection matters.

#### `support_count`
Tests whether a simple recurrence-based heuristic is already strong.
This is also motivated by `Trace2Skill`.

#### `smallest_patch`
Tests whether compactness bias alone is useful.
This is motivated by the skill bloat evidence.

#### `LinUCB`
Current contextual-bandit-style learned selector.
This is the immediate research-facing method.

#### `supervised`
Natural baseline if immediate rewards are informative enough.
This is explicitly advisor-endorsed and important even if it beats RL/bandits.

---

## Selector comparison protocol

This is one of the most important parts of `0.2.0`.

### The unit of evaluation is the full curve
We should not wait for the bandit to “finish exploring.”

Exploration is part of the algorithm.
Its cost must be measured.

Therefore, selectors should be compared by:
- cumulative reward over a fixed round budget
- and the full reward/improvement curve over rounds

### Required protocol
For every selector comparison experiment:
- same benchmark split
- same seed skill
- same executor settings
- same patch proposer settings
- same patch pools when replay is enabled
- same round budget
- same seed list
- same evaluation metrics
- only the selector changes

### Required repetitions
Each selector should be run:
- multiple times
- under matched seeds
- with mean and standard deviation reported

Advisor suggestion was roughly 5–10 repeats.
That should be treated as the target range.

---

## Success criteria for `0.2.0`

The harness should support explicit success criteria checks from the beginning.

A reasonable initial success criterion is:

- `LinUCB` significantly beats `random` and `noop` on mean cumulative reward under a fixed budget.

Other useful criteria:
- `LinUCB` mean final validation score exceeds `random`
- `supervised` exceeds `random` and `noop`
- `support_count` exceeds `noop`
- token growth remains bounded enough to interpret performance meaningfully

The exact thresholds may change later, but `0.2.0` should support defining them explicitly in experiment configs or evaluation scripts.

---

## State design requirements

The current RL draft and `v1_env` converge on the same basic structure.
`0.2.0` should keep that structure but make it cleaner and versioned.

### Required state groups

#### A. Current skill summary
Minimum fields:
- `skill_tokens_main`
- `skill_tokens_total`
- `num_files`
- `num_scripts`
- `num_references`

These fields expose skill size and structure without requiring semantic analysis.

#### B. Recent evaluation summary
Minimum fields:
- `pass_rate`
- `avg_score`
- failure histogram:
  - `n_wrong_answer`
  - `n_format_fail`
  - `n_tool_fail`
  - `n_timeout`
  - `n_other`

These fields expose how the current skill is failing.

#### C. Candidate patch features
Minimum fields per patch:
- `patch_type`
- `delta_tokens`
- `target_file`
- `target_section`
- `support_count`

These fields expose what each action currently means.

### Strong recommended additions
Because of lessons from the papers and advisor comments, `0.2.0` should make room for:
- compatibility/task-family features
- previous round reward
- recent reward trend
- last selected patch type
- anchor regression count

### What should not be required yet
Frozen LLM critic features are interesting but should not be required for `0.2.0`.
They add complexity before the basic comparison loop is stable.

---

## Action design requirements

For `0.2.0`, the action space should stay intentionally simple.

### Required action space
At each round:
- choose exactly one patch from the current patch pool
- or choose `noop`

Formally:
- `a_t ∈ {0, 1, ..., K}`
- `0` means `noop`
- `i` means select patch `p_i`

### Why this is the right first action space
- it keeps the setup interpretable
- it keeps causal attribution relatively clean
- it avoids immediate combinatorial explosion
- it aligns with the advisor’s environment-first recommendation

### What should be deferred
Subset selection should be deferred.
The literature strongly suggests it may matter eventually, but it is not the right first comparison problem.

---

## Reward design requirements

This is one of the most important places to move beyond `v1_env`.

### Reward Tier 1: minimal reward
The harness must support:
- `reward = after_score - before_score`

This is the minimum viable reward.

### Reward Tier 2: research reward
The harness should also support an extended reward:

`reward = Δval_score - λ * token_growth - μ * anchor_regressions`

where:
- `Δval_score` is change in validation score
- `token_growth` measures skill size increase
- `anchor_regressions` counts tasks in the anchor split that were previously passing and now fail
- `λ` and `μ` are configurable

### Why this matters
The papers strongly support the need to measure:
- performance improvement
- regressions
- bloat/context overhead

So `0.2.0` should support both the simple reward and the more realistic one, even if we begin experiments with the simpler version.

---

## Logging and artifact requirements

`0.2.0` should be built as if debugging and post-hoc analysis are first-class needs.

### Every run should be reconstructible
That means storing:
- run config
- random seed
- selector config
- executor config
- patch proposer config
- benchmark split spec
- skill version path
- patch pool
- selected action
- reward components

### Every round should be auditable
That means storing:
- raw traces
- verifier outputs
- generated code or execution artifacts if applicable
- patch application result
- before/after summaries

### Why this matters
The advisor explicitly expects important unanswered questions to emerge only after implementation.
Those questions can only be answered if the artifacts are rich enough to inspect.

---

## Domain scope expectations

`0.2.0` does **not** need to solve broad cross-domain generality yet.

But it should be designed so that the architecture does not hard-code itself irreversibly to spreadsheets.

### Good practical target
- benchmark implementation may start with spreadsheets again or another narrow domain,
- but the harness interfaces should remain generic enough for future domains.

That means using generic terms like:
- task
- trace
- patch
- selector state
- reward

instead of domain-specific assumptions embedded everywhere.

---

## Relationship to the research question

If `0.2.0` is built correctly, it should directly move us closer to the final research answer because it will let us answer questions such as:
- Is patch selection meaningful at all relative to `noop`?
- Does intelligent selection beat random?
- Is immediate reward stable enough for contextual bandits?
- Does supervised patch scoring outperform bandits?
- Are current patch pools diverse enough for selector learning to matter?
- Do reward penalties for regressions and bloat materially change selector behavior?

These are exactly the empirical questions the advisor says should come before more theoretical refinement.

---

## Final alignment summary

If we stay aligned, then by the end of `0.2.0` we should have:
- a clean rebuilt harness,
- deterministic enough execution,
- fixed benchmark split support,
- replayable patch pools,
- multiple selectors compared under identical conditions,
- repeated-run statistics,
- full cumulative reward curves,
- and enough artifacts to diagnose reward/state/action weaknesses.

That would mean `0.2.0` has succeeded even if:
- RL is not yet the winner,
- the reward still needs refinement,
- or the patch proposer still needs improvement.

Because the primary success criterion for this phase is not proving the final method.
It is building the environment that makes those questions answerable.

---

# Detailed Checklist

## A. Alignment and scope
- [ ] Confirm that `legacy/v1_env` is reference-only and will not be extended directly
- [ ] Confirm that `0.2.0` is a clean rebuild
- [ ] Confirm that selector comparison is the immediate experimental priority
- [ ] Confirm that RL is not assumed to be the final winner
- [ ] Confirm that supervised selection remains a first-class baseline
- [ ] Confirm that subset selection is out of scope for `0.2.0`

## B. Harness architecture
- [ ] Define the atomic patch-selection episode abstraction
- [ ] Define the multi-round improvement run abstraction
- [ ] Define the selector comparison experiment abstraction
- [ ] Separate proposer, selector, evaluator, reward, and artifact logging into distinct modules
- [ ] Ensure the harness is generic enough not to hard-code spreadsheet-specific assumptions everywhere

## C. Inputs and experiment spec
- [ ] Create a unified experiment spec format
- [ ] Include benchmark/task source references in the spec
- [ ] Include benchmark split references in the spec
- [ ] Include skill path references in the spec
- [ ] Include executor model/config in the spec
- [ ] Include patch proposer model/config in the spec
- [ ] Include selector config in the spec
- [ ] Include reward config in the spec
- [ ] Include round budget and repeat count in the spec
- [ ] Include seed list in the spec

## D. Benchmark split support
- [ ] Support `train` split
- [ ] Support `val` split
- [ ] Support `anchor` split
- [ ] Support `test` split
- [ ] Make split loading deterministic
- [ ] Ensure split metadata is saved with artifacts
- [ ] Ensure reward can be computed from `val`
- [ ] Ensure regressions can be computed from `anchor`
- [ ] Ensure final comparison can be reported on `test`

## E. Deterministic executor
- [ ] Set executor generation temperature to `0`
- [ ] Use a fixed seed if backend supports it
- [ ] Make task ordering deterministic
- [ ] Make evaluation ordering deterministic
- [ ] Make result serialization deterministic
- [ ] Make patch application deterministic
- [ ] Record all executor settings per run
- [ ] Verify repeatability by rerunning the same selector/seed combination and checking whether outputs are stable enough

## F. Evaluator and traces
- [ ] Implement a benchmark evaluator that produces a benchmark summary for the current skill
- [ ] Save per-task traces
- [ ] Save benchmark-level summaries
- [ ] Record pass/fail and task-level score
- [ ] Record executor outputs, stdout/stderr, and verifier outputs
- [ ] Ensure traces are sufficient for patch proposal and post-hoc analysis

## G. Patch proposer
- [ ] Implement a fixed patch proposer interface
- [ ] Ensure proposer emits structured patch objects
- [ ] Include `patch_id`
- [ ] Include `patch_type`
- [ ] Include `target_file`
- [ ] Include `target_section`
- [ ] Include `operation`
- [ ] Include `content`
- [ ] Include `delta_tokens`
- [ ] Include `support_count`
- [ ] Make proposer output savable and replayable
- [ ] Support generating a patch pool once and replaying it across selectors

## H. Skill versioning and patch application
- [ ] Create a deterministic patch application interface
- [ ] Support `noop`
- [ ] Support creating versioned skill outputs per round
- [ ] Save resulting skill directory path/version metadata
- [ ] Save patch application success/failure details

## I. State featurization
- [ ] Implement current-skill summary features
- [ ] Include `skill_tokens_main`
- [ ] Include `skill_tokens_total`
- [ ] Include `num_files`
- [ ] Include `num_scripts`
- [ ] Include `num_references`
- [ ] Implement evaluation summary features
- [ ] Include `pass_rate`
- [ ] Include `avg_score`
- [ ] Include `n_wrong_answer`
- [ ] Include `n_format_fail`
- [ ] Include `n_tool_fail`
- [ ] Include `n_timeout`
- [ ] Include `n_other`
- [ ] Implement candidate patch features
- [ ] Include `patch_type`
- [ ] Include `delta_tokens`
- [ ] Include `target_file`
- [ ] Include `target_section`
- [ ] Include `support_count`
- [ ] Version the state schema
- [ ] Save selector state per round

## J. Action space
- [ ] Implement single-patch selection
- [ ] Implement `noop`
- [ ] Ensure action IDs are tied to the current patch pool only
- [ ] Save selected action index and resolved patch ID separately
- [ ] Keep subset selection explicitly deferred for now

## K. Reward
- [ ] Implement simple reward: `after_score - before_score`
- [ ] Implement reward component logging
- [ ] Implement token growth measurement
- [ ] Implement anchor regression counting
- [ ] Implement extended reward with optional penalties
- [ ] Make `λ` configurable
- [ ] Make `μ` configurable
- [ ] Save raw reward components and final scalar reward separately
- [ ] Allow experiments to switch reward modes without code changes

## L. Required selectors
- [ ] Implement or port `noop`
- [ ] Implement or port `random`
- [ ] Implement or port `support_count`
- [ ] Implement or port `smallest_patch`
- [ ] Implement or port `LinUCB`
- [ ] Implement or port `supervised`
- [ ] Ensure all selectors conform to the same selector interface
- [ ] Ensure all selectors can operate on the same saved patch pool format

## M. Selector comparison protocol
- [ ] Ensure all selectors run under matched benchmark conditions
- [ ] Ensure all selectors use identical executor settings
- [ ] Ensure all selectors use identical proposer settings
- [ ] Ensure all selectors use identical patch pools when replay is enabled
- [ ] Ensure all selectors use identical round budgets
- [ ] Ensure all selectors use identical run seed schedules
- [ ] Evaluate selectors on full cumulative reward curves
- [ ] Do not exclude exploration rounds from comparison
- [ ] Treat exploration cost as part of selector quality

## N. Repeated-run evaluation
- [ ] Support repeated runs per selector
- [ ] Support 5–10 repeat target range
- [ ] Save per-repeat results separately
- [ ] Compute mean cumulative reward
- [ ] Compute standard deviation of cumulative reward
- [ ] Compute mean final score
- [ ] Compute standard deviation of final score
- [ ] Aggregate over selectors in a consistent reporting format

## O. Success criteria
- [ ] Define explicit success criteria before running the main comparison
- [ ] Include criterion: `LinUCB` > `random` on cumulative reward
- [ ] Include criterion: `LinUCB` > `noop` on cumulative reward
- [ ] Include criterion: `supervised` > `random` and `noop`
- [ ] Optionally include bounded growth/regression criteria
- [ ] Save success-criteria definitions with experiment artifacts

## P. Reporting artifacts
- [ ] Save per-round reward curves
- [ ] Save cumulative reward curves
- [ ] Save final-score comparison tables
- [ ] Save skill-size-over-round plots or tabular equivalents
- [ ] Save anchor-regression-over-round outputs if enabled
- [ ] Save comparison-ready summary artifacts in `docs/` or experiment output directories

## Q. Post-run diagnosability
- [ ] Make it easy to inspect why a selector chose a patch
- [ ] Make it easy to inspect why a patch helped or hurt
- [ ] Make it easy to inspect whether patch pools were diverse enough
- [ ] Make it easy to inspect reward variance across repeats
- [ ] Make it easy to inspect whether state features appear predictive of reward

## R. Explicit deferrals
- [ ] Do not implement subset selection in `0.2.0`
- [ ] Do not implement learned patch generation in `0.2.0`
- [ ] Do not prioritize LLM critic state features in `0.2.0`
- [ ] Do not over-refine paper theory before the first clean selector comparison exists

---

## Definition of `0.2.0` done

`0.2.0` should be considered complete when:
- the clean rebuild exists,
- the end-to-end loop works,
- deterministic execution is in place,
- the required selectors can all be run,
- patch pools can be replayed for matched comparison,
- repeated selector runs can be executed,
- cumulative reward curves can be reported,
- and we can compare selector performance under fixed budget with `noop` and `random` included.

If that is true, then we have successfully built the harness needed to move the research forward.
