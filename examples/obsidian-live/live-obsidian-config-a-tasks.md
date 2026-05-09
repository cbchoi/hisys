# Live-Obsidian-Config-A scaffold tasks

This task scaffold reflects the Claude Code architecture review and keeps the
next implementation fixture-only. There are no real vault writes.

## Increment A1: planner-only vault boundary

- Add `hisys vault-plan --dry-run`.
- It computes topic/group/investigation paths from fixture config only.
- It writes a planner artifact with `vault_write_attempted=false`,
  `external_call_made=false`, and `mutation_performed=false`.
- It rejects path traversal, absolute durable refs, invalid IDs, and overlong
  paths.

## Increment A2: vault validator

- Add `hisys vault-validate`.
- It validates `registry.json`, `topics/INDEX.json`, `groups/INDEX.json`,
  `topic-manifest.json`, `investigation-manifest.json`, `runtime-index.json`,
  `attachment-index.json`, and gatekeeper decision artifacts.
- It operates on `tests/fixtures/vault/` or another explicit fixture root, not on
  `/home/cbchoi/obsidian` during CI.

## Increment A3: gatekeeper schema and scorer

- Add schema skeletons for Topic Gatekeeper decisions.
- Require evidence refs for each active score dimension.
- Reject `merge_with_existing_topic`, `same_as_existing_topic`, and
  `split_topic_recommended` when an approval ref is required but absent.
- Keep group operations overlay-only.

## Increment A4: memo ontology templates

- Add templates for topic, investigation, source, evidence, quote, claim,
  registry, ledger, summary, gate, synthesis, decision, and gatekeeper-decision
  notes.
- Use `type` and `phase` frontmatter fields rather than phase tags.
- Treat Obsidian wikilinks as human-navigation projections only; structured
  links are the governance record.

## Full gate

```bash
python3 -m pytest
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py --json .
git status --short --branch
```
