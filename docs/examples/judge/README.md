# Judge example artifacts

This directory contains committed, deterministic, local-fixture Judge evidence artifacts. They are intended for agent/human discoverability, diffing, and review of the Judge subsystem smoke surface.

These artifacts do **not** authorize execution, mutation, publication, remote push, live-provider use, or removal of human review. In short: this evidence does not authorize execution. They preserve the Judge advisory-only / requires-human-review boundary.

## Artifacts

| Artifact | Producer | Purpose | Boundary |
| --- | --- | --- | --- |
| `judge-advisory-smoke-report.json` | `PYTHONPATH=src:. python3 -m hisys.judge.smoke --format json` | Full local fixture smoke report. Includes fixture outcomes, invariant checks, advisory panel review bundle, bundle serialization/fingerprint metadata, side-effect flags, and authority locks. | Local fixture evidence only; no live provider, network, credentials, mutation, or execution authority. |
| `judge-advisory-smoke-status-review-bundle.json` | `PYTHONPATH=src:. python3 -m hisys.judge.smoke --status-bundle` | Compact discoverability artifact pairing the smoke status summary with the short human/agent-readable status text. Use this first when a reviewer needs the current Judge smoke readiness at a glance. | Local fixture evidence only; top-level locks remain advisory-only and require human review; no escalation-authority keys. |

## Related CLI views

Use these read-only commands from the repository root:

```bash
PYTHONPATH=src:. python3 -m hisys.judge.smoke --format json
PYTHONPATH=src:. python3 -m hisys.judge.smoke --summary
PYTHONPATH=src:. python3 -m hisys.judge.smoke --text
PYTHONPATH=src:. python3 -m hisys.judge.smoke --status-bundle
PYTHONPATH=src:. python3 -m hisys.judge.smoke --status-bundle-canonical
PYTHONPATH=src:. python3 -m hisys.judge.smoke --status-bundle-fingerprint
```

The committed JSON artifacts are golden examples for the first and fourth views above. The canonical and fingerprint views are derived identity/checksum views for stable comparison and deduplication.

## Review guidance

- Start with `judge-advisory-smoke-status-review-bundle.json` for a compact machine/human status packet.
- Use `judge-advisory-smoke-report.json` when a reviewer needs detailed fixture outcomes, check names, side-effect flags, or embedded panel review content.
- Regenerate artifacts only as a controlled local fixture update; do not include timestamps, live-provider responses, credentials, or network-derived data.
- A smoke `PASS` is evidence for human review only. It does not grant permission for consequential action.
