# Local DARS and ByeSys Provenance Implementation Plan

> **For Hermes:** Use test-driven-development skill to implement this plan task-by-task.

**Goal:** Make DARS runnable through a localhost-only local LLM adapter, enforce Hisys boundary semantics for model/provenance crossings, assign zero evidential weight to ByeSys-generated evidence, and normalize reviewer terminology to the Jeweler/Appraiser metaphor.

**Architecture:** Keep DARS advisory-only. Add a localhost-restricted `openai_compatible` adapter with fake HTTP server tests before any live local model. Treat local LLM calls as local model-boundary events that require explicit approval but do not count as live external calls when endpoint authority is localhost-only. Add a provenance/weight policy so generated or ungrounded evidence is explicitly sourced as `ByeSys` and assigned weight 0 in Hisys and Hermes-facing guidance.

**Hisys review result:** A read-only `investigate-domain` review of this plan on 2026-05-16 returned `status=needs_more_evidence`, `quality_gate=needs_more_evidence`, `summary=human_review_required`, `external_call_made=false`, and `mutation_performed=false`. Treat this plan as implementation-ready only after the hardening items below are reflected in tests: strict localhost parsing, explicit local-model boundary fields, fake-server fail-closed coverage, machine-readable DARS provenance, and DARS decision artifact integrity.

**Tech Stack:** Python 3.11, pytest, `http.server`/threaded fake HTTP server fixtures, Pydantic config schemas, Hisys runtime artifacts, Hermes `SOUL.md` for global generation policy.

---

## Accepted Requirements

1. **Localhost-only local LLM boundary**
   - Local DARS endpoints must resolve to loopback only: `127.0.0.1`, `::1`, or the hostname `localhost` after URL parsing.
   - Any non-localhost endpoint configured as local must fail closed.
   - Reject deceptive or ambiguous authorities such as `localhost.evil.com`, `127.0.0.1.evil.com`, user-info host tricks, empty hosts, unsupported schemes, and remote IPs.
   - Do not rely on substring matching. Parse with `urllib.parse`, normalize host/port, and use `ipaddress` for IP literals.
   - Local LLM dispatch requires an explicit `approval_ref` even though it remains local.
   - Hisys records the distinction in boundary artifacts and critique records:
     - `model_boundary_crossed=true`
     - `local_model_call_made=true`
     - `endpoint_scope=localhost_only`
     - `external_call_made=false` for localhost-only local model calls
     - `mutation_performed=false`

2. **Adapter implementation**
   - Implement `kind="openai_compatible"` in `DarsRuntime`.
   - Use `POST <endpoint>` with OpenAI-compatible chat payload.
   - Extract `choices[0].message.content`.
   - Persist output as `DarsCritiqueRecord`.
   - Fail closed on timeout, non-2xx HTTP, malformed JSON, missing content, non-local endpoint in local mode, or missing approval ref.

3. **DARS quality and provenance strengthening**
   - DARS prompt must separate:
     - internal knowledge-management sources;
     - externally retrieved sources, when external search is explicitly allowed, with DOI/URL/source location;
     - generated or inferred unsupported content.
   - If DARS combines absent evidence, unstated assumptions, or generated synthesis into evidence-like content, it must mark that source as `ByeSys`.
   - DARS must not present `ByeSys` as factual evidence.

4. **ByeSys zero-weight policy**
   - Any evidential content whose source is `ByeSys` has weight `0.0`.
   - Jeweler review must assign zero contribution to `ByeSys` evidence.
   - Hermes global generation policy must also treat `ByeSys` evidence as weight 0.

5. **Terminology normalization**
   - Use **Jeweler** as the decision/review metaphor replacing user-facing **Chief Editor** terminology.
   - Use **Appraiser** for DARS/advisory critique separation.
   - Preserve legacy Python package/class names temporarily where migration would be too large, but add user-facing aliases and documentation so future generated docs and prompts use Jeweler/Appraiser consistently.
   - Add a deprecation map: `Chief Editor -> Jeweler`; `DARS devil/reviewer -> Appraiser`.

---

## Milestone 0: Controlled terminology and policy baseline

**Objective:** Capture the new names and ByeSys zero-weight policy before changing runtime behavior.

**Files:**
- Create: `src/hisys/provenance/source_weighting.py`
- Create/modify tests: `tests/unit/test_source_weighting.py`
- Modify docs: `docs/traceability/README.md` or a dedicated governance doc
- Modify examples/harness guidelines that mention user-facing `Chief Editor`

**RED tests:**
- `test_byesys_source_has_zero_weight()`
- `test_non_byesys_source_preserves_configured_weight()`
- `test_reviewer_metaphor_alias_maps_chief_editor_to_jeweler()`

**Acceptance:**
- `ByeSys` source weight resolves to `0.0` regardless of provided raw weight.
- Jeweler/Appraiser alias map exists and is documented.
- Legacy code can still import existing names.

**Validation:**
```bash
python3 -m pytest tests/unit/test_source_weighting.py -q
```

---

## Milestone 1: Localhost endpoint policy for DARS config

**Objective:** Add deterministic endpoint validation for local LLM mode before any HTTP adapter exists.

**Files:**
- Modify: `src/hisys/agents/dars_config.py`
- Modify/create tests: `tests/unit/test_dars_config.py`

**RED tests:**
- `test_local_openai_compatible_backend_accepts_localhost_endpoint()`
- `test_local_openai_compatible_backend_accepts_ipv4_loopback_endpoint()`
- `test_local_openai_compatible_backend_accepts_ipv6_loopback_endpoint()`
- `test_local_openai_compatible_backend_rejects_remote_endpoint()`
- `test_local_openai_compatible_backend_rejects_deceptive_localhost_suffix()`
- `test_local_openai_compatible_backend_rejects_userinfo_host_trick()`
- `test_local_openai_compatible_backend_rejects_missing_or_unsupported_scheme()`
- `test_local_llm_backend_requires_policy_enabled_and_approval_gate()`

**Rules:**
- `kind="openai_compatible"`, `mode="local_network_only"` permits only parsed loopback authorities.
- `http` and `https` are the only URL schemes allowed at config validation time; production local smoke should prefer `http://127.0.0.1:<port>/v1/chat/completions` unless TLS is explicitly configured.
- `localhost` is allowed as a hostname only when parsed as the full hostname. Strings containing `localhost` as a prefix/suffix are not local.
- IP literals are allowed only when `ipaddress.ip_address(host).is_loopback` is true.
- `mode="external_api"` remains external and requires the existing external approval path.
- `credential_ref` must be optional for local models and must not be required for localhost.
- The selected backend should expose deterministic metadata for downstream dispatch: `endpoint_scope="localhost_only"`, `model_boundary_required=true`, and `external_call_expected=false`.

**Validation:**
```bash
python3 -m pytest tests/unit/test_dars_config.py -q
```

---

## Milestone 2: Fake HTTP Server adapter harness

**Objective:** Build a fake OpenAI-compatible server test harness before implementing production adapter behavior.

**Files:**
- Create: `tests/unit/helpers/fake_openai_server.py` or inline fixture in `tests/unit/test_dars_runtime.py`
- Modify: `tests/unit/test_dars_runtime.py`

**RED tests:**
- `test_dars_runtime_calls_local_openai_compatible_backend()`
- `test_dars_runtime_rejects_local_backend_without_approval_ref()`
- `test_dars_runtime_records_local_model_boundary_not_external_call()`
- `test_dars_runtime_fails_closed_on_malformed_local_llm_response()`
- `test_dars_runtime_fails_closed_on_missing_message_content()`
- `test_dars_runtime_fails_closed_on_non_2xx_local_llm_response()`
- `test_dars_runtime_fails_closed_on_local_llm_timeout()`
- `test_dars_runtime_rejects_remote_endpoint_before_http_request()`

**Fake server behavior:**
- Listen on `127.0.0.1` with an ephemeral port.
- Assert request path `/v1/chat/completions`.
- Capture request JSON for assertions.
- Record whether the fake server was contacted so remote-endpoint rejection can prove no HTTP request was attempted.
- Return one response fixture per failure class: success, non-2xx, malformed JSON, missing content, delayed timeout.
- Assert the request body contains:
  - configured model;
  - DARS advisory/no-mutation instructions;
  - provenance instructions for internal sources, external DOI/URL only when allowed, and ByeSys unsupported synthesis;
  - no tool/search/browser authorization.
```json
{
  "choices": [
    {"message": {"content": "local DARS critique with provenance sections"}}
  ]
}
```

**Expected artifacts:**
- Critique JSON records `dars_backend="local_llm_dars"`.
- Critique JSON records `external_call_made=false`.
- Critique JSON records `model_boundary_crossed=true`, `local_model_call_made=true`, and `endpoint_scope="localhost_only"`.
- Boundary JSON records approval ref, `endpoint_scope="localhost_only"`, `model_boundary_crossed=true`, `external_call_made=false`, and no mutation.
- Failure artifacts record a safe error summary without raw model credentials, stack traces, or prompt secrets.

**Validation:**
```bash
python3 -m pytest tests/unit/test_dars_runtime.py::test_dars_runtime_calls_local_openai_compatible_backend -q
```

---

## Milestone 2.5: DARS decision artifact integrity guard

**Objective:** Prevent Hisys from recording DARS decision refs that do not exist. The Hisys plan review found a `runtime-boundary/dars/.../dars-decision-...json` ref in the domain result without a corresponding artifact.

**Files:**
- Modify/create tests around the domain decision layer or runtime artifact writer.
- Likely inspect: `src/hisys/domain/use_cases.py`, `src/hisys/domain/runtime.py`, `src/hisys/domain/layers.py`, and `src/hisys/cli/main.py`.

**RED tests:**
- `test_domain_investigation_writes_every_dars_decision_ref_it_records()`
- `test_domain_investigation_fails_or_omits_missing_dars_refs()`
- `test_run_summary_runtime_boundary_refs_exist_under_instance()`

**Acceptance:**
- Every `runtime_boundary_refs` entry in `domain-investigation-result`, `hisys-tool-result`, and run summary resolves to a real artifact under the instance root.
- Missing optional DARS output is represented as an explicit skipped/unavailable status, not as a dangling ref.
- No artifact integrity fix should introduce external calls or mutation outside the instance root.

**Validation:**
```bash
python3 -m pytest tests/unit/test_domain_runtime_artifacts.py tests/unit/test_cli_runtime.py -q
```

---

## Milestone 3: Implement `openai_compatible` DARS adapter

**Objective:** Implement minimal production code to satisfy the fake server tests.

**Files:**
- Modify: `src/hisys/agents/dars.py`
- Optionally create: `src/hisys/agents/dars_openai_compatible.py`

**Implementation notes:**
- Use Python stdlib `urllib.request` unless project conventions prefer a dependency.
- Build chat payload from current DARS prompt plus provenance instructions.
- Apply timeout from `config.spec.policy.max_runtime_seconds`.
- Do not resolve credentials for localhost endpoints.
- Never allow adapter to perform writes, posts, publication, browser calls, or search.

**Validation:**
```bash
python3 -m pytest tests/unit/test_dars_runtime.py tests/unit/test_dars_dispatch.py -q
```

---

## Milestone 4: Provenance-aware DARS prompt/output contract

**Objective:** Make every DARS output separate evidence provenance and mark unsupported generated content as ByeSys.

**Files:**
- Modify: `src/hisys/agents/dars.py`
- Modify: `src/hisys/agents/dars_config.py` if schema extension is needed
- Modify tests: `tests/unit/test_dars_runtime.py`

**Prompt requirements:**
DARS must include these sections or equivalent structured fields. Prefer machine-readable fields in the persisted critique so Jeweler can enforce source weights without re-parsing prose:

```text
Internal knowledge-management sources:
- source_ref: ...
- claim supported: ...

External sources, if external search was explicitly allowed:
- DOI/URL/location: ...
- claim supported: ...

ByeSys generated/unsupported synthesis:
- generated statement: ...
- reason source is ByeSys: missing direct evidence / inferred / combined absent evidence
- evidential_weight: 0.0
```

**RED tests:**
- `test_dars_prompt_requires_byesys_for_unsupported_generated_evidence()`
- `test_dars_prompt_requires_doi_or_url_for_external_sources_when_allowed()`
- `test_dars_critique_records_byesys_evidence_weight_zero()`
- `test_dars_critique_records_machine_readable_source_weights()`
- `test_dars_critique_does_not_mark_byesys_as_corroborating_source()`

**Validation:**
```bash
python3 -m pytest tests/unit/test_dars_runtime.py tests/unit/test_source_weighting.py -q
```

---

## Milestone 5: Jeweler zero-weight enforcement

**Objective:** Ensure the Jeweler/legacy Chief Editor review path gives ByeSys evidence zero contribution.

**Files:**
- Identify current review/weight code under `src/hisys/chief_editor/`, browser review chain, or Lapidary governance modules.
- Add/modify tests under `tests/unit/` for the actual path.

**RED tests:**
- `test_jeweler_review_assigns_zero_weight_to_byesys_sources()`
- `test_jeweler_review_does_not_accept_byesys_as_corroborating_evidence()`

**Acceptance:**
- A claim with only `ByeSys` evidence cannot pass an evidence sufficiency gate.
- Mixed evidence keeps non-ByeSys contributions but ignores ByeSys contribution.

**Validation:**
```bash
python3 -m pytest tests/unit -q
```

---

## Milestone 6: Hermes global configuration/prompt update

**Objective:** Make future Hermes-generated evidential content respect ByeSys zero-weight semantics outside Hisys too.

**Files:**
- Modify: `/home/cbchoi/.hermes/SOUL.md`
- Optional memory update: compact user/project convention

**Required durable rule:**
- When generated content is evidence-like but lacks a verifiable source, Hermes must label its source as `ByeSys`.
- Any `ByeSys` source has evidential weight `0.0`.
- Claims supported only by `ByeSys` must be reported as unsupported/provisional, not evidence-backed.

**Validation:**
```bash
hermes config check
# Manual check: read SOUL.md and verify the rule is present.
```

---

## Milestone 7: Runtime config and smoke tests

**Objective:** Switch a controlled runtime instance to local DARS after fake-server tests pass.

**Files:**
- Host-local runtime config, e.g. `/home/cbchoi/.hermes/tools/hisys/runtime/config/dars.json`

**Config example:**
```json
{
  "spec": {
    "default_backend": "local_llm_dars",
    "policy": {
      "enabled": true,
      "allowed_actions": "advisory_only",
      "require_human_approval_for_external_call": true,
      "allow_external_side_effects": false,
      "max_runtime_seconds": 120
    },
    "backends": {
      "local_llm_dars": {
        "kind": "openai_compatible",
        "enabled": true,
        "mode": "local_network_only",
        "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
        "model": "qwen2.5:14b-instruct",
        "external_call_allowed": false,
        "output_contract": "DarsCritiqueRecord"
      }
    }
  }
}
```

**Smoke command:**
```bash
/home/cbchoi/.hermes/tools/hisys/bin/hisys request-dars-critique \
  --instance /home/cbchoi/.hermes/tools/hisys/runtime \
  --date <YYYYMMDD> \
  --source-execution-id <EXEC-ID> \
  --producer-id dars-local-llm-smoke \
  --backend configured \
  --approval-ref <APPROVAL-REF>
```

**Expected output:**
```text
dars_backend: local_llm_dars
external_call_made: false
model_boundary_crossed: true
local_model_call_made: true
endpoint_scope: localhost_only
```

---

## Milestone 8: Full validation, deployment, and commit discipline

**Objective:** Finish with repository and deployed-tool validation.

**Commands:**
```bash
python3 -m pytest tests/unit -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
PYTHONPATH=src python3 -m hisys.cli.main deploy-hermes-tool \
  --source-root /home/cbchoi/workspaces/sysailab/develop/repos/hisys \
  --target /home/cbchoi/.hermes/tools/hisys \
  --channel-id 1502110114704916501 \
  --channel-name "sysailab/develop/Hisys" \
  --force
```

**Commit sequence:**
1. `docs: plan local dars and byesys provenance`
2. `feat: add byesys source weighting policy`
3. `feat: validate localhost dars endpoints`
4. `test: guard dars decision artifact integrity`
5. `feat: add openai-compatible local dars adapter`
6. `feat: enforce byesys zero weight in jeweler review`
7. `docs: normalize jeweler appraiser terminology`

---

## Stop / Gate Conditions

Pause for user confirmation if any of these occur:

- The implementation needs to install a local LLM runner or download a model.
- Endpoint is not localhost-only.
- Any live external search, DOI lookup, URL fetch, or browser call is needed.
- A broad package/class rename from `chief_editor` to `jeweler` would affect many artifacts and migrations.
- Runtime config would replace the currently working Claude DARS backend before local fake-server tests pass.
