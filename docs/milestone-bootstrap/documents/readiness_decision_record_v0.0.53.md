# Readiness Decision Record v0.0.53 — Codex CLI subprocess prompt-mode PREP

- **Decision ID:** `DARS-CODEX-CLI-SUBPROCESS-PROMPT-MODE-PREP-20260522`
- **Recorded at:** `2026-05-22T13:19:44Z`
- **Approving operator:** `choi-cb`
- **User instruction:** `진행`
- **Prior HEAD:** `17135d0 docs: revise dars codex path to subprocess prompt mode`
- **Prepared module:** `src/hisys/agents/dars_codex_cli_subprocess.py`
- **Prepared tests:** `tests/unit/test_dars_codex_cli_subprocess.py`
- **Revised dispatch harness:** `src/hisys/agents/dars_remote_subscription_dispatch.py`

## Decision

The `DARS-CODEX-CLI-SUBPROCESS-PROMPT-MODE-PREP` row is implemented as a
fixture-tested preparation surface for a future single Codex CLI subprocess
smoke. The checkpoint prepares the exact wrapper shape and runtime-boundary
transport label without running Codex.

The prepared transport remains:

```text
transport_kind = codex_cli_subprocess_prompt_mode
provider_id = codex
adapter_class = codex_subscription
```

`adapter_class=codex_subscription` remains compatible with the current remote
subscription policy allowlist. `transport_kind=codex_cli_subprocess_prompt_mode`
now flows through the dispatch request, executor payload, and single-critic
runtime-boundary writer so a later smoke record can distinguish Codex CLI
subprocess prompt mode from generic injected-executor, SDK, or raw API transport.

## Prepared implementation surface

The new `build_codex_cli_prompt_mode_executor(...)` surface returns the existing
M-DARS-BE-6 executor shape:

```python
Callable[[dict[str, Any]], str]
```

The prepared executor constructs a fixed noninteractive read-only command:

```bash
codex --ask-for-approval never exec \
  --sandbox read-only \
  --cd <controlled-workdir> \
  -- "<redacted bounded DARS critic prompt packet>"
```

The tests use an injected fake subprocess runner. No test invokes the real
`codex` binary.

## Guards prepared in this row

The PREP row pins the following fail-closed guards:

- provider must be `codex`;
- adapter class must be `codex_subscription`;
- transport kind must be `codex_cli_subprocess_prompt_mode`;
- allowed actions must be `advisory_only`;
- mutation and publication flags must be false;
- prompt packet must not contain obvious raw-secret markers;
- command uses `--sandbox read-only` and `--ask-for-approval never`;
- forbidden flags are absent: `--search`, `--full-auto`, `--yolo`,
  `--sandbox danger-full-access`, and
  `--dangerously-bypass-approvals-and-sandbox`;
- subprocess call uses `shell=False`, bounded `timeout`, captured stdout/stderr,
  and environment restricted to `PATH`;
- non-zero exit fails closed as `codex_cli_subprocess_failed`;
- blank stdout fails closed as `codex_cli_subprocess_empty_output`;
- output containing raw-secret markers fails closed as
  `codex_cli_output_not_redacted`.

## Boundaries preserved

This checkpoint does not run Codex and does not write a runtime-boundary record.
The following remain out of scope until a later execution row passes its gates:

- live Codex subprocess invocation;
- Codex SDK import or raw provider API call from Hisys;
- API-key, token, refresh-token, vault, or `Authorization` header lookup by
  Hisys/Ralph;
- provider account configuration;
- web search, browser use, tool/shell delegation requested by the model, file
  mutation, git mutation, publication, deployment, release, PR/issue creation,
  or workspace-write execution;
- `--search`, `--full-auto`, `--yolo`, `--sandbox danger-full-access`, or
  `--dangerously-bypass-approvals-and-sandbox` for the DARS smoke;
- multi-critic panel execution;
- completion-claim upgrade beyond
  `local_fixture_localhost_controlled_advisory_complete`.

## Validation evidence at PREP time

Focused RED was observed before implementation:

```text
PYTHONPATH=src pytest tests/unit/test_dars_codex_cli_subprocess.py -q
-> 9 failed
   ModuleNotFoundError: No module named 'hisys.agents.dars_codex_cli_subprocess'
   TypeError: RemoteSubscriptionDispatchRequest.__init__() got an unexpected keyword argument 'transport_kind'
```

Focused GREEN after implementation:

```text
PYTHONPATH=src pytest tests/unit/test_dars_codex_cli_subprocess.py tests/unit/test_dars_remote_subscription_dispatch.py -q
-> 28 passed
```

## Next safe row

The next row is a human-gated single-smoke decision/checkpoint:

```text
DARS-CODEX-CLI-SUBPROCESS-SINGLE-SMOKE-GATE
```

That row may run at most one Codex CLI subprocess smoke only if the operator
accepts the final command, controlled workdir/instance root, redacted prompt
packet, no-mutation guard, and runtime-boundary record path. If any prerequisite
is missing or Codex requires broader sandbox/search/mutation authority, the row
must stop without running Codex.
