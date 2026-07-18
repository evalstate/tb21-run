from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

EXPECTED_DATASET = "terminal-bench/terminal-bench-2-1"
EXPECTED_REF = "sha256:7d7bdc1cbedad549fc1140404bd4dc45e5fd0ea7c4186773687d177ad3a0699a"
EXPECTED_MODEL = "openai/gpt-5.6-luna"
EXPECTED_ROUTE = "codexresponses.gpt-5.6-luna?reasoning=xhigh"
EXPECTED_PRICING = {
    "model_name": EXPECTED_MODEL,
    "input_cost_per_token": 0.000001,
    "cache_read_input_token_cost": 0.0000001,
    "output_cost_per_token": 0.000006,
}


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    require(isinstance(value, dict), f"{path} must contain a mapping")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()
    profile = args.profile.resolve()
    manifest = json.loads((profile / "partition-manifest.json").read_text())
    configs = {name: load(profile / f"{name}.yaml") for name in ("local", "daytona")}
    tasks = {name: set(configs[name]["datasets"][0]["task_names"]) for name in configs}
    require(len(tasks["local"]) == 4, "local partition must contain 4 tasks")
    require(len(tasks["daytona"]) == 85, "Daytona partition must contain 85 tasks")
    require(not tasks["local"] & tasks["daytona"], "partitions overlap")
    require(len(tasks["local"] | tasks["daytona"]) == 89, "expected 89 tasks")
    for name, config in configs.items():
        require(config["n_attempts"] == 5, f"{name}: expected five attempts")
        require(config["retry"]["max_retries"] == 0, f"{name}: retries must be disabled")
        require(
            config["environment"]["type"] == ("docker" if name == "local" else "daytona"),
            f"{name}: wrong environment",
        )
        dataset = config["datasets"][0]
        require(dataset["name"] == EXPECTED_DATASET, f"{name}: wrong dataset")
        require(
            dataset["ref"] == EXPECTED_REF == manifest["dataset_ref"],
            f"{name}: wrong dataset digest",
        )
        agent = config["agents"][0]
        kwargs = agent["kwargs"]
        require(agent["name"] == "fast-agent", f"{name}: wrong agent")
        require(agent["model_name"] == EXPECTED_MODEL, f"{name}: wrong Harbor model")
        require(kwargs["version"] == "0.9.14", f"{name}: wrong fast-agent version")
        require(kwargs["fast_agent_model"] == EXPECTED_ROUTE, f"{name}: wrong route")
        require(kwargs["reasoning_effort"] == "xhigh", f"{name}: wrong effort")
        require(kwargs["pricing"] == EXPECTED_PRICING, f"{name}: wrong pricing")
        require(
            kwargs["codex_auth_path"] == str(Path.home() / ".codex/auth.json"),
            f"{name}: wrong Codex auth path",
        )
    require(manifest["totals"] == {"tasks": 89, "trials": 445}, "wrong manifest totals")
    print("OK: 89 tasks, 445 trials, five attempts/task, zero retries, exact model pricing")


if __name__ == "__main__":
    main()
