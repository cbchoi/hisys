# Agent workflow packets

Hisys records Superpowers-style workflow discipline as local runtime-boundary artifacts rather than by installing an external agent plugin. The supported workflow is:

```text
spec-first packet -> bounded implementation/evidence work -> review gate -> finish packet
```

This pattern is intended for governed development and investigation runs where an agent, subagent, Ralph loop, or Hermes orchestration session may otherwise proceed without an explicit scope, evidence contract, or closure record.

## Spec-first packet

`hisys build-spec-first-packet` writes a JSON and Markdown packet under:

```text
runtime-boundary/agent-workflows/<YYYYMMDD>/<PACKET_ID>.json
runtime-boundary/agent-workflows/<YYYYMMDD>/<PACKET_ID>.md
```

The packet records:

- objective;
- scope and non-goals;
- allowed actions;
- evidence contract;
- expected artifacts;
- gate criteria;
- human approval boundary;
- no-action safety flags.

Example:

```bash
hisys build-spec-first-packet \
  --instance /path/to/instance \
  --date 20260516 \
  --packet-id SPEC-EXAMPLE-001 \
  --objective "Apply a bounded workflow change" \
  --scope "agent workflow packet schema" \
  --non-goal "automatic plugin installation" \
  --allowed-action "local file edits" \
  --allowed-action "fixture-only tests" \
  --evidence-contract "each claim cites a test, doc, or artifact ref" \
  --expected-artifact "runtime-boundary/agent-workflows/20260516/SPEC-EXAMPLE-001.json" \
  --gate-criterion "focused tests pass" \
  --gate-criterion "git diff --check passes" \
  --human-approval-boundary "Required before live external action, publication, vault mutation, or governance-gate weakening." \
  --format json
```

## Finish packet

`hisys build-finish-packet` closes a bounded run without authorizing live action. It records:

- spec packet reference;
- completed tasks;
- validation results;
- review findings;
- unresolved blockers;
- next actions;
- human gate state;
- no-action safety flags.

Example:

```bash
hisys build-finish-packet \
  --instance /path/to/instance \
  --date 20260516 \
  --packet-id FINISH-EXAMPLE-001 \
  --spec-packet-ref runtime-boundary/agent-workflows/20260516/SPEC-EXAMPLE-001.json \
  --completed-task "added spec packet schema" \
  --validation-result "pytest tests/unit/test_agent_workflow_packets.py -q: passed" \
  --review-finding "subagents remain evidence collectors, not final decision owners" \
  --unresolved-blocker "full source audit not performed" \
  --next-action "map deeper adoption after review" \
  --human-gate-state "required_before_live_external_action" \
  --format json
```

Use `--decision blocked_needs_more_evidence` when the run should close as blocked rather than complete for human review.

## Safety boundaries

The packet commands intentionally record:

- `external_call_made=false`;
- `mutation_performed=false`;
- `publication_or_live_action_approved=false`;
- `action_taken=none`.

They create local runtime-boundary artifacts only. They do not perform web access, connector execution, vault writes, publication, Git push, broker/order execution, or approval transitions.

## Subagent boundary

When packets involve subagents, the subagent contract should restrict them to evidence collection, inspection, or implementation subtasks with explicit verification handles. Subagents should not:

- approve consequential actions;
- weaken `needs_more_evidence` gates;
- write final Hisys decisions;
- perform live external actions unless a separate approved connector boundary permits it.

## Related implementation

- `src/hisys/operations/agent_workflow.py`
- `src/hisys/cli/main.py`
- `tests/unit/test_agent_workflow_packets.py`
