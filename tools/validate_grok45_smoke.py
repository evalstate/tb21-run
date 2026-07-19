from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

EXPECTED_DATASET = "terminal-bench/terminal-bench-2-1"
EXPECTED_REF = "sha256:7d7bdc1cbedad549fc1140404bd4dc45e5fd0ea7c4186773687d177ad3a0699a"
EXPECTED_TASKS = [
    "terminal-bench/chess-best-move",
    "terminal-bench/sanitize-git-repo",
    "terminal-bench/fix-ocaml-gc",
]
EXPECTED_VERSION = "0.9.15"
EXPECTED_WHEEL = "fast_agent_mcp-0.9.15-py3-none-any.whl"
EXPECTED_WHEEL_SHA256 = (
    "ab2807625716a55694664504a3a9348c5c7a19af1e1b738f67b9a4442ca4ad5f"
)
EXPECTED_MODEL = "xai/grok-4.5"
EXPECTED_ROUTE = "xai/grok-4.5?reasoning=high"
EXPECTED_PRICING = {
    "model_name": EXPECTED_MODEL,
    "input_cost_per_token": 0.000002,
    "cache_read_input_token_cost": 0.0000005,
    "output_cost_per_token": 0.000006,
}


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    require(isinstance(value, dict), f"{path} must contain a mapping")
    return value


def main() -> None:
    profile = Path(__file__).resolve().parents[1] / "profiles/grok45-high-0915"
    config = load_yaml(profile / "smoke-daytona.yaml")
    manifest = json.loads((profile / "smoke-manifest.json").read_text())

    require(config["n_attempts"] == 3, "expected three attempts per task")
    require(config["n_concurrent_trials"] == 3, "expected concurrency three")
    require(config["retry"]["max_retries"] == 0, "retries must be disabled")
    require(config["environment"]["type"] == "daytona", "expected Daytona")

    dataset = config["datasets"][0]
    require(dataset["name"] == EXPECTED_DATASET, "wrong dataset")
    require(dataset["ref"] == EXPECTED_REF, "wrong dataset digest")
    require(dataset["task_names"] == EXPECTED_TASKS, "wrong smoke tasks or order")

    agent = config["agents"][0]
    kwargs = agent["kwargs"]
    require(agent["name"] == "fast-agent", "wrong agent")
    require(agent["model_name"] == EXPECTED_MODEL, "wrong Harbor model")
    require(
        agent.get("env") == {"XAI_API_KEY": "${XAI_API_KEY}"},
        "XAI credential must be passed by environment reference",
    )
    require(kwargs["version"] == EXPECTED_VERSION, "wrong fast-agent version")
    require(kwargs["fast_agent_model"] == EXPECTED_ROUTE, "wrong route")
    require(kwargs["reasoning_effort"] == "high", "wrong reasoning effort")
    require(kwargs["pricing"] == EXPECTED_PRICING, "wrong configured pricing")
    require("auth_path" not in kwargs, "xAI API-key smoke must not stage provider auth")

    require(manifest["dataset"] == EXPECTED_DATASET, "wrong manifest dataset")
    require(manifest["dataset_ref"] == EXPECTED_REF, "wrong manifest digest")
    require(manifest["tasks"] == EXPECTED_TASKS, "wrong manifest tasks")
    require(manifest["n_tasks"] == 3 and manifest["n_trials"] == 9, "wrong totals")
    require(manifest["attempts_per_task"] == 3, "wrong manifest attempts")
    require(manifest["concurrency"] == 3, "wrong manifest concurrency")
    require(manifest["max_retries"] == 0, "wrong manifest retries")
    require(manifest["upload"] is False, "smoke upload must be disabled")
    require(manifest["harbor_model"] == EXPECTED_MODEL, "wrong manifest model")
    require(manifest["fast_agent_model"] == EXPECTED_ROUTE, "wrong manifest route")
    require(manifest["reasoning_effort"] == "high", "wrong manifest effort")
    require(
        {key: manifest["pricing"][key] for key in EXPECTED_PRICING}
        == EXPECTED_PRICING,
        "wrong manifest pricing",
    )
    distribution = manifest["agent_distribution"]
    require(
        manifest["agent_version"] == f"fast-agent-mcp v{EXPECTED_VERSION}"
        and distribution["source"] == "PyPI"
        and distribution["wheel"] == EXPECTED_WHEEL
        and distribution["sha256"] == EXPECTED_WHEEL_SHA256,
        "wrong fast-agent distribution provenance",
    )
    expected_baseline = 3 * sum(
        manifest["cursor_baseline"]["mean_cost_usd_per_attempt"].values()
    )
    require(
        abs(
            manifest["cursor_baseline"]["expected_nine_trial_cost_usd"]
            - expected_baseline
        )
        < 1e-12,
        "wrong Cursor nine-trial baseline",
    )
    print(
        "OK: Grok 4.5 high smoke; 3 tasks, 3 attempts/task, "
        "Daytona concurrency 3, zero retries, upload disabled"
    )


if __name__ == "__main__":
    main()
