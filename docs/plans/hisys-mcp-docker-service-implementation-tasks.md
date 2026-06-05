# Hisys MCP Docker Service Implementation Plan

> **For Hermes:** Use `subagent-driven-development` or a Ralph/PDR loop to implement this plan task-by-task. This plan is a planning artifact only; no production code is changed by this file.

**Accepted scope note:** This plan belongs to the `hermes-mcp` feature branch. The immediate objective is Hermes-container lightweighting by running Hisys as a separate MCP sidecar service, not general MCP interoperability or DRLOO protocol development. DRLOO remains a separate work unit/branch and may later consume Hisys-MCP as a fixture after Hisys-MCP has its own validated checkpoint.

**Claude review handle:** `docs/reviews/hisys-mcp-claude-plan-review-20260605.md` reviewed this plan as `READY_WITH_REVISIONS`. Before production implementation starts, close or explicitly carry forward the review's required revisions: MCP SDK transport pin, first-slice in-process health tool, request/artifact path policy, Docker non-root/runtime details, compose mount path correction, and future Altas/DARS/Judge tool exposure flag.

**Goal:** Keep the Hermes Docker container lightweight by moving Hisys and its heavier runtime dependencies into a separate Dockerized MCP service, while preserving Hisys governance boundaries and enabling later Altas, DARS, and Judge service separation.

**Architecture:** Start with a single `hisys-mcp` gateway service that exposes a small read-only/gated MCP tool surface over HTTP MCP. The gateway calls existing Hisys CLI/Python seams and returns schema-backed JSON plus safe artifact refs. Altas, DARS, and Judge remain internal subsystems at first, then gain explicit service interfaces and may later become sidecar services or independent MCP servers.

**Tech Stack:** Python 3.11+, existing Hisys package (`src/hisys`), MCP Python SDK, Docker/Compose, pytest, Pydantic schemas, existing Hisys CLI commands and runtime artifacts.

**Context Packet:**
- Repo: `/home/cbchoi/workspaces/develop/repos/hisys`
- Current branch/status observed: `main...origin/main`, clean working tree at plan creation.
- CodeGraph was not initialized in this repo; source handles were collected via file search.
- Existing CLI entrypoint: `src/hisys/cli/main.py`
- Existing CLI command seams found: `health-status`, `environment-status`, `list-run-artifacts`, `show-artifact`, `release-readiness`, `investigate-domain`
- Existing subsystem seams: `src/hisys/dars/`, `src/hisys/judge/`, `src/hisys/domain/`, `src/hisys/operations/`, `src/hisys/connectors/`
- Existing tests: `tests/unit/test_health_status.py`, `tests/unit/test_release_ops_cli.py`, `tests/integration/test_pass_contract_self_improvement_flow.py`
- Current dependency baseline: `pyproject.toml` has minimal runtime deps (`pydantic`, `pyyaml`) and optional browser/headroom extras; no MCP/Docker packaging currently detected.

**Boundary Record:**
- This plan allows local code/docs/test/docker-file edits only after implementation approval.
- No live external browser/search/provider calls during initial implementation.
- MCP `sampling` must be disabled by default.
- Live connector, browser run, publication, upload/post, investment execution, credentials, and mutation-capable operations remain gated and fail closed unless a later explicit approval/ref contract is added.
- Docker/Compose smoke uses local fixtures and local runtime mounts only.

---

## Design Decision Summary

### Recommended staged design

1. **Phase 1: Single Hisys MCP gateway service**
   - Hermes container remains lightweight and only contains Hermes + MCP client configuration.
   - `hisys-mcp` container owns Hisys dependencies, runtime instance, evidence store, and report artifacts.
   - MCP server exposes a small stable tool surface over HTTP.

2. **Phase 2: Internal subsystem contracts**
   - Add explicit internal service contracts for Altas, DARS, and Judge.
   - Keep them in-process or subprocess-backed under `hisys-mcp` first.

3. **Phase 3: Sidecar services**
   - Split Altas first if evidence/index/cache dependencies justify it.
   - Split DARS second if model/provider/runtime dependency isolation becomes valuable.
   - Split Judge last because it is the most governance-sensitive decision boundary.

4. **Phase 4: Independent MCP servers only if needed**
   - `altas-mcp`, `dars-mcp`, `judge-mcp` can be registered separately later.
   - Do this only after request envelopes, artifact refs, health checks, and approval boundaries are stable.

### Initial MCP tool surface

Expose only these first:

```text
health_status
machine_status / environment_status
investigate_domain
list_run_artifacts
show_artifact
release_readiness
```

Defer or keep gated:

```text
public_browser_run
source_connector_preflight with live providers
DARS live backend dispatch
external model/provider panel execution
publication/upload/post/write actions
investment execution or brokerage-like actions
```

---

## Proposed repository layout

Create or modify these paths during implementation:

```text
src/hisys/mcp/__init__.py
src/hisys/mcp/contracts.py
src/hisys/mcp/config.py
src/hisys/mcp/cli_adapter.py
src/hisys/mcp/server.py
src/hisys/mcp/tools.py
src/hisys/services/__init__.py
src/hisys/services/altas.py
src/hisys/services/dars.py
src/hisys/services/judge.py
tests/unit/test_mcp_contracts.py
tests/unit/test_mcp_cli_adapter.py
tests/unit/test_mcp_tools.py
tests/integration/test_mcp_server_smoke.py
Dockerfile.hisys-mcp
docker/compose.hisys-mcp-smoke.yaml
docs/public/hisys-mcp-service.md
docs/plans/hisys-mcp-docker-service-implementation-tasks.md
```

Optional later paths:

```text
src/hisys/altas/                 # if Altas becomes a first-class package
src/hisys/altas/rloo.py
docker/compose.hisys-subsystems.yaml
Dockerfile.altas-mcp
Dockerfile.dars-mcp
Dockerfile.judge-mcp
```

---

## Phase 0 — Alignment and non-goals

### Task 0.1: Preserve this plan as a repo-local implementation plan

**Objective:** Copy this `.hermes/plans` plan into `docs/plans/` before coding so future agents find it in project docs.

**Files:**
- Create: `docs/plans/hisys-mcp-docker-service-implementation-tasks.md`

**Steps:**
1. Copy the accepted version of this plan into `docs/plans/hisys-mcp-docker-service-implementation-tasks.md`.
2. Add a short “accepted scope” note stating that the immediate objective is Hermes-container lightweighting, not full public interoperability.
3. Do not modify production code in this task.

**Verification:**
```bash
git diff --check
```
Expected: no whitespace errors.

### Task 0.2: Add an explicit MCP service decision note

**Objective:** Record the architectural decision that Hisys is split into a Dockerized MCP sidecar to keep Hermes lightweight.

**Files:**
- Create or update: `docs/public/hisys-mcp-service.md`

**Minimum content:**
- Hermes container responsibility: orchestrator + MCP client only.
- Hisys MCP container responsibility: Hisys runtime, heavy deps, evidence store, reports.
- Single gateway first; Altas/DARS/Judge split later.
- Sampling disabled by default.
- Live/external actions gated.

**Verification:**
```bash
git diff --check
```

---

## Phase 1 — MCP contracts and fail-closed configuration

### Task 1.1: Add MCP optional dependency

**Objective:** Make MCP an optional dependency so base Hisys installs remain lightweight.

**Files:**
- Modify: `pyproject.toml`

**Expected change:**
```toml
[project.optional-dependencies]
mcp = [
  "mcp>=1.0",
]
```

Keep existing `dev`, `browser`, and `headroom` extras intact.

**Test first:**
- Add a test or package metadata check only if the repo has existing metadata tests; otherwise this is config-only.

**Verification:**
```bash
python3 -m pytest tests/unit/test_health_status.py -q
```
Expected: existing health tests still pass.

### Task 1.2: Define MCP request/response envelope schemas

**Objective:** Establish a stable boundary contract before implementing server tools.

**Files:**
- Create: `src/hisys/mcp/__init__.py`
- Create: `src/hisys/mcp/contracts.py`
- Test: `tests/unit/test_mcp_contracts.py`

**Schemas to define:**
- `McpSafetyFlags`
  - `external_call_allowed: bool = False`
  - `mutation_allowed: bool = False`
  - `publication_allowed: bool = False`
  - `live_provider_allowed: bool = False`
- `McpRequestEnvelope`
  - `request_id: str`
  - `trace_id: str | None`
  - `tool_name: str`
  - `safety: McpSafetyFlags`
  - `approval_ref: str | None = None`
- `McpToolResultEnvelope`
  - `status: Literal["ok", "blocked", "needs_more_evidence", "error"]`
  - `tool_name: str`
  - `request_id: str | None`
  - `external_call_made: bool = False`
  - `mutation_performed: bool = False`
  - `publication_or_live_action_approved: bool = False`
  - `human_approval_required: bool = True`
  - `artifact_refs: list[str] = []`
  - `payload: dict[str, Any] = {}`
  - `error: str | None = None`

**RED test examples:**
```bash
PYTHONPATH=src pytest tests/unit/test_mcp_contracts.py::test_mcp_result_defaults_are_fail_closed -q
```
Expected initially: fail because contracts do not exist.

**Acceptance:**
- Default result has all live/mutation/publication flags false.
- Safety flags default false.
- JSON serialization is deterministic enough for snapshot-style checks.

### Task 1.3: Add MCP server config loader

**Objective:** Centralize environment variable and runtime path handling for Docker service mode.

**Files:**
- Create: `src/hisys/mcp/config.py`
- Test: `tests/unit/test_mcp_contracts.py` or `tests/unit/test_mcp_config.py`

**Config fields:**
- `instance_root: Path` from `HISYS_INSTANCE_ROOT`, default `/runtime`
- `environment_config: Path | None` from `HISYS_ENVIRONMENT_CONFIG`
- `store_config: Path | None` from `HISYS_STORE_CONFIG`
- `allow_live_actions: bool` from `HISYS_ALLOW_LIVE_ACTIONS`, default false
- `sampling_enabled: bool` from `HISYS_MCP_SAMPLING_ENABLED`, default false
- `subprocess_timeout_seconds: int`, default 180

**Acceptance:**
- Missing env vars produce safe defaults.
- `allow_live_actions` and `sampling_enabled` are false unless explicitly set to true.
- Config loader does not create files or directories.

---

## Phase 2 — CLI adapter layer

### Task 2.1: Add a subprocess-safe Hisys CLI adapter

**Objective:** Let MCP tools call existing CLI commands without importing the whole CLI into the MCP server path unnecessarily.

**Files:**
- Create: `src/hisys/mcp/cli_adapter.py`
- Test: `tests/unit/test_mcp_cli_adapter.py`

**Design:**
- Function: `run_hisys_cli(args: Sequence[str], *, timeout_seconds: int, env: Mapping[str, str] | None = None) -> CliInvocationResult`
- Capture `stdout`, `stderr`, `returncode`, `timed_out`.
- Never pass unfiltered full environment except explicit safe baseline plus explicit overrides.
- Return structured result; do not raise for nonzero exit except programming errors.

**RED test:**
```bash
PYTHONPATH=src pytest tests/unit/test_mcp_cli_adapter.py::test_cli_adapter_captures_json_stdout -q
```
Expected initially: fail because adapter does not exist.

**Acceptance:**
- A Python one-liner fixture command can be captured.
- Nonzero exit returns `returncode != 0` and stderr text.
- Timeout returns `timed_out=True` and no live side effects.

### Task 2.2: Add JSON parsing helper with bounded errors

**Objective:** Convert CLI JSON stdout into MCP payloads safely.

**Files:**
- Modify: `src/hisys/mcp/cli_adapter.py`
- Test: `tests/unit/test_mcp_cli_adapter.py`

**Acceptance:**
- Valid JSON stdout returns dict/list payload.
- Invalid JSON returns a structured error envelope and preserves stderr summary.
- Error messages must not expose secrets; at minimum redact `token=`, `password=`, `secret=`, `Authorization: Bearer` patterns.

---

## Phase 3 — Initial MCP tools

### Task 3.1: Implement tool functions independent of transport

**Objective:** Implement Python functions for the MCP tool surface before binding them to an MCP server runtime.

**Files:**
- Create: `src/hisys/mcp/tools.py`
- Test: `tests/unit/test_mcp_tools.py`

**Functions:**
```python
hisys_health_status(...)
hisys_environment_status(...)
hisys_investigate_domain(...)
hisys_list_run_artifacts(...)
hisys_show_artifact(...)
hisys_release_readiness(...)
```

**Acceptance:**
- Each function returns `McpToolResultEnvelope` or plain JSON compatible with it.
- Each function sets `external_call_made=false`, `mutation_performed=false`, and `publication_or_live_action_approved=false` unless a future explicit tool proves otherwise.
- `show_artifact` accepts only safe relative `.json` or `.md` refs and delegates to existing `show-artifact` behavior.

### Task 3.2: Add health/status tool wrapper

**Objective:** Prove the simplest MCP tool path with a no-live-action local command.

**Files:**
- Modify: `src/hisys/mcp/tools.py`
- Test: `tests/unit/test_mcp_tools.py`

**Command mapping:**
```text
health_status -> hisys health-status --instance <instance_root> --date <yyyymmdd> --format json
```

**RED test:**
```bash
PYTHONPATH=src pytest tests/unit/test_mcp_tools.py::test_health_status_tool_returns_fail_closed_envelope -q
```

**Acceptance:**
- Tool writes only local report artifacts under the provided temp instance.
- Envelope includes artifact refs to the report JSON/Markdown if available.

### Task 3.3: Add artifact listing and display wrappers

**Objective:** Preserve safe artifact refs as the MCP data access contract.

**Files:**
- Modify: `src/hisys/mcp/tools.py`
- Test: `tests/unit/test_mcp_tools.py`

**Command mapping:**
```text
list_run_artifacts -> hisys list-run-artifacts --instance <root> --date <yyyymmdd> [--request-id <id>]
show_artifact -> hisys show-artifact --instance <root> --ref <safe-ref>
```

**Acceptance:**
- Reject absolute paths and `..` traversal before calling CLI.
- Return payload containing safe refs, not host absolute paths.

### Task 3.4: Add investigate-domain wrapper for local/fixture request files

**Objective:** Expose the main Hisys investigation path without live connector escalation.

**Files:**
- Modify: `src/hisys/mcp/tools.py`
- Test: `tests/unit/test_mcp_tools.py`

**Command mapping:**
```text
investigate_domain -> hisys investigate-domain --instance <root> --request <request_json_path> --date <yyyymmdd>
```

**Safety requirements:**
- Accept either an already-mounted request path under allowed roots or a request JSON object written to a temp request file under the instance runtime.
- Reject request fields that imply live external action unless `allow_live_actions=true` and explicit `approval_ref` exists. Initial implementation should simply reject these.
- Preserve formal `needs_more_evidence` status if Hisys returns it.

**Acceptance:**
- Fixture/local request runs in a temp instance.
- No external call flag is set by the wrapper.
- Result includes output artifact refs where available.

### Task 3.5: Add release-readiness wrapper

**Objective:** Allow MCP callers to request a release-readiness report from explicit quality gates and trace refs.

**Files:**
- Modify: `src/hisys/mcp/tools.py`
- Test: `tests/unit/test_mcp_tools.py`

**Acceptance:**
- Quality gates and trace refs are explicit arguments.
- Missing quality gates produce a bounded error or no-go report, not an invented pass.
- Result remains human-review oriented.

---

## Phase 4 — MCP server transport

### Task 4.1: Add HTTP MCP server entrypoint

**Objective:** Expose the implemented tool functions through an MCP server process.

**Files:**
- Create: `src/hisys/mcp/server.py`
- Test: `tests/integration/test_mcp_server_smoke.py`

**Server modes:**
```bash
python -m hisys.mcp.server --stdio
python -m hisys.mcp.server --host 0.0.0.0 --port 8765
```

**Acceptance:**
- `--stdio` exists for local client tests.
- HTTP/streamable mode exists for Docker Compose.
- Startup does not create runtime artifacts until a tool is called.
- Server reports tool names deterministically.

### Task 4.2: Add transport-level smoke test

**Objective:** Verify that a real MCP client can list and call at least `health_status`.

**Files:**
- Modify: `tests/integration/test_mcp_server_smoke.py`

**Verification command:**
```bash
PYTHONPATH=src pytest tests/integration/test_mcp_server_smoke.py -q
```

**Acceptance:**
- Test uses temp directories.
- Test does not require external network.
- Test does not require Docker yet.

---

## Phase 5 — Docker sidecar packaging

### Task 5.1: Add Hisys MCP Dockerfile

**Objective:** Build a container that contains Hisys and MCP dependencies, not Hermes.

**Files:**
- Create: `Dockerfile.hisys-mcp`

**Expected properties:**
- Python 3.11+ base image.
- Install `.[mcp]`.
- Optional browser dependencies are not installed in the first image unless needed by a gated follow-up.
- Entrypoint runs `python -m hisys.mcp.server --host 0.0.0.0 --port 8765`.

**Acceptance:**
```bash
docker build -f Dockerfile.hisys-mcp -t hisys-mcp:local .
```
Expected: image builds without installing Hermes.

### Task 5.2: Add local Compose smoke stack

**Objective:** Validate service separation without changing production Hermes config.

**Files:**
- Create: `docker/compose.hisys-mcp-smoke.yaml`

**Service:**
```yaml
services:
  hisys-mcp:
    build:
      context: ..
      dockerfile: Dockerfile.hisys-mcp
    environment:
      HISYS_INSTANCE_ROOT: /runtime
      HISYS_MCP_SAMPLING_ENABLED: "false"
      HISYS_ALLOW_LIVE_ACTIONS: "false"
    volumes:
      - ./tmp/hisys-runtime:/runtime
    ports:
      - "8765:8765"
```

**Acceptance:**
```bash
docker compose -f docker/compose.hisys-mcp-smoke.yaml up --build
```
Then, from host or a test client, list tools and call `health_status`.

### Task 5.3: Add Hermes candidate config snippet

**Objective:** Document how lightweight Hermes connects to the sidecar without baking Hisys into the Hermes image.

**Files:**
- Modify: `docs/public/hisys-mcp-service.md`

**Candidate config only; do not auto-apply:**
```yaml
mcp_servers:
  hisys:
    url: "http://hisys-mcp:8765/mcp"
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

**Acceptance:**
- Docs state this is a candidate config requiring operator approval/restart.
- Docs include rollback: remove `mcp_servers.hisys`, restart Hermes, stop/remove `hisys-mcp` container.

---

## Phase 6 — Altas, DARS, Judge service boundaries

### Task 6.1: Define subsystem service contracts

**Objective:** Prepare future separation without prematurely creating three services.

**Files:**
- Create: `src/hisys/services/__init__.py`
- Create: `src/hisys/services/altas.py`
- Create: `src/hisys/services/dars.py`
- Create: `src/hisys/services/judge.py`
- Test: `tests/unit/test_mcp_contracts.py` or new `tests/unit/test_service_contracts.py`

**Contract shape:**
```python
@dataclass(frozen=True)
class ServiceInvocationEnvelope:
    request_id: str
    trace_id: str | None
    objective: str
    evidence_refs: tuple[str, ...]
    safety: McpSafetyFlags
    approval_ref: str | None = None
```

**Service responsibilities:**
- Altas: evidence/source handle resolution, retrieval/index interface, evidence package construction; sensor-first.
- DARS: adversarial critique, Devil/multi-critic review, residual-risk surfacing; advisory-only.
- Judge: rubric scoring, bounded decision packet, human-review gate; governance-sensitive.

**Acceptance:**
- Contracts are pure data and do not start subprocesses.
- Defaults remain fail-closed.

### Task 6.2: Add internal gateway routing placeholders

**Objective:** Let Hisys MCP expose future names without claiming unimplemented behavior.

**Files:**
- Modify: `src/hisys/mcp/tools.py`
- Test: `tests/unit/test_mcp_tools.py`

**Initial tool behavior:**
- `altas_status` may report available/unimplemented subsystem status.
- `dars_status` may call existing DARS readiness command if safe and local.
- `judge_status` may call existing Judge readiness command if safe and local.
- Do not expose `judge_decide` as final authoritative approval.

**Acceptance:**
- Unimplemented service calls return `status="blocked"` or `status="error"` with clear reason, not fake results.
- Existing subsystem-local commands such as `python -m hisys.dars.rloo --check --format json` and `python -m hisys.judge.rloo --check --format json` can be wrapped later with tests.

### Task 6.3: Decide first extraction target

**Objective:** Use evidence after Phase 1-5 to decide whether to split Altas first.

**Decision packet fields:**
- Dependency weight in `hisys-mcp` image.
- Runtime cache/index volume needs.
- Startup latency.
- Failure isolation need.
- Tool surface stability.

**Default recommendation:** Split Altas first only if it introduces index/cache dependencies that materially bloat or destabilize the gateway. Keep DARS/Judge inside the gateway longer.

---

## Phase 7 — Verification, traceability, and rollout

### Task 7.1: Focused test gate

**Objective:** Validate MCP unit/integration behavior without full suite cost.

**Commands:**
```bash
PYTHONPATH=src pytest \
  tests/unit/test_mcp_contracts.py \
  tests/unit/test_mcp_cli_adapter.py \
  tests/unit/test_mcp_tools.py \
  tests/integration/test_mcp_server_smoke.py \
  -q
```

**Expected:** all pass.

### Task 7.2: Existing regression gate

**Objective:** Ensure new MCP sidecar work does not break existing Hisys CLI seams.

**Commands:**
```bash
PYTHONPATH=src pytest \
  tests/unit/test_health_status.py \
  tests/unit/test_release_ops_cli.py \
  tests/integration/test_pass_contract_self_improvement_flow.py \
  -q
```

**Expected:** all pass.

### Task 7.3: Project-level gate

**Objective:** Run standard Hisys validation before declaring implementation complete.

**Commands:**
```bash
PYTHONPATH=src pytest -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short
```

**Expected:** pytest passes, traceability passes, secret scan passes, diff check clean.

### Task 7.4: Docker smoke gate

**Objective:** Prove the target deployment model: Hermes can stay lightweight because Hisys is reachable as a separate service.

**Commands:**
```bash
docker build -f Dockerfile.hisys-mcp -t hisys-mcp:local .
docker compose -f docker/compose.hisys-mcp-smoke.yaml up --build
```

Then call the server with a minimal MCP client or test fixture.

**Acceptance:**
- Hisys MCP container starts.
- Tool list includes initial tools.
- `health_status` works with mounted `/runtime`.
- No external call, mutation, or publication flags are true.

---

## Rollback Plan

If MCP service registration causes trouble:

1. Stop the sidecar:
   ```bash
   docker compose -f docker/compose.hisys-mcp-smoke.yaml down
   ```
2. Remove candidate Hermes config entry:
   ```yaml
   mcp_servers:
     hisys: ...
   ```
3. Restart Hermes gateway/container.
4. Keep existing Hisys CLI/Hermes tool snapshot path available as fallback.
5. Delete only generated smoke runtime directories after confirming they contain no needed evidence.

---

## Open Questions / Gates

1. **MCP SDK transport choice:** confirm exact Python MCP SDK API for HTTP/streamable server in the implementation environment before coding `server.py`.
2. **Image layering:** decide whether `hisys-mcp` first image should include browser extras. Recommendation: no; create a later `hisys-mcp-browser` or gated extra image.
3. **Altas package status:** Altas appears conceptually present in memory/governance, but an explicit `src/hisys/altas` package was not found in initial file search. Plan assumes an initial service contract placeholder before implementation.
4. **Hermes config mutation:** do not edit production Hermes config until Docker smoke passes and the operator approves registration.
5. **Live action policy:** all live/external operations remain blocked in this increment.

---

## Definition of Done

- [ ] Hisys MCP optional dependency exists and base install remains lightweight.
- [ ] Fail-closed MCP contracts exist with tests.
- [ ] Initial tool wrappers exist for health/status, investigation, artifact list/show, and release readiness.
- [ ] MCP server starts in stdio and HTTP modes.
- [ ] Docker image builds without Hermes inside it.
- [ ] Compose smoke proves `hisys-mcp` is reachable as a separate service.
- [ ] Docs explain Hermes lightweight-sidecar architecture and rollback.
- [ ] Existing Hisys CLI regression tests pass.
- [ ] Full Hisys validation gates pass before commit/push.
