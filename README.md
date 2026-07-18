# Terminal-Bench 2.1 run control

A clean, credential-free home for reproducible Harbor + fast-agent Terminal-Bench runs. Harbor source stays in a separate checkout; generated jobs, logs, and replacement YAML stay ignored here.

See `docs/lessons-learned.md` for the evidence-backed operating lessons from
the July 2026 campaigns.

## One-time setup

```bash
cd ~/source/tb21-run
cp .env.example .env
$EDITOR .env                    # point HARBOR_ROOT at the Harbor checkout to use
export DAYTONA_API_KEY=...      # keep secrets in your shell, not this repository
codex login                     # creates ~/.codex/auth.json
```

`HARBOR_ROOT` must contain Harbor's built-in fast-agent adapter from PR #2365 or newer.

## Validate

```bash
bin/preflight all
```

This checks the exact 89-task partition, dataset digest, fast-agent/model/route, five attempts, zero retries, pricing, Codex auth, Docker, Daytona auth, and the PyPI wheel.

## Run primary partitions

```bash
bin/run local
bin/run daytona
```

Or launch both and write logs/PIDs under this repository:

```bash
bin/run-both
```

Jobs default to `~/source/tb21-run/jobs`. Set `TB21_UPLOAD=0` for local-only artifacts or `TB21_PUBLIC=0` for private Hub uploads.

## Run approved replacements

```bash
bin/replace git-leak-recovery
TB21_REPLACEMENT_CONCURRENCY=3 bin/replace task-a task-b task-c
```

Each replacement task runs once on Daytona with zero Harbor retries. Never use this command to reroute normal benchmark failures without explicit approval.

## Summarize jobs

```bash
HARBOR_ROOT=~/source/harbor uv run --project "$HARBOR_ROOT" \
  python tools/summarize.py jobs/<daytona-job> jobs/<local-job>
```

`cost_usd` is emitted only when every selected trial has cost; partial pricing is reported as `null` with a coverage count.

## Layout

```text
profiles/   pinned run configurations and partition manifest
bin/        preflight, primary-run, and replacement commands
tools/      validators, config renderer, and result summary
docs/       leaderboard policy/workflow notes
records/    concise provenance for completed campaigns
jobs/       ignored run output
logs/       ignored launch logs
state/      ignored generated configs and PID files
```
