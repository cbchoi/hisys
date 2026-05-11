# Hisys as an Agentic AI Tool

This manual describes Hisys as a tool layer for agents such as Hermes, Claude Code,
Codex, OpenCode, and future MCP-compatible assistants.

Hisys is not intended to be a competing chat agent. Its role is to give agents a
safe, governed investigation tool that can collect public evidence, preserve
traceability, run review gates, and return local artifacts that a human can audit.

## What "browser support" means

In the public beta docs, **browser support** means:

```text
Hisys has an optional Playwright Chromium dependency and a governed
playwright_read_only connector for collecting visible text from approved public
web pages.
```

It does **not** mean:

```text
Hisys is itself a browser UI
Hisys should replace Hermes' browser tool
Hisys can browse freely without approval
Hisys can log in, post, submit forms, upload, purchase, bypass CAPTCHA, or evade bot checks
```

For agentic AI use, the better phrase is:

```text
agent-facing governed browser evidence tool
```

## Target architecture

```text
Hermes / agentic AI
  -> calls Hisys tool interface
    -> Hisys validates profile/config/safety gates
    -> Hisys optionally performs read-only public browser acquisition
    -> Hisys writes evidence, provenance, review, DARS, and final artifacts
  -> Hermes reads the artifacts and explains/acts only within approved boundaries
  -> human decides any consequential/public action
```

## Current integration interface

Today, Hisys is usable by agents through the CLI. An agent like Hermes can call:

```bash
hisys validate-public-browser-profile ...
hisys public-browser-readiness ...
hisys public-browser-run ...
```

This is already agent-usable because agents can invoke CLI commands and read the
resulting JSON/Markdown artifacts.

## Recommended future interface

For a first-class agent tool, add an MCP server around the same Hisys functions.
Hermes can connect to MCP servers at startup and expose their tools directly as
LLM-callable tools.

Recommended tool set:

| MCP tool | Purpose | Live network? |
|---|---|---:|
| `hisys_validate_public_browser_profile` | Validate public beta profile | No |
| `hisys_public_browser_readiness` | Check config/profile/import readiness | No |
| `hisys_public_browser_run` | Run governed public browser chain | Yes, only after gates |
| `hisys_get_run_summary` | Read public run summary artifact | No |
| `hisys_show_artifact` | Read a specific JSON/Markdown artifact by safe ref | No |
| `hisys_list_run_artifacts` | List artifacts for a date/request id | No |

Optional later tools:

| MCP tool | Purpose |
|---|---|
| `hisys_review_browser_investigation` | Manual gate-by-gate Chief Editor readiness review |
| `hisys_request_browser_dars_review` | Advisory DARS/Devil review package |
| `hisys_resolve_browser_dars_revisions` | Deterministic revision gate |
| `hisys_final_review_browser_investigation` | Final bounded Chief Editor acceptance |

## Why MCP is the right shape

CLI is good for development and local operations. MCP is better for agents
because:

1. Tools have explicit JSON schemas.
2. Hermes can discover the tools at startup.
3. Tool names appear directly to the LLM.
4. Inputs/outputs can be constrained and audited.
5. Hisys can remain the governance boundary while Hermes remains the planner.

## Agent boundary contract

A Hisys tool should always return or persist these boundary fields when relevant:

```json
{
  "external_call_made": false,
  "mutation_performed": false,
  "publication_or_live_action_approved": false,
  "human_approval_required_for_consequential_use": true
}
```

For the browser acquisition stage only, `external_call_made` may become `true`
after explicit approval/env/config/domain gates pass. Mutation still remains
`false`.

## Recommended Hermes integration flow

An operator asks Hermes:

```text
Use Hisys to investigate these approved public URLs and produce a governed review package.
```

Hermes should then call Hisys tools in this order:

```text
1. hisys_validate_public_browser_profile
2. hisys_public_browser_readiness
3. hisys_public_browser_run
4. hisys_get_run_summary
5. hisys_list_run_artifacts and hisys_show_artifact for final Chief Editor review if needed
```

Hermes should answer the user with:

```text
- run status
- report paths
- evidence sufficiency / blockers
- final Chief Editor decision
- explicit statement that no publication/live action was approved
```

## Example Hermes-facing CLI flow today

Until MCP tools are added, Hermes can use the CLI:

```bash
export HISYS_INSTANCE="$PWD/.runtime/public-beta-demo"
export HISYS_SOURCE_CONFIG="$HISYS_INSTANCE/config/public-source-connectors.yaml"
mkdir -p "$HISYS_INSTANCE/config"

hisys validate-public-browser-profile \
  --profile examples/instance/config/profiles/public-browser.yaml

hisys public-browser-readiness \
  --instance "$HISYS_INSTANCE" \
  --config "$HISYS_SOURCE_CONFIG" \
  --profile examples/instance/config/profiles/public-browser.yaml \
  --date 20260511

export HISYS_ALLOW_BROWSER_SMOKE=1

hisys public-browser-run \
  --instance "$HISYS_INSTANCE" \
  --config "$HISYS_SOURCE_CONFIG" \
  --profile examples/instance/config/profiles/public-browser.yaml \
  --date 20260511 \
  --request-id HISYS-REQ-PUBLIC-DEMO-001 \
  --topic "approved public evidence investigation" \
  --user-opinion "Hermes requested governed Hisys evidence collection." \
  --approval-ref APPROVAL-PUBLIC-BETA-DEMO-001 \
  --follow-links \
  --max-follow-links-per-source 2 \
  --source-url https://example.com/page-a \
  --source-url https://example.org/page-b
```

## Proposed MCP server implementation plan

### Phase A: Thin wrapper MCP server

Create a small server that shells out to the existing `hisys` CLI and returns
safe JSON outputs. This avoids changing Hisys internals first.

Suggested path:

```text
src/hisys/mcp/server.py
```

Suggested command:

```bash
python -m hisys.mcp.server
```

Hermes config example:

```yaml
mcp_servers:
  hisys:
    command: "python"
    args: ["-m", "hisys.mcp.server"]
    timeout: 300
```

Hermes would then expose tools with names like:

```text
mcp_hisys_validate_public_browser_profile
mcp_hisys_public_browser_readiness
mcp_hisys_public_browser_run
mcp_hisys_get_run_summary
mcp_hisys_list_run_artifacts
mcp_hisys_show_artifact
```

### Phase B: Native Python API tools

After the wrapper is stable, move from shelling out to calling Hisys Python
functions directly. This reduces process overhead and makes structured errors
cleaner.

### Phase C: Multi-agent orchestration

Add explicit agent orchestration helpers:

```text
hisys_create_investigation_request
hisys_attach_agent_context
hisys_record_agent_boundary
hisys_read_review_package
```

These let Hermes and other agents treat Hisys as a governed evidence memory and
review substrate.

## Design principle

Hisys should be the **governed tool substrate** for agents:

```text
Hermes thinks/plans/orchestrates.
Hisys investigates/records/reviews/gates.
Human approves consequential action.
```

That is the clean separation.
