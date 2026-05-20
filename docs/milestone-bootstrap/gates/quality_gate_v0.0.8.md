# Quality Gate v0.0.8

M21.2 implementation may start only if:

- Current repo state is clean before RED test edits.
- M21.1 reporter tests remain green.
- The first M21.2 behavior starts with a RED CLI smoke.
- The CLI wrapper does not add live/external access, credential use, process spawning, publication, or approval authority.
- Final validation runs focused traceability/domain CLI tests, DARS focused regression, traceability validator, secret scan, and `git diff --check`.
