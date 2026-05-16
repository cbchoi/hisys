# Hisys Revision Plan v004: Codebase Analysis Harness and Hermes Application

> **For Hermes:** Use `subagent-driven-development` only after this plan is converted into a scoped implementation packet. Subagents may collect read-only evidence and produce verification handles; they must not make final Hisys decisions, mutate repositories, publish, push, or weaken `needs_more_evidence` gates.

**Created:** 2026-05-16 20:02 +0900  
**Status:** planning  
**Scope:** Hisys codebase-analysis improvements plus Hermes harness lessons  
**Primary sources:**
- Personal Stone: `/home/cbchoi/me/10 Mine/Links/202605161915-claude-code-large-codebases.md`
- Personal Stone: `/home/cbchoi/me/10 Mine/Links/202605161915-deerflow-2-superagent-harness.md`
- Existing Hisys use case: `docs/use-cases/codebase-analysis-design-candidates.md`
- Existing Hisys domain adapter design: `docs/use-cases/hermes-hisys-domain-tool.md`
- Current code seams: `src/hisys/domain/use_cases.py`, `src/hisys/domain/specs.py`, `src/hisys/domain/domain_adapters.py`, `src/hisys/operations/agent_workflow.py`

## 1. Goal

Build a governed codebase-analysis harness for Hisys that converts local repository inspection into durable, reviewable JSON/Markdown evidence artifacts. The harness should help Hermes and human reviewers answer code-analysis questions with traceable evidence instead of ad hoc LLM file browsing.

The target operating model is:

```text
spec-first packet
  -> scope-first codebase inventory
  -> deterministic source/symbol/test/doc evidence
  -> bounded advisory synthesis
  -> DARS/Chief Editor review gate
  -> finish packet for human review
```

This plan absorbs useful lessons from Claude Code large-codebase practices and DeerFlow 2.0 without copying their runtime model into Hisys.

## 2. Non-goals and safety boundaries

Do not implement or authorize the following by default:

- live external repository cloning or fetching;
- sending proprietary source code to external LLMs;
- repository mutation, branch creation, commit, push, PR creation, package publication, deployment, or live connector execution;
- unrestricted shell execution from analyzed repositories;
- subagent final decisions;
- automatic lowering of `needs_more_evidence` or Chief Editor/DARS gates;
- long-term storage of raw codebase contents in personal vaults or Hermes memory.

Required boundary fields for every artifact in this plan:

```text
external_call_made=false
mutation_performed=false
publication_or_live_action_approved=false
credential_use_allowed=false
action_taken=none
```

## 3. Current-state observation

A local bounded inspection on 2026-05-16 found the current Hisys repository is already large enough to benefit from a structured code-analysis harness:

- file count excluding common transient/dependency/build paths: `326`
- Python files: `250`
- approximate Python lines: `48,577`
- Markdown docs: `45` files, approximately `15,939` lines
- existing codebase domain seam:
  - `src/hisys/domain/specs.py` defines `codebase_spec()`;
  - `src/hisys/domain/use_cases.py` defines `CodeAnalysisUseCase` and `CodeInvestigationLayer`;
  - `docs/use-cases/codebase-analysis-design-candidates.md` already defines the future evidence package direction.

The gap is that current codebase analysis mostly records local targets and evidence references. It does not yet construct a deterministic source inventory, symbol index, scope map, validation plan, risk-boundary scan, or source-inspection decision artifact.

## 4. Design principles imported from the source material

### 4.1 Scope-first analysis

Large-codebase agent work should start from a bounded scope, not from a blind full-repository read. Hisys should classify code-analysis requests into scopes such as:

- `domain-adapter`
- `source-connector`
- `runtime-boundary`
- `schema`
- `cli`
- `tests`
- `docs-traceability`
- `hermes-tool-deployment`
- `release-readiness`
- `full-repo-overview`

Each scope should define entry files, related tests, related docs, allowed commands, excluded paths, and review gates.

### 4.2 Thin root map, detailed scope maps

The Claude Code lesson about thin hierarchical `CLAUDE.md` files translates into Hisys as thin root code maps plus detailed scope maps. Do not put all repository knowledge into one prompt or one document. Persist maps as runtime-boundary artifacts.

Recommended artifact convention:

```text
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/codebase-root-map.json
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/codebase-root-map.md
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/scope-<scope-id>-map.json
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/scope-<scope-id>-map.md
```

### 4.3 Deterministic local code intelligence before LSP/MCP

Before adding LSP, MCP, or external tools, Hisys should implement deterministic local analysis:

- file inventory;
- suffix/language counts;
- Python AST symbol index;
- import/dependency edges;
- CLI command discovery;
- test function discovery;
- doc/traceability anchor discovery;
- runtime-boundary field scanner.

LSP/MCP integration is a later optional increment because it adds tool availability, permission, runtime, and reproducibility concerns.

### 4.4 Artifact offloading for long-running analysis

DeerFlow's context-engineering lesson maps well to Hisys: intermediate results should be written to files, not kept in one agent context. Codebase analysis should produce composable artifacts that later review steps consume by reference.

### 4.5 Subagents are evidence collectors, not decision makers

Subagents may inspect bounded paths and return artifacts or verification handles. The parent agent or Hisys review layer must preserve final judgment as advisory and human-gated.

## 5. Implementation roadmap

### Increment 1: Codebase inventory packet

**Objective:** Add deterministic local repository inventory artifacts.

**Files:**
- Create: `src/hisys/operations/codebase_analysis.py`
- Create: `tests/unit/test_codebase_analysis_inventory.py`
- Modify: `src/hisys/cli/main.py`
- Modify: `docs/traceability/README.md`
- Create: `docs/public/codebase-analysis.md`

**CLI:**

```bash
PYTHONPATH=src python3 -m hisys.cli.main build-codebase-inventory \
  --repo /path/to/repo \
  --instance /tmp/hisys-codebase-analysis \
  --date <YYYYMMDD> \
  --request-id REQ-CODEBASE-001 \
  --scope src/hisys/domain \
  --format json
```

**Artifact refs:**

```text
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/inventory.json
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/inventory.md
```

**Required fields:**

- `schema_id=hisys.codebase.inventory`
- `repo_root`
- `git_branch`
- `git_commit`
- `git_status_short`
- `analysis_scope`
- `excluded_paths`
- `file_count`
- `suffix_counts`
- `line_counts`
- `source_file_count`
- `test_file_count`
- `doc_file_count`
- `required_path_existence`
- safety boundary fields.

**Tests:**

- fixture repo excludes `.git`, `.venv`, `__pycache__`, build/cache paths;
- inventory records required path existence;
- writer creates JSON and Markdown;
- CLI roundtrip returns safe refs;
- no-live-action flags remain false.

**Validation:**

```bash
python3 -m pytest tests/unit/test_codebase_analysis_inventory.py -q
python3 scripts/scan_secrets.py --json src/hisys/operations/codebase_analysis.py tests/unit/test_codebase_analysis_inventory.py docs/public/codebase-analysis.md
python3 scripts/validate_traceability.py
git diff --check
```

### Increment 2: Python AST symbol index packet

**Objective:** Add local symbol-level code intelligence before any LSP dependency.

**Files:**
- Modify: `src/hisys/operations/codebase_analysis.py`
- Create: `tests/unit/test_codebase_symbol_index.py`
- Modify: `src/hisys/cli/main.py`
- Modify: `docs/public/codebase-analysis.md`

**CLI:**

```bash
PYTHONPATH=src python3 -m hisys.cli.main build-code-symbol-index \
  --repo /path/to/repo \
  --instance /tmp/hisys-codebase-analysis \
  --date <YYYYMMDD> \
  --request-id REQ-CODEBASE-001 \
  --include src/hisys/domain \
  --include src/hisys/operations \
  --format json
```

**Artifact refs:**

```text
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/symbol-index.json
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/symbol-index.md
```

**Required fields:**

- modules;
- classes;
- functions;
- imports;
- Pydantic/BaseModel-like classes;
- argparse parser builders and command handlers when detectable;
- pytest test functions;
- file path and line range for each symbol;
- parse errors separated from tool failures.

**Tests:**

- fixture Python files with classes/functions/imports;
- syntax-error file records parse error without failing whole run;
- CLI symbols include file and line;
- output is deterministic and sorted.

### Increment 3: Scope map and validation plan

**Objective:** Convert inventory and symbol index into a scope-specific code map and validation plan.

**Files:**
- Modify: `src/hisys/operations/codebase_analysis.py`
- Create: `tests/unit/test_codebase_scope_map.py`
- Modify: `docs/public/codebase-analysis.md`

**CLI:**

```bash
PYTHONPATH=src python3 -m hisys.cli.main build-codebase-map \
  --repo /path/to/repo \
  --instance /tmp/hisys-codebase-analysis \
  --date <YYYYMMDD> \
  --request-id REQ-CODEBASE-001 \
  --scope domain-adapter \
  --inventory-ref runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/inventory.json \
  --symbol-index-ref runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/symbol-index.json
```

**Scope map fields:**

- `scope_id`
- `entry_files`
- `related_source_files`
- `related_tests`
- `related_docs`
- `traceability_refs`
- `runtime_boundary_refs`
- `focused_validation_commands`
- `full_validation_commands`
- `known_risks`
- `needs_more_evidence_conditions`.

**Validation plan examples:**

- domain adapter: `tests/unit/test_domain_adapter_registry.py`, `tests/unit/test_structured_domain_adapter.py`, `tests/unit/test_domain_runtime_artifacts.py`
- spec-first workflow: `tests/unit/test_agent_workflow_packets.py`
- source connectors: connector-specific tests plus secret scan and traceability validation.

### Increment 4: Risk-boundary scanner

**Objective:** Detect code paths likely to cross sensitive boundaries.

**Detected categories:**

- network/browser/API external call;
- filesystem mutation;
- Git mutation;
- credential/environment access;
- publication/upload/post/send action;
- subprocess/shell execution;
- vault write;
- runtime-boundary artifact write.

**Important distinction:** A scanner finding is not a vulnerability verdict. It is an evidence item for review. The scanner must distinguish allowed local artifact writes from live external effects.

**Artifacts:**

```text
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/risk-boundary-scan.json
runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/risk-boundary-scan.md
```

**Tests:**

- fixture files with `requests.get`, `subprocess.run`, `Path.write_text`, `git push` strings, and safe local artifact writes;
- scanner classifies findings conservatively;
- no finding authorizes action.

### Increment 5: Codebase source-inspection decision packet

**Objective:** Review codebase-analysis artifacts and decide whether the evidence is complete enough for human review.

**CLI:**

```bash
PYTHONPATH=src python3 -m hisys.cli.main review-codebase-analysis \
  --instance /tmp/hisys-codebase-analysis \
  --date <YYYYMMDD> \
  --request-id REQ-CODEBASE-001 \
  --inventory-ref .../inventory.json \
  --symbol-index-ref .../symbol-index.json \
  --scope-map-ref .../scope-domain-adapter-map.json \
  --risk-scan-ref .../risk-boundary-scan.json \
  --format json
```

**Decision values:**

```text
complete_for_human_review
blocked_needs_more_evidence
```

Do not add `approved`, `safe_to_deploy`, or `ready_for_live_action` decision values.

### Increment 6: Bridge into `investigate-domain --domain codebase`

**Objective:** Make the structured domain adapter consume local codebase-analysis artifacts rather than merely preserving broad evidence refs.

**Implementation direction:**

- Keep `DomainAdapterRegistry` as the dispatch seam.
- Extend `CodeInvestigationLayer` to optionally read explicit inventory/symbol/scope/risk refs from request sources or config snapshot refs.
- Preserve formal `needs_more_evidence` when required artifacts are missing.
- Report advisory synthesis separately from formal Hisys result.

### Increment 7: Advanced codebase-analysis features after the foundation

These should be implemented only after Increments 1-6 are green and documented.

#### 7.1 Change-impact analyzer

Input: `git diff --name-only`, inventory, symbol index.  
Output: likely impacted modules, tests, docs, traceability rows, and risk-boundary categories.

Use case:

```bash
hisys analyze-code-change-impact --repo /path/to/repo --since HEAD~1
```

This helps Hermes choose focused tests and documentation updates before editing.

#### 7.2 Traceability coverage checker

Input: source paths, tests, docs, `docs/traceability/README.md`.  
Output: missing or stale source-test-doc-trace links.

Checks:

- new CLI command has tests;
- new schema has docs and traceability row;
- new runtime-boundary artifact has safety fields;
- docs mention no-live-action boundary when applicable.

#### 7.3 Runtime-boundary consistency checker

Scan artifact builders and persisted JSON examples for required boundary fields:

```text
external_call_made
mutation_performed
publication_or_live_action_approved
action_taken
human_approval_required_for_consequential_use
```

This is especially useful after adding new source connectors or decision packets.

#### 7.4 Code-analysis pass-contract loop

When `review-codebase-analysis` repeatedly returns `blocked_needs_more_evidence`, create a pass-contract proposal instead of weakening the gate.

Flow:

```text
audit code-analysis blockers
  -> propose code-analysis pass contract
  -> convert proposal to tests/fixtures
  -> evaluate proposal
  -> DARS/Chief Editor/human review
  -> promote only after approval
```

#### 7.5 Architecture candidate generator

Use source evidence to propose architecture/refactor candidates, but keep them advisory.

Candidate fields:

- candidate id;
- affected modules;
- source evidence refs;
- expected benefit;
- coupling/risk score;
- validation plan;
- implementation increment size;
- human gate state.

#### 7.6 Open-source comparison adapter

Compare a local codebase with approved OSS references only after source-governance approval.

Rules:

- preserve license metadata;
- avoid code copying;
- store only architecture claims and source refs unless the OSS source is explicitly approved for deeper inspection;
- label conclusions as comparative advisory.

#### 7.7 Optional local LSP adapter

Add LSP only after AST indexing is insufficient.

Requirements:

- local-only server;
- explicit language server prerequisite check;
- no external telemetry unless approved;
- deterministic fallback to AST index;
- artifact refs for LSP query inputs/outputs;
- no mutation commands such as rename/apply-edit in the first version.

#### 7.8 Subagent evidence collector protocol

Define a standard packet for Hermes subagents that inspect bounded scopes.

Subagent input:

- task;
- repo path;
- include/exclude paths;
- allowed read-only tools;
- expected artifact schema;
- what not to do.

Subagent output:

- summary;
- artifact paths;
- source refs;
- test/validation suggestions;
- blockers;
- `external_call_made=false`, `mutation_performed=false`.

The parent must verify returned artifact paths before reporting success.

#### 7.9 Codebase-analysis regression benchmark

Create fixture repositories that represent common codebase shapes:

- small Python package;
- CLI-heavy package;
- docs-heavy package;
- syntax-error package;
- generated-file-heavy package;
- multi-language package;
- runtime-boundary artifact package.

Use these fixtures to prevent analyzer regressions.

#### 7.10 Codebase map freshness and drift review

Add a periodic or manual review that detects stale scope maps after large changes.

Signals:

- inventory file hash changed;
- new CLI commands without scope-map entries;
- new top-level packages;
- traceability row changed without code map update.

## 6. Hermes application analysis

The same lessons should be applied to Hermes, but Hermes should not import Hisys raw code evidence into global memory or treat Hisys artifacts as automatic approval.

### 6.1 Hermes skill loading and context hygiene

Hermes already has skills. The improvement is to make skill loading more scope-aware and evidence-backed:

- root instructions should stay thin;
- task-specific skills should carry exact triggers, failure modes, verification commands, and safety boundaries;
- long procedural content should live in linked references, not always-loaded skill text;
- if a skill becomes stale after a model/runtime change, patch it immediately and record the verification.

Concrete Hermes skill updates to consider:

- `software-development/hisys-cli-tool`: add a codebase-analysis subsection after the new CLI exists;
- `autonomous-ai-agents/hermes-agent`: add a large-codebase harness note emphasizing scope-first context and artifact verification;
- `software-development/subagent-driven-development`: add a read-only evidence collector contract for codebase analysis;
- `software-development/systematic-debugging`: add codebase-map and symbol-index checks before broad file reads.

### 6.2 Hermes planning discipline

For large codebase work, Hermes should create or request a spec-first packet before implementation:

```text
objective
scope
non-goals
allowed actions
evidence contract
expected artifacts
focused validation commands
full validation commands
human approval boundary
```

The existing Hisys `build-spec-first-packet` and `build-finish-packet` commands can record this boundary for Hisys work. For non-Hisys repos, Hermes can use a lighter Markdown plan but should keep the same fields.

### 6.3 Hermes subagent use

Hermes subagents are useful for parallel codebase inspection, but only with bounded contracts:

- one subagent per scope;
- read-only by default;
- return file paths and artifact handles;
- do not rely on self-reported success;
- parent verifies files/tests/status;
- no subagent final decision for Hisys governance.

### 6.4 Hermes memory and vault boundary

Do not store raw codebase evidence in Hermes memory or the personal vault. Durable cross-session memory should only hold compact conventions, tool quirks, and stable user preferences. Codebase evidence belongs in:

```text
Hisys runtime-boundary artifacts
Hisys evidence store
repository docs when explicitly promoted
```

The personal vault may receive curated Stone/Gem/Jewel summaries only after explicit capture or synthesis.

### 6.5 Hermes verification habit

For any large-codebase answer, Hermes should report:

- what scope was inspected;
- which artifact refs or files support the answer;
- which tests/checks ran;
- which evidence is missing;
- whether the conclusion is formal Hisys result or Hermes advisory synthesis;
- no-live-action/no-mutation boundary.

### 6.6 Hermes periodic harness review

Borrow the 3-6 month review rule from the Claude Code article:

- remove stale instructions that were added for older model/tool limitations;
- check whether skills are too long or too broad;
- verify tool commands still work;
- review subagent contracts and verification handles;
- check whether new Hisys codebase-analysis artifacts should replace manual search patterns.

## 7. Recommended first execution packet

The first implementation packet should be narrow:

```text
Packet: SPEC-HISYS-CODEBASE-ANALYSIS-001
Objective: implement codebase inventory packet only
Scope: Increment 1
Non-goals: symbol index, LSP, subagent protocol, DARS review, external repo clone
Allowed actions: local repo reads, tests, docs, traceability edit, local commit after green validation
Evidence contract: JSON+Markdown inventory artifact; focused tests; secret scan; traceability validation; git diff check
Human boundary: no live action, no publication, no push unless explicitly requested
```

Recommended focused tests after Increment 1:

```bash
python3 -m pytest tests/unit/test_codebase_analysis_inventory.py -q
python3 scripts/scan_secrets.py --json src/hisys/operations/codebase_analysis.py tests/unit/test_codebase_analysis_inventory.py docs/public/codebase-analysis.md docs/traceability/README.md
git diff --check
```

Run the full test suite before committing a production-facing change:

```bash
python3 -m pytest -q
```

## 8. Acceptance checklist for this plan

- [ ] The plan is saved as `revision_plan_v004.md` in the Hisys repository.
- [ ] The plan includes advanced post-foundation codebase-analysis features.
- [ ] The plan includes Hermes applicability analysis.
- [ ] The plan preserves Hisys governance boundaries.
- [ ] The plan does not authorize live external actions, mutation, publication, or gate weakening.
