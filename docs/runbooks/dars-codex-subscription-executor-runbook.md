# DARS Codex CLI subprocess prompt-mode runbook (docs/control)

> **Status:** human-gated, revised by readiness decision v0.0.52 and
> prepared by readiness decision v0.0.53.
> This runbook supersedes the earlier callable-only external executor wording.
> The intended Codex path is now a governed **Codex CLI subprocess prompt-mode**
> path: Hisys/Ralph may prepare and, only in a later execution row, invoke a
> bounded local `codex` subprocess. Hisys/Ralph still does **not** import a Codex
> SDK, call a raw provider API, inspect credentials, read API keys, send
> `Authorization` headers, configure provider accounts, or handle raw secrets.

This runbook is a docs/control artifact for the Codex DARS critic path. It keeps
the existing M-DARS-BE-5 policy packet, M-DARS-BE-1 activation packet, and
M-DARS-BE-6 dispatch/boundary-record concepts, but changes the operator
integration surface from "operator-owned callable that may not spawn a
subprocess" to "governed local subprocess executor that invokes the installed
Codex CLI in prompt mode".

The DARS completion claim remains
`local_fixture_localhost_controlled_advisory_complete` until a later GREEN/GATE
row reviews a real runtime-boundary record. This revision itself does not run
Codex.

## Controlled anchors

| Short name | Path |
|---|---|
| Remote subscription PREP | `docs/plans/dars-remote-subscription-auth-prep-tasks.md` |
| Codex live-smoke authorization | `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.51.md` |
| Subprocess path revision | `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.52.md` |
| Subprocess PREP implementation | `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.53.md`; `src/hisys/agents/dars_codex_cli_subprocess.py`; `tests/unit/test_dars_codex_cli_subprocess.py` |
| Live-provider policy + fake transport (R1) | `src/hisys/agents/dars_live_provider_policy.py`; `src/hisys/agents/dars_live_provider_transport.py`; `tests/unit/test_dars_live_provider_policy.py`; `tests/unit/test_dars_live_provider_transport.py` |
| Fail-closed live-provider adapter (R2) | `src/hisys/agents/dars_live_provider_adapter.py`; `tests/unit/test_dars_live_provider_adapter.py` |
| Codex policy packet draft | `docs/examples/dars/codex-subscription-policy.recommended.json` |
| Codex activation packet draft | `docs/examples/dars/codex-subscription-activation.recommended.json` |
| Remote subscription dispatch harness (M-DARS-BE-6) | `src/hisys/agents/dars_remote_subscription_dispatch.py` |
| Codex CLI | `/usr/bin/codex` observed as `codex-cli 0.128.0` on 2026-05-22 |

## 1. Revised decision

The current intended transport is:

```text
transport_kind = codex_cli_subprocess_prompt_mode
adapter_class = codex_subscription   # retained for the existing validator allowlist
provider_id = codex
```

The validator-facing `adapter_class` remains `codex_subscription` because the
current M-DARS-BE-5 allowlist accepts `codex_subscription` for provider `codex`.
The runtime-boundary transport label must distinguish the actual execution
mechanism as `codex_cli_subprocess_prompt_mode`.

This path deliberately avoids:

- Codex SDK imports inside Hisys;
- raw HTTP/API provider calls from Hisys;
- API-key or `Authorization` header handling by Hisys;
- vault unseal or credential lookup by Hisys;
- provider account configuration by Hisys.

The installed Codex CLI may use its own operator-managed login/session outside
Hisys. Hisys must not read, serialize, log, or validate that credential material.

## 2. Subprocess executor contract

A future implementation row may introduce a narrow executor with this logical
shape:

```python
def codex_cli_prompt_mode_executor(payload: dict[str, object]) -> str:
    """Run a bounded Codex CLI prompt-mode subprocess and return critique text."""
```

The executor may spawn **only** the allowlisted `codex` binary and only for the
single DARS critique subprocess. No other subprocess family is authorized.

Required subprocess constraints:

- executable: `codex` resolved from an operator-approved path such as
  `/usr/bin/codex`;
- command family: Codex prompt-mode / noninteractive prompt execution only;
- sandbox: read-only or stricter where supported, e.g. `--sandbox read-only`;
- approval policy: no interactive escalation from the model, e.g.
  `--ask-for-approval never` for noninteractive execution rows;
- web search: disabled; do not pass `--search`;
- working directory: a controlled read-only work directory or scratch directory,
  not a mutable production checkout unless the execution row separately proves
  read-only behavior;
- prompt input: the redacted bounded DARS prompt packet only;
- output: captured stdout/stderr sanitized to a non-empty critique text and
  bounded diagnostic metadata;
- timeout: finite and recorded;
- mutation: no file writes, git writes, publication, deployment, release,
  issue/PR creation, network tooling beyond Codex's own model transport, or
  downstream tool invocation.

## 3. Prompt packet and redaction

Before spawning `codex`, the execution row must construct a bounded prompt packet
that contains only:

- the DARS critic instruction;
- bounded evidence summary selected for critique;
- explicit advisory-only action scope;
- explicit prohibition on file mutation, shell/tool use, browser/search, git
  mutation, publication, deployment, and completion-claim upgrade;
- request identifiers needed for traceability.

The prompt packet must be redacted under
`policy://hisys/dars/codex-subscription-redaction-v1` before it reaches the
Codex subprocess. The subprocess executor must not add system prompts or flags
that grant tools, web search, mutation, or publication authority.

## 4. Command shape for a future execution row

This revision records the intended command family but does not execute it.
A later implementation row must validate the exact installed Codex CLI behavior
before use. The candidate command shape is:

```bash
codex exec   --sandbox read-only   --ask-for-approval never   --cd <controlled-read-only-workdir>   -- "<redacted bounded DARS critic prompt>"
```

If `codex exec` cannot run in the host sandbox without broader permissions, the
execution row must stop and ask. `--dangerously-bypass-approvals-and-sandbox`,
`--sandbox danger-full-access`, `--search`, `--full-auto`, `--yolo`, shell-write
permissions, and workspace-write permissions are not authorized by this revision.

## 5. Runtime-boundary record requirements

A successful future smoke must write a runtime-boundary JSON + Markdown pair
under the existing M-DARS-BE-6 partition and include at minimum:

```text
transport_kind=codex_cli_subprocess_prompt_mode
provider_id=codex
adapter_class=codex_subscription
external_call_made=true
model_boundary_crossed=true
local_model_call_made=false
codex_sdk_invoked=false
raw_provider_api_invoked=false
credential_lookup_by_hisys=false
mutation_performed=false
publication_performed=false
allowed_actions=advisory_only
requires_human_review=true
```

The record may include command metadata such as executable path, Codex CLI
version, sandbox mode, approval policy, timeout, prompt packet hash, redaction
policy ref, egress scope label, and bounded critique preview. It must not include
raw prompts if they contain sensitive evidence, raw credentials, tokens,
Authorization headers, provider account identifiers, or unredacted secrets.

## 6. Stop-condition matrix

| Signal | Required action / deterministic code |
|---|---|
| `codex` binary missing or version unknown | Stop before execution; record tool readiness only |
| Codex CLI requires SDK/API key material from Hisys | Stop; Hisys must not handle credentials |
| Prompt packet not redacted | `codex_cli_prompt_not_redacted` (raised before subprocess spawn) |
| Requested command uses `--search`, `--full-auto`, `--yolo`, `danger-full-access`, or sandbox bypass | Stop and ask; not authorized by this runbook |
| Codex asks to run shell/tools, mutate files, search web, browse, publish, deploy, or create PR/issues | Stop and record blocked request |
| Subprocess timed out | `codex_cli_subprocess_timeout: timeout_seconds=<n>` |
| Subprocess exited non-zero | `codex_cli_subprocess_failed: returncode=<n>: <stderr-preview>` (stderr preview is replaced with `<stderr-redacted-secret-detected len=N>` when it carries raw-secret markers) |
| Subprocess output is empty / whitespace-only | `codex_cli_subprocess_empty_output` |
| Subprocess output exceeds `_MAX_CRITIQUE_CHARS` (32_000) | `codex_cli_subprocess_output_too_long` |
| Subprocess output contains forbidden control characters | `codex_cli_subprocess_output_contains_control_chars` |
| Subprocess output claims unauthorized authority (`workspace_write`, `web_search`, `sandbox bypass`, `danger-full-access`, `mutation_performed`, `publication_performed`, `requires_human_review=false`, `<<executing shell>>`, `<<tool call>>`) | `codex_cli_subprocess_output_claims_unauthorized_authority` |
| Output contains raw-secret markers | `codex_cli_output_not_redacted` (do not write as critique evidence) |
| Working tree changes after a supposed read-only run | Stop; treat as mutation incident |
| Runtime-boundary record cannot be written under `HISYS_INSTANCE` | Stop; no completion claim upgrade |

## 8. PREP implementation surface (v0.0.53)

`src/hisys/agents/dars_codex_cli_subprocess.py` prepares the governed Codex CLI
subprocess prompt-mode executor without running Codex in tests. The surface is
still shaped as the M-DARS-BE-6 executor seam:

```python
Callable[[dict[str, Any]], str]
```

The prepared command is fixed to:

```bash
codex --ask-for-approval never exec \
  --sandbox read-only \
  --cd <controlled-workdir> \
  -- "<redacted bounded DARS critic prompt packet>"
```

The wrapper validates `provider_id=codex`, `adapter_class=codex_subscription`,
`transport_kind=codex_cli_subprocess_prompt_mode`, `allowed_actions=advisory_only`,
false mutation/publication flags, a configured workdir, a bounded timeout, and a
prompt packet that does not contain obvious raw-secret markers. It calls
`subprocess.run(..., shell=False, capture_output=True, text=True, check=False,
env={"PATH": ...})` only after those checks pass. Subprocess timeout, non-zero
exit, blank/whitespace-only output, output exceeding `_MAX_CRITIQUE_CHARS`,
output containing forbidden control characters, output claiming unauthorized
authority (tool/shell/search/mutation/publication or `requires_human_review=false`),
and output carrying raw-secret markers each fail closed with the deterministic
codes named in §6. The non-zero-exit message redacts secret-shaped stderr
substrings via `<stderr-redacted-secret-detected len=N>` so focused error
messages cannot leak the secret payload.

The local-only failure-mode fixture cohort
`DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP` exercises each of these
codes with injected fake runners under
`tests/unit/test_dars_codex_cli_subprocess.py` so the implementation cannot
regress without breaking the focused tests. No real `/usr/bin/codex` subprocess
is launched by that cohort.

`src/hisys/agents/dars_remote_subscription_dispatch.py` now carries
`transport_kind` through `RemoteSubscriptionDispatchRequest`, the executor
payload, and the single-critic boundary record writer. The default remains
`injected_subscription_executor`; the Codex CLI path must explicitly request
`codex_cli_subprocess_prompt_mode`.

The PREP tests use fake runners/executors. They do not invoke `/usr/bin/codex`.

## 9. Verification commands for this docs/control revision

```bash
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

No Codex subprocess is run by this revision. The observed local tool fact
`/usr/bin/codex` and `codex-cli 0.128.0` is readiness context only.

## 10. Next safe Ralph row

The next safe row becomes a human-gated single-smoke gate:

```text
DARS-CODEX-CLI-SUBPROCESS-SINGLE-SMOKE-GATE
```

That row may run at most one real Codex CLI subprocess smoke only after the final
command, workdir/instance root, redacted prompt packet, no-mutation guard, and
runtime-boundary output path are confirmed. If Codex requires broader sandbox,
search, tool, mutation, or account/credential authority, the row must stop.
