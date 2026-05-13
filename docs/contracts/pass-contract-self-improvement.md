# Pass Contract Self-Improvement

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.

## Purpose

Hisys can reduce repeated `needs_more_evidence` outcomes by proposing new or broader pass contracts, but it must not silently weaken evidence gates or self-authorize production behavior.

The approved pattern is:

```text
needs_more_evidence run artifacts
  -> classify dominant reason
  -> propose candidate pass contract
  -> generate fixture/test/review artifact plan
  -> DARS/Chief Editor/human review
  -> traceable promotion to active registry in a later change
```

## Boundary Rule

Hisys does not self-authorize lower standards. It may self-diagnose missing contracts and produce bounded proposal artifacts, but active contract promotion requires a human-reviewed, traceable code/config/docs change.

The proposal boundary must preserve:

- `automatic_promotion_allowed = false`
- `external_call_made = false`
- `mutation_performed = false`
- `publication_or_live_action_approved = false`

## Reason Taxonomy

Use these reasons to distinguish why a run stayed at `needs_more_evidence`:

| Reason | Meaning | Improvement path |
|---|---|---|
| `adapter_missing` | No domain/question adapter can produce a governed result. | Propose a domain adapter and pass contract fixture. |
| `domain_contract_missing` | Adapter may exist, but no explicit sufficiency profile defines pass criteria. | Propose a registry contract. |
| `source_count_insufficient` | Source count/diversity below contract threshold. | Add governed collection plan. |
| `independent_corroboration_missing` | Evidence lacks non-self interested corroboration. | Add corroborating source classes. |
| `contradiction_unchecked` | No Devil/DARS/negative-evidence pass. | Add contradiction-search/check requirement. |
| `claim_coverage_incomplete` | Claims are not all linked to evidence. | Add claim coverage gate. |
| `confidence_below_threshold` | Evidence exists but confidence is not sufficient for the decision class. | Add confidence/risk calibration. |
| `human_approval_required` | Evidence may be sufficient, but the action scope needs human approval. | Preserve approval gate; do not auto-promote. |

## CLI

Create a governed proposal artifact:

```bash
hisys propose-pass-contract \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --domain product_architecture \
  --question-type architecture_choice \
  --failure-mode adapter_missing \
  --example-request-id REQ-ARCH-001 \
  --format json
```

Run the full local governed improvement loop:

```bash
hisys convert-pass-contract-proposal \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --proposal-ref runtime-boundary/pass-contract-proposals/<YYYYMMDD>/CONTRACT-PROP-*.json \
  --format json

hisys evaluate-pass-contract \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --contract-ref runtime-boundary/pass-contract-candidates/<YYYYMMDD>/<contract_id>.json \
  --evidence-summary evidence-summary.json \
  --format json

hisys request-pass-contract-review \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --candidate-ref runtime-boundary/pass-contract-candidates/<YYYYMMDD>/<contract_id>.json \
  --reviewer chief_editor \
  --reviewer dars_devil \
  --format json

hisys promote-pass-contract \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --candidate-ref runtime-boundary/pass-contract-candidates/<YYYYMMDD>/<contract_id>.json \
  --review-ref runtime-boundary/pass-contract-reviews/<YYYYMMDD>/REVIEW-*.json \
  --validation-ref reports/run-summaries/<YYYYMMDD>/pass-contract-evaluation-report.json \
  --human-approval-ref APPROVAL-PASS-CONTRACT-<YYYYMMDD>-001 \
  --format json

hisys audit-needs-more-evidence \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --format json
```

Active contracts can be consumed by `investigate-domain` only when an explicit registry and evidence summary are supplied:

```bash
hisys investigate-domain \
  --instance "$HISYS_INSTANCE" \
  --request request.json \
  --date <YYYYMMDD> \
  --pass-contract-registry active-registry.json \
  --question-type architecture_choice \
  --evidence-summary evidence-summary.json
```

Expected artifacts:

```text
runtime-boundary/pass-contract-proposals/<YYYYMMDD>/CONTRACT-PROP-*.json
runtime-boundary/pass-contract-proposals/<YYYYMMDD>/CONTRACT-PROP-*.md
reports/run-summaries/<YYYYMMDD>/pass-contract-proposal-report.json
```

## Promotion Criteria

A proposal can become an active pass contract only after a later increment adds:

1. a machine-readable contract fixture or registry entry;
2. focused pass/fail/needs_more_evidence tests;
3. traceability documentation;
4. DARS/Chief Editor review where relevant;
5. validation results from pytest, traceability, secret scan, and diff checks;
6. human approval for the exact promotion scope.

This expands Hisys coverage by adding domain-specific criteria, not by reducing evidence quality.
