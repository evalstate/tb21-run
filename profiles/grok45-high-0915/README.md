# Grok 4.5 high smoke / fast-agent 0.9.15

Authorized nine-trial Daytona smoke for cost and adapter calibration:

- `chess-best-move`: 3 attempts
- `sanitize-git-repo`: 3 attempts
- `fix-ocaml-gc`: 3 attempts
- Daytona concurrency: 3
- Harbor retries: 0
- Hub upload: disabled

The profile uses Harbor model `xai/grok-4.5`, fast-agent route
`xai/grok-4.5?reasoning=high`, and a configured LiteLLM pricing estimate of
$2.00/M uncached input, $0.50/M cached input, and $6.00/M output. It is not
provider-reported cost.

Set `XAI_API_KEY` and `DAYTONA_API_KEY` in the current shell or the ignored
repository `.env`, then run:

```bash
bin/run-grok45-smoke
```

The launcher validates the profile and wheel digest, checks xAI model access
and Daytona authentication, prints the complete run contract, and starts the
local-only job. It accepts no Harbor argument overrides.

The matching nine-trial Cursor baseline is `$2.3957988`. After the smoke:

```text
fast-agent/Cursor multiplier = observed smoke cost / 2.3957988
estimated Daytona campaign = 127.9097 * multiplier
estimated full campaign = 134.08523 * multiplier
```
