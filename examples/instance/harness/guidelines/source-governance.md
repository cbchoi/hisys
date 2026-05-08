# Source Governance Harness Guideline

Traceability: HISYS-T-001, HISYS-T-002, HISYS-NFR-SEC-003, HISYS-NFR-SEC-005.

## Procedure

1. Load source registry entries from `config/source-registry.yaml`.
2. Load web compliance reviews from `config/web-compliance/`.
3. Confirm approved sources have reliability evidence.
4. Confirm web/news collection has compliance evidence.
5. Confirm blocked/suspended/retired/X-class sources are not collectable.

## Pass Criteria

- Hardware fixture is collectable.
- Web fixture is collectable only with matching compliance review.
- Missing compliance review blocks web/news collection.
