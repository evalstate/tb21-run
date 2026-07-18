from __future__ import annotations

import argparse
from pathlib import Path
import re

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("tasks", nargs="+")
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()
    if args.concurrency < 1:
        raise SystemExit("concurrency must be positive")
    tasks = []
    for task in args.tasks:
        task = task if task.startswith("terminal-bench/") else f"terminal-bench/{task}"
        if not re.fullmatch(r"terminal-bench/[a-z0-9][a-z0-9.-]*", task):
            raise SystemExit(f"invalid task name: {task}")
        tasks.append(task)
    config = yaml.safe_load((args.profile / "daytona.yaml").read_text())
    config["n_attempts"] = 1
    config["n_concurrent_trials"] = min(args.concurrency, len(tasks))
    config["retry"] = {"max_retries": 0}
    config["datasets"][0]["task_names"] = tasks
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(config, sort_keys=False))
    print(args.output)


if __name__ == "__main__":
    main()
