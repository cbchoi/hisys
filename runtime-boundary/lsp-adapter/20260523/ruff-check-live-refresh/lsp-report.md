# LSP Adapter Report — hisys.lsp_adapter.v1

- date: 20260523
- current_head_short: 3ce9ab1
- command_id: ruff-check-live-refresh
- output_format: ruff_json
- workspace_root_ref: .
- diagnostic_count: 14
- error_count: 14
- warning_count: 0
- info_count: 0
- subprocess_exit_code: 1
- subprocess_timed_out: false
- subprocess_killed: false
- output_truncated: false
- output_bytes: 12655
- advisory_only: true
- requires_human_review: true
- external_call_made: false
- mutation_performed: false
- raw_source_content_persisted: false
- live_external_action_authorized: false
- allowed_actions: advisory_only

## Target refs
- src
- tests/unit/test_lsp_adapter.py

## Category refs
- unused

## Unsafe refs
- (none)

## Diagnostics
| severity | code | file_ref | line | column | category_ref | message_digest |
| --- | --- | --- | --- | --- | --- | --- |
| error | F401 | src/hisys/agents/dars_dispatch.py | 15 | 21 | unused | e95fe318fd888b29 |
| error | F401 | src/hisys/agents/dars_dispatch.py | 23 | 5 | unused | c448d27cb1884df1 |
| error | F401 | src/hisys/agents/dars_dispatch.py | 24 | 5 | unused | 94abd3f3845c4ac5 |
| error | F401 | src/hisys/agents/dars_dispatch.py | 25 | 5 | unused | 68f1587365ee9493 |
| error | F401 | src/hisys/agents/dars_panel_live_adapter.py | 17 | 25 | unused | e208bfe39daa0de7 |
| error | F401 | src/hisys/cli/main.py | 24 | 37 | unused | 8e3773ac8eecdecb |
| error | F401 | src/hisys/cli/main.py | 35 | 5 | unused | 7182b7889d9038ea |
| error | F401 | src/hisys/cli/main.py | 50 | 5 | unused | 74bfedf5beefd4aa |
| error | F401 | src/hisys/cli/main.py | 58 | 5 | unused | a59a43696d7be0fd |
| error | F401 | src/hisys/cli/main.py | 74 | 5 | unused | 6782955877c433a8 |
| error | F541 | src/hisys/cli/main.py | 5073 | 21 | unused | 9eb0d14a088f075d |
| error | F401 | src/hisys/operations/backup.py | 9 | 8 | unused | 163ed5fab7212b7e |
| error | F401 | src/hisys/operations/codebase_regression_benchmarks.py | 16 | 33 | unused | 99987f2c392ad002 |
| error | F841 | src/hisys/operations/governance_docs.py | 111 | 5 | unused | efe3e9b5be116cb7 |

