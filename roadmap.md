# Hisys Roadmap

This file records product-code roadmap items that are not yet authorized for live implementation. Controlled requirements, design, interface, and test baselines remain governed by the pre-develop package and traceability documents referenced from `README.md`.

## Future governed features

### Real OSS comparison and license adjudication

Goal: extend the current fixture/local approved-OSS comparison adapter into a human-gated workflow that can use real external open-source repositories as comparison references.

Scope to define before implementation:

- approved target OSS repository list and source-of-truth URLs;
- explicit operator authorization for each network fetch or local clone;
- clone/fetch location, retention policy, and cleanup policy;
- LICENSE file capture and full license-text preservation;
- license compatibility/adjudication packet for comparison use;
- provenance records for repository URL, commit/tag, fetch time, and operator approval;
- source-ingestion boundary that avoids copying OSS code into Hisys product artifacts unless separately approved;
- advisory comparison output that stores architecture-level claims, file/source refs, hashes, and license metadata rather than raw source bodies by default.

Safety boundary:

- not part of the current M23 live/local LSP or fixture OSS adapter closure;
- no arbitrary network search, external clone, credential lookup, raw source archival, or legal conclusion is authorized by this roadmap note alone;
- implementation should begin with document-RED tests, deterministic fixtures, and a decision packet before any live repository access.

Related current surfaces:

- `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md`
- `docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md`
- `docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md`
- `src/hisys/operations/oss_comparison_adapter.py`
- `tests/unit/test_oss_comparison_adapter.py`
