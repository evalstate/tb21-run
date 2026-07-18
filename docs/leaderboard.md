# Leaderboard workflow

1. Keep the two primary jobs immutable and public.
2. Classify replacements before running them. Normal agent timeouts and nonzero agent exits remain outcomes unless maintainers approve otherwise.
3. Run one-for-one replacements with `bin/replace`; keep every post-setup outcome. Document any second-level replacement approval in the PR.
4. Require exactly 89 tasks and at least five selected trials per task.
5. Every rewarded trial must have a public ATIF `trajectory_path`.
6. Do not report partial cost as total cost. Use explicit pricing for an entire new campaign; otherwise normalize submission-mirror cost to null and explain why.
7. Generate the submission with the leaderboard repository's `uv run lb filter`, fill metadata, and run full static analysis before opening a PR.

The leaderboard source JSON should reference a filtered public mirror plus any unchanged partition jobs. A mirror may deterministically re-key `/id`, `/trial_uri`, `/config/job_id`, and `/config/trials_dir`; preserve and verify all evaluation artifacts.
