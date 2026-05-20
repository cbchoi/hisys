# M21.2 Milestone Plan — Traceability Coverage CLI Wrapper

## Objective

Prepare a controlled CLI wrapper for the existing M21.1 traceability coverage reporter.

## Milestones

1. RED: add CLI smoke test for `hisys traceability-coverage`.
2. GREEN: add only the argparse command and dispatcher needed to call the M21.1 reporter/writer.
3. Gate: update traceability/Ralph and validate domain, DARS, traceability, secret scan, and whitespace gates.

## Boundaries

- Local-only repo reads.
- Runtime-boundary JSON/Markdown writes only.
- Advisory-only report; human review required.
- No external calls, credentials, publication, live connector execution, or remote push.
