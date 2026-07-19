# AGENTS.md — Terminal-Bench 2.1 Run Control

## Purpose

This repository is the clean control plane for planning, launching, validating,
and submitting Terminal-Bench 2.1 evaluations with Harbor and fast-agent.

Keep Harbor source code, fast-agent source code, generated jobs, and temporary
analysis outside tracked files here. Product-facing spelling is always
**fast-agent**.

## Repository layout

```text
profiles/   Pinned benchmark profiles and the predeclared environment partition
bin/        Operator commands for preflight, primary runs, and replacements
tools/      Validation, rendering, and result-summary utilities
docs/       Durable workflow and policy notes
records/    Concise provenance for completed campaigns
jobs/       Generated Harbor job output; ignored
logs/       Launch logs; ignored
state/      Generated replacement configs and PID files; ignored
```

Read `README.md` first. For leaderboard work, also read
`docs/leaderboard.md`, `docs/lessons-learned.md`, and the relevant campaign
file under `records/`.

## Environment

Local, non-secret configuration lives in `.env` and is ignored by Git.
Start from `.env.example`.

Required:

- `HARBOR_ROOT`: Harbor checkout containing the built-in fast-agent adapter
  from Harbor PR #2365 or newer.
- A provider-scoped fast-agent OAuth export for Codex or xAI runs, or the
  matching provider API key.
- `DAYTONA_API_KEY`: exported in the shell for Daytona runs.
- Docker: required only for the local partition.

Never print, copy, commit, or serialize credential values. It is safe to report
whether a credential is present or accepted. Do not run broad `env`, process
environment, or credential-file inspection commands when avoidable.

The active shell may not inherit environment changes made in another terminal.
Before a Daytona run, verify provider and Daytona authentication from the same
execution session:

```bash
bin/preflight daytona
```

### Provider authentication for Harbor runs

Prefer fast-agent OAuth with a provider-scoped export. Do not pass the shared
keyring directly to Harbor and do not use the Codex CLI's `~/.codex/auth.json`
as `auth_path`.

Create restrictive export storage once:

```bash
mkdir -p ~/.fast-agent/exports
chmod 700 ~/.fast-agent/exports
```

For Codex:

```bash
fast-agent auth login codex
fast-agent auth status codex
fast-agent auth export codex ~/.fast-agent/exports/codex.auth.json --force
```

For xAI:

```bash
fast-agent auth login xai
fast-agent auth status xai
fast-agent auth export xai ~/.fast-agent/exports/xai.auth.json --force
```

Set the matching export in the Harbor fast-agent configuration:

```yaml
agents:
  - name: fast-agent
    model_name: openai/gpt-5.6-terra
    kwargs:
      fast_agent_model: codexresponses.gpt-5.6-terra?reasoning=high
      auth_path: ~/.fast-agent/exports/codex.auth.json
```

```yaml
agents:
  - name: fast-agent
    model_name: xai/grok-4.5
    kwargs:
      fast_agent_model: xai/grok-4.5?reasoning=high
      auth_path: ~/.fast-agent/exports/xai.auth.json
```

Harbor validates that the export contains the provider selected by
`fast_agent_model`, stages only that provider credential into the sandbox,
sets `FAST_AGENT_AUTH_FILE` there, synchronizes refreshed credentials back to
the export, and removes the staged secret after the run.

API keys remain supported as an alternative:

- Codex: `CODEX_API_KEY`
- xAI: `XAI_API_KEY`

Pass an API key by environment reference in the agent `env` mapping and omit
`auth_path`. Never configure both `auth_path` and the matching provider API key;
Harbor rejects ambiguous dual credentials. An explicit API key takes precedence
over OAuth in fast-agent outside Harbor as well.

`FAST_AGENT_AUTH_FILE` is authoritative. When Harbor sets it in the sandbox,
fast-agent does not fall back to the operator's keyring, default fast-agent auth
file, or Codex CLI account. Generate a fresh provider-scoped export after
logging in or changing accounts, and validate that exact file before spending
tokens.

Repository preflight must validate the `auth_path` configured by the selected
profile. A guard that only checks `~/.codex/auth.json` is legacy behavior; update
the guard instead of creating, copying, or staging a Codex CLI auth file merely
to satisfy it. Existing xAI profiles that intentionally use `XAI_API_KEY` remain
valid until migrated; update their profile, validator, and operator notes
together when switching them to OAuth.

## Current pinned profile

`profiles/terra-high-0915/` defines:

- Dataset: `terminal-bench/terminal-bench-2-1`
- Dataset digest:
  `sha256:7d7bdc1cbedad549fc1140404bd4dc45e5fd0ea7c4186773687d177ad3a0699a`
- Agent: fast-agent 0.9.15
- Harbor model identity: `openai/gpt-5.6-terra`
- Provider route: `codexresponses.gpt-5.6-terra?reasoning=high`
- Reasoning effort: `high`
- Attempts: 5 per task
- Harbor retries: 0
- Partition: 85 Daytona tasks and 4 local Docker tasks
- Primary concurrency: Daytona 6, local 1
- Explicit configured estimate tied to the exact Harbor model, sourced from
  the LiteLLM model table on 2026-07-18:
  - uncached input: $2.50 / 1M tokens
  - cached input: $0.25 / 1M tokens
  - output: $15.00 / 1M tokens

The `fast-agent-mcp==0.9.15` PyPI wheel is available and its SHA-256 digest is
pinned in the profile manifest and preflight.

The partition is predeclared by task. Never reroute individual outcomes between
local and Daytona after seeing results.

## Safe operating rule

Do not start primary, smoke, replacement, or leaderboard-repair model runs
unless the user explicitly requests or authorizes them.

Read-only preflight, validation, inspection, aggregation, and planning are
allowed without additional confirmation.

When a run is authorized, state exactly what will run before launching:

- profile/version/model/route
- tasks and attempts
- environment and concurrency
- retry count
- upload visibility

## Normal workflow

### 1. Validate

```bash
bin/preflight all
```

This checks the partition, pinned version/model/route, pricing, PyPI wheel,
provider auth path, Docker, and Daytona credentials.

If only one environment matters:

```bash
bin/preflight local
bin/preflight daytona
```

Do not bypass a failed credential or environment preflight.

### 2. Launch primary partitions

Run separately:

```bash
bin/run local
bin/run daytona
```

Or launch both:

```bash
bin/run-both
```

Outputs default to `jobs/`. Uploads are public by default because leaderboard
CI requires anonymous access. Override intentionally with:

```bash
TB21_UPLOAD=0 bin/run daytona
TB21_PUBLIC=0 bin/run daytona
```

Do not use retries for leaderboard campaigns.

### 3. Summarize

```bash
uv run --project "$HARBOR_ROOT" \
  python tools/summarize.py jobs/<daytona-job> jobs/<local-job>
```

Treat missing rewards and errored trials as score zero. Input tokens include
cached input. Report:

- passes / total and score
- input tokens
- cached input tokens
- uncached input = input - cached
- output tokens
- cost only when coverage is complete

Never present replacement-only or otherwise partial cost as campaign total.

## Planning a new fast-agent version

Do not edit an existing pinned profile in place after it has produced a
campaign. Create a new profile directory, for example:

```text
profiles/luna-xhigh-0915/
```

Update together:

1. fast-agent package version
2. profile directory name
3. validation constants
4. manifest `agent_version`
5. generated job-name prefix
6. README/record references

Then:

1. Confirm the exact wheel exists on PyPI.
2. Review fast-agent release notes and breaking changes.
3. Confirm Harbor's adapter supports the version.
4. Run profile validation.
5. Request authorization for a small smoke test.
6. Inspect ATIF, token accounting, shell lifecycle, Windows support, and cost.
7. Request authorization before the full campaign.

Do not silently substitute a local wheel for a pinned PyPI version. If a local
wheel is intentionally used, record its path and digest and do not label the
run as the published package version.

## Planning model or reasoning changes

The Harbor model identity, fast-agent provider route, reasoning effort, and
pricing model must agree.

For a model switch:

1. Create a new profile.
2. Update `agents[].model_name`.
3. Update `fast_agent_model`.
4. Update `reasoning_effort`.
5. Update `pricing.model_name` and rates.
6. Update validation constants.
7. Validate before spending tokens.

The adapter intentionally rejects configured pricing whose `model_name` does
not exactly match the selected Harbor model.

Do not infer or invent prices. Distinguish provider-reported cost from a
configured or LiteLLM estimate.

## Replacement policy

Use:

```bash
bin/replace task-name
TB21_REPLACEMENT_CONCURRENCY=3 bin/replace task-a task-b task-c
```

Each task receives exactly one attempt with zero Harbor retries.

Reasonable infrastructure replacement candidates include:

- pre-inference `AgentSetupTimeoutError`
- authentication-independent provider bootstrap failures
- clear external download stalls with strong sibling-run evidence
- environment loss or provider sandbox failure

Do not replace merely because an outcome is undesirable. Normally retain:

- active `AgentTimeoutError`
- model-generated implementation mistakes
- verifier mismatches caused by the agent
- nonzero agent exits caused by agent-created workloads
- failures after productive inference unless infrastructure causation is clear

Every authorized replacement outcome must be retained. If the replacement
itself fails before inference due to clear infrastructure, request explicit
approval before a second-level replacement. Record the original, first
replacement, second-level replacement, reasons, and public job links.

## ATIF and rewarded timeouts

Leaderboard CI requires a public ATIF trajectory for every rewarded trial.
A trial can earn reward after the agent process times out, but fast-agent may
be killed before writing ATIF. Such a reward-1/no-ATIF result cannot pass
leaderboard static analysis.

Do not fabricate or reconstruct ATIF merely to satisfy CI. Request approval
for a one-for-one replacement and retain its outcome.

Failed or errored reward-zero trials do not require ATIF.

## Leaderboard workflow

The leaderboard repository is:

```text
https://github.com/harbor-framework/terminal-bench-2-1
```

Follow its current `leaderboard/SUBMIT.md`; do not rely on older Terminal-Bench
submission repositories.

Expected submission shape:

- one JSON under `leaderboard/submissions/`
- public `source_jobs`
- exact `source_filter`
- complete display metadata
- `metrics: null`
- `disqualified_trials: []` at intake

Run the repository's full static analysis before opening a PR:

```bash
uv run python -m leaderboard.ci.static_analysis submissions/<file>.json
```

Require all checks to pass:

- valid source filter and metadata
- canonical timeout/resource settings
- 89 tasks with at least 5 trials each
- valid per-trial records
- canonical task digests
- trajectories for every rewarded trial

The intake PR is normally closed after CI promotes it to a repository-owned
PR. Review and merge continue on the promoted PR.

## Filtered public mirrors

When raw source jobs contain invalid originals and replacement attempts, the
submission source union must select the intended outcomes cleanly.
`disqualified_trials` does not remove extra attempts; it only zeroes rewards.

If needed, build a filtered public mirror with deterministic UUIDv5 job/trial
identities. Preserve evaluation content and document changed fields.
Established identity/path changes are:

- `/id`
- `/trial_uri`
- `/config/job_id`
- `/config/trials_dir`

Verify non-result artifact bytes against source artifacts. If source jobs have
incomplete pricing, normalize partial mirror cost to null and document it
rather than reporting a misleading partial total.

The aggregate job archive can be slimmed after all individual trial archives
and direct trajectories upload; leaderboard validation reads Hub trial rows,
per-trial archives, and direct trajectory paths.

## Security

Historical Harbor trajectories and logs may contain commands that exposed
environment variables or credential assignments. Credentials have been
rotated, but do not copy raw logs into Git repositories or submission bundles.

Before publishing:

1. Confirm source jobs are intentionally public.
2. Test anonymous Hub visibility.
3. Scan new tracked files for credential-like values.
4. Reference Hub trial artifacts instead of copying logs.
5. Never include auth files, `.env`, session logs, or full process listings.

## Current campaign

See `records/2026-07-18-luna-xhigh/README.md`.

Current promoted submission:

```text
https://github.com/harbor-framework/terminal-bench-2-1/pull/158
```

The Git-leak second-level replacement job is:

```text
7b009ddb-894e-4ab4-b2f7-966e39cfce7a
```

It completed with reward 1 and valid ATIF. The promoted submission must be
amended only after maintainer approval for that second-level replacement.

## Quality expectations

- Keep notes terse, factual, and evidence-based.
- Preserve native Windows support when changing the Harbor adapter.
- Prefer explicit runtime checks over assertions in reusable tooling.
- Prefer `Path.read_text()` / `Path.write_text()` in Python.
- Use `asyncio.TaskGroup` rather than `asyncio.gather` in new async tools.
- Avoid broad refactors while preparing or repairing a submission.
- Do not modify Harbor or fast-agent source from this repository unless the
  user explicitly asks for a code change in that project.
