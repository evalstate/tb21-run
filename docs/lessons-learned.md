# Lessons learned

Evidence-backed lessons from the July 2026 fast-agent Terminal-Bench 2.1
campaigns. Raw subagent research remains ignored under `state/lessons/`.

## 1. Freeze the evaluation contract before spending tokens

Pin and validate together:

- dataset and digest
- agent package version
- Harbor model identity
- provider route and reasoning effort
- task-level environment partition
- attempts, concurrency, timeout policy, and retries
- pricing model and rates

The 85-Daytona/4-local split was declared before outcomes and kept every attempt
for a task in one environment. That is materially more defensible than moving
tasks after seeing failures.

**Guardrail:** treat a profile directory as immutable after its first campaign.
Create a new profile for every version, model, route, or policy change.

## 2. Replacement eligibility is causal, not outcome-based

The most difficult judgment was not whether a trial failed, but who owned the
failure and during which phase.

Strong infrastructure candidates included pre-inference setup failures and one
externally evidenced silent model-download stall. Genuine active agent timeouts,
model implementation errors, verifier mismatches caused by the solution, and
PyStan signal exits from agent-created workloads remained benchmark outcomes.

**Guardrail:** record phase, exception, inference evidence, sibling evidence,
and replacement rationale before launching a replacement. Never replace simply
because the reward is zero.

## 3. One-for-one means retain the replacement outcome

An approved replacement is not permission to retry until success. The first
Git-leak replacement repeated the setup timeout; the first path-tracing
replacement also failed during setup. Each second-level attempt required
explicit approval and a complete provenance chain.

**Guardrail:** zero Harbor retries, one attempt per approved replacement, and
explicit approval before any second-level attempt.

## 4. ATIF is a submission invariant

Three original trials timed out after producing reward 1, but fast-agent was
killed before exporting ATIF. Local score aggregation accepted them; leaderboard
static analysis rejected them because rewarded trials must be auditable.

The approved replacements retained every outcome:

- adaptive-rejection-sampler: pass with ATIF
- largest-eigenval: active timeout, reward zero
- path-tracing: setup failure followed by an approved second-level pass with
  ATIF

The score correctly decreased when the largest-eigenval replacement timed out.

**Guardrail:** audit `reward > 0 => public trajectory_path` before constructing a
submission. Never fabricate or reconstruct ATIF solely to satisfy CI.

## 5. Preserve raw jobs; select exact outcomes in a separate mirror

Adding replacement jobs to the original jobs creates more than five attempts for
affected tasks. `disqualified_trials` does not remove extra attempts; it only
sets their reward to zero.

The successful pattern was:

1. leave raw public jobs unchanged;
2. construct a deterministic filtered mirror;
3. re-key only documented identity/path fields;
4. preserve and verify evaluation artifacts;
5. assert 89 tasks and exactly five selected outcomes per task.

**Guardrail:** never mutate the raw campaign into the desired answer. Build a
separate, reproducible source set with an explicit original-to-replacement map.

## 6. Process lifecycle must be explicit

The shell lifecycle work was successful: managed background processes no longer
showed a systemic registry or execution failure, and open descendant pipes were
handled without blocking completion. However, session-managed processes and
verifier-persistent services are different requirements.

Model-created `nohup`, PID files, `ps`, and log polling are compatibility hacks.
They are less reliable than trial-owned opaque process handles.

**Guardrail:** specify foreground/background and session/persistent lifetime
independently. Test the agent-exit to verifier transition, descendant cleanup,
explicit termination, and timeout behavior.

## 7. A tool schema is useful only when runtime validation agrees

Historical agents repeatedly supplied plausible but unsupported arguments such
as timeout and output controls. Silent acceptance caused the model to believe a
longer timeout or different output policy was active when it was not.

The current runtime rejects unknown arguments before execution, which is better
than silently ignoring them. Current trajectories still showed malformed poll
arguments and unsupported output-limit requests, but these were model misuse
rather than systemic shell failure.

**Guardrail:** generate descriptions from the actual typed runtime contract,
reject unknown fields, and test that rejected calls have no side effects.

## 8. Bounded context and durable output are separate requirements

Current head/tail truncation protects model context, but the campaign contained
209 truncated outputs across 106 trials. Agents sometimes reran broad commands,
narrowed queries, or chunked overlapping ranges to recover omitted information.

This is an efficiency and timeout risk even when it does not directly change
reward.

**Guardrail:** spool complete stdout/stderr from process start, return a bounded
head/tail preview plus byte count and handle, and expose offset/search/tail reads.
Make spools session-scoped, permission-restricted, redacted, and not uploaded by
default.

## 9. Working directories and artifact roots must be separate

A prior MTEB trial cloned working data under `/logs/agent`, producing a
multi-gigabyte artifact tree with roughly one hundred thousand files. The cause
was a workspace/cwd mismatch, not the benchmark itself.

The adapter now uses an absolute task workspace and execution cwd.

**Guardrail:** treat `/logs/agent` as an evidence plane, never a worktree. Audit
smoke jobs for total bytes, file count, largest directories, repositories,
caches, and model downloads before a full campaign.

## 10. Credential safety is an artifact-pipeline property

Credential minimization and restrictive auth staging are necessary but
insufficient. Historical trajectories retained commands and outputs that exposed
credential-bearing environment state. Rotating the credential does not make the
artifact appropriate to republish.

**Guardrail:** control and redact separately:

- inherited environment
- command arguments
- stdout/stderr
- exceptions
- session history
- ATIF
- result metadata
- archives and public uploads

Avoid broad environment/process inspection, scan before publication, and
reference public Hub artifacts rather than copying raw logs into Git.

## 11. Version provenance includes the whole bootstrap

The effective runtime is more than `fast-agent-mcp==X`:

- Harbor adapter commit
- fast-agent wheel version or digest
- Python patch version
- uv installer/version
- dependency resolution
- model route
- dataset digest

Earlier campaigns lost attempts to deterministic compatibility or bootstrap
failures that had nothing to do with model quality.

**Guardrail:** preflight the exact launcher session and run one authenticated
smoke per environment before the full campaign.

## 12. Completion has multiple states

These are not equivalent:

1. process launched;
2. trials completed locally;
3. individual trial archives uploaded;
4. aggregate job archive finalized;
5. job anonymously readable;
6. leaderboard static analysis passed;
7. intake promoted;
8. judge/apply completed;
9. promoted PR merged.

The 425-trial filtered mirror uploaded all individual trial artifacts but its
large aggregate archive failed storage finalization. Idempotent re-upload with a
slim wrapper archive finalized the job without changing trial artifacts.

**Guardrail:** supervise and record each state explicitly. Do not call a campaign
submitted or accepted based only on local completion or promotion.

## 13. Token and cost reporting must be complete

Input tokens include cached input. The correct decomposition is:

```text
uncached input = input - cached input
```

Cached input must not be added to total input again. Likewise, replacement-only
pricing is not campaign cost. The submission intentionally omitted cost when
the original campaign lacked complete cost coverage, even though later
replacement jobs had explicit pricing.

**Guardrail:** report input, cached input, uncached input, output, pricing source,
and cost coverage. Emit campaign cost only with complete, model-consistent
coverage.

## 14. Promotion is not final acceptance

The intake PR passed static analysis and was automatically closed after the bot
opened promoted PR #158. Maintainer review, trajectory judging, disqualification
application, and merge remain separate steps.

**Guardrail:** track the promoted PR and provenance, not only the intake PR.
Never describe a promoted but unmerged row as accepted.

## Highest-ROI automation

### Small

1. Add a source-set validator: 89 tasks, five selected outcomes each, no logical
   duplicates, explicit replacement mapping.
2. Add a reward-to-public-ATIF audit before mirror construction.
3. Add artifact size/file-count and complete-cost-coverage checks to smoke
   validation.

### Strategic

1. Durable searchable process-output spooling with redaction.
2. Structured typed terminal errors with phase, ownership, and retryability.
3. A supervised campaign state machine covering launch through leaderboard
   merge.
