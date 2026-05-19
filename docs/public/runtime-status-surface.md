# Hisys Runtime Status Surface

Traceability: `docs/plans/2026-05-19-runtime-status-surface-cli.md`.

`hisys runtime-status-surface` writes a local, redacted operator status packet for the current work unit. It is a sensor/reporting surface only. It does not call external services, mutate live runtimes, publish, push, or authorize action.

## Command

```bash
hisys runtime-status-surface \
  --instance /path/to/hisys-instance \
  --date YYYYMMDD \
  --workdir /path/to/repo \
  --approval-state pending \
  --context-budget unknown \
  --format text
```

Optional fields:

- `--model`: current model label; credential-like values are redacted.
- `--session`: current session label; credential-like values are redacted.
- `--format`: `text`, `json`, or `markdown`.

## Artifacts

The command writes:

- `reports/run-summaries/YYYYMMDD/hisys-runtime-status-surface.json`
- `reports/run-summaries/YYYYMMDD/hisys-runtime-status-surface.md`

The JSON packet uses schema `hisys.runtime_status_surface@0.1.0`.

## Boundary flags

Every first-increment packet records:

```json
{
  "external_call_made": false,
  "mutation_performed": false,
  "publication_or_live_action_approved": false,
  "execution_authorized": false,
  "action_taken": "none"
}
```

These fields are evidence about the runtime-status command itself. They do not approve a later action.

## Redaction

The command redacts credential-like strings and home-directory usernames. Treat the output as operator-visible evidence, not as a secure secret scanner. Run the repository secret scan before commits or release packages.

## Deferred adapters

This command is not a Claude Code statusline, tmux status bar, Hermes TUI adapter, or live gateway integration. Those adapters should consume this packet only after separate design, tests, and approval.
