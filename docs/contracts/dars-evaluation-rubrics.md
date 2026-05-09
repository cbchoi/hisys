# DARS Progressive Decision Evaluation Rubrics

**Status:** design-baseline  
**Version:** 0.1.0  
**Traceability:** HISYS-DARS-CONTRACT-001; HISYS-FR-AGT-001..005; HISYS-T-019; HISYS-T-020; HISYS-T-024; HISYS-CON-010; HISYS-CON-011; HISYS-CON-012

## 1. Purpose

This document defines the evaluation matrix used by DARS critic agents in the progressive adversarial decision loop. The goal is not to block decisions by default. The goal is to improve candidate decisions, memos, alerts, hypotheses, or solution proposals by identifying logical, evidential, risk, and implementation weaknesses.

The matrix is a controlled artifact. LLM agents should receive a referenced rubric snapshot as part of the DARS request package rather than relying on hidden prompt memory.

## 2. File Loading Rule

Yes: each DARS agent should load a **separate rubric file** selected by Hisys and referenced in the request envelope.

Recommended runtime layout:

```text
<instance-root>/harness/rubrics/dars/
  progressive-decision-v0.1.0.json
  logical-conservative-devil-v0.1.0.json
  domain-expert-devil-v0.1.0.json
```

Product-design source:

```text
docs/contracts/dars-evaluation-rubrics.md
```

Runtime request reference:

```json
{
  "rubric_refs": [
    {
      "rubric_id": "dars-progressive-decision",
      "rubric_version": "0.1.0",
      "artifact_ref": "harness/rubrics/dars/progressive-decision-v0.1.0.json",
      "sha256": "hex-string",
      "applies_to_roles": ["logical_conservative_devil", "domain_expert_devil"]
    }
  ]
}
```

The adapter may inline the rubric text into a backend prompt, but the canonical `DarsRequestEnvelope` should preserve the file reference and hash so the evaluation basis is auditable.

## 3. Why Separate Rubric Files

Separate rubric files are preferable to embedding the whole rubric in `config/dars.json` because:

1. **Traceability:** rubric changes can be versioned and reviewed separately from backend credentials/policy/config.
2. **Reproducibility:** each critique records the exact rubric ID, version, artifact path, and hash.
3. **Role specialization:** different critic personas can use different rubrics while sharing the same request/response schema.
4. **Prompt clarity:** LLM agents receive a focused evaluation matrix instead of an oversized config blob.
5. **Safety:** the config chooses approved rubric refs; arbitrary user prompts cannot replace the rubric.
6. **Progressive refinement:** rubrics can define thresholds for revise/accept/escalate without granting DARS execution authority.

Do not allow runtime user text to provide an unvalidated rubric. User focus may select an approved rubric or emphasize an axis, but Hisys must validate the rubric reference first.

## 4. Common Scoring Model

Each evaluation axis should produce:

```json
{
  "axis_id": "logical_validity",
  "score": 4,
  "max_score": 5,
  "severity": "medium",
  "confidence": "high",
  "rationale": "The conclusion is mostly supported, but one causal link is assumed rather than evidenced.",
  "evidence_refs": ["EVID-001"],
  "improvement_recommendation": "Add direct evidence for the causal link or lower confidence."
}
```

Score semantics:

| Score | Meaning | Default improvement direction |
|---:|---|---|
| 0 | Not evaluated / not applicable | no-op with rationale |
| 1 | Critical weakness | revise candidate or escalate to human |
| 2 | Major weakness | request more evidence or revise candidate |
| 3 | Acceptable but incomplete | improve if low-cost; lower confidence if needed |
| 4 | Strong | accept with minor edits |
| 5 | Excellent | accept candidate for this axis |

Scores are advisory evidence. They do not approve or block by themselves.

## 5. Progressive Decision Matrix

| Axis | Question | Conservative critic behavior | Score 1 signal | Score 3 signal | Score 5 signal |
|---|---|---|---|---|---|
| `logical_validity` | Does the conclusion follow from premises and evidence? | Look for invalid inference, circular reasoning, contradiction, missing premise | conclusion does not follow | conclusion mostly follows with gaps | conclusion follows cleanly |
| `evidence_support` | Are key claims supported by cited evidence? | Prefer lower confidence when evidence is indirect or missing | central claims unsupported | partial evidence with limitations | direct, sufficient, cited evidence |
| `causal_reasoning` | Are causal claims justified? | Challenge correlation/causation jumps and mechanism gaps | causal claim asserted only | plausible but missing mechanism | mechanism and alternatives addressed |
| `alternative_explanations` | Were plausible alternatives considered? | Search for counterexamples and rival hypotheses | alternatives ignored | some alternatives listed | strong alternatives evaluated and bounded |
| `risk_exposure` | What could go wrong if this decision is wrong? | Identify safety, operational, compliance, financial, or research risk | severe risk unmitigated | manageable risk with gaps | risk bounded with mitigation |
| `requirements_traceability` | Is the decision linked to relevant requirements/policies? | Check missing refs and uncontrolled assumptions | no trace links | partial trace links | complete relevant trace links |
| `actionability` | Does the output define useful next actions? | Prefer concrete improvement paths over generic criticism | no useful action | broad action stated | specific evidence-linked action |
| `confidence_calibration` | Is confidence proportional to evidence? | Penalize overconfidence | confidence clearly inflated | confidence partly calibrated | confidence matches evidence |
| `novelty_or_solution_quality` | Does revision improve the solution, not just reject it? | Require constructive alternatives | only negative critique | some improvement idea | better feasible solution proposed |

## 6. Role-Specific Rubric Emphasis

### 6.1 Logical Conservative Devil

Primary axes:

```text
logical_validity
evidence_support
causal_reasoning
alternative_explanations
confidence_calibration
```

Default behavior:

```text
strictness = high
creativity = low
temperature = 0.2
stance = skeptical_but_constructive
```

The logical conservative devil should penalize unsupported inference more strongly than novelty. It should propose a safer revised statement or evidence requirement instead of simply saying “reject.”

### 6.2 Domain Expert Devil

Primary axes:

```text
evidence_support
causal_reasoning
alternative_explanations
risk_exposure
novelty_or_solution_quality
```

The domain expert devil should challenge field-specific assumptions and propose better experiments, measurements, models, or literature checks.

### 6.3 Systems Safety Devil

Primary axes:

```text
risk_exposure
requirements_traceability
actionability
confidence_calibration
```

The systems safety devil should identify hazards, approval gates, boundary violations, and missing runtime evidence.

## 7. Aggregation and Synthesis

Hisys should keep individual critic scores separate, then compute or record a synthesis report.

Recommended aggregation fields:

```json
{
  "rubric_summary": {
    "overall_score": 3.4,
    "min_axis_score": 2,
    "highest_severity": "medium",
    "unresolved_high_severity_findings": 0,
    "recommended_improvement_direction": "revise_candidate",
    "rationale": "Most evidence is adequate, but causal reasoning and confidence calibration need revision."
  }
}
```

Default synthesis policy:

| Condition | Suggested direction | Blocking? |
|---|---|---:|
| any critical safety/compliance finding | `escalate_to_human` | only if existing Hisys gate says so |
| any axis score 1 | `revise_candidate` or `request_more_evidence` | no, advisory |
| min score 2 and no high severity | `revise_candidate` | no |
| all primary axes >= 3 | `accept_candidate` with improvements | no |
| all primary axes >= 4 | `accept_candidate` | no |

DARS must set `blocks_decision=false`. If a critic says a candidate should be blocked, Hisys records that as `recommended_actions[].action_type = "escalate_to_human"` or `"revise_candidate"`, not as direct blocking authority.

## 8. Rubric Versioning Rules

1. Rubrics must include `rubric_id`, `rubric_version`, and `schema_version`.
2. Request envelopes must include rubric refs and hashes.
3. Response envelopes must echo the rubric refs used by the critic.
4. Rubric changes require a new version or a controlled status update.
5. Agents may not invent new scoring axes unless the response records them as `validation_warnings` and Hisys accepts them through a later schema update.

## 9. Minimal JSON Rubric Shape

```json
{
  "schema_id": "hisys.dars.rubric",
  "schema_version": "0.1.0",
  "rubric_id": "dars-progressive-decision",
  "rubric_version": "0.1.0",
  "status": "draft",
  "objective": "Improve candidate decisions through conservative logical and evidence-linked critique.",
  "axes": [
    {
      "axis_id": "logical_validity",
      "weight": 1.0,
      "question": "Does the conclusion follow from premises and evidence?",
      "score_scale": {"min": 1, "max": 5},
      "low_score_signal": "Conclusion does not follow from the provided premises.",
      "high_score_signal": "Conclusion follows cleanly from stated premises and evidence."
    }
  ],
  "aggregation": {
    "method": "weighted_average_with_min_axis_guard",
    "default_improvement_direction": "revise_candidate",
    "blocking_policy": "advisory_only"
  }
}
```
