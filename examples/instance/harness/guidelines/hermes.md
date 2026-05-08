# Hermes Harness Guideline

Traceability: HISYS-D-016, HISYS-T-005A, HISYS-DATA-005.

## Purpose

Validate Hermes as a controlled hierarchical collection source within
preapproved collection-only scope.

## Procedure

1. Confirm source ID is listed in `config/hermes-scope.yaml`.
2. Create/read Markdown boundary records under
   `runtime-boundary/hermes/<YYYYMMDD>/<campaign_id>/`.
3. Preserve user input, prompt/query, tool output, and boundary record refs.
4. Build HermesCollectionTrace records under `data/hermes-traces/<YYYYMMDD>/`.
5. Prohibit live notification, software trigger, public posting, credential
   handling, paywall/login/CAPTCHA bypass, and access-control bypass.

## Pass Criteria

- Boundary refs match schema path convention.
- Hermes trace links raw observation refs and audit event refs.
- All actions remain collection-only.
