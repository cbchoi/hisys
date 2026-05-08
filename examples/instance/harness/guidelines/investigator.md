# Investigator Harness Guideline

Traceability: HISYS-INST-INV-001, HISYS-T-006, HISYS-T-007, HISYS-T-008,
HISYS-T-026, HISYS-T-027, HISYS-T-029, HISYS-TPL-RESEARCH-SEARCH-001.

## Purpose

Validate that the Investigator collects only from registered collectable sources,
normalizes adapter results into RawObservation records, preserves provenance, and
records audit events. Validate that `investigate-memo` can turn a research
topic/goal into a template-based Investigator memo artifact before Chief Editor
orchestration, and that optional fixture research agents produce validated
EvidencePackage artifacts before the memo is synthesized.

## Procedure

1. Load `config/source-registry.yaml` and `config/web-compliance/*.yaml`.
2. Refuse unregistered, blocked, suspended, retired, or X-class sources.
3. Execute adapters through the registry-gated adapter runtime.
4. Write RawObservation JSON files under `data/raw-observations/<YYYYMMDD>/`.
5. Append AuditEvent JSONL records under `data/audit/<YYYYMMDD>/`.
6. Continue collecting registered sources even if one source fails.
7. For direct memo runs, execute `hisys investigate-memo` with a research topic,
   goal, perspective, and one or more registered sources.
8. Optionally pass `--agent fixture --agent fixture_contradiction` to dispatch
   deterministic fixture research agents; for formalism/self-organizing-system
   topics, pass `--agent formalism_comparison --agent
   self_organization_mechanism` to dispatch domain fixture agents.
9. Verify each `ResearchTask` is persisted under
   `data/research-tasks/<YYYYMMDD>/` and each `EvidencePackage` is persisted
   under `data/evidence-packages/<YYYYMMDD>/`.
10. Verify the memo body follows `HISYS-TPL-RESEARCH-SEARCH-001` sections:
   research question, query set, accepted source records, skipped/rejected
   records, investigation findings, purpose guideline, research agent evidence,
   evidence trace, interpretation, agent limitations, and open questions.
11. For purpose-specific runs, use `--purpose auto` or an explicit purpose
   profile. Research idea discovery profiles require gap/novelty/evaluation
   framing and may dispatch `formalism_gap_analysis`; investment decision-support
   profiles require fundamentals, market trend, competitor, valuation, risk, and
   buy/hold/avoid/needs-more-evidence framing plus a not-financial-advice safety
   note and may dispatch `investment_decision_support`.
12. If no `--agent` is supplied, verify the selected guideline produces the
   default controlled evidence-agent plan: research idea discovery ->
   `formalism_gap_analysis`, investment decision support ->
   `investment_decision_support`, and general investigation -> no extra agent.
   Explicit `--agent` values remain authoritative for manual plans.

## Pass Criteria

- Registered fixture source produces a RawObservation.
- Unregistered source is skipped and audited.
- Adapter failure is bounded and does not stop other sources.
- No live network or credential access is required.
- `investigate-memo` writes `data/investigation-memos/<YYYYMMDD>/*.json/.md`
  and `reports/run-summaries/<YYYYMMDD>/investigation-memo-report.{json,md}`.
- Multi-agent fixture runs also write `data/research-tasks/<YYYYMMDD>/*.json`
  and `data/evidence-packages/<YYYYMMDD>/*.json` before memo synthesis.
- Formalism domain fixture runs include evidence claims for Dynamic Structure
  DEVS, graph rewriting, agent-based modeling, assessment criteria, selection
  heuristics, expressiveness/simulation/verification tradeoffs, local interaction
  rules, emergent global structure, structural change as first-class state, and
  follow-up questions about simulation semantics/proof/topology change.
- Purpose-specific guideline runs persist `guideline_profile_id` in the report
  and memo tags/body; auto-selected investment decision-support runs include
  the not-financial-advice safety note and bounded evidence requirements.
- `formalism_gap_analysis` runs include explicit gap statements, hybrid novelty
  candidates, evaluation scenarios, and research questions with evidence refs.
- `investment_decision_support` runs include fundamentals, market/competitor,
  valuation/risk, and needs-more-evidence decision-frame claims with evidence refs.
- Auto-planned purpose runs create research task/evidence package refs without
  requiring explicit `--agent` when the purpose is research idea discovery or
  investment decision support.
- Investigation memos reference `source_refs`, `observation_refs`, `signal_refs`,
  `research_task_refs`, and `evidence_package_refs` but do not copy raw payload
  content into the memo body.
