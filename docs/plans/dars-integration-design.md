# DARS Integration Design and Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task after the design is accepted. Keep Ralph/TDD loops active until this queue is finished, a new queue is required, or token/session limit is reached.

**Goal:** Replace the current DARS loopback placeholder with a controlled, disabled-by-default DARS integration architecture that can ingest structured critique as advisory evidence before any real external DARS call is enabled.

**Architecture:** Hisys remains the system of record. DARS is an external advisory agent behind a narrow adapter boundary: Hisys builds an `AgentHandoffPackage`, wraps it in the canonical `DarsRequestEnvelope`, dispatches it only through a configured adapter, validates a canonical `DarsResponseEnvelope` containing a `DarsCritiqueRecord`, links the critique back to source execution/memo/alert/evidence, and records every boundary crossing. The decision process is progressive and GAN-like: one or more generator agents propose a candidate decision or memo, several specialized conservative critic agents challenge it from different professional/persona/knowledge lenses, and Hisys records improvement proposals without blocking the decision unless an existing safety or approval gate requires review. The first executable increments stay fixture/local-only; real DARS dispatch is enabled only after mock contract tests, safety gates, traceability, and human approval controls pass. The boundary data format is defined in `docs/contracts/dars-data-format.md`.

**Tech Stack:** Python 3.11, Pydantic v2 schemas, runtime-local JSON/Markdown artifacts, pytest, existing `InstanceRoot`, `AgentHandoffPackage`, `DarsRuntime`, traceability validator, secret scanner.

---

## 1. Current Baseline

Current implementation:

- `src/hisys/schemas/handoff.py` defines `AgentHandoffPackage` with `allowed_actions`, approval, boundary refs, result refs, and status.
- `src/hisys/agents/dars.py` implements `DarsRuntime` loopback/fixture critique behavior.
- `tests/unit/test_dars_runtime.py` verifies local handoff/critique artifacts.
- README and traceability docs explicitly state DARS itself is not implemented.

Current safety posture:

- `dars_backend=loopback_placeholder`
- `external_call_made=false`
- `allowed_actions=advisory_only`
- `action_taken=none`
- DARS cannot directly trigger external software or alert actions.

Controlled anchors:

- `HISYS-DARS-CONTRACT-001`
- `HISYS-FR-AGT-001..005`
- `HISYS-T-005`, `HISYS-T-019`, `HISYS-T-020`, `HISYS-T-024`
- `HISYS-CON-010`, `HISYS-CON-011`, `HISYS-CON-012`

---

## 2. Target DARS Boundary

### 2.1 Roles

| Role | Responsibility | May perform live action? |
|---|---|---|
| Hisys `DarsRuntime` | Owns request preparation, adapter selection, validation, persistence, linking, reports | No direct live action except through adapter gate |
| DARS adapter | Converts a validated handoff package into a backend-specific request and returns raw response envelope | Only if enabled and approved |
| Critique ingester | Validates/normalizes DARS output into controlled records | No |
| Chief Editor / human reviewer | Decides whether critique affects alert, memo, CAPA, or requirement status | Only through existing approval gate |

### 2.2 Boundary Rule

DARS output is **advisory evidence**, not an approved decision. It may create review items or recommendation records, but must not mutate alerts, memos, connectors, requirements, or software triggers without explicit downstream approval.

### 2.3 Progressive GAN-like Decision Model

DARS should support a **progressive adversarial decision loop** rather than a single blocking reviewer. The analogy is GAN-like, but the objective is not to defeat the generator; it is to improve the decision artifact until it is safer, better supported, and more logically coherent.

Core roles:

| Role | Function | Output |
|---|---|---|
| `generator` | Produces the candidate memo, alert, decision, hypothesis, or solution proposal | candidate artifact ref |
| `critic` / `devil_advocate` | Conservatively challenges the candidate using logical analysis and evidence gaps | structured critique |
| `synthesizer` | Converts critiques into an improvement plan or revised candidate | improvement proposal |
| `arbiter` / human | Decides whether to accept, revise, escalate, or defer | controlled decision record |

The default devil should be **conservative, logically strict, and constructive**:

- conservative: prefer lower confidence when evidence is weak;
- logical: identify invalid inference, missing premises, contradictions, and unsupported causal claims;
- critic: actively search for counterexamples and alternative explanations;
- constructive: recommend a better solution, not only reject the current one;
- advisory: cannot block or mutate decisions by itself.

Progression states:

```text
candidate_prepared -> critique_requested -> critique_received -> improvement_proposed -> candidate_revised -> review_closed
```

A DARS critique may mark `requires_human_review=true`, but it does **not** block execution by itself. Blocking remains the responsibility of existing Hisys approval/safety gates such as live connector approval, high/critical alert approval, secret-scan failure, traceability failure, or explicit human hold.

The progressive loop should evaluate candidates with a versioned rubric/evaluation matrix. The rubric should live in a separate controlled file, selected by Hisys and referenced by ID/version/hash in the request envelope, rather than being embedded as arbitrary prompt text. The design baseline is `docs/contracts/dars-evaluation-rubrics.md`; runtime instances should place approved JSON rubrics under `<instance-root>/harness/rubrics/dars/`.

### 2.4 Backend Modes

| Mode | Purpose | External call | Default |
|---|---|---:|---:|
| `loopback_placeholder` | Current no-DARS placeholder | false | yes until replaced |
| `fixture_file` | Local deterministic DARS response fixture | false | allowed in tests |
| `mock_http` | Local/mock endpoint contract test | false or local-only | later test increment |
| `real_dars_disabled` | Configured real backend but blocked | false | required before live |
| `real_dars_enabled` | Actual DARS backend | true | future explicit approval only |

### 2.5 Configuration Model

Yes: DARS must be configurable because a site may use different LLM/agent backends. The product should not hard-code “DARS = one service”. Treat DARS as a **role/contract** and select a backend adapter through runtime instance config.

Recommended config path:

```text
<instance-root>/config/dars.json
```

Recommended non-secret example:

```json
{
  "schema_id": "hisys.dars.config",
  "schema_version": "0.1.0",
  "config_id": "dars-default",
  "config_version": "0.1.0",
  "owner": "sysailab",
  "status": "draft",
  "classification": "runtime_config",
  "traceability": {
    "requirements": ["HISYS-FR-AGT-001", "HISYS-T-019", "HISYS-T-020"],
    "constraints": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"]
  },
  "spec": {
    "default_backend": "loopback_placeholder",
    "policy": {
      "enabled": false,
      "allowed_actions": "advisory_only",
      "require_human_approval_for_external_call": true,
      "require_structured_output_schema": "DarsCritiqueRecord",
      "allow_external_side_effects": false,
      "max_runtime_seconds": 300,
      "redact_markdown_outputs": true
    },
    "roles": {
      "default_devil_advocate": {
        "kind": "devil_advocate",
        "profession": "systems_safety_reviewer",
        "stance": "skeptical_but_constructive",
        "strictness": "high",
        "creativity": "medium",
        "verbosity": "concise_structured",
        "critique_dimensions": ["unsupported_claims", "counterarguments", "risk_findings", "missing_evidence"],
        "prompt": {
          "objective": "Challenge unsupported claims and hidden assumptions.",
          "focus": "Prefer evidence-linked objections over generic criticism."
        },
        "sampling": {"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 2000},
        "output_contract": "DarsCritiqueRecord"
      }
    },
    "backends": {
      "loopback_placeholder": {
        "kind": "loopback",
        "enabled": true,
        "mode": "local_only",
        "external_call_allowed": false,
        "output_contract": "DarsCritiqueRecord"
      },
      "fixture_file": {
        "kind": "fixture_file",
        "enabled": false,
        "mode": "local_only",
        "fixture_path": "harness/fixtures/dars/critique-response.json",
        "external_call_allowed": false,
        "output_contract": "DarsCritiqueRecord"
      }
    }
  }
}
```

Configuration rules:

1. The checked-in example config must keep every non-loopback backend disabled.
2. Secrets are never stored in `config/dars.json`; use `credential_ref` pointing to local-only `secrets/` or environment-specific secret stores.
3. A backend can be configured but still blocked by dispatch policy. Configuration alone is not approval.
4. Every backend must declare `output_contract: DarsCritiqueRecord`; adapter output is rejected unless it validates.
5. CLI agents such as Claude, Codex, OpenCode, or a local LLM are just adapter kinds. They must return structured critique JSON and may not write files, execute triggers, or alter Hisys state.
6. A runtime-boundary dispatch decision must record the selected backend, enabled state, approval ref, blocked reasons, and whether any external call was made.
7. Role/persona settings are controlled configuration, not free-form runtime prompt injection. A runtime prompt is assembled from: approved role profile + handoff context + evidence refs + output schema + safety constraints.
8. Model sampling knobs such as `temperature`, `top_p`, and `max_output_tokens` belong in role/backend config and must be recorded in boundary metadata for reproducibility.
9. User-provided prompt text may request a critique type or focus area, but it must not override safety constraints, output contract, allowed actions, tool restrictions, or approval gates.
10. Keep configuration concise for LLM interpretation: deterministic choices are key/value enum fields; only semantically open guidance goes under a small `prompt:` block.
11. All configuration files must pass schema validation and cross-field policy validation before runtime use.
12. Hisys should use a common configuration envelope so validators can produce consistent diagnostics across DARS, Investigator, live connectors, and future agent configs.
13. The conservative logical devil is the default critic role. Additional critics should differ by `profession`, `persona`, `knowledge_scope`, and `critique_dimensions`, not by weakening safety or output contracts.
14. Progressive decision settings should describe how critiques improve a candidate artifact across rounds; they must not grant DARS blocking authority or execution authority.

Target schema extension for multi-agent progressive critique:

```json
{
  "spec": {
    "decision_process": {
      "mode": "progressive_adversarial",
      "objective": "improve_solution",
      "blocking_policy": "advisory_only",
      "max_rounds": 3,
      "stop_condition": "no_high_severity_unresolved_findings",
      "synthesis_strategy": "revise_candidate_with_evidence_linked_improvements"
    },
    "roles": {
      "logical_conservative_devil": {
        "kind": "devil_advocate",
        "profession": "logic_reviewer",
        "persona": "conservative_critic",
        "knowledge_scope": ["formal_logic", "causal_reasoning", "evidence_quality"],
        "stance": "skeptical_but_constructive",
        "strictness": "high",
        "creativity": "low",
        "verbosity": "concise_structured",
        "critique_dimensions": ["logical_validity", "unsupported_claims", "contradictions", "missing_premises"],
        "prompt": {
          "objective": "Find logical gaps, invalid inference, contradictions, and unsupported claims.",
          "focus": "Improve the decision by proposing evidence-linked corrections rather than blocking it."
        },
        "output_contract": "DarsCritiqueRecord"
      },
      "domain_expert_devil": {
        "kind": "devil_advocate",
        "profession": "domain_scientist",
        "persona": "technical_reviewer",
        "knowledge_scope": ["domain_assumptions", "mechanism_validity", "experimental_design"],
        "stance": "skeptical_but_constructive",
        "strictness": "medium",
        "creativity": "medium",
        "verbosity": "concise_structured",
        "critique_dimensions": ["missing_evidence", "mechanism_gaps", "alternative_explanations"],
        "prompt": {
          "objective": "Challenge weak domain assumptions and propose stronger technical evidence.",
          "focus": "Prefer constructive alternatives and better validation paths."
        },
        "output_contract": "DarsCritiqueRecord"
      }
    },
    "agent_panel": [
      {"role_ref": "logical_conservative_devil", "backend_ref": "loopback_placeholder", "round": 1},
      {"role_ref": "domain_expert_devil", "backend_ref": "fixture_file", "round": 1}
    ]
  }
}
```

This is a target extension for the next schema increment. The currently executable checked-in `config/dars.json` remains minimal until validator models are extended by TDD.

This mirrors the existing `investigator-agents.yaml` pattern: optional LLM/search/agent integrations are declared as future integration points, disabled by default, and bounded by output contracts and side-effect policy.

### 2.6 Adapter Kind Contract

Use an adapter registry rather than one DARS implementation:

| `kind` | Intended backend | Initial status |
|---|---|---|
| `loopback` | current placeholder | enabled local-only |
| `fixture_file` | deterministic test fixture | implement first |
| `mock_http` | local mock endpoint | later |
| `openai_compatible` | local Ollama/vLLM/OpenAI-compatible endpoint | disabled |
| `cli_agent` | Claude/Codex/OpenCode/custom command | disabled |
| `hermes_delegate` | Hermes delegated task as DARS role | disabled |

All adapter kinds must normalize to the same `DarsCritiqueRecord`; downstream Hisys code should not care which LLM/agent produced the critique.

### 2.7 Prompt and Role Assembly

DARS should include configurable "devil" characteristics, but they should be encoded as **approved role profiles** and prompt templates, not as arbitrary prompt text that can bypass the product boundary.

Configuration must stay concise and easy for an LLM to interpret. Use this rule:

- If a setting has deterministic meaning, express it as a key/value pair with an enum-like value.
- If a setting needs interpretation, place it inside a small `prompt:` block.
- Avoid long prose at the top level of config.
- Avoid multiple synonymous fields that ask the LLM to infer the same thing.

Examples:

```yaml
# deterministic / enum-like
kind: devil_advocate
profession: systems_safety_reviewer
stance: skeptical_but_constructive
strictness: high
creativity: medium
verbosity: concise_structured
critique_dimensions: [unsupported_claims, counterarguments, risk_findings]

# interpretive / prompt-like
prompt:
  objective: "Challenge unsupported claims and hidden assumptions."
  focus: "Prefer evidence-linked objections over generic criticism."
```

Separate the design into four layers:

1. **Stable system contract** — non-overridable safety rules, output schema, allowed actions, traceability requirements.
2. **Role profile** — devil's advocate characteristics, profession, domain expertise, strictness, creativity, verbosity, and sampling defaults.
3. **Task/handoff context** — concrete memo/alert/source/requirement evidence to critique.
4. **User focus request** — optional emphasis such as "challenge financial assumptions" or "review as a safety engineer".

The final prompt should be assembled deterministically:

```text
system_contract + role_profile + handoff_context + evidence_refs + output_schema + user_focus
```

User focus is last-mile guidance only. It may narrow the critique lens, but cannot change safety policy, schema, tools, or approval gates.

Recommended role profile fields:

| Field | Type | Purpose | Example |
|---|---|---|---|
| `kind` | enum key/value | stable role kind | `devil_advocate` |
| `profession` | enum key/value | professional lens | `logic_reviewer`, `systems_safety_reviewer`, `security_reviewer`, `domain_scientist`, `investment_risk_reviewer` |
| `persona` | enum key/value | behavior style | `conservative_critic`, `technical_reviewer`, `safety_reviewer` |
| `knowledge_scope` | enum list | knowledge lens assigned to this critic | formal_logic, causal_reasoning, evidence_quality |
| `stance` | enum key/value | critique posture | `skeptical_but_constructive` |
| `strictness` | enum key/value | threshold for flagging issues | low/medium/high |
| `creativity` | enum key/value | how much to search for non-obvious objections | low/medium/high |
| `verbosity` | enum key/value | output style | concise_structured |
| `critique_dimensions` | enum list | required critique axes | logical_validity, unsupported_claims, counterarguments, risks |
| `sampling.temperature` | numeric key/value | model sampling | usually `0.1` to `0.3` for reproducible critique |
| `prompt.objective` | prompt text | concise interpretive goal | challenge weak evidence |
| `prompt.focus` | prompt text | optional emphasis | prefer evidence-linked objections |
| `output_contract` | enum key/value | required schema | `DarsCritiqueRecord` |

Suggested default: `persona=conservative_critic`, `profession=logic_reviewer`, `temperature=0.2`, `strictness=high`, `creativity=low`, `verbosity=concise_structured`. Increase creativity only for ideation/assumption discovery; keep low temperature for compliance, release, and evidence review.

### 2.8 Common Configuration Format and Validator

Yes: define a common configuration envelope. DARS can have its own domain schema, but every Hisys runtime configuration file should share a small top-level format so validation, reports, and errors are consistent.

Recommended common envelope:

```json
{
  "schema_id": "hisys.dars.config",
  "schema_version": "0.1.0",
  "config_id": "dars-default",
  "config_version": "0.1.0",
  "owner": "sysailab",
  "status": "draft",
  "classification": "runtime_config",
  "traceability": {
    "requirements": ["HISYS-FR-AGT-001", "HISYS-T-019", "HISYS-T-020"],
    "constraints": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"]
  },
  "metadata": {
    "description": "DARS backend and role configuration.",
    "updated": "2026-05-09"
  },
  "spec": {
    "default_backend": "loopback_placeholder",
    "policy": {},
    "roles": {},
    "backends": {}
  }
}
```

Common fields:

| Field | Required | Purpose |
|---|---:|---|
| `schema_id` | yes | selects validator/model, e.g. `hisys.dars.config` |
| `schema_version` | yes | schema compatibility check |
| `config_id` | yes | stable config artifact id |
| `config_version` | yes | controlled configuration version |
| `owner` | yes | accountable maintainer/site |
| `status` | yes | `draft`, `active`, `deprecated`, `disabled` |
| `classification` | yes | `runtime_config`, `harness_config`, etc. |
| `traceability` | yes | requirement/constraint refs |
| `metadata` | optional | short human description only |
| `spec` | yes | domain-specific validated payload |

Validation should have three layers:

1. **Envelope validation** — all configs share this.
   - required common fields exist;
   - `schema_id` is known;
   - version is supported;
   - `traceability.requirements` and `traceability.constraints` are non-empty for controlled configs;
   - no secret-like raw values appear in config text.
2. **Domain schema validation** — DARS-specific Pydantic model.
   - `default_backend` exists in `spec.backends`;
   - enum values are valid;
   - `roles.*.prompt` is the only location for interpretive prose;
   - sampling bounds are valid, e.g. `0 <= temperature <= 1`, `0 < top_p <= 1`;
   - `output_contract == DarsCritiqueRecord` for all DARS roles/backends.
3. **Cross-field policy validation** — safety logic that basic schema cannot express.
   - non-loopback backends are disabled by default in checked-in examples;
   - `external_call_allowed=true` requires `policy.enabled=true`, human approval, credential reference, and non-local test evidence;
   - `credential_ref` is allowed, raw credential values are not;
   - `cli_agent` backends must declare allowed/disallowed tools;
   - `openai_compatible` external API backends must not be enabled in example configs;
   - user prompt/focus fields cannot set tools, actions, approval, schema, or backend.

Validator API design:

```python
class ConfigValidationIssue(BaseModel):
    path: str
    severity: Literal["error", "warning"]
    code: str
    message: str

class ConfigValidationReport(BaseModel):
    config_ref: str
    schema_id: str
    valid: bool
    issues: list[ConfigValidationIssue]
```

Suggested CLI:

```bash
hisys validate-config --instance examples/instance
hisys validate-config --path examples/instance/config/dars.json --schema hisys.dars.config
```

Suggested output files when running full validation:

```text
reports/config-validation/<YYYYMMDD>/config-validation-report.json
reports/config-validation/<YYYYMMDD>/config-validation-report.md
```

Implementation approach:

- Add generic validator foundation first: `src/hisys/config/validation.py`.
- Add DARS models second: `src/hisys/agents/dars_config.py`.
- Keep the Pydantic model strict: reject unknown top-level/domain fields to preserve concise configuration.
- Provide clear path-based errors like `spec.roles.default_devil_advocate.strictness`.

### 2.9 Minimal Valid DARS Config Example

With the common envelope, the DARS example should look like this:

```json
{
  "schema_id": "hisys.dars.config",
  "schema_version": "0.1.0",
  "config_id": "dars-default",
  "config_version": "0.1.0",
  "owner": "sysailab",
  "status": "draft",
  "classification": "runtime_config",
  "traceability": {
    "requirements": ["HISYS-FR-AGT-001", "HISYS-T-019", "HISYS-T-020"],
    "constraints": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"]
  },
  "spec": {
    "default_backend": "loopback_placeholder",
    "policy": {
      "enabled": false,
      "allowed_actions": "advisory_only",
      "require_human_approval_for_external_call": true,
      "require_structured_output_schema": "DarsCritiqueRecord",
      "allow_external_side_effects": false,
      "max_runtime_seconds": 300,
      "redact_markdown_outputs": true
    },
    "roles": {
      "default_devil_advocate": {
        "kind": "devil_advocate",
        "profession": "systems_safety_reviewer",
        "stance": "skeptical_but_constructive",
        "strictness": "high",
        "creativity": "medium",
        "verbosity": "concise_structured",
        "critique_dimensions": ["unsupported_claims", "counterarguments", "risk_findings", "missing_evidence"],
        "prompt": {
          "objective": "Challenge unsupported claims and hidden assumptions.",
          "focus": "Prefer evidence-linked objections over generic criticism."
        },
        "sampling": {"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 2000},
        "output_contract": "DarsCritiqueRecord"
      }
    },
    "backends": {
      "loopback_placeholder": {
        "kind": "loopback",
        "enabled": true,
        "mode": "local_only",
        "external_call_allowed": false,
        "output_contract": "DarsCritiqueRecord"
      }
    }
  }
}
```

---

## 3. Data Format Contract

Hisys and DARS exchange data through canonical JSON-compatible envelopes documented in `docs/contracts/dars-data-format.md`:

1. `DarsRequestEnvelope` — Hisys → DARS. Wraps the existing `AgentHandoffPackage` with stable schema/version metadata, non-overridable safety contract, selected role profile, sampling metadata, record refs, evidence refs, constraints, and optional user focus.
2. `DarsResponseEnvelope` — DARS → Hisys. Contains producer provenance plus a structured `DarsCritiqueRecord` and boundary evidence proving the response stayed advisory-only.

The adapter layer may translate those envelopes to backend-specific prompts/API/CLI inputs, but Hisys only accepts normalized envelopes. Response validation must reject mismatched `request_id`/`handoff_id`, invalid enums, malformed JSON, raw secrets, unsupported action types, or any claim that DARS already mutated state or performed an external side effect.

---

## 4. Data Model Design

### 4.1 Existing Handoff Package

Keep `AgentHandoffPackage` as the outbound request object. Strengthen use of existing fields before adding new schema fields:

- `handoff_id`
- `target_agent_system="DARS"`
- `task`
- `context`
- `evidence_bundle`
- `constraints`
- `expected_output`
- `allowed_actions="advisory_only"`
- `approval_state`
- `source_registry_refs`
- `scope_policy_ref`
- `boundary_record_refs`
- `collection_output_refs`
- `prohibited_actions`
- `result_refs`
- `status`

Potential later additions only if tests prove necessary:

- `handoff_type`: `critique | risk_review | requirements_review | evidence_gap_review`
- `requester`
- explicit structured `record_refs` object

### 4.2 DARS Critique Record

Evolve `DarsCritiqueRecord` from plain text into structured advisory evidence.

Target fields:

```yaml
critique_id: CRITIQUE-...
handoff_ref: HANDOFF-...
source_execution_ref: EXEC-...
target_agent_system: DARS
dars_backend: loopback_placeholder | fixture_file | mock_http | real_dars_disabled | real_dars_enabled
external_call_made: boolean
allowed_actions: advisory_only
action_taken: none
status: received | linked | rejected | closed
producer_id: string
critique_summary: string
unsupported_claims: list[string]
counterarguments: list[string]
risk_findings: list[string]
confidence_assessment: none | low | medium | high | unknown
recommended_actions: list[string]
requires_human_review: boolean
linked_record_refs:
  sources: list[string]
  observations: list[string]
  signals: list[string]
  memos: list[string]
  alerts: list[string]
validation_warnings: list[string]
policy_refs: list[string]
```

### 4.3 DARS Dispatch Decision

Before any adapter is called, write a runtime-boundary dispatch decision.

```yaml
decision_id: DARS-DISPATCH-...
handoff_ref: HANDOFF-...
backend_mode: fixture_file | mock_http | real_dars_disabled | real_dars_enabled
adapter_id: string
enabled: boolean
approval_ref: string | null
allowed_actions: advisory_only
external_call_permitted: boolean
external_call_made: false
blocked_reasons: list[string]
action_taken: none
```

This mirrors the live connector safety decision pattern and makes DARS dispatch auditable.

---

## 5. Runtime Flow

### 4.1 Fixture/Mock Flow

1. Load source execution / alert / memo context.
2. Build `AgentHandoffPackage`.
3. Write handoff JSON/Markdown to `data/agent-handoffs/<YYYYMMDD>/`.
4. Evaluate DARS dispatch decision.
5. If backend is `fixture_file`, load local fixture response.
6. Validate response into structured `DarsCritiqueRecord`.
7. Link critique to execution/memo/alert/evidence refs.
8. Write critique JSON/Markdown to `data/agent-critiques/<YYYYMMDD>/`.
9. Write dispatch/report artifacts to:
   - `runtime-boundary/dars/<YYYYMMDD>/`
   - `reports/run-summaries/<YYYYMMDD>/dars-critique-report.{json,md}`

### 4.2 Real Backend Flow — Future Only

Real dispatch remains blocked until all are true:

- DARS backend config exists and is explicitly enabled.
- Adapter action is allow-listed.
- Handoff `allowed_actions` remains `advisory_only` unless a later controlled policy changes it.
- Human or controlled-policy approval ref exists.
- Secrets are loaded only from local-only secret storage, never committed.
- Mock/fixture tests and traceability gate pass.
- Runtime-boundary dispatch decision records `external_call_permitted=true` before adapter execution.

Even then, DARS response remains advisory and cannot directly trigger downstream action.

---

## 6. Failure and Safety Rules

1. Missing source execution -> report skipped execution; no handoff dispatch.
2. Disabled backend -> write blocked dispatch decision; no external call.
3. Missing approval for real backend -> blocked dispatch decision.
4. Malformed DARS response -> write rejected critique with validation warnings; do not link as accepted evidence.
5. DARS timeout/error -> bounded failure record; unrelated workflows continue.
6. Secret-like values in DARS payload/response -> redact in Markdown/report output; secret scan must remain clean.
7. Recommended actions from DARS are advisory strings only; never executed by DARS ingestion.

---

## 7. Ralph/TDD Implementation Queue

### Task DARS-0: Common configuration validator and DARS configuration contract

**Objective:** Add a common configuration envelope plus disabled-by-default `config/dars.json` schema/loading behavior so users can choose different DARS LLM/agent backends without changing product code.

**Files:**

- Create: `src/hisys/config/validation.py`
- Create: `examples/instance/config/dars.json`
- Create or modify: `src/hisys/agents/dars_config.py`
- Modify: `src/hisys/config/loader.py` only if shared loader support is useful
- Test: `tests/unit/test_config_validation.py`
- Test: `tests/unit/test_dars_config.py`
- Modify: `docs/traceability/README.md`

**RED:** Add tests asserting the common envelope is required, unknown schema IDs fail, path-based validation issues are reported, multiple backend kinds and concise role profiles can be declared, deterministic role fields are enum-like key/value pairs, interpretive fields are contained under `prompt:`, non-loopback backends remain disabled by default, secrets are referenced only by `credential_ref`, model knobs are bounded, and invalid backend/output contract values are rejected.

**GREEN:** Implement minimal Pydantic config envelope, validation report/issue objects, DARS config model, and JSON loader. Do not dispatch any backend yet.

**Verify:**

```bash
python3 -m pytest tests/unit/test_dars_config.py -q
python3 -m pytest
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py --json .
```

**Commit:** `feat: add dars backend configuration contract`

---

### Task DARS-A: DARS protocol envelope and structured critique ingestion schema

**Objective:** Implement the canonical `DarsRequestEnvelope` and `DarsResponseEnvelope` from `docs/contracts/dars-data-format.md`, then map validated responses into structured advisory critique records while preserving current loopback tests.

**Files:**

- Create: `src/hisys/agents/dars_protocol.py`
- Create: `tests/unit/test_dars_protocol.py`
- Modify: `src/hisys/agents/dars.py`
- Modify: `tests/unit/test_dars_runtime.py`
- Modify: `docs/traceability/README.md`

**RED:** Add tests asserting valid request/response envelopes pass, response `request_id`/`handoff_id` mismatches fail, mutation/external-side-effect claims are rejected, enum paths are reported, `decision_process`, `rubric_refs`, `critic_panel`, `decision_trace`, and `rubric_scores` preserve progressive adversarial evaluation metadata, `blocks_decision=false` is enforced for DARS critique, and `unsupported_claims`, `counterarguments`, `risk_findings`, `recommended_actions`, `requires_human_review`, and `linked_record_refs` are persisted as advisory evidence.

**GREEN:** Add minimal Pydantic protocol models and response validation helpers, extend `DarsCritiqueRecord` with defaults plus progressive decision trace and rubric-score metadata, and keep loopback/fixture behavior local-only.

**Verify:**

```bash
python3 -m pytest tests/unit/test_dars_runtime.py -q
python3 -m pytest
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py --json .
```

**Commit:** `feat: structure dars critique ingestion`

---

### Task DARS-B: Dispatch decision gate

**Objective:** Add runtime-boundary DARS dispatch decisions before backend selection.

**Files:**

- Create: `src/hisys/agents/dars_dispatch.py` or extend `src/hisys/agents/dars.py`
- Modify: `tests/unit/test_dars_runtime.py`
- Modify: `examples/instance/harness/guidelines/dars.md`

**RED:** Add tests for disabled real backend and fixture backend decision artifacts.

**GREEN:** Persist `DarsDispatchDecision` Markdown/JSON under `runtime-boundary/dars/<YYYYMMDD>/`.

**Commit:** `feat: add dars dispatch safety decisions`

---

### Task DARS-C: Fixture-file DARS backend

**Objective:** Replace ad hoc `--critique-text` fixture path with a deterministic fixture backend contract.

**Files:**

- Add fixture under `examples/instance/harness/fixtures/dars/`
- Modify: `src/hisys/agents/dars.py`
- Modify: CLI command for `request-dars-critique` if needed
- Test: `tests/unit/test_dars_runtime.py`

**RED:** Test fixture response ingestion with multiple structured critique lists.

**GREEN:** Load fixture file and validate into `DarsCritiqueRecord`.

**Commit:** `feat: add fixture dars backend contract`

---

### Task DARS-D: Malformed critique rejection

**Objective:** Reject unsafe/malformed DARS responses without breaking the run.

**Files:**

- Modify: `src/hisys/agents/dars.py`
- Test: `tests/unit/test_dars_runtime.py`

**RED:** Test missing summary, invalid severity, or action-like recommendation that violates allowed actions.

**GREEN:** Mark critique `status=rejected`, preserve warnings, keep `action_taken=none`.

**Commit:** `fix: reject malformed dars critiques safely`

---

### Task DARS-E: End-to-end trace link

**Objective:** Extend trace-path evidence so DARS critique is reconstructable from source execution/memo/alert.

**Files:**

- Modify: `tests/integration/test_trace_path.py`
- Modify: `src/hisys/operations/release_readiness.py` if needed
- Modify: `docs/traceability/README.md`

**RED:** Test source -> observation/signal/memo/alert -> DARS handoff -> critique refs.

**GREEN:** Add missing refs/report fields only where necessary.

**Commit:** `feat: link dars critique in trace path`

---

### Task DARS-F: Mock endpoint adapter, disabled by default

**Objective:** Add adapter interface and local/mock transport without enabling real DARS.

**Files:**

- Create: `src/hisys/agents/dars_adapters.py`
- Modify: `src/hisys/agents/dars.py`
- Test: `tests/unit/test_dars_adapters.py`

**RED:** Test disabled mock adapter blocks external-style calls unless config explicitly selects local mock.

**GREEN:** Implement adapter protocol and local mock response path.

**Commit:** `feat: add disabled dars adapter interface`

---

## 7. Acceptance Criteria for Design Phase

The design is ready for implementation when:

- The first executable increment is local-only and testable.
- Real DARS calls are explicitly deferred behind disabled-by-default config and approval.
- DARS output cannot directly mutate records or trigger connectors.
- Structured critique fields satisfy `HISYS-DARS-CONTRACT-001` expected output.
- The progressive adversarial loop improves candidate decisions through conservative logical critique and synthesis rather than automatic blocking.
- The queue supports Ralph/TDD execution in small commits.

---

## 8. Recommended Next Ralph Start

Start with **Task DARS-A: DARS protocol envelope and structured critique ingestion schema**.

DARS-0 is already implemented as the JSON configuration validator baseline. DARS-A should now include the progressive adversarial fields (`decision_process`, `critic_panel`, `decision_trace`) so the conservative logical devil and future multi-profession critics can be represented before any real backend is enabled.

Reason:

- Users may choose different DARS agent backends such as Claude, Codex, OpenCode, Hermes delegation, a local LLM, or an OpenAI-compatible service.
- The backend selection must be declarative and disabled-by-default before any adapter execution is implemented.
- The DARS request/response envelopes now define progressive adversarial process metadata, so DARS-A has stable inputs for critic role, critic panel, rubric refs, rubric scores, round index, non-blocking policy, and improvement direction.
- DARS-A remains local and testable after the config contract exists.
