# AI Collaboration Process Quality Rubrics

**Status:** design-baseline  
**Version:** 0.1.0  
**Traceability:** HISYS-DARS-CONTRACT-001; HISYS-FR-AGT-001..005; HISYS-CON-010; HISYS-CON-011; HISYS-CON-012

## 1. Purpose

This document defines evaluation rubrics for AI-assisted work processes. It
assesses whether an AI collaboration is structured, reviewable, reproducible,
and governed. It does not evaluate prompt style, persona appeal, or model
fluency by itself.

The rubric is intended for Hisys reviews of code analysis, research synthesis,
agent-assisted implementation, education/training workflows, and Hermes skill or
persona changes. It complements the DARS progressive decision rubric in
`docs/contracts/dars-evaluation-rubrics.md`.

## 2. Design Basis

This rubric distills four operating observations:

1. A useful prompt is a work-design artifact, not a clever sentence.
2. AI-assisted results are weaker when the process trail, evidence refs, and
   validation criteria are missing.
3. Persona and tone can improve collaboration, but they must not override
   controlled requirements, verification rules, safety boundaries, or human
   approval gates.
4. AI collaboration logs are useful only when privacy, retention, access, and
   redaction rules are explicit.

## 3. Applicability

Use this rubric when evaluating:

- a spec-first packet, finish packet, or agent workflow packet;
- a codebase analysis, source-inspection report, or change-impact analysis;
- a research memo, literature synthesis, or evidence-backed decision packet;
- a Hermes skill, SOUL/persona change, or agent behavior guideline;
- an AI education/training rubric or process portfolio;
- a reusable workflow that claims to improve future human/agent performance.

Do not use this rubric as a substitute for domain-specific correctness checks.
It evaluates collaboration process quality. Domain evidence, statistical claims,
code behavior, and security findings still require their own source-specific
validation.

## 4. Common Scoring Model

Each axis should produce a structured finding:

```json
{
  "axis_id": "task_structure_quality",
  "score": 4,
  "max_score": 5,
  "severity": "medium",
  "confidence": "high",
  "rationale": "The packet defines objective, scope, and expected artifacts, but the validation criteria do not name focused tests.",
  "evidence_refs": ["PACKET-001", "DOC-002"],
  "improvement_recommendation": "Add focused validation commands and expected pass/fail evidence."
}
```

Score semantics:

| Score | Meaning | Default improvement direction |
|---:|---|---|
| 0 | Not evaluated / not applicable | no-op with rationale |
| 1 | Critical weakness | revise process or request more evidence |
| 2 | Major weakness | add structure, evidence, or governance boundary |
| 3 | Acceptable but incomplete | improve if low-cost; lower confidence if needed |
| 4 | Strong | accept with minor process edits |
| 5 | Excellent | accept process for this axis |

Scores are advisory evidence. They do not approve, block, publish, deploy, or
mutate artifacts by themselves.

## 5. Process Quality Matrix

| Axis | Question | Score 1 signal | Score 3 signal | Score 5 signal |
|---|---|---|---|---|
| `task_structure_quality` | Are objective, scope, non-goals, inputs, constraints, expected artifacts, and validation criteria defined? | Output requested without structure or acceptance criteria | Most structure exists, but scope or validation is incomplete | Work is framed as a bounded executable/reviewable packet with explicit validation |
| `process_reproducibility` | Can another reviewer or agent reproduce the process from recorded steps, artifacts, prompts, evidence refs, and validation results? | No process trail, artifact refs, or validation record | Some steps and refs exist, but replay would require guessing | Versioned inputs, steps, artifacts, refs, commands, and results support replay |
| `answer_interrogation_quality` | Were assumptions, uncertainty, and failure cases challenged before accepting generated output? | Generated answer accepted directly | Some caveats or checks are present | Assumptions, alternatives, failures, and confidence changes are explicitly tested or recorded |
| `evidence_boundary_integrity` | Are facts, interpretations, generated content, user-provided data, and inaccessible sources separated? | Provenance and claim strength are mixed | Main evidence boundaries are noted, but some claims are over-broad | Source access, evidence type, confidence, and interpretation boundaries are explicit |
| `persona_boundary_integrity` | Does persona guidance improve collaboration without overriding governance? | Persona weakens gates, grants authority, or bypasses source/tool rules | Persona is mostly harmless but boundary precedence is unclear | Persona improves tone while explicitly preserving controlled requirements and human gates |
| `privacy_and_log_governance` | Are AI collaboration logs safe to retain, evaluate, and share? | Raw sensitive data is retained without policy | Some redaction or access caution exists | Redaction, retention, access, minimization, and evaluation use are explicit |
| `learning_transfer` | Does the work preserve reusable lessons, templates, checks, tests, or examples? | Disposable result only | Some reusable observation is present | Durable convention, template, rubric, test, or skill candidate is extracted without raw sensitive data |
| `tool_boundary_discipline` | Are external calls, mutations, publications, credentials, and live actions controlled? | Tool side effects occur without boundary record or approval | Boundary is partly recorded but approval or evidence is incomplete | Boundary records and approval constraints are explicit; live action remains human-gated when required |
| `scope_and_context_hygiene` | Is the context focused enough for large-codebase or long-running work? | The agent is asked to inspect everything with no starting map | Scope is bounded but still includes unnecessary context | Work starts from a thin map, scoped files, relevant tests, and explicit exclusion rules |

## 6. Role-Specific Use

### 6.1 Process Reviewer

Primary axes:

```text
task_structure_quality
process_reproducibility
answer_interrogation_quality
learning_transfer
```

The process reviewer checks whether the collaboration can be repeated and
improved, not whether the final domain claim is true by itself.

### 6.2 Evidence Boundary Reviewer

Primary axes:

```text
evidence_boundary_integrity
answer_interrogation_quality
tool_boundary_discipline
privacy_and_log_governance
```

The evidence boundary reviewer checks claim strength, source access, provenance,
log safety, and side-effect boundaries.

### 6.3 Persona/Governance Reviewer

Primary axes:

```text
persona_boundary_integrity
privacy_and_log_governance
tool_boundary_discipline
scope_and_context_hygiene
```

The persona/governance reviewer checks whether SOUL/persona/skill changes improve
collaboration without weakening controlled requirements, source verification,
human approval boundaries, or project governance.

### 6.4 Large-Codebase Reviewer

Primary axes:

```text
scope_and_context_hygiene
task_structure_quality
process_reproducibility
tool_boundary_discipline
learning_transfer
```

The large-codebase reviewer checks whether the work starts from a scoped map,
uses deterministic inventory/symbol evidence when available, records focused
validation commands, and avoids dumping generated/dependency files into the
analysis context.

## 7. Aggregation and Synthesis

Recommended aggregation fields:

```json
{
  "rubric_summary": {
    "rubric_id": "ai-collaboration-process-quality",
    "rubric_version": "0.1.0",
    "overall_score": 3.7,
    "min_axis_score": 2,
    "highest_severity": "medium",
    "unresolved_high_severity_findings": 0,
    "recommended_improvement_direction": "revise_process_packet",
    "rationale": "The task structure is adequate, but privacy governance and replay evidence need revision."
  }
}
```

Default synthesis policy:

| Condition | Suggested direction | Blocking? |
|---|---|---:|
| persona guidance weakens controlled requirements or safety gates | `escalate_to_human` and revise persona/rubric | no, advisory unless another Hisys gate blocks |
| live action, mutation, publication, or credential use lacks boundary record | `request_more_evidence` or `escalate_to_human` | no, advisory unless controlled policy blocks |
| any axis score 1 | `revise_process_packet` or `request_more_evidence` | no |
| min score 2 and no high severity | `revise_process_packet` | no |
| all primary axes >= 3 | `accept_for_human_review` with improvements | no |
| all primary axes >= 4 | `accept_for_human_review` | no |

This rubric must not grant agents authority to approve live external actions,
publish results, weaken `needs_more_evidence`, or bypass human gates.

## 8. Minimal JSON Rubric Shape

```json
{
  "schema_id": "hisys.ai_collaboration.rubric",
  "schema_version": "0.1.0",
  "rubric_id": "ai-collaboration-process-quality",
  "rubric_version": "0.1.0",
  "status": "design-baseline",
  "objective": "Evaluate whether AI-assisted work is structured, reviewable, reproducible, and governed.",
  "axes": [
    {
      "axis_id": "task_structure_quality",
      "weight": 1.0,
      "question": "Are objective, scope, non-goals, inputs, constraints, expected artifacts, and validation criteria defined?",
      "score_scale": {"min": 1, "max": 5},
      "low_score_signal": "Output requested without structure or acceptance criteria.",
      "high_score_signal": "Work is framed as a bounded executable/reviewable packet with explicit validation."
    }
  ],
  "aggregation": {
    "method": "weighted_average_with_min_axis_guard",
    "default_improvement_direction": "revise_process_packet",
    "blocking_policy": "advisory_only"
  }
}
```

## 9. Versioning Rules

1. Rubrics must include `rubric_id`, `rubric_version`, and `schema_version`.
2. Request envelopes should include rubric refs and hashes when the rubric is
   used as a governed evaluation basis.
3. Response envelopes should echo the rubric refs used by the reviewer.
4. Rubric changes require a new version or a controlled status update.
5. Agents may not invent new scoring axes unless the response records them as
   `validation_warnings` and Hisys accepts them through a later schema update.
6. Raw collaboration logs should not be copied into durable memory or personal
   vaults by default. Store curated lessons, templates, tests, or rubric changes
   instead.
