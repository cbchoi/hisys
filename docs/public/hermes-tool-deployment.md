# Deploy Hisys as a Hermes Tool

This guide installs a controlled Hermes-side wrapper for Hisys under a stable tool directory such as:

```text
~/.hermes/tools/hisys
```

The deployment is intentionally CLI-first. It does **not** require MCP and does not mutate Hermes configuration automatically. The script writes a wrapper, manifest, public browser profile copy, runtime directory, and channel configuration snippet for human review. Installs are staged in a sibling temporary directory and then renamed into place so failed writes do not leave a partial tool tree.

The wrapper runs from an immutable deployment snapshot under `releases/<release_id>/source`, exposed through `releases/current/source`. It does **not** execute the live development checkout directly; this keeps uncommitted work, partial edits, or branch switches in the source repository from changing the deployed Hermes tool unexpectedly.

## Command

From the Hisys repository:

```bash
cd /home/cbchoi/workspaces/sysailab/develop/repos/hisys

python3 -m hisys.cli.main deploy-hermes-tool \
  --source-root /home/cbchoi/workspaces/sysailab/develop/repos/hisys \
  --target ~/.hermes/tools/hisys \
  --channel-id 1502110114704916501 \
  --channel-name "develop / Hisys" \
  --force
```

If using the project environment:

```bash
uv run --extra browser python -m hisys.cli.main deploy-hermes-tool \
  --source-root /home/cbchoi/workspaces/sysailab/develop/repos/hisys \
  --target ~/.hermes/tools/hisys \
  --channel-id 1502110114704916501 \
  --channel-name "develop / Hisys" \
  --force
```

## Installed layout

```text
~/.hermes/tools/hisys/
  bin/hisys                         # executable wrapper
  manifest.json                     # machine-readable deployment record
  README.md                         # operator note
  channel-prompt.md                 # prompt text for the target channel/thread
  hermes-channel-snippet.yaml       # config snippet for ~/.hermes/config.yaml
  config/public-browser.yaml        # copied public browser profile
  runtime/                          # suggested ad-hoc runtime root
  docs/                             # reserved for future tool-local docs
  releases/<release_id>/source/      # immutable source snapshot for this deployment
  releases/current -> <release_id>   # stable pointer used by the wrapper
```

The wrapper runs Hisys from the deployed snapshot, not the live development checkout. It unsets Hermes' active `VIRTUAL_ENV` before invoking `uv` so the snapshot project environment is selected cleanly. It prefers:

```bash
uv run --project "$HISYS_SOURCE_ROOT" --extra browser python -m hisys.cli.main "$@"
```

and falls back to:

```bash
PYTHONPATH="$HISYS_SOURCE_ROOT/src" python3 -m hisys.cli.main "$@"
```

## Deployment status, report, and rollback

Inspect the currently installed tool snapshot:

```bash
hisys deployment-status \
  --target /home/cbchoi/.hermes/tools/hisys \
  --format json
```

Build a governed deploy report that can be attached to CI artifacts or operator
approval packages:

```bash
hisys build-hermes-deploy-report \
  --target /home/cbchoi/.hermes/tools/hisys \
  --validation pytest=passed \
  --validation traceability=passed \
  --validation secret_scan=passed \
  --output /tmp/hisys-hermes-tool-deploy-report.json \
  --format json
```

The report preserves the boundary that CI can validate deployability but does not
implicitly approve host installation:

```text
promotion_allowed=false
human_approval_required_for_host_install=true
external_call_made=false
mutation_performed=false
publication_or_live_action_approved=false
```

Rollback moves only the local `releases/current` pointer and rewrites the top
manifest with rollback provenance. Use the previous release by default:

```bash
hisys rollback-hermes-tool \
  --target /home/cbchoi/.hermes/tools/hisys \
  --previous \
  --format json
```

Or choose a specific release id from `deployment-status`:

```bash
hisys rollback-hermes-tool \
  --target /home/cbchoi/.hermes/tools/hisys \
  --to-release <release_id> \
  --format json
```

## CI/CD

The deployment path is covered by GitHub Actions:

- `.github/workflows/test.yml` runs `Hisys CI` on pushes and pull requests.
- `.github/workflows/deploy-hermes-tool.yml` runs after successful `Hisys CI`
  completion, and can also be started manually with `workflow_dispatch`.
- The deploy workflow performs release validation, deploys a snapshot into the CI
  runner workspace, verifies that the wrapper does not point at the live checkout,
  and smoke-tests the deployed wrapper.

The deploy workflow is intentionally side-effect bounded in CI: it validates the
Hermes tool deployment artifact and wrapper layout inside the runner temporary
directory. It does not mutate a production `~/.hermes/config.yaml` or publish
external artifacts. Production installation remains an operator action using the
same `deploy-hermes-tool` command after CI is green.

Local equivalent:

```bash
python -m pytest -q
python scripts/validate_traceability.py
python scripts/scan_secrets.py
git diff --check
python -m hisys.cli.main deploy-hermes-tool \
  --source-root "$PWD" \
  --target /tmp/hisys-hermes-tool \
  --channel-id 1502110114704916501 \
  --channel-name "develop / Hisys" \
  --force
python scripts/verify_hermes_tool_deploy.py \
  --tool-root /tmp/hisys-hermes-tool \
  --upstream-source-root "$PWD" \
  --expect-source-commit "$(git rev-parse HEAD)"
/tmp/hisys-hermes-tool/bin/hisys --version
```

## Verify the deployed wrapper

```bash
~/.hermes/tools/hisys/bin/hisys validate-public-browser-profile \
  --profile ~/.hermes/tools/hisys/config/public-browser.yaml
```

Expected result:

```text
public browser profile: valid ... transport_kind=playwright_live
```

## Bind to a Discord channel/thread

Open the generated snippet:

```bash
cat ~/.hermes/tools/hisys/hermes-channel-snippet.yaml
```

Reconcile it into the `discord:` section of:

```bash
hermes config edit
```

Then validate and restart:

```bash
hermes config check
hermes gateway restart
hermes gateway status
```

## Boundary

The deployment is a controlled local tool wrapper only. It does not approve publication, posting, outreach, mutation, credential use, login, access-control bypass, CAPTCHA bypass, or proxy rotation. Hisys runs remain governed and should report artifact refs, final decision, blockers, and human-reviewed-use limits.
