# LSP Adapter Report — hisys.lsp_adapter.v1

- date: 20260522
- current_head_short: e54bbf3
- command_id: ruff-check
- output_format: ruff_json
- workspace_root_ref: workspace
- diagnostic_count: 3
- error_count: 2
- warning_count: 1
- info_count: 0
- subprocess_exit_code: 1
- subprocess_timed_out: false
- subprocess_killed: false
- output_truncated: false
- output_bytes: 562
- advisory_only: true
- requires_human_review: true
- external_call_made: false
- mutation_performed: false
- raw_source_content_persisted: false
- live_external_action_authorized: false
- allowed_actions: advisory_only

## Target refs
- src/a.py
- src/b.py

## Category refs
- style
- style_warning
- unused

## Unsafe refs
- (none)

## Diagnostics
| severity | code | file_ref | line | column | category_ref | message_digest |
| --- | --- | --- | --- | --- | --- | --- |
| error | F401 | src/a.py | 1 | 1 | unused | 46324d685ce86d2e |
| error | E501 | src/a.py | 5 | 1 | style | 913467c303f6df39 |
| warning | W292 | src/b.py | 12 | 1 | style_warning | d310a320e365bd5d |

