# DARS Panel Golden Basic Rubric

This rubric is the locked golden fixture used by the DARS panel productization
closure test. It is advisory-only and fixture-local; do not route live model
calls, external evidence, or credentials through it.

## Dimensions

- `logical_validity`: does the candidate's chain of claims hold over the
  checked-in evidence bundle without invoking outside facts?

## Scoring guidance (advisory-only)

- `pass` — the candidate's claims follow from the fixture evidence.
- `needs_more_evidence` — at least one claim depends on something outside the
  checked-in fixture set; flag for human review.
- `reject` — a claim contradicts the fixture evidence.

## Safety reminders

- No live model dispatch, browser/search/tool execution, or credential lookup
  is authorized by this rubric.
- All outputs from a panel round using this rubric remain advisory and
  require human review before any action.
