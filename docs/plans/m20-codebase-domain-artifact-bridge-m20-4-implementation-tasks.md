# Milestone M20.4 — `investigate-domain --domain codebase` CLI Smoke Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the document-RED/Prepare artifact for Milestone M20 Task M20.4 after M20.3 (Task 1+2 production + Task 3 regression pins) shipped local codebase bundle enrichment of `DomainInvestigationResult`.

**Goal:** Implement M20.4 so a codebase-domain `DomainInvestigationRequest` carrying local `runtime_record` artifact bundle refs can be dispatched end-to-end through the existing `investigate-domain` CLI without new flags, producing a tool-result whose `runtime_boundary_refs` include the enriched codebase bundle evidence.

**Architecture:** Reuse the existing CLI plumbing that already validates `DomainInvestigationRequest` JSON, resolves the structured codebase adapter via `_default_domain_adapter_registry`, persists request/result artifacts, and writes a run summary. M20.4 adds only a fixture smoke test plus any minimal CLI wiring required so the codebase-analysis bundle refs flow through `runtime_record` sources, the codebase adapter dispatches, and the enriched evidence package is visible in the persisted tool result. No new CLI argument, no live repo clone, no model/network call, no credential resolution, no destructive Git, no remote push, and no raw source archival is introduced.

**Tech Stack:** Python 3.11, dataclasses, Pydantic v2, pytest, existing `hisys.cli.main.main` argparse entry point. No new dependency.

**Context Packet:** Required source handles: `src/hisys/cli/main.py` (`_cmd_investigate_domain`, `_default_domain_adapter_registry`, run-summary writer), `src/hisys/domain/specs.py` (`codebase_spec`), `src/hisys/domain/domain_adapters.py` (`StructuredDomainAdapter`), `src/hisys/domain/translation.py` (`build_codebase_bundle_enrichment`), `src/hisys/operations/codebase_analysis.py` (`load_codebase_review_bundle`, `resolve_instance_runtime_ref`, artifact writers), `tests/unit/test_domain_cli.py` (existing CLI smoke pattern), `tests/unit/test_codebase_domain_artifact_bridge.py` (M20.1..M20.3 helpers and tests), `docs/traceability/README.md`, and `ralph.md`.

**Boundary Record:** Local fixture-only tests/docs/code mutation and local commit are allowed after validation. Remote push is not authorized. No live repo clone, raw source archival, browser/network/model call, credential resolution, external publication, destructive Git, or action authorization. The CLI smoke proves the dispatch path; the underlying `quality_gate="passed"` continues to mean evidence-ready for human review, not approved-for-live-action.

---

## Accepted decisions

1. **No new CLI flag in M20.4:** Local codebase artifact bundle refs travel as ordered `runtime_record` `DomainSourceRef` entries inside the existing `DomainInvestigationRequest` JSON. A repeatable `--codebase-artifact` argparse flag would be a strict superset; it is intentionally deferred so M20.4 can ship as a fixture smoke alone.
2. **Use existing dispatch registry:** `_default_domain_adapter_registry` already includes `codebase_spec()`. The structured adapter path produced by M20.3 covers both the `candidate_complete` enriched path and the incomplete / unreadable downgrade paths.
3. **Fixture materializes a real complete bundle:** The smoke test reuses the codebase-analysis artifact writers (`write_codebase_inventory`, `write_python_symbol_index`, `write_codebase_scope_map`, `write_codebase_risk_scan`) over a seeded mini-repo under `tmp_path`, exactly as `test_codebase_domain_artifact_bridge.py` Task 1 does. A synthetic `validation-plan.json` ref satisfies the role classifier without being read by the safe loader.
4. **No raw source content surfaced:** The CLI tool-result must not embed raw source text. Bounded counts (`inventory_files`, `scopes`, `risk_categories`) are acceptable; raw file content is not.
5. **Assert governance invariants on the persisted artifact:** The smoke test reads the persisted `hisys-tool-result-*.json` and asserts `external_call_made=false`, `mutation_performed=false`, `requires_human_review=true`, and `quality_gate=="passed"` for the complete bundle path.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm M20.3 is current and the working tree is clean.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:** branch `dars`, HEAD at or after `39efadc test: pin codebase bundle downgrade paths`; combined domain gate plus existing CLI tests pass; DARS gate 48 passes.

---

## Task 1: RED — codebase request JSON + bundle materialization smoke

**Objective:** Add a failing CLI test that builds a complete local codebase-analysis bundle under `tmp_path`, writes a `DomainInvestigationRequest` JSON pointing at the bundle refs, and asserts the persisted tool-result contains the enriched `codebase_analysis_bundle` evidence.

**Files:**

- Modify: `tests/unit/test_domain_cli.py` (add new fixture and test function).
- Inspect before editing: existing `test_investigate_domain_writes_request_and_tool_result_boundary` for the calling convention.

**Test sketch:**

```python
def test_investigate_domain_codebase_smokes_local_bundle(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_codebase_smoke_repo(repo)
    refs = _materialize_complete_codebase_bundle(
        instance_root, repo, date="20260520", request_id="m20_4_smoke"
    )

    request_path = instance_root / "codebase-request.json"
    _write_codebase_request(
        request_path,
        request_id="HISYS-REQ-M20-4-SMOKE",
        refs=refs,
    )

    exit_code = main([
        "investigate-domain",
        "--instance",
        str(instance_root),
        "--request",
        str(request_path),
        "--date",
        "20260520",
    ])

    assert exit_code == 0
    result_artifact = (
        instance_root
        / "runtime-boundary"
        / "domain-investigation"
        / "codebase"
        / "20260520"
        / "hisys-tool-result-HISYS-REQ-M20-4-SMOKE.json"
    )
    assert result_artifact.exists()
    payload = json.loads(result_artifact.read_text(encoding="utf-8"))
    assert payload["domain"] == "codebase"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["requires_human_review"] is True
    assert payload["quality_gate"] == "passed"
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_investigate_domain_codebase_smokes_local_bundle -q
```

**Expected RED:** `FileNotFoundError`/`KeyError`/assertion failure because the helper functions do not exist yet, the request JSON shape lacks codebase-bundle refs, or the persisted tool-result envelope omits expected fields.

---

## Task 2: GREEN — add minimal helpers and ensure CLI path persists enriched result

**Objective:** Add the test helpers and any narrow CLI/translation wiring needed so the smoke passes without changing public CLI behavior beyond persistence of the existing tool result.

**Files:**

- Modify: `tests/unit/test_domain_cli.py` (helpers + new test).
- Modify if needed: `src/hisys/cli/main.py` only for narrow tool-result projection so the persisted JSON exposes `codebase_analysis_bundle` evidence summary refs alongside the existing fields. No new CLI argument.
- Do not modify: `DomainInvestigationRequest` schema, `_default_domain_adapter_registry` dispatch order, or `StructuredDomainAdapter` semantics.

**Implementation constraints:**

- Reuse the existing M20.1..M20.3 fixture writers; do not duplicate inventory/symbol-index/scope-map/risk-scan logic in the test module.
- The request JSON must declare `domain == "codebase"`, an objective string that is not a `requirements-analysis:` prefix, and five `runtime_record` `DomainSourceRef` entries — one per role — so the work-product gate is `candidate_complete`.
- The CLI must continue to write request and result artifacts under `runtime-boundary/domain-investigation/codebase/<YYYYMMDD>/` and a run summary under `reports/run-summaries/<YYYYMMDD>/`. The persisted tool result must remain a compact `HisysToolResult` projection; the full evidence package detail can be retrieved from the `DomainInvestigationResult` artifact written by the structured adapter writer.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_investigate_domain_codebase_smokes_local_bundle -q
PYTHONPATH=src pytest tests/unit/test_domain_cli.py tests/unit/test_codebase_domain_artifact_bridge.py -q
```

---

## Task 3: Documentation, gate, and commit

**Files:**

- Modify: `docs/traceability/README.md` — append an `M20.4` row referencing this plan, the modified test file, and the verified governance invariants.
- Modify: `ralph.md` — add a Reflection Log entry following the existing M20.3 format with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN):**

```bash
git add tests/unit/test_domain_cli.py src/hisys/cli/main.py docs/traceability/README.md ralph.md
git commit -m "feat: bridge codebase artifacts into investigate-domain"
```

---

## Stop conditions

Stop and report if implementation requires a new CLI argument, live external repository access, raw source archival, model/browser/network calls, credential access, destructive Git, publication, or action authorization. Stop and prepare a narrower plan if the CLI dispatch path materially diverges from the codebase adapter expectations established in M20.3.

## Follow-on increments

- **M20.5:** docs/traceability/finish packet for the full M20 milestone after M20.4 turns green.
- **Future:** repeatable `--codebase-artifact` argparse flag if and when the request-JSON convention becomes inconvenient for human-authored runs.
