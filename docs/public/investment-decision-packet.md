# Investment Decision Packet Schema

`InvestmentDecisionPacket` is the Hisys schema for human-in-the-loop investment decision support.
It records an evidence-bounded buy/hold/sell-style recommendation without turning Hisys into an autonomous trading system.

## Boundary

```text
Hisys may recommend and draft.
Hisys must not execute autonomously.
Human approval and responsibility are required for consequential use.
```

The schema is intentionally conservative:

- `execution_authorized` defaults to `false`.
- `publication_or_live_action_approved` defaults to `false`.
- `human_approval.status='approved'` is required before execution authorization or live action approval can be represented.
- Approval scope is explicit: review approval does not imply publication, manual execution, or live connector execution approval.
- `execution_authorized=true` requires an approved `manual_execution` or `live_connector_execution` scope.
- `publication_or_live_action_approved=true` requires an approved `publication` scope.
- An `OrderTicketDraft` is a non-executing draft. It cannot include an execution endpoint reference.
- Live order drafts (`dry_run=false`) require approved human approval.
- Disclaimers must include both `not financial advice` and `no autonomous execution`.

## Core fields

```text
packet_id
asset
instrument_refs
time_horizon
proposed_action
weight_policy_ref
recommendation_summary
confidence
evidence_score
risk_score
contradiction_score
signals
bull_case / base_case / bear_case
decision_boundary
risk_register
chief_editor_status / devil_review_status / dars_review_status
human_insight_refs
human_approval
order_ticket_draft
execution_authorized
publication_or_live_action_approved
```

## Supported actions

```text
buy
staged_buy
hold
reduce
sell
watch
no_action
```

These are decision-support labels, not broker commands.

## Product CLI workflow

The product-level CLI boundary validates an `InvestmentDecisionPacket` JSON input,
writes user-facing JSON/Markdown packet artifacts, persists Lapidary evidence-chain
and weighted-alternative audit records, and writes a compact boundary report:

```bash
hisys build-investment-decision-packet \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --packet packet-input.json \
  --weight-policy investment-weight-policy.json

hisys review-investment-decision-packet \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --packet-id <packet_id> \
  --format json

hisys build-investment-evidence-package \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --request-id <request_id> \
  --asset "S&P 500" \
  --source-access runtime-boundary/source-connectors/<YYYYMMDD>/source-access-ACCESS-....json \
  --source-evidence runtime-boundary/source-connectors/<YYYYMMDD>/source-evidence-EVID-....json

hisys completion-status \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --validation focused=passed \
  --validation full=passed \
  --format json

hisys run-investment-decision-dry-run \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --asset "S&P 500" \
  --instrument SPY \
  --instrument VOO \
  --time-horizon "6-12 months" \
  --evidence-package evidence-package.json \
  --weight-policy investment-weight-policy.json
```

Artifacts:

```text
runtime-boundary/investment-decisions/<YYYYMMDD>/<packet_id>.json
runtime-boundary/investment-decisions/<YYYYMMDD>/<packet_id>.md
runtime-boundary/investment-decisions/<YYYYMMDD>/<policy_id>.json           # when --weight-policy is supplied
runtime-boundary/investment-decisions/<YYYYMMDD>/investment-decision-packet-report.json
data/evidence-packages/<YYYYMMDD>/PKG-INV-SOURCE-*.json                    # source-connector promotion
reports/run-summaries/<YYYYMMDD>/hisys-completion-status.json              # completion/gate report
reports/run-summaries/<YYYYMMDD>/hisys-completion-status.md
reports/run-summaries/<YYYYMMDD>/hisys-release-readiness.json              # release-readiness evidence
reports/run-summaries/<YYYYMMDD>/hisys-release-readiness.md
data/audit/<YYYYMMDD>/lapidary-governance/evidence-chains/<chain_id>.json
data/audit/<YYYYMMDD>/lapidary-governance/weighted-alternatives/<alternative_id>.json
```

The command performs no external call, no live mutation, no publication, and no
execution. It is a product artifact builder for human-reviewed decision support.
The review command reads the persisted packet/report pair and prints a bounded
operator summary for agent or human review; it also performs no mutation or
external call. `InvestmentWeightPolicy` externalizes the decision weighting
profile (`risk_tolerance`, time horizon, evidence/risk/contradiction/confidence
weights, contradiction handling), so product runs can cite a stable policy
artifact instead of relying on implicit or hard-coded weighting assumptions. When
`--weight-policy` is supplied and the packet already names `weight_policy_ref`,
the CLI rejects mismatched policy IDs so the report cannot silently attach the
wrong weighting profile. `build-investment-evidence-package` promotes persisted
source connector `SourceAccessRecord` and `SourceEvidenceItem` artifacts into a
standard investment `EvidencePackage` without a fixture backend or new external
call, preserving the source access URL/hash/time and recording
`external_call_made=false` for the promotion step. `completion-status` summarizes
completed product components, remaining gaps, validation results, and closed
safety gates into machine-readable/Markdown status artifacts; it treats live
external action as gated rather than release-complete. `release-readiness` turns
explicit quality gate evidence (`pytest`, traceability, secret scan,
backup/restore dry-run, and health status), HISYS-T-024 trace refs, and known
gaps into final human-review release evidence without live external calls or
mutations. The dry-run workflow consumes already-materialized
`EvidencePackage` JSON artifacts rather than using a fixture backend. It assembles
a bounded packet, evidence chain, weighted alternative, policy artifact, and
report while recording `fixture_backend_used=false`, `external_call_made=false`,
`mutation_performed=false`, and `action_taken=none`. Evidence packages whose
agent IDs, agent types, evidence agent IDs, or recorded actions indicate `fixture`
or `mock` provenance are rejected from this product dry-run path; fixture-backed
coverage remains isolated to lower-level tests/harnesses.

## Example status progression

```text
1. draft packet
   human_approval.status=pending
   execution_authorized=false
   publication_or_live_action_approved=false

2. Chief Editor / Devil / DARS review
   chief_editor_status=accepted_for_human_reviewed_use
   devil_review_status=completed
   dars_review_status=completed

3. product packet build
   hisys build-investment-decision-packet writes runtime-boundary packet/report artifacts
   Lapidary evidence-chain and weighted-alternative audit records are persisted
   action_taken=none

4. dry-run assembly from evidence artifacts
   hisys run-investment-decision-dry-run reads EvidencePackage artifacts without a fixture backend
   fixture_backend_used=false
   external_call_made=false
   mutation_performed=false

5. human review
   human_approval.status=approved or rejected

6. optional external execution system
   outside this schema and outside Hisys default boundary
```

## Example minimal JSON shape

```json
{
  "schema_id": "hisys.investment_decision_packet",
  "packet_id": "IDP-SP500-001",
  "producer_id": "hisys-investment-decision-support",
  "status": "draft",
  "asset": "S&P 500",
  "instrument_refs": ["SPY", "VOO"],
  "time_horizon": "6-12 months",
  "proposed_action": "staged_buy",
  "recommendation_summary": "Conditional staged exposure only if the human accepts valuation risk.",
  "confidence": 0.58,
  "evidence_score": 0.72,
  "risk_score": 0.61,
  "contradiction_score": 0.54,
  "chief_editor_status": "accepted_for_human_reviewed_use",
  "human_approval": {
    "required": true,
    "status": "pending",
    "approver_ref": "human:professor",
    "requested_scopes": ["human_reviewed_use"],
    "approved_scopes": [],
    "responsibility_statement": "Human accepts responsibility before any consequential use."
  },
  "execution_authorized": false,
  "publication_or_live_action_approved": false,
  "disclaimers": ["not financial advice", "no autonomous execution"]
}
```

## Validation intent

This schema supports professor-controlled investment decision workflows while preserving Hisys' safety model:

```text
Evidence packet -> Review gates -> Human insight -> Human approval -> Optional external action outside default Hisys execution
```

## Structured-Domain Adapter Bridge

Traceability: HISYS-FR-DOM-006, HISYS-FR-DOM-003..004, HISYS-T-028.

`InvestmentDecisionPacket` is also reachable through the structured-domain adapter substrate via `investment_spec()` (`src/hisys/domain/specs.py`) and `InvestmentAnalysisUseCase` (`src/hisys/domain/use_cases.py`). The adapter is advisory-only:

- The structured-domain adapter does not redefine `InvestmentDecisionPacket` or `InvestmentWeightPolicy`. Existing packet/dry-run/operator-review CLI commands (`build-investment-decision-packet`, `run-investment-decision-dry-run`, `review-investment-decision-packet`) remain the system of record for governed investment product artifacts.
- The adapter forwards investment packet and weight-policy refs through `request.sources` and `request.config_snapshot_refs`. Refs flow into the bridged `DomainInvestigationResult` as evidence/source refs without copying packet contents into Hermes-facing tool results.
- The adapter recommendation embeds the safety phrases `not financial advice` and `no autonomous execution` plus the governance flags `execution_authorized=false` and `publication_or_live_action_approved=false`, so audit reviewers can confirm advisory-only handling directly from the runtime artifact.
- `requires_human_review=true`, `external_call_made=false`, and `mutation_performed=false` are preserved.
- The adapter performs no order placement, publication, credential use, broker call, or other live external action. Enabling any consequential action still requires the existing `InvestmentDecisionPacket` human-approval boundary and a separate, controlled change with human-approved scopes and fixture-first tests.
