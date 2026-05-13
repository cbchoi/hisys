# Hisys Evidence Store and Stone Promotion

Hisys evidence/search outputs should be managed in a dedicated evidence store, not in the Hisys code repository and not directly in a personal Obsidian vault.

Recommended local store root:

```text
/home/cbchoi/workspaces/sysailab/research/hisys-evidence-store
```

Recommended config path:

```text
/home/cbchoi/.config/hisys/store.yaml
```

## Boundaries

| Boundary | Purpose |
|---|---|
| Hisys code repo | Source code, tests, schemas, controlled docs, fixtures |
| Hisys evidence store | Search artifacts, source evidence, runtime-boundary records, reports, Stone candidates, approved Stones |
| Personal vault | Optional human-selected projection only; raw evidence is not copied by default |

The store config defaults to:

- `allow_personal_vault_write: false`
- `require_approval_for_write: true`
- `personal_vault_projection.enabled: false`
- `git.auto_push: false`

## Initialize and inspect

```bash
hisys evidence-store-init \
  --config /home/cbchoi/.config/hisys/store.yaml \
  --root /home/cbchoi/workspaces/sysailab/research/hisys-evidence-store \
  --store-id hisys-evidence-store
```

```bash
hisys evidence-store-status \
  --config /home/cbchoi/.config/hisys/store.yaml \
  --format json
```

`evidence-store-status` blocks unsafe roots such as `/home/cbchoi/me` unless a separate policy explicitly enables personal vault writes.

## Import investigation artifacts

Imports are approval-gated when `--write` is used:

```bash
hisys evidence-store-import-investigation \
  --config /home/cbchoi/.config/hisys/store.yaml \
  --topic-id TOPIC-20260513-DAEJEON-AI-CAMP \
  --topic-slug daejeon-ai-convergence-camp \
  --investigation-id INV-20260513-001 \
  --date 2026-05-13 \
  --include /tmp/hisys-ai융합실/domain-request.json \
  --include /tmp/hisys-ai융합실/plan.txt \
  --include /tmp/hisys-ai융합실/idea-ranking-report.md \
  --approval-ref APPROVAL-HISYS-STORE-20260513-001 \
  --write
```

The command writes into the topic-first layout:

```text
topics/<topic_id>__<topic_slug>/investigations/<date>/<investigation_id>/
  input/
  sources/
  runtime-boundary/
  reports/
  investigation-manifest.json
```

## Stone candidates and promotion

Stone candidates are read-only proposals:

```bash
hisys evidence-stone-candidates \
  --config /home/cbchoi/.config/hisys/store.yaml \
  --topic-id TOPIC-20260513-DAEJEON-AI-CAMP \
  --topic-slug daejeon-ai-convergence-camp \
  --investigation-id INV-20260513-001 \
  --output /tmp/hisys-stone-candidates.json
```

Promotion is separate and approval-gated:

```bash
hisys evidence-promote-stone \
  --config /home/cbchoi/.config/hisys/store.yaml \
  --candidate /tmp/hisys-stone-candidates.json \
  --candidate-id STONE-CAND-002 \
  --approval-ref APPROVAL-HISYS-STONE-20260513-001 \
  --write
```

Approved Stones are written under:

```text
topics/<topic_id>__<topic_slug>/canonical/stones/
```

A Stone is a governed projection of a source/evidence artifact. It is not a final Gem/Jewel synthesis. Raw evidence remains in the evidence store, and personal vault projection remains disabled unless a separate approval path is implemented.
