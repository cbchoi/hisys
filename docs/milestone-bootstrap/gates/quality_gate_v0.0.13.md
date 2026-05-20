# Quality Gate v0.0.13

## Gate result

Pass.

## Required checks

- Structural parse of v0.0.13 YAML/JSON artifacts.
- Focused DARS runtime/config/dispatch/panel regression.
- Traceability validator.
- Secret scan.
- `git diff --check`.
- Local commit only after all checks pass.

## Boundary checks

- `live_model_call_authorized=false`
- `live_external_action_authorized=false`
- `credential_lookup_authorized=false`
- `remote_push_authorized=false`
