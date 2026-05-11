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
  --packet packet-input.json
```

Artifacts:

```text
runtime-boundary/investment-decisions/<YYYYMMDD>/<packet_id>.json
runtime-boundary/investment-decisions/<YYYYMMDD>/<packet_id>.md
runtime-boundary/investment-decisions/<YYYYMMDD>/investment-decision-packet-report.json
data/audit/<YYYYMMDD>/lapidary-governance/evidence-chains/<chain_id>.json
data/audit/<YYYYMMDD>/lapidary-governance/weighted-alternatives/<alternative_id>.json
```

The command performs no external call, no live mutation, no publication, and no
execution. It is a product artifact builder for human-reviewed decision support.

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

4. human review
   human_approval.status=approved or rejected

5. optional external execution system
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
