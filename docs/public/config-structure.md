# Hisys Configuration Structure

Hisys uses separate config documents for separate boundaries. A config that records where `/home/cbchoi/me` or `/home/cbchoi/obsidian` lives is a host-local environment registry, not the deployed-wrapper runtime source policy and not the evidence store write-policy file.

## Config roles

| Config | Default path | Responsibility | Must not do |
| --- | --- | --- | --- |
| Environment config | `/home/cbchoi/.config/hisys/environment.yaml` | Records host-local paths for the Hisys tool root, source repo, evidence store, store config, personal vault, and lab vault. | Must not authorize raw evidence writes into vaults. |
| Evidence store config | `/home/cbchoi/.config/hisys/store.yaml` | Records the canonical evidence store root and write safety policy. | Must not point at the Hisys code repo or a personal/lab vault. |
| Deployed runtime config | `/home/cbchoi/.hermes/tools/hisys/config/runtime.json` | Enforces installed-snapshot execution for the deployed wrapper. | Must not point at the live development checkout. |

## Environment config design considerations

The environment config is allowed to know where vaults are. That is different from being allowed to write into them.

Design requirements:

1. Record host-local paths explicitly rather than relying on memory, skill text, or environment variables.
2. Keep `code repo != evidence repo != personal vault` as a validation invariant.
3. Treat `/home/cbchoi/me` and `/home/cbchoi/obsidian` as projection targets, not raw evidence stores.
4. Keep raw evidence writes to any vault forbidden by default.
5. Require human approval for curated Stone/Gem/Jewel projection into a vault.
6. Preserve source repo and tool root paths for traceability only; they must not become evidence store roots.
7. Make status checks side-effect free: no external calls, no vault writes, no mutation.

Example:

```yaml
schema_id: hisys.environment_config
schema_version: 0.1.0
host_id: cbchoi-main
paths:
  hisys_tool_root: /home/cbchoi/.hermes/tools/hisys
  hisys_source_repo: /home/cbchoi/workspaces/sysailab/develop/repos/hisys
stores:
  evidence:
    id: hisys-evidence-store
    root: /home/cbchoi/workspaces/sysailab/research/hisys-evidence-store
    config: /home/cbchoi/.config/hisys/store.yaml
vaults:
  personal:
    id: cbchoi-me
    kind: obsidian
    root: /home/cbchoi/me
    write_policy:
      raw_evidence: forbidden
      curated_projection: approval_required
      default_enabled: false
  lab:
    id: sysailab-obsidian
    kind: obsidian
    root: /home/cbchoi/obsidian
    write_policy:
      raw_evidence: forbidden
      curated_projection: approval_required
      default_enabled: false
projection_targets:
  stone_candidates:
    default_store: evidence
    personal_vault_enabled: false
  approved_stones:
    default_store: evidence
    personal_vault_enabled: false
    require_human_approval: true
```

## CLI

Initialize the host-local registry:

```bash
hisys environment-init \
  --config /home/cbchoi/.config/hisys/environment.yaml \
  --host-id cbchoi-main \
  --hisys-tool-root /home/cbchoi/.hermes/tools/hisys \
  --hisys-source-repo /home/cbchoi/workspaces/sysailab/develop/repos/hisys \
  --evidence-store-root /home/cbchoi/workspaces/sysailab/research/hisys-evidence-store \
  --evidence-store-config /home/cbchoi/.config/hisys/store.yaml \
  --personal-vault-root /home/cbchoi/me \
  --lab-vault-root /home/cbchoi/obsidian
```

Inspect it:

```bash
hisys environment-status \
  --config /home/cbchoi/.config/hisys/environment.yaml \
  --format json
```

`environment-status` returns nonzero and `safe_to_use=false` if:

- the evidence store points to the personal vault;
- the evidence store points to the lab vault;
- the evidence store points to the Hisys source repo;
- the evidence store points to the deployed tool root;
- a vault permits raw evidence writes;
- a vault enables writes by default;
- personal vault Stone projection is enabled without human approval.

## Test cases

The focused test suite is `tests/unit/test_environment_config.py`.

Current covered cases:

1. `environment-init` records personal/lab vault locations while keeping raw evidence writes forbidden.
2. `environment-status` blocks a config where the evidence store root is the personal vault.
3. `environment-status` blocks personal vault projection if human approval is not required.
4. CLI init/status emit machine-readable JSON and do not perform vault writes or external calls.
