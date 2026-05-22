# M24 Real OSS Comparison and License Workflow Plan

> **For Hermes/Ralph:** Execute M24 one checkpoint at a time with PREP -> RED/GREEN -> GATE discipline. The user authorized opening M24 with `go for m24`; this plan intentionally starts with docs/control boundaries only. Do not search, fetch, clone, inspect, or archive any real external repository in this milestone until a later human approval names exact repositories and execution limits.

**Status:** Future-roadmap only after the 2026-05-22 user decision. M24 remains preserved as a planning-only, fail-closed surface; no additional OSS workflow row is active in Ralph.

**Goal:** Extend the completed M23 fixture-local OSS comparison adapter toward a real-OSS comparison/license workflow without crossing the live/network/license boundary in the opening increment. M24 first defines the approval packet, provenance, retention, source-ingestion, and license-adjudication boundaries needed before any real repository access can be considered.

**Authorization packet:** `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.39.md` records the user approval from Discord: `go for m24`.

**Boundary record:**

- Authorized now: local docs/control planning, deterministic fixture design, user-executable runbooks, traceability updates, governance profile/test updates, local validation, local commits, and normal push to existing `origin/dars` after validation.
- Not authorized now: credential lookup or mutation, secret capture, arbitrary network search/clone/fetch, real OSS repository clone/fetch, live OSS API access, package installation, license-text capture, license adjudication, raw upstream source archival, publication/deployment/release, destructive Git/history operations, force push, new or changed remote configuration, mutation of non-fixture/live user data, unbounded live external provider execution, or claiming live-provider DARS completion.

---

## M24 Initial Task Queue

| Row | Task | Type | Status |
|---|---|---|---|
| M24-REAL-OSS-LICENSE-WORKFLOW-PREP | Author the detailed docs/control task packet for approved-repository declarations, provenance records, retention/cleanup policy, license-adjudication handoff, fixture-only RED/GREEN surfaces, and user-executable runbooks. | docs/control | done |
| M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN | Implement only deterministic fixture/local validators or report-shape tests defined by PREP. Must not clone/fetch/search external repositories or capture real license text. | fixture-local implementation | done |
| M24-REAL-OSS-LICENSE-WORKFLOW-GATE | Validate docs/control and fixture-local evidence; decide whether any later live/network/license row is sufficiently bounded for a separate human approval. | docs/control gate | done |
| QUEUE-REFILL-PREP | Re-classify remaining M24/live candidates after the gate. | docs/control | deferred: OSS moved to future roadmap |

## First Executable Row

`M24-REAL-OSS-LICENSE-WORKFLOW-PREP` must create a detailed task packet under `docs/plans/` before any production code, tests, fixtures, runtime reports, or external actions are added.

The PREP packet must specify:

- the approved-repository declaration schema using placeholder fixture descriptors only;
- the operator approval fields required before any later live fetch/clone;
- provenance fields for repository URL, commit/tag, retrieval command, operator approval ref, and timestamp, without executing retrieval;
- retention and cleanup rules for any future clone/cache directory;
- the boundary between license metadata tags and full license text capture;
- the human review handoff needed before license compatibility/adjudication can be claimed;
- source-ingestion defaults that avoid copying raw upstream code into Hisys product artifacts;
- fixture-only RED command(s) and expected failures;
- focused validation gates, traceability updates, and Ralph reflection requirements.

## Out of Scope for This Opening Checkpoint

- Naming or approving real repository URLs.
- Running web search, package-manager search, `git clone`, `git fetch`, `gh repo clone`, `curl`, or any equivalent network retrieval.
- Capturing LICENSE file bodies or adjudicating license compatibility.
- Persisting raw external source, diff hunks, or third-party code snapshots.
- Changing the existing M23 `hisys.oss_comparison_adapter.v1` report contract.
- Expanding DARS live-provider authority.

## Related Current Surfaces

- `roadmap.md` real OSS comparison and license adjudication section.
- `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md`
- `docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md`
- `docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md`
- `src/hisys/operations/oss_comparison_adapter.py`
- `tests/unit/test_oss_comparison_adapter.py`

## Gate Commands for This Opening Checkpoint

```bash
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

Expected: governance current-state passes with `profile_version == "v0.0.39"` and `next_safe_task == "M24-REAL-OSS-LICENSE-WORKFLOW-PREP"`; traceability validates; secret scan reports `hit_count=0`; diff check is clean; branch is `dars` with upstream `origin/dars`.
