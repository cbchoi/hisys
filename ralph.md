# Hisys Domain Adapter Ralph Loop Control Plan

> **For Ralph/Hermes:** Execute this file as the active Hisys Ralph-loop control document. Read this file before every Ralph loop. Each run repeats **Prepare -> Do -> Reflection -> Continue/Stop Decision** under the controlled-document, safety, runtime, quality, and stop rules below. Do not substitute an ad-hoc autonomous loop for this file.

## 0. Control Metadata

| Field | Value |
|---|---|
| Plan ID | `RALPH-HISYS-DOMAIN-ADAPTER` |
| Scope | Hisys domain-adapter registration, hardening, migration preparation, and requirements-analysis example work |
| Owner | Choi Changbeom / SysAI Lab |
| Default working directory | `/home/cbchoi/workspaces/sysailab/develop/repos/hisys` |
| Target branch | `feat/domain-adaptive-requirements-analysis` |
| Original baseline commit | `04d6b01 test: propagate src path to subprocess CLI tests` |
| Current update baseline | `b6ac4ed` |
| Execution mode | `on-demand Discord Ralph loop unless explicitly scheduled` |
| Default runtime limit | `5 hours` |
| User-specified runtime limit | `<none unless stated in the invoking message>` |
| External side effects | `disabled; security/system-risk actions require user-executed commands` |
| Last updated | `2026-05-14` |

## 0.1 Purpose and Existing Baseline

This Ralph loop advances the Hisys domain-refactoring line from the pre-Ralph hardening state to governed example-domain registration and migration.

Current baseline before this loop:

```text
branch: feat/domain-adaptive-requirements-analysis
baseline HEAD: 04d6b01 test: propagate src path to subprocess CLI tests
pre-Ralph gate: 528 passed, traceability OK, secret scan hit_count=0, git diff --check OK
```

The first executable milestone is Increment 5 from the master plan: register `research_spec` and `codebase_spec` as example structured domain specs while preserving the legacy research-gap adapter path.

## 1. Success Criteria

The Hisys Ralph loop is successful when all applicable criteria are met:

- [ ] Prepare confirms task consistency against SRS, SDD, IDD, STD, previous/current `ralph.md`, and the current codebase.
- [ ] Missing or inconsistent tasks are recorded before implementation proceeds.
- [ ] Each behavior change has an observed RED test before production implementation.
- [ ] Generated code is precise, clean, minimally scoped, traceable, and testable.
- [ ] Non-obvious code progression logic is documented with useful comments.
- [ ] Focused validation passes for each task.
- [ ] Milestone/global validation passes before milestone completion.
- [ ] Reflection updates this `ralph.md` with quality-gate result, potential issues, next-loop implications, and success-likelihood estimate.
- [ ] Ralph loop continuation success likelihood remains at least 75%; otherwise the loop stops.
- [ ] Each coherent task increment is committed locally when safe and authorized.
- [ ] Remote push is considered only at milestone completion and remains a user-executed command.
- [ ] The loop stops when the configured runtime limit is reached.

## 2. Non-Delegable Safety Boundary

### 2.1 User-Executed-Command Rule

Ralph/Hermes shall **not directly execute** commands or operations that can create security, integrity, availability, or user-data risk. When such an action is needed, Ralph/Hermes shall stop and provide a precise command block and rationale for the **user to execute manually**.

This rule applies even if local tool permissions would technically allow execution.

### 2.2 Actions Ralph/Hermes Must Not Execute Directly

Ralph/Hermes must convert the following into user-run instructions instead of executing them:

- Delete user data or large directory trees.
- Rewrite Git history.
- Reset branches.
- Force checkout over local changes.
- Remove or recreate `.git` metadata.
- Push to remotes.
- Publish, deploy, release, upload, or send externally.
- Change credentials, tokens, keychains, SSH keys, auth files, or secret stores.
- Change system firewall, package trust, sudoers, kernel, service manager, cron daemon, or gateway service security posture.
- Run destructive shell commands such as recursive delete, disk format, permission-wide chmod/chown, history rewrite, or branch reset.
- Run schema/data migrations against non-fixture data.
- Execute live external actions, transactions, order placement, email sending, social posting, or irreversible API calls.
- Bypass access controls, paywalls, CAPTCHAs, robots restrictions, or browser protections.

### 2.3 Required User-Run Instruction Format

When a non-delegable action is required, report:

```text
Action requires user execution.
Reason: <why Ralph/Hermes must not execute it>
Risk: <security/data/system risk>
Recommended command for user to run manually:
  <exact command>
Expected safe result:
  <what the user should see>
After running it, reply with the output or confirmation so Ralph can continue.
```

## 3. Controlled Inputs and Traceability Anchors

Every milestone and every task shall cite the controlled document anchors below before implementation:

| Short name | Controlled document | Path |
|---|---|---|
| SRS | `HISYS-SRS-001` | `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/requirements-record.md` |
| SDD | `HISYS-SDD-001` | `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/software-design-description.md` |
| IDD | `HISYS-IDD-001` | `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/interface-design-description.md` |
| STD | `HISYS-STD-001` | `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/software-test-description.md` |
| TDD procedure | `test-driven-development` skill | `software-development/test-driven-development` |

### 3.1 Mandatory task-start checklist

Before creating or executing any task:

1. Read or search SRS, SDD, IDD, and STD for the task objective.
2. Record the relevant requirement/design/interface/test IDs in the task header.
3. Confirm the task is a single functional unit derived from SRS + SDD.
4. Confirm the test behavior is derived from STD and follows the TDD procedure.
5. If the needed requirement/design/interface/test anchor is absent:
   - perform a consistency check against existing SRS/SDD/IDD/STD constraints;
   - if consistent, update the controlled document(s) first, validate traceability, commit the document update, then resume the Ralph loop;
   - if inconsistent, stop the Ralph loop and report the inconsistency to the user.

### 3.2 Controlled-document amendment rule

A controlled-document update is allowed only when all are true:

- It strengthens or clarifies existing Hisys product goals.
- It preserves source reliability, provenance, auditability, human review, and no-live-action defaults.
- It does not authorize uncontrolled external calls, mutation, publication, credential use, order execution, or bypassing access controls.
- It can be mapped into at least one SRS requirement, one SDD design element, one IDD interface/record rule, and one STD test.

If any item fails, stop and ask the user.

## 4. Current Controlled-Document Alignment

The domain-adapter Ralph loop is now explicitly supported by the controlled documents:

| Controlled anchor | Summary |
|---|---|
| SRS `HISYS-FR-DOM-001..006` | DomainAdapterRegistry / StructuredDomainAdapter / DomainAdapterSpec / three-layer use cases / bridge contract / example specs / investment governance. |
| SDD `Domain Investigation Adapter Design` | Execution path from registry to structured adapter, three-layer use case, runtime writer, `DomainInvestigationResult`, and `HisysToolResult`. |
| IDD `HISYS-IF-017` and `5.7` | Domain investigation adapter contract, structured spec fields, runtime result fields, and safety validation rules. |
| STD `HISYS-T-025..028` | Spec registration/precedence, bridge, runtime artifact governance, and investment migration governance tests. |

## 5. Ralph Cycle Protocol

Each Ralph loop iteration repeats these stages:

```text
Prepare -> Do -> Reflection -> Continue/Stop Decision
```

The next Ralph loop starts again from Prepare and reuses the updated `ralph.md`.


## 5.1 Hermes Iteration and Context-Compaction Resilience

Ralph loops may span multiple Hermes or Claude Code iterations. A loop must be resumable from repository state, `ralph.md`, and committed/reflection checkpoints without relying on transient chat context.

### 5.1.1 Durable State Rule

At the start and end of every task, Ralph shall record enough durable state for the next Hermes iteration to resume safely:

```text
Resume checkpoint:
- Current HEAD: <git rev-parse --short HEAD>
- Working tree: <clean or exact file list>
- Last completed milestone/task: <ID/title>
- Current in-progress task: <ID/title or none>
- RED observed: <command + expected failure or n/a>
- GREEN observed: <command + pass result or n/a>
- Quality gate status: <commands + pass/fail>
- Next command to run: <single command or Prepare step>
- Stop condition: <none or exact condition>
```

The checkpoint belongs in the Reflection Log after each completed task, after every stop condition, and before any expected long-running or interruption-prone phase.

### 5.1.2 Iteration Budget Rule

Before starting a task, estimate whether the task can finish within the current Hermes/Claude iteration budget. If not, split the task or stop at a clean checkpoint. Do not start production changes that cannot likely reach a focused GREEN state in the current iteration.

Default per-iteration target:

```text
one RED/GREEN/reflection/commit unit per iteration
```

A single run may execute multiple tasks only when each task reaches a committed clean checkpoint before the next task begins.

### 5.1.3 Resume-First Rule

When a new Hermes iteration starts, Ralph shall not assume the previous message context is complete. It shall first reconstruct state from durable sources:

```bash
git status --short
git rev-parse --short HEAD
git log --oneline -12
```

Then read:

```text
ralph.md Reflection Log
current milestone/task section
modified tests/code from recent commits
SRS/SDD/IDD/STD anchors for the next task
```

Only after this reconstruction may Ralph continue the next task.

### 5.1.4 Interrupted-Run Handling

If Hermes, Claude Code, or the user interrupts a loop:

1. Inspect `git status --short`.
2. If the working tree is clean, resume from the latest committed Reflection Log and next task.
3. If the working tree has changes, classify them as:
   - complete and passing checkpoint;
   - partial but recoverable current task work;
   - unrelated or unsafe changes.
4. For partial current-task work, run the focused test for that task before editing further.
5. For unrelated or unsafe changes, stop and report the exact files; do not overwrite or mix them into a commit.

Never use `git reset`, `git checkout`, `git clean`, or history rewrite to recover without explicit user-executed approval under Section 2.

### 5.1.5 Claude/Ralph Invocation Contract

When delegating a Ralph loop to Claude Code or another implementation agent, the prompt shall require:

```text
- read ralph.md first;
- reconstruct state from git and Reflection Log;
- execute at most one coherent task before checkpoint unless explicitly safe;
- commit each completed increment locally;
- append Reflection Log before continuing;
- stop with a resume checkpoint if permissions, iteration budget, tests, or traceability fail;
- never rely on chat-only state for task selection or success claims.
```

This contract exists to overcome Hermes iteration limits and context compaction. The repository state and `ralph.md` are the source of truth.

## 6. Prepare Stage

### 6.1 Objective

Analyze task consistency and task sufficiency before code generation.

### 6.2 Required Inputs

Before selecting or executing a task, read or search:

- SRS document: `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/requirements-record.md`.
- SDD document: `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/software-design-description.md`.
- IDD document: `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/interface-design-description.md`.
- STD document: `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/software-test-description.md`.
- Existing or previously updated `ralph.md`.
- Current Hisys codebase state.
- Current test suite and validation scripts.
- Current Git branch, HEAD, and working tree state.

### 6.3 Required Checks

Prepare shall answer:

1. Which task is next according to `ralph.md`?
2. Is the task consistent with SRS, SDD, IDD, and STD?
3. Is the task still needed given the current codebase?
4. Are there missing prerequisite tasks?
5. Are there newly discovered tasks that must be inserted before the selected task?
6. Are acceptance tests or validation commands already defined?
7. Does the task require a user-executed command under Section 2?
8. Is there unrelated working-tree state that could contaminate the task?
9. Is the task small enough for one coherent increment?
10. What is the expected RED test or validation-first signal?

### 6.4 Prepare Output Format

Record the Prepare result in the active task entry or Reflection log:

```text
Prepare result:
- Selected task: <ID/title>
- Controlled anchors checked: <SRS/SDD/IDD/STD refs>
- Codebase evidence checked: <files/tests/functions>
- Consistency verdict: consistent / inconsistent / needs amendment
- Missing prerequisite tasks: <none or list>
- User-executed command required: yes/no
- Planned RED or validation-first step: <command + expected result>
- Proceed to Do: yes/no + reason
```

If Prepare finds missing prerequisite tasks or inconsistency, update Section 14 task queue before coding. If the update changes scope materially, stop for user confirmation.

## 7. Do Stage

### 7.1 Objective

Generate or modify code precisely and cleanly according to the selected task.

### 7.2 TDD Rule for Behavior Changes

For behavior changes:

1. Write the smallest failing test first.
2. Run the focused test.
3. Confirm it fails for the expected reason, not a typo or fixture error.
4. Implement the smallest code change.
5. Run focused validation.
6. Refactor only after tests pass.

If RED cannot be produced, stop and report why.

### 7.3 Code Quality Requirements

Generated code shall be:

- precise: implements the selected behavior only;
- clean: clear names, simple flow, no avoidable duplication;
- minimal: no unrequested abstraction or scope expansion;
- traceable: connected to task IDs, requirement IDs, or test names where applicable;
- safe: no hidden live action, mutation, credential use, or unbounded side effect;
- testable: side effects are isolated and covered by focused tests.

### 7.4 Commenting Rule

Add comments when they help a maintainer understand the progression logic, boundary rule, or non-obvious decision. Prefer comments that explain **why this step exists** or **which invariant it protects**.

Good comment example:

```python
# Preserve the legacy research-gap adapter ahead of generic research specs so
# existing DARS fixture behavior remains the first match for formalism tasks.
```

Avoid comments that merely restate obvious syntax.

### 7.5 Do Output Format

```text
Do result:
- RED command/result: <command + expected failure>
- Changed files: <list>
- Implementation summary: <brief>
- Comments added for progression logic: <yes/no + where>
- Focused validation: <command + result>
```

## 8. Reflection Stage

### 8.1 Objective

Assess quality, record potential issues, update `ralph.md`, and decide whether the loop remains likely to succeed.

### 8.2 Required Reflection Checks

Reflection shall determine:

1. Did the task-specific quality gate pass?
2. Did global or milestone validation pass when required?
3. Are there new potential issues, risks, or hidden dependencies?
4. Did implementation reveal missing tasks or changed sequencing?
5. Are controlled documents still consistent with the codebase?
6. Is `ralph.md` updated with the result and next-loop implications?
7. What is the estimated probability that continuing the Ralph loop will succeed without unsafe drift?
8. Is the estimated success likelihood at least 75%?

### 8.3 Success-Likelihood Rule

After each Reflection stage, estimate Ralph loop continuation success likelihood as a percentage.

Stop the loop if:

```text
success_likelihood < 75%
```

The estimate shall be based on observable factors, not optimism. Consider:

- quality gate pass/fail state;
- number and severity of unresolved issues;
- task consistency with controlled docs;
- test coverage adequacy;
- working-tree cleanliness;
- scope stability;
- need for user-executed risky commands;
- repeated validation failures;
- remaining runtime budget.

### 8.4 Reflection Update to `ralph.md`

After each task, update this file with:

- completed task ID and result;
- quality gate commands and pass/fail result;
- potential issues discovered;
- new or changed tasks;
- success likelihood estimate;
- continue/stop decision;
- next selected task if continuing.

### 8.5 Reflection Output Format

```text
Reflection result:
- Quality gate: pass/fail
- Potential issues: <none or list>
- `ralph.md` updated: yes/no + section
- Success likelihood: <N>%
- Continue decision: continue / stop
- Stop reason: <none or reason>
- Next loop starts at: Prepare for <task ID/title>
```

## 9. Runtime Limit

Unless the user specifies another duration, a Ralph loop run has a default runtime limit of:

```text
5 hours
```

If the user specifies a runtime limit, use that limit instead. When the runtime limit is reached, stop after the current safe checkpoint, do not start a new task, update the Reflection log with runtime stop reason, and report exact resume instructions.

## 10. Quality Gates

### 10.1 Minimum Task Gate

For code tasks:

```bash
git diff --check
<focused test command>
<related test command>
python3 scripts/validate_traceability.py
<python3 scripts/scan_secrets.py if artifacts/config/docs changed>
```

For docs/control-only tasks:

```bash
git diff --check
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
```

### 10.2 Global Gate

Run this before reporting any milestone complete:

```bash
python3 -m pytest \
  tests/unit/test_domain_name_strategy.py \
  tests/unit/test_domain_three_layer_use_cases.py \
  tests/unit/test_domain_bridge_contract.py \
  tests/unit/test_domain_runtime_artifacts.py \
  tests/unit/test_domain_postprocessing_guard.py \
  tests/unit/test_structured_domain_adapter.py \
  tests/unit/test_domain_adapter_registry.py \
  tests/unit/test_domain_cli.py \
  tests/unit/test_investment_decision_packet_cli.py \
  -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest -q
git status --short
git rev-parse --short HEAD
```

Acceptance:

- Focused tests pass.
- Full tests pass.
- Traceability script reports OK.
- Secret scan reports `hit_count=0`.
- `git diff --check` reports no whitespace errors.
- `git status --short` is clean after commit.
- Each new behavior has a RED test observed before production implementation.
- If this gate completes a milestone, Ralph prepares but does not execute the user-run push command.

### 10.3 Milestone Push Checkpoint

After a Hisys milestone is complete:

1. Confirm all milestone tasks have local commits.
2. Run the Global Gate in Section 10.2.
3. Confirm `git status --short` is clean.
4. Prepare a user-executed push instruction.
5. Do not start the next milestone until the user either confirms the push result or explicitly says to continue without pushing.

Required push instruction format:

```text
Action requires user execution.
Reason: milestone is complete and remote push changes shared repository state.
Risk: publishes local commits and may affect collaborators, CI, or release automation.
Recommended command for user to run manually:
  git push <remote> <branch>
Expected safe result:
  remote reports the branch was pushed successfully.
After running it, reply with the output or confirmation so Ralph can continue.
```

## 11. Commit Rule

When all required gates pass and no non-delegable action is required:

```bash
git status --short
git add <exact files>
git commit -m "<type>: <concise subject>"
git status --short
git rev-parse --short HEAD
```

Rules:

- Commit exactly one coherent task increment locally after its required gates pass.
- Do not commit unrelated user changes.
- Do not commit secrets.
- Do not commit generated heavy artifacts unless explicitly authorized.
- Do not push after every task.
- At milestone completion, run the milestone/global gate, ensure local commits are complete, then prepare a user-executed push instruction.
- Remote push remains non-delegable: Ralph/Hermes must not execute `git push`; it must ask the user to run the exact command manually.
- If commit or milestone push preparation would require risky Git state manipulation, stop and give user-run instructions.

## 12. Stop Conditions

Stop the Ralph loop and report to the user if any condition occurs:

- A task lacks SRS/SDD/IDD/STD or user-instruction support.
- Prepare finds missing prerequisite tasks that require replanning.
- The task requires a non-delegable user-executed command.
- The same task fails RED/GREEN validation three times.
- `scripts/validate_traceability.py` fails.
- `scripts/scan_secrets.py` reports `hit_count > 0`.
- `git diff --check` fails.
- A code path enables live external call, mutation, publication, credential use, order execution, or browser/access-control bypass without explicit controlled approval.
- Investment governance regresses from advisory-only, no autonomous execution, human approval required.
- New task groups are discovered that require user confirmation before continuing.
- Working tree contains unrelated user changes that could be overwritten or mixed into a commit.
- Success likelihood after Reflection is below 75%.
- Runtime limit is reached.
- Session/token/tool limit prevents a safe next increment.

## 13. Reporting Format

After each task or stop condition, report:

```text
Ralph loop: RALPH-HISYS-DOMAIN-ADAPTER
Cycle: Prepare -> Do -> Reflection
Task: <ID and title>
Phase: <Prepare/RED/GREEN/Refactor/Gate/Commit/Reflection/Stopped>
Controlled anchors: <refs>
Validation commands/results: <exact commands + pass/fail>
`ralph.md` update: <yes/no + summary>
Success likelihood: <N>%
Commit: <hash/message or none>
Working tree: <clean or file list>
Next queued task: <ID/title or none>
Stop condition: <none or exact reason>
User-executed command needed: <yes/no + command summary>
Runtime used/limit: <elapsed>/<limit>
```

## 14. Milestones and Tasks

### Milestone M1 — Register Research and Codebase Example Specs

**Goal:** Add example `research_spec` and `codebase_spec` over `StructuredDomainAdapter` and register them behind the legacy research-gap path.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-001`, `HISYS-FR-DOM-002`, `HISYS-FR-DOM-003`, `HISYS-FR-DOM-004`, `HISYS-FR-DOM-005`, `HISYS-NFR-MNT-001`, `HISYS-DATA-003..005`
- SDD: `Domain Investigation Adapter Layer`, `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7 DomainInvestigationAdapter / DomainAdapterSpec`, Interface Validation Rules
- STD: `HISYS-T-025`, `HISYS-T-026`, `HISYS-T-027`
- TDD: RED/GREEN/REFACTOR procedure in `test-driven-development`

#### Task M1.1 — Add RED tests for registry precedence

**Objective:** Lock dispatch order before adding specs.

**Files:**

- Create/modify test: `tests/unit/test_domain_example_specs.py`
- Read/possibly modify later: `src/hisys/cli/main.py`, `src/hisys/domain/specs.py`

**Required test behaviors:**

1. `domain="research"` with formalism/research-gap objective resolves to `_ResearchGapDomainAdapter`.
2. `domain="research"` with a general research objective resolves to `StructuredDomainAdapter(research_spec)`.
3. `domain="codebase"` resolves to `StructuredDomainAdapter(codebase_spec)`.
4. `domain="codebase"` with `objective` beginning `requirements-analysis:` resolves to `codebase_spec`.
5. Structured specs do not apply research-gap DARS fixture / Chief Editor postprocessors.

**RED command:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py -q
```

**Expected RED:** missing `hisys.domain.specs` or missing registry entries.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py -q
python3 -m pytest tests/unit/test_domain_adapter_registry.py tests/unit/test_domain_postprocessing_guard.py -q
python3 scripts/validate_traceability.py
git diff --check
```

#### Task M1.2 — Implement `research_spec` and `codebase_spec`

**Objective:** Provide concrete example specs without adding new CLI branch logic.

**Files:**

- Create: `src/hisys/domain/specs.py`
- Modify: `src/hisys/domain/__init__.py`
- Test: `tests/unit/test_domain_example_specs.py`

**Implementation constraints:**

- `research_spec()` returns a `DomainAdapterSpec` using `ResearchAnalysisUseCase`, `DomainUseCaseArtifactTranslator`, `DomainRuntimeArtifactWriter`, and traceability IDs including `HISYS-FR-DOM-001..005` or local implementation IDs if already established.
- `codebase_spec()` returns a `DomainAdapterSpec` using `CodeAnalysisUseCase`.
- `codebase_spec` shall keep canonical domain `codebase`; do not add `development` to `DomainName`.
- Requirements-analysis remains an objective/subtype convention under `codebase` until controlled schema approval.

**GREEN command:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py -q
```

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_structured_domain_adapter.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

#### Task M1.3 — Register example specs in the CLI default registry

**Objective:** Wire example specs into `_default_domain_adapter_registry` while preserving legacy research-gap precedence.

**Files:**

- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_domain_example_specs.py`, `tests/unit/test_domain_cli.py`

**Implementation constraints:**

- Registry order shall be:

```text
_ResearchGapDomainAdapter(instance)
StructuredDomainAdapter(research_spec())
StructuredDomainAdapter(codebase_spec())
```

- Do not add `if domain == ...` CLI branches for example specs.
- Existing research-gap fixture behavior shall remain unchanged.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_domain_cli.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit message:**

```bash
git commit -m "feat: register research and codebase structured domain specs"
```

### Milestone M2 — Add Spec Collision and Developer-Guide Hardening

**Goal:** Prevent ambiguous spec registration and document how developers add new domain specs.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-001..002`, `HISYS-NFR-MNT-001`
- SDD: `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7`
- STD: `HISYS-T-025`
- TDD: RED/GREEN/REFACTOR procedure

#### Task M2.1 — Add RED tests for duplicate domain/alias collisions

**Objective:** Ensure spec registration cannot silently create ambiguous dispatch.

**Files:**

- Modify: `tests/unit/test_domain_adapter_registry.py` or create `tests/unit/test_domain_spec_collisions.py`
- Modify later: `src/hisys/domain/adapters.py` or `src/hisys/domain/specs.py`

**Required test behaviors:**

1. Duplicate canonical domains are rejected.
2. Alias that collides with another canonical domain is rejected.
3. Alias duplicated across specs is rejected.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_spec_collisions.py tests/unit/test_domain_adapter_registry.py -q
python3 scripts/validate_traceability.py
git diff --check
```

#### Task M2.2 — Implement collision validation helper

**Objective:** Provide a small validation seam without making registry generic logic complex.

**Files:**

- Modify/create: `src/hisys/domain/specs.py` or `src/hisys/domain/domain_adapters.py`
- Test: `tests/unit/test_domain_spec_collisions.py`

**Implementation constraints:**

- Keep validation deterministic and local.
- Do not perform filesystem, network, or source access.
- Keep error messages actionable for domain developers.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_spec_collisions.py tests/unit/test_domain_example_specs.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

#### Task M2.3 — Update developer guide docs

**Objective:** Document the exact steps to add a new domain spec using the example specs.

**Files:**

- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`
- Optionally modify: `.hermes/plans/2026-05-14_074423-hisys-domain-refactoring-tdd-traceability.md`

**Required content:**

- Controlled doc anchors required before a new task.
- Spec fields to define.
- Three-layer use-case files to implement.
- RED tests required before code.
- Alias collision checks.
- Quality gate commands.

**Quality gate:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_domain_spec_collisions.py -q
```

**Commit message:**

```bash
git commit -m "docs: document structured domain spec extension workflow"
```

### Milestone M3 — Complete Investment Structured-Domain Migration

**Goal:** Complete the investment domain migration into the structured-domain substrate by reusing the existing investment product workflow, packet schema, dry-run assembler, weight-policy artifact, operator review CLI, and governance tests. The migrated path shall remain advisory-only and disabled from live external action by default.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-006`, `HISYS-FR-DOM-003..004`, `HISYS-FR-AGT-003..004`, `HISYS-NFR-SEC-001..004`, `HISYS-DATA-003..005`
- SDD: `Domain Investigation Adapter Design`, failure handling design, security/privacy/compliance design
- IDD: `HISYS-IF-017`, `5.7 DomainInvestigationAdapter / DomainAdapterSpec`, Interface Validation Rules
- STD: `HISYS-T-028`, `HISYS-T-026`, `HISYS-T-027`
- TDD: RED/GREEN/REFACTOR procedure
- Existing investment workflow references: `test-driven-development/references/hisys-lapidary-investment-product-workflow.md`, `docs/public/investment-decision-packet.md`, `docs/traceability/README.md`

**Existing implementation to reuse, not duplicate:**

- Schema: `src/hisys/schemas/investment.py`
- CLI/product workflow: `src/hisys/cli/main.py` commands `build-investment-decision-packet`, `run-investment-decision-dry-run`, and `review-investment-decision-packet`
- Tests: `tests/unit/test_investment_decision_packet_schema.py`, `tests/unit/test_investment_decision_packet_cli.py`
- Existing safety invariants: bounded human approval scopes, `execution_authorized=false` by default, `publication_or_live_action_approved=false` by default, not-financial-advice disclaimer, no autonomous execution, read-only operator review, policy mismatch rejection, no persisted computed-field round-trip pollution.

#### Task M3.1 — Add RED tests for investment structured-domain acceptance

**Objective:** Lock the structured-domain acceptance boundary before implementing `investment_spec`.

**Files:**

- Create/modify: `tests/unit/test_investment_structured_domain_spec.py`
- Read existing tests: `tests/unit/test_investment_decision_packet_cli.py`, `tests/unit/test_investment_decision_packet_schema.py`
- Read existing schema/CLI: `src/hisys/schemas/investment.py`, `src/hisys/cli/main.py`

**Required RED test behaviors:**

1. `investment_spec()` exists and returns a `DomainAdapterSpec` with canonical `domain_id="investment"`.
2. `StructuredDomainAdapter(investment_spec())` accepts `DomainInvestigationRequest(domain="investment")` and returns a bridgeable `DomainInvestigationResult`.
3. The result carries investment-specific packet or dry-run artifact refs when such refs are provided in the request/runtime context.
4. `requires_human_review=true` is preserved.
5. `external_call_made=false` and `mutation_performed=false` are preserved.
6. `quality_gate` remains `needs_more_evidence` unless a fixture-backed packet and policy satisfy the existing investment acceptance boundaries.
7. `execution_authorized=false` and `publication_or_live_action_approved=false` are visible either in the packet artifact metadata or in the structured-domain runtime artifact packet.
8. The result includes the safety phrases `not financial advice` and `no autonomous execution` in recommendation/disclaimer text.
9. Fixture-backed product dry-run misuse remains rejected by the existing CLI tests.

**RED command:**

```bash
python3 -m pytest tests/unit/test_investment_structured_domain_spec.py -q
```

**Expected RED:** missing `investment_spec` export, missing investment structured adapter behavior, or missing governance metadata projection.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_investment_structured_domain_spec.py -q
python3 -m pytest tests/unit/test_investment_decision_packet_cli.py tests/unit/test_investment_decision_packet_schema.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

#### Task M3.2 — Implement `investment_spec` over the existing product workflow

**Objective:** Add the smallest structured-domain investment spec that reuses existing investment product artifacts and safety gates instead of creating a parallel investment decision system.

**Files:**

- Modify/create: `src/hisys/domain/specs.py`
- Possibly modify: `src/hisys/domain/domain_adapters.py`, `src/hisys/domain/use_cases.py`, or a new focused helper under `src/hisys/domain/` only if the existing generic seam is insufficient.
- Test: `tests/unit/test_investment_structured_domain_spec.py`

**Implementation constraints:**

- `investment_spec()` returns `DomainAdapterSpec(domain_id="investment", ...)`.
- Reuse `InvestmentDecisionPacket` and `InvestmentWeightPolicy` semantics; do not redefine packet schemas inside domain code.
- Do not execute orders, publish, call brokers, use credentials, perform live market calls, or mutate external systems.
- Do not set `execution_authorized=true` or `publication_or_live_action_approved=true` inside the structured-domain path.
- Keep the path advisory-only unless a later controlled task explicitly adds a human-approved live connector with fixture-first tests.
- Preserve `requires_human_review=true`, `external_call_made=false`, and `mutation_performed=false`.
- Use existing runtime-boundary refs rather than copying large investment artifacts into Hermes-facing tool results.
- Add comments only where they protect a governance invariant, for example why investment remains advisory-only under this adapter.

**GREEN command:**

```bash
python3 -m pytest tests/unit/test_investment_structured_domain_spec.py -q
```

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_investment_structured_domain_spec.py tests/unit/test_domain_example_specs.py tests/unit/test_structured_domain_adapter.py -q
python3 -m pytest tests/unit/test_investment_decision_packet_cli.py tests/unit/test_investment_decision_packet_schema.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

#### Task M3.3 — Register `investment_spec` behind explicit investment routing

**Objective:** Register the investment structured-domain spec without changing research/codebase precedence or adding ad-hoc CLI domain branches.

**Files:**

- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_investment_structured_domain_spec.py`, `tests/unit/test_domain_example_specs.py`, `tests/unit/test_domain_cli.py`

**Implementation constraints:**

- Registry order after M3 shall be:

```text
_ResearchGapDomainAdapter(instance)
StructuredDomainAdapter(research_spec())
StructuredDomainAdapter(codebase_spec())
StructuredDomainAdapter(investment_spec())
```

- Do not allow aliases that collide with `research`, `codebase`, `development`, or other registered domain names.
- Do not route investment through the legacy research-gap postprocessors.
- Keep investment result projection under the same `DomainInvestigationResult` / `HisysToolResult` bridge used by other structured domains.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_investment_structured_domain_spec.py tests/unit/test_domain_example_specs.py tests/unit/test_domain_cli.py -q
python3 -m pytest tests/unit/test_investment_decision_packet_cli.py tests/unit/test_investment_decision_packet_schema.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

#### Task M3.4 — Document investment structured-domain extension and traceability

**Objective:** Update user/developer documentation so the investment structured-domain path is understandable, bounded, and traceable.

**Files:**

- Modify: `docs/public/investment-decision-packet.md`
- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`
- Modify: `docs/traceability/README.md`

**Required content:**

- `investment_spec` is a structured-domain adapter over existing investment product artifacts.
- It is not financial advice.
- It performs no autonomous execution, publication, order placement, credential use, or live external action.
- It preserves human-review and approval-scope boundaries.
- It stores full evidence in runtime-boundary artifacts and returns compact Hermes-facing refs.
- It remains compatible with existing packet/dry-run/operator-review commands.

**Quality gate:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest tests/unit/test_investment_structured_domain_spec.py tests/unit/test_investment_decision_packet_cli.py tests/unit/test_investment_decision_packet_schema.py -q
```

#### Task M3.5 — M3 global gate and commit

**Objective:** Prove that investment migration did not regress domain adapters or investment governance.

**Quality gate:**

```bash
python3 -m pytest \
  tests/unit/test_investment_structured_domain_spec.py \
  tests/unit/test_investment_decision_packet_cli.py \
  tests/unit/test_investment_decision_packet_schema.py \
  tests/unit/test_domain_example_specs.py \
  tests/unit/test_domain_spec_collisions.py \
  tests/unit/test_domain_cli.py \
  tests/unit/test_domain_bridge_contract.py \
  tests/unit/test_domain_runtime_artifacts.py \
  -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest -q
git status --short
git rev-parse --short HEAD
```

**Commit message:**

```bash
git commit -m "feat: migrate investment to structured domain adapter"
```

**M3 completion criteria:**

- `investment_spec` is registered and tested.
- Existing investment packet/schema/CLI tests still pass.
- Investment structured-domain path remains advisory-only.
- No live external action, mutation, publication, order placement, credential use, or access-control bypass is introduced.
- Traceability and secret scans pass.
- `ralph.md` Reflection Log records quality-gate results and next task.

### Milestone M4 — Requirements-Analysis Example Under Codebase Domain

**Goal:** Add requirements-analysis behavior as a codebase objective/subtype without changing `DomainName`.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-005`, `HISYS-FR-DOM-003..004`, `HISYS-DATA-003..005`
- SDD: `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7`
- STD: `HISYS-T-025..027`
- TDD: RED/GREEN/REFACTOR procedure

#### Task M4.1 — Add RED test for requirements-analysis objective routing

**Objective:** Confirm requirements-analysis remains under `codebase` until schema approval.

**Files:**

- Modify: `tests/unit/test_domain_example_specs.py`
- Possibly modify: `src/hisys/domain/specs.py`

**Required test behavior:**

```text
domain="codebase"
objective starts with "requirements-analysis:"
-> codebase_spec / CodeAnalysisUseCase path
```

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_domain_name_strategy.py -q
python3 scripts/validate_traceability.py
git diff --check
```

#### Task M4.2 — Add requirements-analysis work-product labeling

**Objective:** Make runtime artifacts distinguish codebase evaluation from requirements-analysis without schema expansion.

**Files:**

- Modify: `src/hisys/domain/use_cases.py` or `src/hisys/domain/specs.py`
- Test: `tests/unit/test_domain_example_specs.py`, `tests/unit/test_domain_runtime_artifacts.py`

**Implementation constraints:**

- Do not add `requirements_analysis` to `DomainName` in this milestone.
- Use objective/subtype labeling only.
- Preserve no external call and no mutation defaults.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_domain_runtime_artifacts.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```


### Milestone M5 — Resolve Post-M4 Traceability Identifier Risk

**Goal:** Remove the ambiguous local traceability title collision around `HISYS-T-028` so controlled `HISYS-T-028` is uniquely associated with investment domain migration governance.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-006`, `HISYS-FR-DOM-003..004`
- SDD: `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7`
- STD: `HISYS-T-028`
- TDD: RED/GREEN/REFACTOR procedure

#### Task M5.1 — Add RED test for unique `HISYS-T-028` ownership in traceability summary

**Objective:** Ensure the Selenium read-only harness no longer uses the same local increment-title identifier as controlled investment migration governance.

**Files:**

- Modify: `tests/unit/test_domain_risk_resolution.py`
- Modify: `docs/traceability/README.md`
- Possibly modify: `tests/unit/test_traceability_docs_status.py`

**Required test behavior:**

```text
Investment structured-domain adapter migration row remains the controlled `HISYS-T-028` owner.
Selenium read-only research harness uses `HISYS-T-028-SEL` as a historical/local traceability label.
```

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_risk_resolution.py tests/unit/test_traceability_docs_status.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

### Milestone M6 — Typed Investment Governance Runtime Fields

**Goal:** Promote investment governance flags from recommendation-summary text into typed runtime-artifact fields while preserving the existing advisory-only investment product workflow.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-006`, `HISYS-FR-DOM-004`, `HISYS-NFR-SEC-001..004`
- SDD: `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7`
- STD: `HISYS-T-027`, `HISYS-T-028`
- TDD: RED/GREEN/REFACTOR procedure

#### Task M6.1 — Add RED test for typed investment governance flags

**Objective:** Runtime artifacts for `investment_spec()` must expose machine-checkable booleans for the no-execution/no-publication/no-credential/no-live-action boundary.

**Files:**

- Modify: `tests/unit/test_domain_risk_resolution.py`
- Modify: `src/hisys/domain/layers.py`
- Modify: `src/hisys/domain/use_cases.py`
- Modify: `src/hisys/domain/translation.py`

**Required test behavior:**

```text
record["governance_flags"] == {
  "execution_authorized": false,
  "publication_or_live_action_approved": false,
  "autonomous_execution_allowed": false,
  "credential_use_allowed": false,
  "live_external_action_allowed": false
}
```

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_risk_resolution.py tests/unit/test_investment_structured_domain_spec.py tests/unit/test_domain_runtime_artifacts.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

### Milestone M7 — Typed Requirements-Analysis Subtype and Explicit Marker

**Goal:** Preserve `domain="codebase"` while making requirements-analysis subtype classification machine-checkable and slightly more explicit than prefix-only matching.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-005`, `HISYS-FR-DOM-003..004`
- SDD: `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7`
- STD: `HISYS-T-025`, `HISYS-T-027`
- TDD: RED/GREEN/REFACTOR procedure

#### Task M7.1 — Add RED tests for typed subtype field and explicit marker classifier

**Objective:** Requirements-analysis artifacts must carry `domain_subtype="requirements-analysis"`, and the classifier must accept both the original `requirements-analysis:` prefix and an explicit `[requirements-analysis]` marker.

**Files:**

- Modify: `tests/unit/test_domain_risk_resolution.py`
- Modify: `src/hisys/domain/layers.py`
- Modify: `src/hisys/domain/use_cases.py`
- Modify: `src/hisys/domain/translation.py`

**Implementation constraints:**

- Do not add a new `DomainName` value.
- Do not classify generic prose mentions of requirements analysis unless the prefix or explicit marker is present.
- Preserve no external call and no mutation defaults.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_risk_resolution.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_example_specs.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## 15. Reflection Log

Append one entry after each completed task, stop condition, or runtime limit.

### 2026-05-14 16:58 KST — Ralph control structure merged and verified

- Phase completed: Prepare / Do / Reflection / Gate for control-plan update.
- Controlled anchors checked: existing `ralph.md`; standard Ralph template; Hisys controlled-document table preserved.
- Codebase evidence checked: repository branch `feat/domain-adaptive-requirements-analysis`, update baseline `b6ac4ed`, existing Hisys task queue.
- Quality gate result: pass — required sections present, Markdown fences balanced, `git diff --check` passed, `scripts/validate_traceability.py` passed, `scripts/scan_secrets.py` reported `hit_count=0`.
- Potential issues: none known; task queue preserved from prior plan.
- `ralph.md` changes made: added non-delegable safety boundary, Prepare/Do/Reflection cycle, 75% success-likelihood stop rule, 5-hour default runtime, reflection log, and user-executed-command requirement.
- Success likelihood: 90% for control-plan use after validation.
- Continue decision: continue.
- Stop reason: none.
- Next task: Task M1.1 — Add RED tests for registry precedence.
- Commit: `c0d96a3 docs: complete investment ralph milestone`; this verification-log update will be committed as the next local docs/control increment.
- Working tree: modified at entry time — expected clean after local verification commit.


### 2026-05-14 — M3 investment milestone completed as executable migration plan

- Phase completed: Prepare / Do / Reflection for `ralph.md` M3 replanning.
- Controlled anchors checked: SRS `HISYS-FR-DOM-006`, SDD `Domain Investigation Adapter Design`, IDD `HISYS-IF-017`, STD `HISYS-T-028`, TDD investment workflow reference.
- Codebase evidence checked: `src/hisys/schemas/investment.py`, `tests/unit/test_investment_decision_packet_schema.py`, `tests/unit/test_investment_decision_packet_cli.py`, `docs/public/investment-decision-packet.md`, `docs/traceability/README.md`.
- Quality gate result: pass — `validate_traceability.py`, `scan_secrets.py`, `git diff --check`, investment packet/CLI focused tests, and full pytest suite passed for this control-plan edit.
- Potential issues: M3 implementation still depends on M1/M2 outputs (`investment_spec` should be added after `research_spec`/`codebase_spec` and alias-collision validation exist).
- `ralph.md` changes made: replaced the old investment midpoint-stop-only milestone with a full M3 task sequence covering RED acceptance tests, `investment_spec` implementation, registry registration, docs/traceability update, and M3 global gate.
- Success likelihood: 85% after M1/M2 complete; 70% if attempted before M1/M2 because shared specs/registry collision seams may be absent.
- Continue decision: continue after docs/control validation; execute M1 and M2 before M3 implementation.
- Stop reason: none for planning; implementation must stop if investment governance invariants regress.
- Next task: Task M1.1 remains the first execution task unless the user explicitly asks to jump to M3 after prerequisites exist.
- Commit: pending.
- Working tree: pending verification.

### 2026-05-14 — M2 collision validation and developer guide

- Phase completed: Prepare / RED / GREEN / Refactor / Gate / Commit for M2.1..M2.3.
- Controlled anchors checked: SRS `HISYS-FR-DOM-001..002`, `HISYS-NFR-MNT-001`; SDD Domain Investigation Adapter Design; IDD `HISYS-IF-017`, `5.7`; STD `HISYS-T-025`.
- Codebase evidence: `src/hisys/domain/specs.py:validate_spec_collisions`, `src/hisys/cli/main.py:_default_domain_adapter_registry`, `docs/use-cases/hermes-hisys-domain-tool.md`.
- Quality gate result: pass — collisions suite 4/4, example specs 7/7, full focused 19/19, traceability OK, secret_scan hit_count=0.
- Potential issues: self-aliases (an alias equal to the spec's canonical `domain_id`) are accepted as redundancy; future specs may want stricter rejection.
- `ralph.md` changes: M2 Reflection entry; next task M3.1.
- Success likelihood: 85% — investment migration reuses existing schema/CLI so the structured-domain bridge only needs a translator/use-case seam.
- Continue decision: continue.
- Stop reason: none.
- Next task: Task M3.1 — Add RED tests for investment structured-domain acceptance.
- Commit: `5019ee7 docs: document structured domain spec extension workflow`.
- Working tree: clean after this Reflection commit.

### 2026-05-14 — M1 example specs registered

- Phase completed: Prepare / RED / GREEN / Refactor / Gate / Commit for M1.1..M1.3.
- Controlled anchors checked: SRS `HISYS-FR-DOM-001..005`; SDD Domain Investigation Adapter Design; IDD `HISYS-IF-017`, `5.7`; STD `HISYS-T-025..027`.
- Codebase evidence checked: `src/hisys/cli/main.py:_default_domain_adapter_registry`, `src/hisys/domain/{adapters,domain_adapters,use_cases,layers}.py`, `tests/unit/test_domain_adapter_registry.py`, `tests/unit/test_domain_postprocessing_guard.py`.
- Quality gate result: pass — 7 new tests, focused suite 22/22, full suite 535/535, traceability OK, secret_scan hit_count=0, `git diff --check` clean.
- Potential issues: investment routing for `domain="investment"` still falls through to the legacy `needs_more_evidence` branch until M3 lands; `requirements-analysis` objective is currently routed under codebase but the M4 work-product label is not yet applied.
- `ralph.md` changes: added M1 Reflection Log entry; next task is M2.1.
- Success likelihood: 88% (clean registry seam, M2 collision-helper scope contained).
- Continue decision: continue.
- Stop reason: none.
- Next task: Task M2.1 — Add RED tests for duplicate domain/alias collisions.
- Commit: `2c41d39 feat: register research and codebase structured domain specs`.
- Working tree: clean.


### 2026-05-14 — M4 requirements-analysis subtype labeling completed

- Phase completed: Prepare / RED / GREEN / Refactor / Gate for M4.1..M4.2.
- Controlled anchors checked: SRS `HISYS-FR-DOM-005`, `HISYS-FR-DOM-003..004`, `HISYS-DATA-003..005`; SDD Domain Investigation Adapter Design; IDD `HISYS-IF-017`, `5.7`; STD `HISYS-T-025..027`.
- Codebase evidence: `tests/unit/test_domain_example_specs.py` adds two work-product labeling tests; `tests/unit/test_domain_runtime_artifacts.py` adds one runtime-artifact subtype label test; `src/hisys/domain/use_cases.py:CodeInvestigationLayer` now detects `requirements-analysis:` objective prefix and produces `scope="codebase:requirements-analysis"` + work-product-id suffix `REQUIREMENTS-ANALYSIS`; no schema or `DomainName` change.
- Quality gate result: pass — 555/555 full suite; M4-relevant focused suite 58/58; `validate_traceability.py` OK; `scan_secrets.py` hit_count=0; `git diff --check` clean.
- Potential issues: none structural. The work-product label is a string convention rather than a typed enum; if audit reviewers need machine-checked enums, a later controlled task can promote the subtype into a typed field. Generic codebase objectives that include the literal substring `requirements-analysis` *without* the prefix (e.g., a memo objective that mentions "requirements analysis" in prose) remain labeled `codebase` — this is intentional: only the `requirements-analysis:` *prefix* triggers the subtype, matching the documented objective/subtype convention.
- `ralph.md` changes: M4 Reflection entry; no further milestone in current plan.
- Success likelihood: n/a — plan-defined milestones complete; future loops will need a new ralph.md task queue.
- Continue decision: stop after M4 commit; no remaining M-milestones in the current ralph.md plan.
- Stop reason: planned milestone queue exhausted at M4.
- Next task: none in current plan. Future ralph.md iterations may add (a) a controlled schema increment that promotes requirements-analysis to a typed subtype field; (b) a follow-up to reconcile the pre-existing `HISYS-T-028` collision in `docs/traceability/README.md` between the Selenium harness entry and the new Investment domain migration governance entry.
- Commit: pending (`feat: label requirements-analysis codebase subtype`).
- Working tree: pending verification after commit.

Resume checkpoint:
- Current HEAD: 8349295 (pre-M4-commit)
- Working tree: 3 modified files (`src/hisys/domain/use_cases.py`, `tests/unit/test_domain_example_specs.py`, `tests/unit/test_domain_runtime_artifacts.py`, plus `ralph.md` for this entry)
- Last completed milestone/task: M4 (Requirements-Analysis Example Under Codebase Domain)
- Current in-progress task: none after commit
- RED observed: `python3 -m pytest tests/unit/test_domain_example_specs.py -q` — `AssertionError: assert 'requirements-analysis' in 'codebase'`
- GREEN observed: same command — 9/9 pass; runtime-artifact suite 11/11 pass
- Quality gate status: full pytest 555/555 pass; validate_traceability OK; scan_secrets hit_count=0; git diff --check clean
- Next command to run: stop — ralph.md milestone queue exhausted. Future Hermes/Claude iterations should update `ralph.md` Section 14 with a new milestone before continuing.
- Stop condition: planned milestone queue exhausted at M4 (see Continue decision above)

### 2026-05-14 — M3 investment structured-domain migration completed

- Phase completed: Prepare / RED / GREEN / Refactor / Gate / Commit for M3.1..M3.5.
- Controlled anchors checked: SRS `HISYS-FR-DOM-006`, `HISYS-FR-DOM-003..004`, `HISYS-NFR-SEC-001..004`; SDD Domain Investigation Adapter Design; IDD `HISYS-IF-017`, `5.7 DomainInvestigationAdapter / DomainAdapterSpec`; STD `HISYS-T-028` (Investment domain migration governance), `HISYS-T-026..027`.
- Codebase evidence: new `tests/unit/test_investment_structured_domain_spec.py` (13 tests); `src/hisys/domain/specs.py:investment_spec`; `src/hisys/domain/use_cases.py:InvestmentInvestigationLayer`, `InvestmentAdvisoryDecisionLayer`, `InvestmentAnalysisUseCase`; `src/hisys/domain/__init__.py` export; `src/hisys/cli/main.py:_default_domain_adapter_registry` registry order extended to include `StructuredDomainAdapter(investment_spec())`; docs updates in `docs/use-cases/hermes-hisys-domain-tool.md`, `docs/public/investment-decision-packet.md`, `docs/traceability/README.md`.
- Quality gate result: pass — 552/552 full suite; investment+example/spec-collision/CLI/bridge/runtime focused suite 64/64; `validate_traceability.py` OK; `scan_secrets.py` hit_count=0; `git diff --check` clean.
- Potential issues: (a) the structured-domain investment path does not yet copy `execution_authorized` / `publication_or_live_action_approved` from a real `InvestmentDecisionPacket` artifact — they are surfaced only as recommendation-summary governance text; a later controlled task can lift these into a typed runtime-artifact field if audit reviewers require structured booleans; (b) `docs/traceability/README.md` still carries a pre-existing line that re-uses `HISYS-T-028` for the Selenium harness — this conflict is out of M3 scope and should be reconciled in a separate controlled docs task.
- `ralph.md` changes: M3 Reflection entry; next task M4.1.
- Success likelihood: 88% — M4 is small (objective routing + work-product labeling under existing `codebase` spec), reuses already-validated structured-domain seam, and changes no schemas.
- Continue decision: continue.
- Stop reason: none.
- Next task: Task M4.1 — Add RED test for requirements-analysis objective routing.
- Commit: pending (`feat: migrate investment to structured domain adapter`).
- Working tree: pending verification after commit.

Resume checkpoint:
- Current HEAD: ce79077 (pre-commit)
- Working tree: 7 modified files + 1 untracked test file (listed in section above)
- Last completed milestone/task: M3 (Investment Structured-Domain Migration)
- Current in-progress task: none after commit
- RED observed: `python3 -m pytest tests/unit/test_investment_structured_domain_spec.py -q` — initial ImportError for `investment_spec` / `InvestmentAnalysisUseCase`
- GREEN observed: same command — 13/13 pass; with registry tests added later 13/13 still pass
- Quality gate status: full pytest 552/552 pass; validate_traceability OK; scan_secrets hit_count=0; git diff --check clean
- Next command to run: Prepare for Task M4.1 (RED test for `domain="codebase"` + `objective="requirements-analysis: ..."` routing — note `test_codebase_requirements_analysis_objective_resolves_to_codebase_spec` already exists in `test_domain_example_specs.py`; M4.1 should extend it with stricter objective-routing assertions or add a new focused test)
- Stop condition: none

### 2026-05-14 — Hermes iteration resilience rule added

- Phase completed: Prepare / Do / Reflection control update.
- Controlled anchors checked: `ralph.md` control protocol, Ralph loop stop conditions, current repository state after Claude-run M1/M2 commits.
- Codebase evidence checked: branch `feat/domain-adaptive-requirements-analysis`, HEAD `860d4da`, clean working tree before this edit.
- Quality gate result: pass — `validate_traceability.py`, `scan_secrets.py`, `git diff --check`, and focused domain example/spec-collision/CLI tests passed for this control-plan edit.
- Potential issues: long Claude runs can outlive Discord/Hermes iteration windows; durable checkpoints are required before each continuation.
- `ralph.md` changes made: added Section 5.1 defining durable state checkpoints, iteration budget rule, resume-first rule, interrupted-run handling, and Claude/Ralph invocation contract.
- Success likelihood: 90% after this control update; future loops should resume from git + Reflection Log even when chat context is compacted or interrupted.
- Continue decision: continue after validation and commit.
- Stop reason: none.
- Next task: resume Ralph from latest committed task state; after M1/M2, next implementation milestone is M3 unless `ralph.md` Reflection Log says otherwise.
- Commit: pending.
- Working tree: pending verification.

### 2026-05-14 18:35 KST — Milestone push checkpoint rule added

- Phase completed: Prepare / Do / Reflection control update.
- Controlled anchors checked: user instruction in Discord Ralph thread; `ralph-loop-control` skill; standard Ralph template; Hisys `ralph.md` Commit Rule and Global Gate sections.
- Codebase evidence checked: branch `feat/domain-adaptive-requirements-analysis`, HEAD `17853d4`, clean working tree before this edit.
- Quality gate result: pass — required sections present, Markdown fences balanced, `git diff --check` passed, `scripts/validate_traceability.py` passed, `scripts/scan_secrets.py` reported `hit_count=0`.
- Potential issues: remote push remains non-delegable; Ralph must prepare the push instruction only after a milestone/global gate passes and must not execute `git push` directly. Current working tree also contains unrelated uncommitted domain-risk files that must be excluded from this docs/control commit.
- `ralph.md` changes made: updated Commit Rule and Global Gate with milestone-completion push checkpoint; local commits remain per completed task increment.
- Success likelihood: 95% for control-plan consistency after validation.
- Continue decision: continue after local commit.
- Stop reason: none.
- Next task: none in current completed plan unless a new milestone queue is added.
- Commit: pending for this `ralph.md` docs/control update.
- Working tree: `ralph.md` plus unrelated domain-risk files before commit; commit must stage only `ralph.md`.


### 2026-05-14 — M5-M7 post-M4 risk resolution completed

- Phase completed: Prepare / RED / GREEN / Refactor / Gate for M5.1, M6.1, and M7.1.
- Controlled anchors checked: SRS `HISYS-FR-DOM-003..006`, `HISYS-NFR-SEC-001..004`; SDD Domain Investigation Adapter Design; IDD `HISYS-IF-017`, `5.7`; STD `HISYS-T-025`, `HISYS-T-027`, `HISYS-T-028`.
- Codebase evidence: `tests/unit/test_domain_risk_resolution.py` added risk-resolution regressions; `docs/traceability/README.md` now renames the historical Selenium local label to `HISYS-T-028-SEL`; `src/hisys/domain/layers.py` and `src/hisys/domain/translation.py` carry `domain_subtype` and `governance_flags`; `src/hisys/domain/use_cases.py` emits typed investment governance booleans and recognizes the explicit `[requirements-analysis]` marker while preserving the original `requirements-analysis:` prefix.
- Quality gate result: focused pass — 52/52 tests passed for domain risk resolution, runtime artifacts, investment structured-domain spec, example specs, and traceability-doc status; `validate_traceability.py` OK; `scan_secrets.py` hit_count=0; `git diff --check` clean.
- Potential issues: none open for these three risks; controlled document IDs were not expanded because the fixes are within existing `HISYS-FR-DOM-004..006` and `HISYS-T-025/T-027/T-028` scope.
- `ralph.md` changes: added M5, M6, and M7 milestones and this reflection entry.
- Success likelihood: n/a — M5-M7 risk-resolution queue complete after full validation.
- Continue decision: stop after local commit; no open post-M4 risk-resolution milestone remains.
- Stop reason: M5-M7 risk-resolution queue complete.
- Next task: none until a new Ralph milestone is defined.

Resume checkpoint:
- Current HEAD: 17853d4
- Working tree: modified files for M5-M7 risk resolution plus new focused test file
- Last completed milestone/task: M7.1
- Current in-progress task: none after commit
- RED observed: `python3 -m pytest tests/unit/test_domain_risk_resolution.py -q` initially failed 4/4 before implementation
- GREEN observed: focused domain risk suite 52/52 passed
- Quality gate status: focused gate passed; full gate passed (`validate_traceability.py`, `scan_secrets.py`, `git diff --check`, `python3 -m pytest -q` -> 559 passed)
- Next command to run: stop — M5-M7 risk-resolution queue complete
- Stop condition: M5-M7 risk-resolution queue complete

### 2026-05-15 — Ralph loop resume verification at HEAD c8f4bcc

- Phase completed: Prepare / Gate-only verification (no Do stage; no remaining task in queue).
- Controlled anchors checked: SRS/SDD/IDD/STD references in Section 3; Reflection Log entries for M1..M7; Section 14 milestone queue.
- Codebase evidence checked: `git status --short` clean; HEAD `c8f4bcc chore: bump version to 0.0.3`; commits since the M5-M7 resume checkpoint were `6195db5` (milestone push checkpoint rule), `05c5d7f` (M5-M7 implementation + control update), `c8f4bcc` (version bump 0.0.3).
- Quality gate result: pass — `python3 -m pytest -q` 559 passed; `scripts/validate_traceability.py` OK; `scripts/scan_secrets.py` hit_count=0; `git diff --check` clean.
- Potential issues: Section 16 "Initial Next Action" still points at M1.1, but M1.1 is completed (`2c41d39`); the section is a static template anchor, not an active task pointer. If a future Ralph loop is invoked without reading the Reflection Log it could mistakenly restart M1.1.
- `ralph.md` changes: added this verification entry and updated resume checkpoint to point at the current HEAD.
- Success likelihood: n/a — no remaining milestone tasks. Future iterations must add a new milestone (with controlled-document anchors and user confirmation per Sections 3.1, 6.4, 12) before continuing.
- Continue decision: stop.
- Stop reason: no remaining task in current `ralph.md` milestone queue; adding a new milestone requires user confirmation under Sections 3.1 / 6.4 / 12.
- Next task: none until a new Ralph milestone is defined.

Resume checkpoint:
- Current HEAD: c8f4bcc
- Working tree: clean
- Last completed milestone/task: M7.1 (and post-M7 control/version increments `6195db5`, `05c5d7f`, `c8f4bcc`)
- Current in-progress task: none
- RED observed: n/a (verification-only iteration)
- GREEN observed: full suite 559/559 at HEAD c8f4bcc
- Quality gate status: full gate pass — pytest 559/559, validate_traceability OK, scan_secrets hit_count=0, git diff --check clean
- Next command to run: stop — `ralph.md` Section 14 milestone queue exhausted; a new milestone with SRS/SDD/IDD/STD anchors and user confirmation is required before another Ralph loop continues.
- Stop condition: no remaining task in current `ralph.md` milestone queue

## 16. Initial Next Action

Start with **Task M1.1 — Add RED tests for registry precedence**.

The first Ralph-loop action shall be Prepare: inspect Git state, read SRS/SDD/IDD/STD, read this `ralph.md`, inspect current codebase evidence for registry/spec routing, and determine whether Task M1.1 remains consistent and sufficient.

Do not start by editing production code. The first implementation action must be a failing test that proves the registry does not yet route general research and codebase requests through structured example specs.
