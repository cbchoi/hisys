# Obsidian Live Research Layout

Status: Live-Obsidian-Config-A scaffold and design boundary. This document reflects
Claude Code review reflections from the read-only architecture review of the Hisys
Obsidian live-research structure and Topic Gatekeeper.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023, Live-H/I/J/K/L.

## Purpose

Hisys live research data must be usable by humans in Obsidian and by LLM agents
through small, predictable entry points. Raw data, intermediate data, PDFs, HTML
snapshots, JSON payloads, datasets, and other attached files are managed in the
Obsidian vault. Hisys still preserves explicit runtime-boundary provenance,
evidence-vs-interpretation separation, and approval gates.

Live-Obsidian-Config-A is a **planner-only dry-run boundary**. It scaffolds the
layout, manifests, ontology, and Topic Gatekeeper decisions before any controlled
writer is allowed to modify the real vault. There are **no real vault writes** in
this increment, and future `vault-plan --dry-run` artifacts must record
`vault_write_attempted=false`, `external_call_made=false`, and
`mutation_performed=false`.

## Claude Code review reflections

The reviewed design is usable, but the scaffold must encode these corrections:

1. `registry.json is the global entry point` for agents; agents should not start
   by recursively scanning the vault.
2. Hisys repository schemas are authoritative; Obsidian `_shared/schemas/` holds
   only vendored schema snapshots with content hashes.
3. Runtime-boundary authority must be explicit. Obsidian may hold investigation
   workspace records, promoted refs, or projections, but Hisys-controlled runtime
   artifacts remain governed by Hisys boundary rules and hashes.
4. `type`, `phase`, tags, and links are different axes. In particular,
   **phase is structured metadata, not a tag**.
5. **Obsidian wikilinks are human-navigation projections**. Governance links use
   structured `links` fields with `relation`, `ref`, and optional hash fields.
6. Topic Gatekeeper scoring must be **evidence-citing gatekeeper scoring**: no
   score may drive a decision unless it cites source registry/topic/claim/group
   refs.
7. Merge and split are canonical-identity mutations and require explicit human
   approval records. A merge is non-destructive.

## Agent-efficient canonical layout

Use a topic-first layout, lowercase internal folders, and small index files:

```text
91 Hisys/Live Research/
  README.md
  registry.json
  registry.md

  _shared/
    templates/
    schemas/
    policies/
    ontology/

  groups/
    INDEX.json
    GROUP-YYYYMMDD-XXXXXX__group-slug/
      group-config.yaml
      group-manifest.json
      index.md

  topics/
    INDEX.json
    TOPIC-YYYYMMDD-XXXXXX__topic-slug/
      topic-config.yaml
      topic-manifest.json
      index.md
      MERGED_INTO.md        # only for non-destructive merge tombstones

      canonical/
        sources/
          source-index.json
          SRC-*.md
        evidence/
          evidence-index.json
          EVID-*.md
          QUOTE-*.md
        claims/
          claim-index.json
          CLAIM-*.md
          REGISTRY-*.md
          LEDGER-*.md
          SUMMARY-*.md
          GATE-*.md
        synthesis/
          synthesis-index.json
          SYN-*.md
        decisions/
          decision-index.json
          DECISION-*.md
        attachments/
          attachment-index.json
          blobs/
            ab/
              cd/
                <sha256>.<ext>

      investigations/
        INDEX.json
        YYYY-MM-DD/
          INV-YYYYMMDD-HHMM-XXXX/
            investigation-config.yaml
            investigation-manifest.json
            index.md

            input/
              request.md
              request.json

            work/
              source-notes/
              evidence-notes/
              claim-notes/
              synthesis-notes/
              decision-notes/

            attachments/
              attachment-index.json
              blobs/

            runtime-boundary/
              runtime-index.json
              topic-gatekeeper/
              source-connectors/
              investigations/
              dars/
              chief-editor/

            reports/
              report-index.json
              run-summaries/
```

The date partition under `investigations/YYYY-MM-DD/` preserves recurring
investigation readability. `investigations/INDEX.json` is mandatory so LLM agents
can route without scanning date folders.

## Entry-point files

Agents should follow this bounded path:

```text
registry.json
  -> topics/INDEX.json
  -> topics/<TOPIC>/topic-manifest.json
  -> topics/<TOPIC>/investigations/INDEX.json
  -> topics/<TOPIC>/investigations/<date>/<INV>/investigation-manifest.json
  -> runtime-boundary/runtime-index.json
  -> attachments/attachment-index.json
```

`topic-manifest.json`, `investigation-manifest.json`, `runtime-index.json`, and
`attachment-index.json` are required entry points. Binary folders should never be
used as primary indexes.

## Topic and group policy

canonical topics stay under topics/. groups are overlays, not physical
parents. A group may reference many topics, and a topic may belong to multiple
groups.

Topic identifiers:

```text
TOPIC-YYYYMMDD-XXXXXX__topic-slug
GROUP-YYYYMMDD-XXXXXX__group-slug
INV-YYYYMMDD-HHMM-XXXX
```

Slugs are lowercase ASCII kebab-case. The readable title, including Korean title
text, belongs in `topic-config.yaml` and `topic-manifest.json`.

## Topic Gatekeeper

The Topic Gatekeeper runs before creating or reusing a topic. It reads the
registry and candidate manifests, then records an advisory decision before any
canonical identity mutation.

Decision actions:

```text
new_topic
related_to_existing_topic
group_with_existing_topic
same_as_existing_topic
merge_with_existing_topic
split_topic_recommended
needs_human_clarification
```

Approval policy:

| Action | Approval rule |
|---|---|
| `new_topic` | auto-record allowed |
| `related_to_existing_topic` | auto-record allowed |
| `group_with_existing_topic` | overlay-only; policy-dependent approval |
| `same_as_existing_topic` | requires approval unless policy allows very high confidence auto-route |
| `merge_with_existing_topic` | always requires human approval |
| `split_topic_recommended` | always requires human approval and split plan |
| `needs_human_clarification` | requires owner/status and should not mutate anything |

Every decision must cite evidence refs for each active score dimension:

```text
semantic_similarity
source_overlap
claim_overlap
group_affinity
temporal_proximity
governance_compatibility
```

A gatekeeper decision with a score but no `evidence_refs` is invalid.

## Merge, group, and split

- Grouping is overlay-only: update group manifests and topic `group_refs`; do not
  move canonical topic folders.
- Merge is non-destructive: keep the old topic folder, write a `MERGED_INTO.md`
  tombstone, set `status=merged`, and set `merged_into` to the canonical topic.
- Split is staged: create a split plan, require human approval, create new topic
  folders, copy refs rather than binary files, then mark the original topic with
  `split_into` metadata.
- Never delete topic folders during merge or split.

## Memo ontology

Use controlled frontmatter fields:

```yaml
type: hisys/claim-coverage-gate
phase: live-k
topic_uid: TOPIC-20260509-7F3A92
investigation_id: INV-20260509-2101-A8C4
governance:
  advisory_only: true
  conditional: true
  external_call_made: false
  mutation_performed: false
links:
  - relation: gates_claims
    refs:
      - canonical/claims/CLAIM-REQ-001.md
```

Recommended `type` values:

```text
hisys/topic-group
hisys/topic
hisys/investigation
hisys/source
hisys/attachment
hisys/evidence
hisys/quote
hisys/claim
hisys/recommendation-claim-registry
hisys/claim-evidence-ledger
hisys/claim-evidence-summary
hisys/claim-coverage-gate
hisys/synthesis
hisys/decision
hisys/gatekeeper-decision
hisys/report
```

Use tags for navigation and domain labels only, for example
`hisys/live-research`, `research/devs`, or `research/digital-twin`. Do not encode
pipeline phase as tags such as `hisys/live-k`; use `phase: live-k`.

## Link relation policy

Structured links are primary. Wiki links may be generated for human navigation,
but they are not the governance record.

Allowed relation vocabulary starts with:

```text
belongs_to_group
belongs_to_topic
part_of_investigation
derived_from_source
has_attachment
quotes_source
supports_claim
contradicts_claim
needs_evidence_for_claim
summarizes_ledgers
gates_claims
feeds_live_k_coverage_gate
reviewed_by_dars
reviewed_by_chief_editor
decided_by_gatekeeper
merged_into
merged_from
split_into
split_from
related_topics
promoted_from_investigation
tombstoned_by
```

Future validators should type-check relations, e.g. reject a quote note claiming
`belongs_to_topic` with a group target.

## Attachment policy

Use content-addressed attachment blobs. Attachments are immutable; a changed file
is a new hash and a new attachment-index entry.

```text
attachments/
  attachment-index.json
  blobs/
    ab/
      cd/
        abcdef...<sha256>.pdf
```

Raw/intermediate files are investigation-local first. Durable topic knowledge is
promoted to `canonical/` only by an explicit governed promotion step. Heavy
attachments remain out of Git by default unless the user explicitly enables
tracking.

## Runtime-boundary policy

Runtime-boundary records preserve Hisys lineage and safety fields:

```json
{
  "external_call_made": false,
  "mutation_performed": false,
  "advisory_only": true
}
```

Live-Obsidian-Config-A does not decide final runtime authority. It scaffolds the
rule that any vault projection of runtime evidence must preserve vault-relative
refs plus content hashes and must not override Hisys source policy, connector
policy, output schemas, approval gates, external-call policy, or mutation policy.

## Live-Obsidian-Config-A planned tasks

The next implementation should be scaffolded as fixture-only work:

1. Add `hisys vault-plan --dry-run` to compute paths and write a planner report
   with `vault_write_attempted=false` and no real vault writes.
2. Add `hisys vault-validate` to validate fixture vault manifests, indexes,
   relation types, ID formats, and human approval gates.
3. Add schema skeletons for registry, group/topic/investigation manifests,
   attachment indexes, runtime indexes, and gatekeeper decisions.
4. Add tests ensuring no path resolves under `/home/cbchoi/obsidian` during CI;
   use fixture roots only.
5. Add tests rejecting unknown link relations, missing evidence refs in
   gatekeeper scores, missing merge approval refs, path traversal, overlong paths,
   and invalid topic/group/investigation IDs.

## Live-Obsidian-Config-B implementation status

`hisys.config.obsidian_live.build_vault_plan` and `hisys vault-plan --dry-run`
implement the first fixture-only planner. The command reads a registry, computes
canonical topic and recurring investigation paths, writes only
`runtime-boundary/obsidian-live/<YYYYMMDD>/vault-plan-*.json` plus run-summary
reports, and records `vault_write_attempted=false`, `external_call_made=false`,
and `mutation_performed=false`. It rejects unsafe submitted titles before path
construction and does not create any `91 Hisys/` vault content.

## Live-Obsidian-Config-C implementation status

`hisys.config.obsidian_live.validate_vault_manifests` and `hisys vault-validate`
validate fixture-only registry, topic-manifest, investigation-manifest, and
Topic Gatekeeper decision artifacts. The validator rejects missing evidence refs
on gatekeeper scores, unsafe vault-relative refs, invalid topic IDs/slugs, and
merge/split decisions without required approval refs. Validation writes only
run-summary reports and preserves `vault_write_attempted=false`,
`external_call_made=false`, and `mutation_performed=false`.

## Live-Obsidian-Config-D implementation status

`hisys.config.obsidian_live.build_vault_template_plan` and `hisys
vault-template-plan` produce runtime-local template planning artifacts for the
memo ontology. The plan lists controlled note `type` values, required
frontmatter fields, allowed relation vocabulary, and required index files. It
keeps `phase` as structured metadata, treats structured links as the governance
record, and treats Obsidian wikilinks as human-navigation projections only. The
command writes no real vault templates and records `vault_write_attempted=false`,
`external_call_made=false`, and `mutation_performed=false`.

## Live-Obsidian-Config-E implementation status

The vault manifest validator now hardens the Claude-reviewed Obsidian contract
before any vault writer exists. It uses the same controlled relation vocabulary
advertised by `vault-template-plan` and rejects unknown structured link
relations, invalid `GROUP-YYYYMMDD-XXXXXX` group IDs, invalid
`INV-YYYYMMDD-HHMM-XXXX` investigation/run IDs, and overlong vault-relative
refs. These checks apply to registry, topic-manifest, investigation-manifest,
and gatekeeper decision fixtures while still writing only validation reports and
keeping `vault_write_attempted=false`, `external_call_made=false`, and
`mutation_performed=false`.

## Live-Obsidian-Config-F implementation status

`hisys.config.obsidian_live.apply_vault_plan_to_fixture` and `hisys
vault-apply` add a controlled local writer for explicit fixture vault roots. The
command materializes vault-plan projections only when an approval ref is supplied
and `--fixture-vault-only` is set. It blocks the real `/home/cbchoi/obsidian`
vault path, writes apply reports under the Hisys runtime boundary, records
`real_obsidian_vault_write_performed=false`, and makes no external calls. This is
a harness writer, not approval to mutate the user's live Obsidian vault.

## Live-Obsidian-Config-G implementation status

`hisys.config.obsidian_live.build_topic_identity_transition_plan` and `hisys
vault-topic-transition-plan` plan non-destructive canonical topic identity
transitions. `merge_with_existing_topic` and `split_topic_recommended` require
approval refs, never delete source topic folders, produce tombstone refs such as
`MERGED_INTO.md` or `SPLIT_INTO.md`, and preview topic-manifest updates. The
command writes only runtime-boundary plan artifacts and records
`real_obsidian_vault_write_performed=false`.

## Live-Obsidian-Config-H implementation status

`hisys.config.obsidian_live.validate_fixture_vault_roundtrip` and `hisys
vault-roundtrip-validate` close the fixture writer loop by checking that a
`vault-plan` projection applied by `vault-apply` is exactly reflected in the
fixture vault root. The validator detects missing planned files, unexpected
fixture files, invalid projection metadata, and apply-report/fixture drift while
recording `real_obsidian_vault_write_performed=false` and making no external
calls.

## Live-Obsidian-Config-I implementation status

`hisys.config.obsidian_live.build_live_vault_preflight_report` and `hisys
vault-live-preflight` inspect a candidate live Obsidian vault without writing to
it. The preflight checks the vault root, `.obsidian`, a Git repository marker,
and the heavy-attachment ignore policy. It records `write_probe_performed=false`,
`live_write_enabled=false`, and `real_obsidian_vault_write_performed=false`; a
passing preflight only means the next approval-package gate can be prepared.

## Live-Obsidian-Config-J implementation status

`hisys.config.obsidian_live.build_live_vault_approval_package` and `hisys
vault-live-approval-package` generate a human approval package for a future live
vault write without enabling one. The package enumerates planned vault-relative
writes, required human/clean-git/rollback approvals, rollback strategy, and final
gates (`vault-live-preflight`, `vault-roundtrip-validate`, and `git status
--short`) while recording `live_write_enabled=false` and
`real_obsidian_vault_write_performed=false`.

## Live-Obsidian-Config-K implementation status

`hisys.config.obsidian_live.build_live_vault_write_gate_report` and `hisys
vault-live-write-gate` evaluate final live-write preconditions without
implementing a writer. The gate checks approval-package evidence, approval ref,
clean-git status, and explicit enablement, but even the fully signaled path stays
blocked with `reason_code=live_writer_not_implemented`,
`implementation_boundary=gate_only_no_writer`, `live_write_enabled=false`, and
`real_obsidian_vault_write_performed=false`.

## Live-Obsidian-Config-L implementation status

`hisys.config.obsidian_live.build_live_vault_transaction_plan` and `hisys
vault-live-transaction-plan` transform the approval package plus final write gate
report into a non-executable transaction manifest. The manifest enumerates
planned vault-relative operations, rollback hints, and placeholder pre/post hashes
(`not_read_no_live_write` / `not_written_no_live_write`) without reading from or
writing to the live vault. It records
`implementation_boundary=transaction_manifest_only_no_writer`,
`live_write_enabled=false`, and `real_obsidian_vault_write_performed=false`.

## Live-Obsidian-Config-M implementation status

`hisys.config.obsidian_live.rehearse_live_vault_transaction_in_fixture` and
`hisys vault-live-transaction-rehearse` rehearse the non-executable transaction
manifest against an explicit fixture vault only. The rehearsal requires an
approval ref and `--fixture-vault-only`, refuses `/home/cbchoi/obsidian`, writes
fixture projection payloads containing source transaction/operation metadata, and
records `fixture_projection_only=true` and
`real_obsidian_vault_write_performed=false`.

## Live-Obsidian-Config-N implementation status

`hisys.config.obsidian_live.apply_live_vault_transaction` and `hisys
vault-live-transaction-apply` implement the final approval-gated transaction
writer boundary. The command requires an approval ref, an explicit write-enable
switch, and operator-confirmed clean Git status. It refuses `/home/cbchoi/obsidian`
unless `--allow-real-obsidian-vault` is supplied. Unit tests exercise temporary
candidate vault roots only; this Ralph run did not execute the command against the
real Obsidian vault.

## Live-Obsidian-Config-O implementation status

`hisys.config.obsidian_live.build_live_obsidian_config_status_report` and `hisys
vault-live-config-status` produce the completion gate report for Live-Obsidian-
Config. The report records A through O as complete, `open_stage_count=0`, and
`real_obsidian_vault_write_performed=false`. It is a runtime-boundary status
artifact, not an additional vault writer.

## Topic-Gatekeeper implementation status

`hisys.config.obsidian_live.build_topic_gatekeeper_decision` and `hisys
vault-topic-gatekeeper` produce a read-only, evidence-citing topic routing
decision from a proposed topic and registry. The completed sequence includes
approval packaging, transaction planning, fixture-only rehearsal, and completion
status helpers. It preserves the no-live-default boundary:
`external_call_made=false`, `mutation_performed=false` for decision/planning, and
`real_obsidian_vault_write_performed=false` for all tests and default artifacts.

## Obsidian Evidence Promotion-A implementation status

`hisys.config.obsidian_live.build_obsidian_evidence_promotion_plan` and `hisys
vault-evidence-promotion-plan` plan promotion of explicit source, evidence,
claim, and decision refs into topic-level canonical indexes. The plan targets
`canonical/sources/source-index.json`, `canonical/evidence/evidence-index.json`,
`canonical/claims/claim-index.json`, and `canonical/decisions/decision-index.json`
plus a promotion manifest, but records `promotion_plan_only=true` and performs no
real vault mutation. Fixture rehearsal writes projection-only payloads to an
explicit fixture root and still records `real_obsidian_vault_write_performed=false`.

## Obsidian milestone status

`hisys.config.obsidian_live.build_obsidian_milestone_status_report` and `hisys
vault-obsidian-milestone-status` record the Obsidian milestone complete across
Live-Obsidian-Config, Topic-Gatekeeper, and Obsidian Evidence Promotion. The
status artifact records `open_milestone_count=0`, `obsidian_milestone_complete=true`,
`external_call_made=false`, `mutation_performed=false`, and
`real_obsidian_vault_write_performed=false`.

## Obsidian Git management design correction

Hisys should treat Git management as part of the Obsidian vault lifecycle, not as
an external afterthought. During initialization, Hisys plans setup of the vault as
a Git-managed repository: verify/create the vault root, initialize Git if needed,
configure `origin`, install the lightweight `.gitignore` policy, bind an
operator-provided `credential_ref`, and perform the initial commit/push only after
an explicit `approval_ref`. Credentials are provided to Hisys by reference
(`env:`, `keyring:`, `file:`, `ssh-agent:`, `secretstore:`, `op:`, `aws-sm:`, or
equivalent secret-store refs), never as raw tokens in config, prompts, repository
files, or runtime-boundary records.

During operation, after an approved vault transaction writes a memo projection,
runtime-boundary record, or governance-only runtime-boundary update, Hisys should
stage only the approved memo and/or runtime-boundary refs. At least one scoped ref
must be present, but memo refs are not required when the approved change is a
runtime-boundary-only governance update. Hisys then commits with a traceable
message, pushes to the configured remote/branch using the credential ref, and
records pre/post Git status plus push result under the runtime boundary. The
current implementation adds plan builders for this lifecycle:

- `build_obsidian_git_initialization_plan`: initialization-phase Git setup plan,
  with raw credential rejection, approval ref, explicit operation approval markers,
  and lightweight-vault policy.
- `build_obsidian_git_sync_plan`: operation-phase memo/runtime-boundary commit/push
  plan, with approved vault refs, approval ref, credential ref, explicit operation
  approval markers, and no raw credential persistence.

These builders are still plan-only: they record `mutation_performed=false` and
`external_call_made=false`. The next increment should turn the plan into a gated
executor tested against fixture Git remotes before any live Obsidian push.

## Non-goals

This scaffold does not write files into the real Obsidian vault, download PDFs,
fetch live sources, mutate topic identities, execute merges/splits, or promote
attachments automatically.
