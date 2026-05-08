# Investigator Multi-Agent Research Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Turn the HISYS Investigator into a controlled research orchestrator that can dispatch multiple research agents, collect schema-validated evidence packages, and build template-based memos without allowing uncontrolled browser, network, or external-agent side effects.

**Architecture:** The Investigator remains the orchestrator and final memo owner. Research agents only produce `EvidencePackage` artifacts; `EvidenceMerger` validates and combines those packages; `InvestigationMemoBuilder` writes template sections from validated evidence. Selenium and delegated LLM/Hermes subagents are adapters behind the same `ResearchAgent` interface and must pass read-only safety gates before they are enabled.

**Tech Stack:** Python 3.11, Pydantic v2 schemas, pytest, runtime-local JSON/Markdown artifacts, optional Selenium/browser adapter in a later gated increment.

**Traceability:** HISYS-T-027, HISYS-T-028, HISYS-INST-INV-001, HISYS-FR-INV-001..006, HISYS-FR-MEM-001..005, HISYS-D-015, HISYS-DATA-002, HISYS-TPL-RESEARCH-SEARCH-001.

---

## Design Principles

1. **Investigator orchestrates; agents collect evidence.** Subagents must not write final memos directly.
2. **All agents return `EvidencePackage`.** Free-form prose is not accepted as a runtime artifact.
3. **Browser/Selenium is read-only first.** No login, POST, form submission, uploads, comments, purchases, or credential use.
4. **MemoBuilder owns the template.** Template sections are filled from validated claims, evidence, limitations, and open questions.
5. **No live external action until harness passes.** Fixture agents come first; Selenium and delegated agents are planned but disabled until dedicated harnesses pass.
6. **Evidence is traceable.** Every claim must cite evidence refs; every evidence item must identify source URL/path/ref, retrieval timestamp or fixture timestamp, content hash when available, and agent/task IDs.

---

## Target Runtime Shape

```text
hisys investigate-memo
  -> InvestigationPlanner
  -> ResearchTask[]
  -> ResearchAgentFactory
       -> FixtureResearchAgent
       -> FixtureContradictionAgent
       -> LocalPDFResearchAgent      # planned after fixture multi-agent
       -> SeleniumReadOnlyAgent      # HISYS-T-028, disabled until harness passes
       -> DelegatedLLMResearchAgent  # later, disabled by default
  -> EvidencePackage[]
  -> EvidenceGate
  -> EvidenceMerger / ConflictDetector
  -> InvestigationMemoBuilder
  -> ZettelMemo JSON/Markdown
  -> investigation-memo-report JSON/Markdown
```

Runtime artifact paths:

```text
data/research-tasks/<YYYYMMDD>/*.json
data/evidence-packages/<YYYYMMDD>/*.json
data/investigation-memos/<YYYYMMDD>/*.json|*.md
reports/run-summaries/<YYYYMMDD>/investigation-memo-report.json|md
```

---

## Core Schemas to Add

Suggested file:

```text
src/hisys/investigator/research.py
```

Minimum schema set:

```python
from typing import Literal
from pydantic import BaseModel, Field

AgentType = Literal[
    "fixture",
    "fixture_contradiction",
    "local_pdf",
    "selenium_read_only",
    "delegated_llm",
]

class ResearchTask(BaseModel):
    task_id: str
    agent_type: AgentType
    question: str
    query: str | None = None
    allowed_source_ids: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    disallowed_actions: list[str] = Field(default_factory=lambda: [
        "login", "post", "form_submit", "upload", "purchase", "credential_use"
    ])
    expected_output_schema: str = "EvidencePackage"

class EvidenceItem(BaseModel):
    evidence_id: str
    task_id: str
    agent_id: str
    source_id: str | None = None
    url: str | None = None
    path: str | None = None
    title: str
    quoted_text: str | None = None
    excerpt_ref: str | None = None
    retrieved_at: str
    content_hash: str | None = None

class ClaimRecord(BaseModel):
    claim_id: str
    text: str
    confidence: float
    evidence_refs: list[str]
    limitations: list[str] = Field(default_factory=list)

class EvidencePackage(BaseModel):
    package_id: str
    task_id: str
    agent_id: str
    agent_type: AgentType
    claims: list[ClaimRecord]
    evidence: list[EvidenceItem]
    limitations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    external_side_effects: bool = False
    actions_taken: list[str] = Field(default_factory=list)
```

---

## Task Roadmap

### Task 1: Add ResearchTask and EvidencePackage schemas

**Objective:** Define the common contract every Investigator subagent must use.

**Files:**
- Create: `src/hisys/investigator/research.py`
- Modify: `src/hisys/investigator/__init__.py`
- Test: `tests/unit/test_investigator_research_agents.py`

**Step 1: Write failing tests**

Test requirements:
- `ResearchTask` defaults include disallowed actions.
- `EvidencePackage.external_side_effects` defaults to `False`.
- Every `ClaimRecord` can cite evidence refs.
- Unknown agent type is rejected by Pydantic.

Run:

```bash
python3 -m pytest tests/unit/test_investigator_research_agents.py -q
```

Expected: FAIL because schemas do not exist.

**Step 2: Implement minimal schemas**

Use the schema definitions above. Keep them deterministic and runtime-local.

**Step 3: Verify**

```bash
python3 -m pytest tests/unit/test_investigator_research_agents.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/hisys/investigator/research.py src/hisys/investigator/__init__.py tests/unit/test_investigator_research_agents.py
git commit -m "feat: add investigator research evidence schemas"
```

---

### Task 2: Add fixture ResearchAgent interface and factory

**Objective:** Introduce deterministic research agents before live browser/network integrations.

**Files:**
- Create: `src/hisys/investigator/agents.py`
- Modify: `src/hisys/investigator/__init__.py`
- Test: `tests/unit/test_investigator_research_agents.py`

**Implementation shape:**

```python
from typing import Protocol

class ResearchAgent(Protocol):
    agent_id: str
    agent_type: str
    def run(self, task: ResearchTask) -> EvidencePackage: ...

class FixtureResearchAgent:
    agent_id = "fixture-research-agent"
    agent_type = "fixture"
    def run(self, task: ResearchTask) -> EvidencePackage:
        ...

class FixtureContradictionAgent:
    agent_id = "fixture-contradiction-agent"
    agent_type = "fixture_contradiction"
    def run(self, task: ResearchTask) -> EvidencePackage:
        ...

def create_research_agent(agent_type: str) -> ResearchAgent:
    ...
```

**Step 1: RED tests**

Tests:
- Factory returns fixture agents.
- Unknown agent type raises clear `ValueError`.
- Fixture agent returns one claim and one evidence item.
- Contradiction fixture returns an open question or limitation.

**Step 2: GREEN implementation**

Keep outputs deterministic. Use fixture URLs/paths only.

**Step 3: Verify**

```bash
python3 -m pytest tests/unit/test_investigator_research_agents.py -q
```

**Step 4: Commit**

```bash
git add src/hisys/investigator/agents.py src/hisys/investigator/__init__.py tests/unit/test_investigator_research_agents.py
git commit -m "feat: add fixture investigator research agents"
```

---

### Task 3: Add EvidenceGate and EvidenceMerger

**Objective:** Ensure subagent output is valid before memo synthesis.

**Files:**
- Create: `src/hisys/investigator/evidence.py`
- Test: `tests/unit/test_investigator_evidence_gate.py`

**Gate requirements:**
- Reject packages where `external_side_effects=True`.
- Reject claims with no `evidence_refs`.
- Reject `evidence_refs` that do not exist in the package.
- Merge claims/evidence across packages.
- Surface `open_questions` and `limitations`.

**Step 1: RED tests**

Run:

```bash
python3 -m pytest tests/unit/test_investigator_evidence_gate.py -q
```

Expected: FAIL.

**Step 2: Implement gate/merger**

Suggested functions:

```python
def validate_evidence_package(package: EvidencePackage) -> None: ...
def merge_evidence_packages(packages: list[EvidencePackage]) -> MergedEvidence: ...
```

**Step 3: Verify and commit**

```bash
python3 -m pytest tests/unit/test_investigator_evidence_gate.py -q
git add src/hisys/investigator/evidence.py tests/unit/test_investigator_evidence_gate.py
git commit -m "feat: add investigator evidence gate"
```

---

### Task 4: Add multi-agent fixture orchestration to `investigate-memo`

**Objective:** Let `investigate-memo` dispatch multiple fixture agents and build one memo from merged evidence.

**Files:**
- Modify: `src/hisys/cli/main.py`
- Modify/Create: `src/hisys/investigator/orchestration.py`
- Test: `tests/unit/test_cli_runtime.py`

**CLI target:**

```bash
PYTHONPATH=src python3 -m hisys.cli.main investigate-memo \
  --instance /tmp/hisys-investigation \
  --config-from examples/instance \
  --date 20260508 \
  --topic "hardware overheating risk" \
  --goal "Assess whether evidence requires operations attention." \
  --perspective PERSP-OPS-001 \
  --agent fixture \
  --agent fixture_contradiction
```

**Expected report additions:**

```json
{
  "research_task_refs": ["TASK-..."],
  "evidence_package_refs": ["EPKG-..."],
  "agent_ids": ["fixture-research-agent", "fixture-contradiction-agent"],
  "open_questions": [...],
  "limitations": [...]
}
```

**Step 1: RED CLI test**

Test that two agents create two evidence packages and one memo containing:
- accepted evidence section,
- limitations/open questions section,
- evidence trace section,
- no raw payload copy.

**Step 2: Implement orchestration**

Persist:

```text
data/research-tasks/<date>/*.json
data/evidence-packages/<date>/*.json
```

**Step 3: Verify and commit**

```bash
python3 -m pytest tests/unit/test_cli_runtime.py::test_investigate_memo_dispatches_multiple_fixture_agents -q
python3 -m pytest
python3 scripts/validate_traceability.py
git add src/hisys/cli/main.py src/hisys/investigator tests/unit/test_cli_runtime.py
git commit -m "feat: orchestrate fixture research agents"
```

---

### Task 5: Document HISYS-T-027 multi-agent Investigator foundation

**Objective:** Update docs and harness guidelines after fixture multi-agent orchestration passes.

**Files:**
- Modify: `README.md`
- Modify: `docs/traceability/README.md`
- Modify: `examples/instance/harness/guidelines/investigator.md`

**Required docs:**
- Explain `--agent fixture --agent fixture_contradiction`.
- Document evidence package artifact paths.
- State that browser/Selenium/delegated agents remain disabled until separate harnesses pass.
- Add traceability row for `HISYS-T-027`.

**Verify:**

```bash
python3 scripts/validate_traceability.py
```

**Commit:**

```bash
git add README.md docs/traceability/README.md examples/instance/harness/guidelines/investigator.md
git commit -m "docs: document investigator multi-agent foundation"
```

---

### Task 6: Add SeleniumReadOnlyAgent design harness only

**Objective:** Add a disabled-by-default Selenium read-only adapter contract without live browsing in CI.

**Files:**
- Create: `src/hisys/investigator/browser.py`
- Create: `tests/unit/test_investigator_browser_agent.py`
- Create/Modify: `examples/instance/config/investigator-agents.yaml`

**Safety contract:**

```yaml
selenium_read_only:
  enabled: false
  read_only: true
  max_pages: 5
  max_depth: 1
  allowed_domains: []
  forbidden_actions:
    - login
    - post
    - form_submit
    - upload
    - purchase
    - credential_use
```

**Tests:**
- Agent refuses to run when disabled.
- Agent refuses non-allowed domain.
- Agent refuses any task with forbidden action.
- Agent output schema is still `EvidencePackage`.
- CI test uses static local HTML fixture, not live web.

**Commit:**

```bash
git add src/hisys/investigator/browser.py tests/unit/test_investigator_browser_agent.py examples/instance/config/investigator-agents.yaml
git commit -m "feat: add disabled selenium read-only agent harness"
```

---

### Task 7: Enable local static HTML Selenium/browser fixture

**Objective:** Prove Selenium/browser extraction works on local static HTML before any live domain is allowed.

**Files:**
- Create: `examples/fixtures/browser/static-overheating-guide.html`
- Modify: `src/hisys/investigator/browser.py`
- Test: `tests/unit/test_investigator_browser_agent.py`

**Expected behavior:**
- Browser agent reads local fixture HTML.
- Extracts title, selected text, URL/path, and content hash.
- Returns `EvidencePackage` with `external_side_effects=false`.
- No network call is made.

**Commit:**

```bash
git add examples/fixtures/browser/static-overheating-guide.html src/hisys/investigator/browser.py tests/unit/test_investigator_browser_agent.py
git commit -m "feat: validate browser evidence extraction on local fixture"
```

---

### Task 8: Add delegated LLM/Hermes subagent adapter contract disabled by default

**Objective:** Prepare for external research subagents while preserving schema and safety boundaries.

**Files:**
- Create: `src/hisys/investigator/delegated.py`
- Create: `tests/unit/test_investigator_delegated_agent.py`
- Modify: `examples/instance/config/investigator-agents.yaml`

**Contract:**
- Disabled by default.
- Must return JSON matching `EvidencePackage`.
- Any free-form answer is rejected.
- Tool boundary/action log must be recorded.
- No direct final memo writing.

**Commit:**

```bash
git add src/hisys/investigator/delegated.py tests/unit/test_investigator_delegated_agent.py examples/instance/config/investigator-agents.yaml
git commit -m "feat: add disabled delegated research agent contract"
```

---

## Acceptance Criteria

HISYS-T-027 is complete when:

```text
investigate-memo --agent fixture --agent fixture_contradiction
```

produces:

```text
1+ ResearchTask JSON artifacts
2+ EvidencePackage JSON artifacts
1 InvestigationMemo JSON/Markdown artifact
1 investigation-memo-report JSON/Markdown artifact
```

and full validation passes:

```bash
python3 -m pytest
python3 scripts/validate_traceability.py
```

HISYS-T-028 is complete when:

```text
SeleniumReadOnlyAgent is disabled by default,
passes local static HTML fixture tests,
records no external side effects,
and refuses live/non-allowed domains unless explicitly configured.
```

---

## Notes for Implementers

- Do not let subagents write final memo bodies.
- Do not allow Selenium or delegated LLM agents to run live by default.
- Do not copy raw payload content into memo bodies; use evidence refs, excerpt refs, and hashes.
- Keep all outputs runtime-local until Chief Editor/approval/live-connector harnesses exist.
- Commit each task separately.
