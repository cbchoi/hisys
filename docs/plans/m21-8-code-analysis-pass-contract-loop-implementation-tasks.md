# Milestone M21.8 — Code-Analysis Pass-Contract Loop Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. This plan is the document-RED/Prepare artifact for the M21.8 code-analysis pass-contract loop. The existing pass-contract infrastructure (`src/hisys/contracts/pass_registry.py`, `evaluator.py`, `evidence_reasons.py`, `review_package.py` plus the `propose-pass-contract` / `evaluate-pass-contract` / `convert-pass-contract-proposal` / `request-pass-contract-review` / `promote-pass-contract` / `audit-needs-more-evidence` CLI surface) is reused as-is. M21.8 only adds a thin code-analysis-specific evidence-summary adapter, fixture contracts for code-analysis question types, and a deterministic local writer that persists evaluation reports under `runtime-boundary/code-analysis-pass-contracts/<YYYYMMDD>/`. M21.8 does not grant any new promotion authority, never enables automatic promotion, never authorizes live external action, never reads raw source, never calls `subprocess` or `.git/`, and never calls `date.today()`.

**Goal:** Let a caller ask "do the M21.1..M21.7 code-analysis reports for instance `I` meet a registry pass-contract `C` for code-analysis question type `Q`?" and receive a deterministic, advisory-only `passed | needs_more_evidence | failed | human_approval_required` result with reason codes and supporting refs. The loop is local-only, fixture-driven, and never advances a candidate to `active` outside the existing human-approved promotion gate.

**Architecture:** Reuse all four existing pass-contract surfaces:

- `src/hisys/contracts/pass_registry.PassContractRegistryEntry` (status/active/promotion gating preserved)
- `src/hisys/contracts/evaluator.EvidenceSummary` / `evaluate_pass_contract` (no new fields; reuse `artifact_refs`, `alternative_count`, `claims_covered`, `contradiction_checked`, `dars_critique_refs`, `consequential_use`, `human_approval_ref`, `boundary_violation_detected`)
- `src/hisys/contracts/evidence_reasons.NeedsMoreEvidenceReason` (reuse existing reason codes; M21.8 does not introduce new codes)
- `src/hisys/contracts/review_package` (reuse for human-gate review when a code-analysis evaluation reaches `human_approval_required`)

M21.8 adds:

1. `src/hisys/operations/code_analysis_pass_contract.py` — a pure adapter that ingests trusted M21.1 `hisys.traceability.coverage.v1`, M21.3 `hisys.runtime_boundary.consistency.v1`, M21.4 `hisys.codebase_map.freshness.v1`, M21.5 `hisys.codebase_regression_benchmarks.v1`, M21.6 `hisys.change_impact.v1`, and M21.7 `hisys.architecture_candidates.v1` dict payloads and renders a typed `EvidenceSummary` plus a deterministic Markdown/JSON writer for the evaluation report. Inputs are caller-supplied trusted payloads only. No file bodies, no `runtime-boundary/` directory crawls, no `.git/` reads, no `subprocess`, no `date.today()`.
2. `tests/fixtures/pass-contracts/code_analysis/` — fixture pass-contract entries for code-analysis question types, all `status=candidate`, `active=false`, `automatic_promotion_allowed=false`, `promotion_gate=human_reviewed_traceable_change`.
3. A thin `hisys evaluate-code-analysis-contract` CLI subcommand that wraps the adapter (later increment; not in the M21.8 PREP commit).

**Tech Stack:** Python, dataclasses, json, pathlib, pytest, existing Hisys CLI `main(argv)` tests, existing pass-contract package.

**Context Packet:**
- Current HEAD: `0ad5a63 feat: add architecture candidates cli wrapper` (post-M21.7-CLI).
- Existing reusable pass-contract surfaces: `src/hisys/contracts/{pass_registry.py,evaluator.py,evidence_reasons.py,review_package.py}`; CLI dispatcher branches in `src/hisys/cli/main.py` for `propose-pass-contract`, `evaluate-pass-contract`, `convert-pass-contract-proposal`, `request-pass-contract-review`, `promote-pass-contract`, `audit-needs-more-evidence`.
- Existing M21 code-analysis report producers and schemas: `src/hisys/operations/traceability_coverage.py` (M21.1, `hisys.traceability.coverage.v1`); `src/hisys/operations/runtime_boundary_consistency.py` (M21.3, `hisys.runtime_boundary.consistency.v1`); `src/hisys/operations/codebase_map_freshness.py` (M21.4, `hisys.codebase_map.freshness.v1`); `src/hisys/operations/codebase_regression_benchmarks.py` (M21.5, `hisys.codebase_regression_benchmarks.v1`); `src/hisys/operations/change_impact.py` (M21.6, `hisys.change_impact.v1`); `src/hisys/operations/architecture_candidates.py` (M21.7, `hisys.architecture_candidates.v1`).
- Existing fixture: `tests/fixtures/pass-contracts/product_architecture_architecture_choice.json` (shape precedent only; M21.8 does not modify it).
- Pre-existing higher-level roadmap: `docs/plans/2026-05-13-pass-contract-self-improvement-roadmap.md` (M21.8 inherits Phase 0..5 surfaces; M21.8 does not advance promotion past `candidate` and does not change the human-approved promotion gate).
- Documentation/control: `docs/traceability/README.md` and `ralph.md`.

**Boundary Record:** Local docs/control preparation only. The M21.8 PREP commit adds this plan plus a `ralph.md` Reflection Log entry and Resume checkpoint. No production code, no tests, no CLI surface, no fixture data, no remote push, no live external action, no credential lookup, no `subprocess`, no `.git/` read, no `date.today()`, no raw source archival, no new pass-contract reason codes, no new promotion authority, no expansion of `active` registry without an explicit human-approval ref carried verbatim, and no live model call.

---

## Accepted decisions

1. **Reuse, do not extend, the existing pass-contract types.** The M21.8 adapter must reuse `PassContractRegistryEntry`, `EvidenceSummary`, `PassContractEvaluationResult`, and the existing reason taxonomy without adding or removing fields. Code-analysis-specific information rides on existing fields (`artifact_refs`, `dars_critique_refs`, `boundary_violation_detected`, etc.).
2. **Inputs are trusted caller-supplied report payloads only.** The adapter accepts dict payloads matching the M21.1/M21.3/M21.4/M21.5/M21.6/M21.7 schema IDs. It does not load files itself, does not crawl `runtime-boundary/`, does not call `subprocess`, and does not call `date.today()`.
3. **Code-analysis question_type taxonomy is bounded.** M21.8 introduces five candidate question types via fixture contracts only:
   - `traceability_coverage_review` (consumes M21.1 + M21.7 cross-signal)
   - `runtime_boundary_consistency_review` (consumes M21.3)
   - `codebase_map_freshness_review` (consumes M21.4)
   - `change_impact_review` (consumes M21.6 + M21.1)
   - `architecture_candidate_review` (consumes M21.7 + M21.1 + M21.4 + M21.6)
   Each fixture contract is `domain=code_analysis`, `status=candidate`, `active=false`, `automatic_promotion_allowed=false`, `promotion_gate=human_reviewed_traceable_change`. M21.8 does NOT mark any fixture contract `active`. Promotion to `active` continues to require the existing human-approved promotion CLI flow.
4. **Evidence mapping rules are deterministic and observation-only.** Mapping rules consume only count/list/flag fields already present in the M21.1..M21.7 schemas (e.g., `coverage_count`, `unreferenced_requirements`, `stale_partitions`, `unsafe_partitions`, `unsafe_changed_refs`, `candidates`). The adapter never opens a referenced file, never interprets raw source content, and never expands the schema vocabulary.
5. **Reports are written under a dedicated runtime-boundary partition.** Output path is `runtime-boundary/code-analysis-pass-contracts/<YYYYMMDD>/<contract_id>-evaluation.{json,md}`. The writer rejects non-`YYYYMMDD` dates, persists `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, and records the verbatim `human_approval_ref` only if the caller supplied one.
6. **CLI surface is deferred to M21.8-CLI.** The M21.8 GREEN module ships without a CLI surface. The thin `hisys evaluate-code-analysis-contract --instance <root> --date <YYYYMMDD> --contract-ref <json> --evidence-summary <json>` wrapper comes in a separate `M21.8-CLI` Prepare/RED that mirrors the M21.7-CLI thin-wrapper pattern.
7. **No rollback to active registry from M21.8.** A `failed` or `needs_more_evidence` evaluation never rolls back an `active` contract. Active-contract lifecycle remains under the existing `promote-pass-contract` flow. M21.8 only writes advisory evaluation artifacts and does not modify any `active/` or `candidate/` registry entry.
8. **Traceability required.** The M21.8 GREEN commit will add a `M21.8` row to `docs/traceability/README.md` linking the plan, adapter module, fixture directory, and tests; M21.8 PREP only adds the PREP doc and the ralph.md Reflection Log entry.

---

## Sub-task split

M21.8 ships in four increments. Only the PREP commit is authorized by this document.

| Task | Scope | Authorized by this PREP? |
|---|---|---|
| `M21.8` PREP | This plan + ralph.md Reflection Log + Resume checkpoint | yes (this commit) |
| `M21.8.1` RED/GREEN | `src/hisys/operations/code_analysis_pass_contract.py` adapter + writer + `tests/unit/test_code_analysis_pass_contract.py` | no (next PREP-authorized increment) |
| `M21.8.2` Fixture contracts | `tests/fixtures/pass-contracts/code_analysis/*.json` | no (depends on M21.8.1 schema) |
| `M21.8-CLI` Prepare + RED/GREEN | `hisys evaluate-code-analysis-contract` thin wrapper | no (separate Prepare) |

---

## Task 0: Reconstruct baseline before editing

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py tests/unit/test_change_impact.py tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_pass_contract_improvement_cli.py tests/unit/test_pass_contract_registry_schema.py tests/unit/test_pass_contract_evaluator.py tests/unit/test_pass_contract_proposal_conversion.py tests/unit/test_pass_contract_review_package.py tests/unit/test_pass_contract_promotion.py tests/unit/test_needs_more_evidence_reasons.py tests/unit/test_needs_more_evidence_audit_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `0ad5a63 feat: add architecture candidates cli wrapper`; code-analysis focused gate green; existing pass-contract focused gate green; DARS focused gate 50 passes; traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

---

## Task 1: PREP — author this plan + ralph.md entry

**Files:**
- Create: `docs/plans/m21-8-code-analysis-pass-contract-loop-implementation-tasks.md` (this file)
- Modify: `ralph.md` (Reflection Log entry + Resume checkpoint for `M21.8` Prepare)

**Validation:**
```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**
```bash
git add docs/plans/m21-8-code-analysis-pass-contract-loop-implementation-tasks.md ralph.md
git commit -m "docs: prepare code-analysis pass-contract loop"
```

Stop after this PREP commit. The next safe queue row is `M21.8.1` Task 1 RED: author the failing adapter unit test for `tests/unit/test_code_analysis_pass_contract.py::test_build_code_analysis_evidence_summary_maps_m21_1_payload_to_artifact_refs` before any production module exists.

---

## Task M21.8.1: RED — failing adapter unit test (next iteration)

**Files (M21.8.1 RED iteration, not this PREP):**
- Modify: `tests/unit/test_code_analysis_pass_contract.py` (new file)

**Planned RED test sketch (illustrative; precise shape will be pinned in M21.8.1 PREP review):**

```python
def test_build_code_analysis_evidence_summary_maps_m21_1_payload_to_artifact_refs() -> None:
    coverage_payload = {
        "schema_id": "hisys.traceability.coverage.v1",
        "covered_refs": ["docs/d1.md", "docs/d2.md"],
        "unreferenced_requirements": [],
    }
    summary = build_code_analysis_evidence_summary(
        question_type="traceability_coverage_review",
        coverage_report=coverage_payload,
    )
    assert summary.artifact_refs == ["docs/d1.md", "docs/d2.md"]
    assert summary.claims_covered is True
    assert summary.boundary_violation_detected is False
```

**Expected RED:** `ModuleNotFoundError: No module named 'hisys.operations.code_analysis_pass_contract'`.

---

## Task M21.8.1: GREEN — minimal adapter + writer (next iteration)

**Files (M21.8.1 GREEN iteration, not this PREP):**
- Create: `src/hisys/operations/code_analysis_pass_contract.py`
- Modify: `tests/unit/test_code_analysis_pass_contract.py`

**Minimum surface:**

```python
from typing import Any, Literal

CodeAnalysisQuestionType = Literal[
    "traceability_coverage_review",
    "runtime_boundary_consistency_review",
    "codebase_map_freshness_review",
    "change_impact_review",
    "architecture_candidate_review",
]


def build_code_analysis_evidence_summary(
    *,
    question_type: CodeAnalysisQuestionType,
    coverage_report: dict[str, Any] | None = None,
    boundary_report: dict[str, Any] | None = None,
    freshness_report: dict[str, Any] | None = None,
    benchmark_report: dict[str, Any] | None = None,
    change_impact_report: dict[str, Any] | None = None,
    architecture_candidates_report: dict[str, Any] | None = None,
) -> EvidenceSummary: ...


def write_code_analysis_pass_contract_evaluation(
    *,
    instance_root: Path,
    date: str,
    contract_id: str,
    result: PassContractEvaluationResult,
    human_approval_ref: str | None = None,
) -> dict[str, object]: ...
```

**Boundary invariants pinned by tests:**
- Adapter never opens a file body.
- Adapter never reads `runtime-boundary/` directly; inputs are dict payloads only.
- Adapter never calls `subprocess` or `.git/`.
- Adapter never calls `date.today()`.
- Writer rejects non-`YYYYMMDD` dates.
- Writer persists `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`.
- `boundary_violation_detected=true` when the input reports list any `unsafe_*` partitions/refs.

---

## Task M21.8.2: Fixture contracts (next iteration)

**Files (M21.8.2, not this PREP):**
- Create: `tests/fixtures/pass-contracts/code_analysis/traceability_coverage_review.json`
- Create: `tests/fixtures/pass-contracts/code_analysis/runtime_boundary_consistency_review.json`
- Create: `tests/fixtures/pass-contracts/code_analysis/codebase_map_freshness_review.json`
- Create: `tests/fixtures/pass-contracts/code_analysis/change_impact_review.json`
- Create: `tests/fixtures/pass-contracts/code_analysis/architecture_candidate_review.json`

**Constraints:** Each fixture is `status=candidate`, `active=false`, `automatic_promotion_allowed=false`, `promotion_gate=human_reviewed_traceable_change`, no `human_approval_ref`. `minimum_evidence` keys reuse the existing taxonomy (`artifact_refs_required`, `alternative_set_required`, `claim_coverage_required`, `contradiction_check_required`, `dars_critique_required`). `blocked_if` reuses existing reason codes (`no_traceable_artifact_refs`, `boundary_violation_detected`, etc.).

---

## Task M21.8-CLI: Thin CLI wrapper (separate Prepare/RED)

**Out of scope for this PREP.** A separate `M21.8-CLI` Prepare/document-RED authors the thin `hisys evaluate-code-analysis-contract --instance <root> --date <YYYYMMDD> --contract-ref <json> --coverage-report <json> --boundary-report <json> --freshness-report <json> --benchmark-report <json> --change-impact-report <json> --architecture-candidates-report <json> [--human-approval-ref <token>]` subcommand. Boundary mirrors M21.7-CLI: explicit JSON paths only, no auto-discovery, no `.git/` read, no `subprocess`, no `date.today()`, advisory-only exit code `0`.

---

## Stop / continue rule

Stop after this M21.8 PREP package is committed. The next safe row is `M21.8.1` Task 1 RED: add the failing adapter unit test in `tests/unit/test_code_analysis_pass_contract.py`, observe `ModuleNotFoundError`, then implement the minimal adapter + writer. Do not start GREEN in the same Prepare-only increment unless explicitly authorized by the user.

If a future iteration discovers that the deterministic mapping rules from M21.1..M21.7 report fields to `EvidenceSummary` fields disagree with existing pass-contract semantics, stop and ask the user before changing either side. Do not expand the reason-code taxonomy without an explicit Prepare/RED.
