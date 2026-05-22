# Readiness decision record v0.0.59

## Decision

`DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-SMOKE-GATE` completed with
findings. The governed panel dispatch harness ran two Codex CLI subprocess
prompt-mode critics and wrote runtime-boundary evidence under
`/tmp/hisys-dars-codex-panel-smoke`.

## Evidence scope

- Prepared packet: `docs/examples/dars/codex-cli-subprocess-multi-critic-panel.prepared.json`
- Smoke report: `docs/reports/dars-codex-cli-subprocess-multi-critic-panel-smoke-2026-05-22.md`
- Runtime-boundary aggregate record:
  `/tmp/hisys-dars-codex-panel-smoke/runtime-boundary/dars-remote-subscription-panels/20260522/REQ-DARS-CODEX-PANEL-SMOKE-20260522-001/PANEL-DARS-CODEX-SUBPROCESS-20260522-001.json`
- Per-critic records under:
  `/tmp/hisys-dars-codex-panel-smoke/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-PANEL-SMOKE-20260522-001/`
- Local redaction refinement:
  `src/hisys/agents/dars_codex_cli_subprocess.py`
  and `tests/unit/test_dars_codex_cli_subprocess.py`

## Findings

The panel completed and preserved the required boundary fields:

```text
critic_count=2
completed_critic_count=2
external_call_made=true
model_boundary_crossed=true
local_model_call_made=false
mutation_performed=false
publication_performed=false
requires_human_review=true
```

A fail-closed redaction issue was observed and corrected locally: benign
governance vocabulary in Codex output was initially classified as a raw-secret
marker. The secret detector now blocks explicit secret field/value forms while
allowing advisory boundary language such as credential lookup not being
performed.

The logical-consistency critic reported that the prepared panel prompt did not
contain the actual DARS panel claim and bounded runtime-boundary evidence needed
to validate the claim. Therefore the smoke gate is not a no-issue continuation
point.

## Result

```text
formal_hisys_result: codex_cli_subprocess_multi_critic_panel_smoke_completed_with_findings
```

No DARS completion-claim upgrade is made. Further live panel execution is not
authorized by this record.

## Next safe row

```text
DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-EVIDENCE-PACKET-PREP
```

The next row is local/docs-control and should prepare a revised bounded panel
packet that includes the exact claim and evidence summary before any additional
live Codex panel execution.
