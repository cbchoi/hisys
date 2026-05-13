# Pass Contract Self-Improvement Roadmap Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Expand Hisys from proposal-only `needs_more_evidence` self-diagnosis into a governed pass-contract improvement loop that can classify failures, propose contracts, test them, review them, and promote approved contracts without weakening evidence standards.

**Architecture:** Keep Hisys CLI-first and governed. The active system remains conservative: proposal generation is local/report-only, active contract promotion is blocked unless a human-reviewed traceable promotion artifact is present, and DARS/Chief Editor remain advisory/review gates rather than approval authorities. Build this as small registry/schema/CLI/test increments on top of the existing `propose-pass-contract` command.

**Tech Stack:** Python CLI in `src/hisys/cli/main.py`, typed dataclasses/Pydantic-style schema modules where already used, YAML/JSON registry fixtures, pytest, existing `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, `git diff --check`.

---

## Current Baseline

Already implemented in the current working tree:

- `hisys propose-pass-contract` writes governed proposal JSON/Markdown and a run-summary report.
- Proposal artifacts preserve:
  - `automatic_promotion_allowed=false`
  - `external_call_made=false`
  - `mutation_performed=false`
  - `publication_or_live_action_approved=false`
- Documentation exists at `docs/contracts/pass-contract-self-improvement.md`.
- Traceability entry exists in `docs/traceability/README.md`.
- Unit test exists at `tests/unit/test_pass_contract_improvement_cli.py`.
- Full validation has passed once: `475 passed`, traceability OK, secret scan OK, diff check OK.

Known repository state before executing this roadmap:

- Modified: `src/hisys/cli/main.py`
- Modified: `docs/use-cases/hermes-hisys-domain-tool.md`
- Modified: `docs/traceability/README.md`
- New: `docs/contracts/pass-contract-self-improvement.md`
- New: `tests/unit/test_pass_contract_improvement_cli.py`
- Pre-existing untracked: `uv.lock` — do not stage unless separately approved.

## Design Decision: Recommended Path

| Option | Description | Pros | Cons | Decision |
|---|---|---|---|---|
| A. Keep proposal-only CLI | Only document proposal artifacts. | Safe, already done. | Does not actually widen passable coverage. | Baseline only. |
| B. Add active registry directly | Implement registry and promotion in one step. | Fast path to functionality. | Higher risk: accidental standard weakening or promotion bugs. | Reject for now. |
| C. Stage registry, evaluation, review, promotion | Add schema/registry, then evaluation, then review/promotion gates. | Best traceability and safety; matches governed tool intent. | More increments. | Recommended. |

Proceed with Option C.

## Acceptance Criteria for the Whole Roadmap

1. Every `needs_more_evidence` result can carry at least one machine-readable reason code.
2. Pass contracts are represented in a registry, not hardcoded only in CLI prose.
3. Contract evaluation returns one of: `passed`, `needs_more_evidence`, `failed`, or `human_approval_required` with evidence-backed blockers.
4. Proposal artifacts can be transformed into candidate registry entries, but only as inactive candidates.
5. Promotion to active registry requires explicit human approval metadata and passes tests.
6. DARS/Chief Editor review artifacts remain advisory/review-only and cannot approve live action by themselves.
7. No external calls, publication, mutation, credential resolution, or live action is introduced by routine contract planning/evaluation tests.
8. Full validation passes: focused pytest, full pytest, traceability, secret scan, diff check.

---

## Phase 0: Freeze Current Proposal Increment

### Task 0.1: Review current diff before adding more work

**Objective:** Ensure the baseline proposal increment is clean before extending it.

**Files:**
- Inspect: `src/hisys/cli/main.py`
- Inspect: `tests/unit/test_pass_contract_improvement_cli.py`
- Inspect: `docs/contracts/pass-contract-self-improvement.md`
- Inspect: `docs/use-cases/hermes-hisys-domain-tool.md`
- Inspect: `docs/traceability/README.md`

**Step 1: Run status and diff checks**

```bash
git status --short
git diff --check
python3 -m pytest tests/unit/test_pass_contract_improvement_cli.py -q
```

Expected:

```text
1 passed
git diff --check has no output
```

**Step 2: Commit baseline if approved**

Only stage the known intended files. Do not stage `uv.lock` unless explicitly approved.

```bash
git add \
  src/hisys/cli/main.py \
  tests/unit/test_pass_contract_improvement_cli.py \
  docs/contracts/pass-contract-self-improvement.md \
  docs/use-cases/hermes-hisys-domain-tool.md \
  docs/traceability/README.md

git commit -m "feat: add governed pass-contract proposal path"
```

Expected: one focused commit.

---

## Phase 1: Introduce Pass Contract Registry Schema

### Task 1.1: Add schema tests for registry records

**Objective:** Define a machine-readable pass-contract registry entry with safe defaults.

**Files:**
- Create: `tests/unit/test_pass_contract_registry_schema.py`
- Create later: `src/hisys/contracts/pass_registry.py`

**Step 1: Write failing test**

```python
from __future__ import annotations

import pytest

from hisys.contracts.pass_registry import PassContractRegistryEntry, load_pass_contract_registry


def test_registry_entry_defaults_to_inactive_candidate():
    entry = PassContractRegistryEntry(
        contract_id="product_architecture_architecture_choice_v0_1_candidate",
        domain="product_architecture",
        question_type="architecture_choice",
        status="candidate",
        version="0.1.0",
        minimum_evidence={"artifact_refs_required": True},
        blocked_if=["no_traceable_artifact_refs"],
        promotion_gate="human_reviewed_traceable_change",
    )

    assert entry.status == "candidate"
    assert entry.active is False
    assert entry.automatic_promotion_allowed is False
    assert entry.external_call_made is False
    assert entry.mutation_performed is False
    assert entry.publication_or_live_action_approved is False


def test_registry_rejects_active_without_human_approval_ref():
    with pytest.raises(ValueError, match="human_approval_ref"):
        PassContractRegistryEntry(
            contract_id="unsafe_active",
            domain="product_architecture",
            question_type="architecture_choice",
            status="active",
            active=True,
            version="0.1.0",
            minimum_evidence={"artifact_refs_required": True},
            blocked_if=["no_traceable_artifact_refs"],
            promotion_gate="human_reviewed_traceable_change",
        )
```

**Step 2: Run RED**

```bash
python3 -m pytest tests/unit/test_pass_contract_registry_schema.py -q
```

Expected: FAIL because `hisys.contracts.pass_registry` does not exist.

### Task 1.2: Implement minimal registry schema

**Objective:** Add the schema module and package init.

**Files:**
- Create: `src/hisys/contracts/__init__.py`
- Create: `src/hisys/contracts/pass_registry.py`

**Step 1: Implement minimal code**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


_ALLOWED_STATUS = {"candidate", "active", "retired"}


@dataclass(frozen=True)
class PassContractRegistryEntry:
    contract_id: str
    domain: str
    question_type: str
    status: str
    version: str
    minimum_evidence: dict[str, Any]
    blocked_if: list[str]
    promotion_gate: str
    active: bool = False
    human_approval_ref: str | None = None
    automatic_promotion_allowed: bool = False
    external_call_made: bool = False
    mutation_performed: bool = False
    publication_or_live_action_approved: bool = False
    review_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_STATUS:
            raise ValueError(f"invalid status: {self.status}")
        if not self.contract_id.strip():
            raise ValueError("contract_id is required")
        if self.active and self.status != "active":
            raise ValueError("active entries must use status=active")
        if self.status == "active" and not self.human_approval_ref:
            raise ValueError("human_approval_ref is required for active contracts")
        if self.automatic_promotion_allowed:
            raise ValueError("automatic promotion is not allowed")
        if self.external_call_made or self.mutation_performed or self.publication_or_live_action_approved:
            raise ValueError("registry entries must not record live side effects")


def load_pass_contract_registry(path: Path) -> list[PassContractRegistryEntry]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("contracts", data if isinstance(data, list) else [])
    return [PassContractRegistryEntry(**entry) for entry in entries]
```

**Step 2: Run GREEN**

```bash
python3 -m pytest tests/unit/test_pass_contract_registry_schema.py -q
```

Expected: PASS.

### Task 1.3: Add registry fixture and docs

**Objective:** Provide an inactive candidate fixture for architecture-choice coverage.

**Files:**
- Create: `tests/fixtures/pass-contracts/product_architecture_architecture_choice.json`
- Modify: `docs/contracts/pass-contract-self-improvement.md`
- Modify: `docs/traceability/README.md`

**Step 1: Create fixture**

```json
{
  "schema_id": "hisys.pass_contract.registry",
  "schema_version": "0.1.0",
  "contracts": [
    {
      "contract_id": "product_architecture_architecture_choice_v0_1_candidate",
      "domain": "product_architecture",
      "question_type": "architecture_choice",
      "status": "candidate",
      "active": false,
      "version": "0.1.0",
      "minimum_evidence": {
        "artifact_refs_required": true,
        "alternative_set_required": true,
        "claim_coverage_required": true,
        "contradiction_check_required": true,
        "dars_critique_required": true
      },
      "blocked_if": [
        "only_user_opinion",
        "only_fixture_evidence_for_live_claims",
        "no_traceable_artifact_refs",
        "boundary_violation_detected"
      ],
      "promotion_gate": "human_reviewed_traceable_change",
      "automatic_promotion_allowed": false,
      "external_call_made": false,
      "mutation_performed": false,
      "publication_or_live_action_approved": false
    }
  ]
}
```

**Step 2: Run focused tests**

```bash
python3 -m pytest tests/unit/test_pass_contract_registry_schema.py -q
```

Expected: PASS.

**Step 3: Commit**

```bash
git add src/hisys/contracts tests/unit/test_pass_contract_registry_schema.py tests/fixtures/pass-contracts docs/contracts/pass-contract-self-improvement.md docs/traceability/README.md
git commit -m "feat: add pass-contract registry schema"
```

---

## Phase 2: Add Needs-More-Evidence Reason Records

### Task 2.1: Add reason taxonomy schema tests

**Objective:** Standardize `needs_more_evidence` reason codes and blocker metadata.

**Files:**
- Create: `tests/unit/test_needs_more_evidence_reasons.py`
- Create later: `src/hisys/contracts/evidence_reasons.py`

**Step 1: Write failing test**

```python
from hisys.contracts.evidence_reasons import NeedsMoreEvidenceReason, classify_reason


def test_classifies_adapter_missing():
    reason = classify_reason(adapter_found=False, contract_found=False, source_count=0, contradiction_checked=False)
    assert reason.code == NeedsMoreEvidenceReason.ADAPTER_MISSING
    assert reason.blocks_passing is True


def test_classifies_independent_corroboration_missing_after_sources_exist():
    reason = classify_reason(
        adapter_found=True,
        contract_found=True,
        source_count=3,
        independent_corroboration=False,
        contradiction_checked=True,
    )
    assert reason.code == NeedsMoreEvidenceReason.INDEPENDENT_CORROBORATION_MISSING
```

**Step 2: Run RED**

```bash
python3 -m pytest tests/unit/test_needs_more_evidence_reasons.py -q
```

Expected: FAIL.

### Task 2.2: Implement reason classification helper

**Objective:** Create deterministic classification independent of LLM judgment.

**Files:**
- Create: `src/hisys/contracts/evidence_reasons.py`

**Implementation note:** Use `Enum` and frozen dataclass. Keep it simple; do not wire into all domain results yet.

**Step 1: Implement helper**

Include codes:

```text
adapter_missing
domain_contract_missing
source_count_insufficient
independent_corroboration_missing
contradiction_unchecked
claim_coverage_incomplete
confidence_below_threshold
human_approval_required
```

**Step 2: Run GREEN**

```bash
python3 -m pytest tests/unit/test_needs_more_evidence_reasons.py -q
```

Expected: PASS.

### Task 2.3: Wire reason codes into proposal artifacts

**Objective:** Replace duplicated hardcoded taxonomy in `src/hisys/cli/main.py` with the shared taxonomy.

**Files:**
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_pass_contract_improvement_cli.py`

**Step 1: Add test assertion**

Assert the proposal JSON includes all reason taxonomy codes from `NeedsMoreEvidenceReason`.

**Step 2: Update implementation**

Import the shared taxonomy and render codes from it.

**Step 3: Run tests**

```bash
python3 -m pytest tests/unit/test_pass_contract_improvement_cli.py tests/unit/test_needs_more_evidence_reasons.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/hisys/contracts/evidence_reasons.py src/hisys/cli/main.py tests/unit/test_needs_more_evidence_reasons.py tests/unit/test_pass_contract_improvement_cli.py
git commit -m "feat: add needs-more-evidence reason taxonomy"
```

---

## Phase 3: Add Contract Evaluation Engine

### Task 3.1: Write evaluator tests

**Objective:** Evaluate evidence summaries against a registry entry and return a gated result.

**Files:**
- Create: `tests/unit/test_pass_contract_evaluator.py`
- Create later: `src/hisys/contracts/evaluator.py`

**Step 1: Write failing tests**

Test cases:

1. Missing artifact refs -> `needs_more_evidence` with `no_traceable_artifact_refs`.
2. Full candidate evidence -> `passed` only for human-reviewed use, not live action.
3. Human approval required -> `human_approval_required` when the contract class needs approval.
4. Boundary violation -> `failed`.

**Minimal test shape:**

```python
from hisys.contracts.evaluator import EvidenceSummary, evaluate_pass_contract
from hisys.contracts.pass_registry import PassContractRegistryEntry


def test_missing_artifact_refs_blocks_passing():
    entry = PassContractRegistryEntry(...)
    summary = EvidenceSummary(artifact_refs=[], alternative_count=2, claims_covered=True)
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "needs_more_evidence"
    assert "no_traceable_artifact_refs" in result.blockers
```

**Step 2: Run RED**

```bash
python3 -m pytest tests/unit/test_pass_contract_evaluator.py -q
```

Expected: FAIL.

### Task 3.2: Implement minimal evaluator

**Objective:** Create pure function evaluation with no filesystem/external calls.

**Files:**
- Create: `src/hisys/contracts/evaluator.py`

**Rules:**

- If boundary violation exists -> `failed`.
- If required artifact refs missing -> `needs_more_evidence`.
- If alternatives required and fewer than 2 alternatives -> `needs_more_evidence`.
- If contradiction check required but missing -> `needs_more_evidence`.
- If the result is consequential and no human approval ref -> `human_approval_required`.
- Else -> `passed` with `human_reviewed_use_only=true`.

**Step 1: Implement dataclasses**

- `EvidenceSummary`
- `PassContractEvaluationResult`
- `evaluate_pass_contract(entry, summary)`

**Step 2: Run GREEN**

```bash
python3 -m pytest tests/unit/test_pass_contract_evaluator.py -q
```

Expected: PASS.

### Task 3.3: Add CLI for dry-run evaluation

**Objective:** Let Hermes/Hisys evaluate a registry entry against a local JSON evidence summary.

**Files:**
- Modify: `src/hisys/cli/main.py`
- Create: `tests/unit/test_pass_contract_evaluate_cli.py`

**CLI:**

```bash
hisys evaluate-pass-contract \
  --instance "$HISYS_INSTANCE" \
  --date 20260513 \
  --contract-ref tests/fixtures/pass-contracts/product_architecture_architecture_choice.json \
  --evidence-summary tests/fixtures/pass-contracts/evidence-summary-passing.json \
  --format json
```

**Expected artifacts:**

```text
reports/run-summaries/<date>/pass-contract-evaluation-report.json
runtime-boundary/pass-contract-evaluations/<date>/EVAL-*.json
```

**Step 1: Write failing CLI test**

Use `tmp_path`, local fixture JSON, and assert report flags remain false.

**Step 2: Implement CLI parser/handler**

Keep it local-only. Do not make external calls.

**Step 3: Run tests**

```bash
python3 -m pytest tests/unit/test_pass_contract_evaluate_cli.py tests/unit/test_pass_contract_evaluator.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/hisys/contracts/evaluator.py src/hisys/cli/main.py tests/unit/test_pass_contract_evaluator.py tests/unit/test_pass_contract_evaluate_cli.py tests/fixtures/pass-contracts
git commit -m "feat: evaluate pass contracts against evidence summaries"
```

---

## Phase 4: Convert Proposal to Candidate Registry Entry

### Task 4.1: Add proposal-to-registry conversion tests

**Objective:** Transform `propose-pass-contract` output into an inactive registry candidate.

**Files:**
- Create: `tests/unit/test_pass_contract_proposal_conversion.py`
- Modify later: `src/hisys/contracts/pass_registry.py`

**Step 1: Write failing test**

```python
from hisys.contracts.pass_registry import candidate_from_proposal


def test_candidate_from_proposal_is_inactive_and_not_auto_promoted(proposal_dict):
    candidate = candidate_from_proposal(proposal_dict)
    assert candidate.status == "candidate"
    assert candidate.active is False
    assert candidate.automatic_promotion_allowed is False
```

**Step 2: Run RED**

```bash
python3 -m pytest tests/unit/test_pass_contract_proposal_conversion.py -q
```

Expected: FAIL.

### Task 4.2: Implement conversion helper and CLI

**Objective:** Add an explicit conversion command that writes candidate registry JSON without activating it.

**Files:**
- Modify: `src/hisys/contracts/pass_registry.py`
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_pass_contract_proposal_conversion.py`

**CLI:**

```bash
hisys convert-pass-contract-proposal \
  --instance "$HISYS_INSTANCE" \
  --date 20260513 \
  --proposal-ref runtime-boundary/pass-contract-proposals/20260513/CONTRACT-PROP-*.json \
  --format json
```

**Expected artifact:**

```text
runtime-boundary/pass-contract-candidates/<date>/<contract_id>.json
reports/run-summaries/<date>/pass-contract-candidate-report.json
```

**Step 1:** Implement relative-ref safe loading under instance root.

**Step 2:** Write candidate artifact with inactive status.

**Step 3:** Preserve boundary flags false.

**Step 4:** Run focused tests.

```bash
python3 -m pytest tests/unit/test_pass_contract_proposal_conversion.py tests/unit/test_pass_contract_improvement_cli.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/hisys/contracts/pass_registry.py src/hisys/cli/main.py tests/unit/test_pass_contract_proposal_conversion.py
git commit -m "feat: convert pass-contract proposals to inactive candidates"
```

---

## Phase 5: Add Advisory Review Package

### Task 5.1: Create review package schema tests

**Objective:** Generate DARS/Chief Editor review artifacts for candidate contracts without granting approval authority.

**Files:**
- Create: `tests/unit/test_pass_contract_review_package.py`
- Create later: `src/hisys/contracts/review_package.py`

**Step 1: Write failing tests**

Assertions:

- Review package includes candidate contract ref.
- Review package records requested reviewer roles: `chief_editor`, `dars_devil`.
- `approval_authority_transferred=false`.
- `promotion_allowed=false` unless a later human approval artifact exists.

**Step 2: Run RED**

```bash
python3 -m pytest tests/unit/test_pass_contract_review_package.py -q
```

Expected: FAIL.

### Task 5.2: Implement review package CLI

**Objective:** Produce a local review request artifact for candidate contracts.

**Files:**
- Create: `src/hisys/contracts/review_package.py`
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_pass_contract_review_package.py`

**CLI:**

```bash
hisys request-pass-contract-review \
  --instance "$HISYS_INSTANCE" \
  --date 20260513 \
  --candidate-ref runtime-boundary/pass-contract-candidates/20260513/<contract_id>.json \
  --reviewer chief_editor \
  --reviewer dars_devil \
  --format json
```

**Expected artifacts:**

```text
runtime-boundary/pass-contract-reviews/<date>/REVIEW-*.json
reports/run-summaries/<date>/pass-contract-review-report.json
```

**Step 1:** Implement local-only artifact generation.

**Step 2:** Verify no external DARS call occurs.

**Step 3:** Run tests.

```bash
python3 -m pytest tests/unit/test_pass_contract_review_package.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/hisys/contracts/review_package.py src/hisys/cli/main.py tests/unit/test_pass_contract_review_package.py
git commit -m "feat: add advisory pass-contract review packages"
```

---

## Phase 6: Human-Approved Promotion Gate

> **High-impact gate:** Stop here and ask for confirmation before implementing. This phase changes the path from proposal/candidate artifacts to active registry promotion.

### Task 6.1: Define promotion schema tests

**Objective:** Require explicit human approval before candidate contract activation.

**Files:**
- Create: `tests/unit/test_pass_contract_promotion.py`
- Modify later: `src/hisys/contracts/pass_registry.py`

**Step 1: Write failing tests**

Assertions:

- Promotion without `--human-approval-ref` fails.
- Promotion with human approval writes active registry artifact.
- Promotion refuses candidates whose tests/reviews are missing.
- Promotion preserves no live action flags.

**Step 2: Run RED**

```bash
python3 -m pytest tests/unit/test_pass_contract_promotion.py -q
```

Expected: FAIL.

### Task 6.2: Implement promotion CLI with strict gates

**Objective:** Promote an inactive candidate to active registry only after explicit approval and validation refs.

**Files:**
- Modify: `src/hisys/contracts/pass_registry.py`
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_pass_contract_promotion.py`

**CLI:**

```bash
hisys promote-pass-contract \
  --instance "$HISYS_INSTANCE" \
  --date 20260513 \
  --candidate-ref runtime-boundary/pass-contract-candidates/20260513/<contract_id>.json \
  --review-ref runtime-boundary/pass-contract-reviews/20260513/REVIEW-*.json \
  --validation-ref reports/run-summaries/20260513/pass-contract-evaluation-report.json \
  --human-approval-ref APPROVAL-PASS-CONTRACT-20260513-001 \
  --format json
```

**Expected artifacts:**

```text
runtime-boundary/pass-contract-promotions/<date>/PROMOTION-*.json
config/pass-contract-registry/active/<contract_id>.json
reports/run-summaries/<date>/pass-contract-promotion-report.json
```

**Safety rules:**

- Fail closed if approval ref is blank.
- Fail closed if review ref missing.
- Fail closed if validation ref missing.
- Do not execute any live action.
- Do not call DARS live; only consume local review artifacts.

**Step 1:** Implement safe relative path loading.

**Step 2:** Write active registry entry with `human_approval_ref`.

**Step 3:** Write promotion report.

**Step 4:** Run tests.

```bash
python3 -m pytest tests/unit/test_pass_contract_promotion.py tests/unit/test_pass_contract_registry_schema.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/hisys/contracts/pass_registry.py src/hisys/cli/main.py tests/unit/test_pass_contract_promotion.py
git commit -m "feat: add human-approved pass-contract promotion gate"
```

---

## Phase 7: Integrate Active Registry into Domain Investigation

> **Midpoint/high-impact gate:** Confirm which domain should be integrated first. Recommended first target: `product_architecture / architecture_choice`, because it matches the current user problem and avoids broad research claims.

### Task 7.1: Locate domain investigation decision point

**Objective:** Identify the exact function where `quality_gate` is assigned for domain investigations.

**Files:**
- Inspect: `src/hisys/cli/main.py`
- Inspect: `src/hisys/schemas/domain_investigation.py`
- Inspect: related tests under `tests/unit/test_domain_investigation.py`

**Step 1: Search**

```bash
python3 - <<'PY'
from pathlib import Path
for p in Path('src/hisys').rglob('*.py'):
    text = p.read_text(encoding='utf-8')
    if 'needs_more_evidence' in text or 'quality_gate' in text:
        print(p)
PY
```

**Expected:** list of candidate files.

### Task 7.2: Add integration tests for active registry override

**Objective:** A domain investigation can pass only when active contract criteria are met.

**Files:**
- Modify: `tests/unit/test_domain_investigation.py`
- Possibly create: `tests/unit/test_domain_investigation_pass_contracts.py`

**Test cases:**

1. No active contract -> `needs_more_evidence` with `domain_contract_missing`.
2. Active contract but insufficient evidence -> `needs_more_evidence` with blocker.
3. Active contract and sufficient evidence -> `completed` or `quality_gate=passed` for human-reviewed use.
4. Consequential/live action request -> `human_approval_required`, not auto-completed.

**Step 1: Write failing tests.**

**Step 2: Run RED.**

```bash
python3 -m pytest tests/unit/test_domain_investigation_pass_contracts.py -q
```

Expected: FAIL.

### Task 7.3: Implement active registry lookup in domain investigation path

**Objective:** Use active registry contracts when resolving domain/question-type evidence gates.

**Files:**
- Modify: likely `src/hisys/cli/main.py` or dedicated domain investigation module
- Modify: `src/hisys/contracts/evaluator.py`

**Rules:**

- If no active contract, preserve conservative fallback.
- If active contract exists, evaluate evidence summary.
- Pass only for human-reviewed use.
- Preserve existing browser/public-web sufficiency gates.

**Step 1:** Implement minimal lookup by domain/question_type.

**Step 2:** Run focused tests.

```bash
python3 -m pytest tests/unit/test_domain_investigation_pass_contracts.py tests/unit/test_domain_investigation.py -q
```

Expected: PASS.

**Step 3: Commit**

```bash
git add src/hisys tests/unit/test_domain_investigation_pass_contracts.py tests/unit/test_domain_investigation.py
git commit -m "feat: apply active pass contracts to domain investigations"
```

---

## Phase 8: Operator Audit and Metrics

### Task 8.1: Add needs-more-evidence audit report

**Objective:** Summarize repeated failures by reason, domain, and question type.

**Files:**
- Create: `tests/unit/test_needs_more_evidence_audit_cli.py`
- Create later: `src/hisys/contracts/audit.py`
- Modify: `src/hisys/cli/main.py`

**CLI:**

```bash
hisys audit-needs-more-evidence \
  --instance "$HISYS_INSTANCE" \
  --date 20260513 \
  --format json
```

**Expected report:**

```json
{
  "schema_id": "hisys.needs_more_evidence.audit_report",
  "dominant_reasons": [
    {"reason": "adapter_missing", "count": 3}
  ],
  "recommended_next_actions": [
    "propose_pass_contract"
  ]
}
```

**Step 1:** Write failing test using local fixture artifacts.

**Step 2:** Implement local artifact scanner.

**Step 3:** Run focused tests.

```bash
python3 -m pytest tests/unit/test_needs_more_evidence_audit_cli.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/hisys/contracts/audit.py src/hisys/cli/main.py tests/unit/test_needs_more_evidence_audit_cli.py
git commit -m "feat: audit needs-more-evidence failure patterns"
```

---

## Phase 9: End-to-End Harness

### Task 9.1: Add full local E2E test

**Objective:** Verify the whole governed loop without live side effects.

**Files:**
- Create: `tests/integration/test_pass_contract_self_improvement_flow.py`

**Flow:**

```text
propose-pass-contract
  -> convert-pass-contract-proposal
  -> evaluate-pass-contract
  -> request-pass-contract-review
  -> promote-pass-contract with human approval ref
  -> domain investigation uses active contract
```

**Assertions:**

- All artifacts exist.
- All routine steps before promotion keep promotion inactive.
- Promotion requires human approval ref.
- No external calls/mutations/publication/live action.
- Active registry affects only scoped domain/question type.

**Step 1:** Write failing integration test.

**Step 2:** Fix integration gaps.

**Step 3:** Run integration test.

```bash
python3 -m pytest tests/integration/test_pass_contract_self_improvement_flow.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add tests/integration/test_pass_contract_self_improvement_flow.py src/hisys docs/traceability/README.md
git commit -m "test: cover governed pass-contract self-improvement flow"
```

---

## Phase 10: Final Documentation and Release Readiness

### Task 10.1: Update public/operator docs

**Objective:** Make the workflow usable by Hermes/operator without source diving.

**Files:**
- Modify: `docs/contracts/pass-contract-self-improvement.md`
- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`
- Modify: `docs/public/agent-tool-manual.md` if public tool docs include CLI command lists
- Modify: `docs/traceability/README.md`

**Content required:**

- Command sequence.
- Artifact paths.
- Safety gates.
- Failure reason taxonomy.
- Promotion approval requirements.
- Examples for `product_architecture / architecture_choice`.

**Verification:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected: all pass.

### Task 10.2: Run full validation

**Objective:** Verify the complete roadmap implementation.

**Commands:**

```bash
python3 -m pytest -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected:

```text
all tests pass
traceability OK
secret_scan hit_count=0
git diff --check has no output
```

### Task 10.3: Final review and commit

**Objective:** Complete the feature with a focused final docs/traceability commit.

```bash
git add docs src tests
git status --short
git commit -m "docs: document pass-contract self-improvement workflow"
```

---

## 50% Gate Recommendation

After Phase 5, stop and report:

- registry schema implemented or not;
- evaluator implemented or not;
- candidate conversion implemented or not;
- advisory review package implemented or not;
- validation results;
- whether promotion should proceed.

Ask for explicit approval before Phase 6 because promotion writes active registry artifacts.

## High-Impact Gate Recommendation

Before Phase 7, ask which domain/question type should be activated first. Recommended first scope:

```text
domain=product_architecture
question_type=architecture_choice
```

Do not generalize to all research/domain questions until at least one domain has a green E2E harness.

## Final Validation Checklist

- [ ] Focused tests for each new module pass.
- [ ] Full `python3 -m pytest -q` passes.
- [ ] `python3 scripts/validate_traceability.py` passes.
- [ ] `python3 scripts/scan_secrets.py` reports `hit_count=0`.
- [ ] `git diff --check` has no output.
- [ ] No raw credential/token values added.
- [ ] `uv.lock` remains unstaged unless explicitly approved.
- [ ] Every active contract promotion has a human approval ref.
- [ ] No live external call, mutation, publication, or execution is introduced by routine tests.
