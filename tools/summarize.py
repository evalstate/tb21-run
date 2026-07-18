from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Harbor job directories")
    parser.add_argument("jobs", nargs="+", type=Path)
    args = parser.parse_args()
    trials = []
    for job in args.jobs:
        paths = sorted(job.glob("*/result.json"))
        if not paths:
            raise SystemExit(f"no trial results in {job}")
        trials.extend(json.loads(path.read_text()) for path in paths)
    rewards = []
    errors = Counter()
    input_tokens = cached_tokens = output_tokens = 0
    costs = []
    for trial in trials:
        reward = ((trial.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        rewards.append(float(reward or 0))
        exception = (trial.get("exception_info") or {}).get("exception_type")
        if exception:
            errors[exception] += 1
        context = trial.get("agent_result") or {}
        input_tokens += int(context.get("n_input_tokens") or 0)
        cached_tokens += int(context.get("n_cache_tokens") or 0)
        output_tokens += int(context.get("n_output_tokens") or 0)
        if context.get("cost_usd") is not None:
            costs.append(float(context["cost_usd"]))
    payload = {
        "n_trials": len(trials),
        "n_passed": sum(rewards),
        "score": sum(rewards) / len(trials),
        "errors": dict(errors),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "uncached_input_tokens": input_tokens - cached_tokens,
        "output_tokens": output_tokens,
        "cost_usd": sum(costs) if len(costs) == len(trials) else None,
        "cost_coverage": f"{len(costs)}/{len(trials)}",
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
