# Hisys Public Launch Optimization Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Optimize Hisys for controlled public beta by separating the browser workflow from the monolithic CLI, adding public-profile validation, improving public run UX, and preserving governed safety boundaries.

**Architecture:** Keep existing governed artifacts and decisions unchanged. Refactor browser-specific command handlers into dedicated modules, add a public profile validator and public orchestration wrapper, then document and validate the public launch path. Fixture mode remains available for CI/developer reproducibility but is hidden from public quickstart UX.

**Tech Stack:** Python 3.11, argparse, Pydantic v2, PyYAML, pytest, Playwright optional extra, existing Hisys runtime artifact layout.

---

## Current Baseline

Repository:

```text
/home/cbchoi/workspaces/sysailab/develop/repos/hisys
```

Current known HEAD when this plan was written:

```text
e2f2142 feat: formalize browser acceptance schemas
```

Recent validation baseline:

```text
342 pytest tests passing
traceability validation OK
secret scan 0 hits
working tree clean
```

Main optimization findings:

```text
src/hisys/cli/main.py                       7617 lines
_build_parser                                  722 lines
main                                           496 lines
_cmd_browser_investigate_topic                 304 lines
tests/unit/test_source_connector_cli.py       2166 lines
tests/unit/test_cli_runtime.py                1868 lines
```

Primary risk before public profile: browser/public-launch logic is buried inside a large general CLI module, making launch hardening and review harder than necessary.

---

## Non-Negotiable Governance Constraints

Do not weaken these invariants:

```text
DARS is advisory only.
Chief Editor final browser acceptance is for human-reviewed use only.
No automatic publication/live/consequential action.
No credentials, login, upload, post, purchase, form submit, mutation, or access-control bypass.
Fixture mode remains available for CI/developer reproducibility.
Public path defaults to live read-only Playwright mode.
Every public-facing expected failure writes a blocked report rather than raw traceback where feasible.
```

Final accepted public-browser state must remain:

```text
decision = accept_for_human_reviewed_use
publication_or_live_action_approved = false
human_approval_required_for_consequential_use = true
action_taken = none
mutation_performed = false
```

---

# Phase 0: Safety Net and Baseline Capture

### Task 0.1: Capture current validation baseline

**Objective:** Confirm the repo is clean and tests pass before refactoring.

**Files:**
- Read only: repository root

**Step 1: Check status and commit baseline**

```bash
git status --short
git log --oneline -5
```

Expected:

```text
clean working tree
latest commit is the formal schema commit or later
```

**Step 2: Run focused browser tests**

```bash
python3 -m pytest \
  tests/unit/test_cli_runtime.py::test_full_browser_review_chain_from_investigation_report_to_final_acceptance \
  tests/unit/test_cli_runtime.py::test_resolve_browser_dars_revisions_marks_segment_and_corroboration_ready \
  tests/unit/test_cli_runtime.py::test_final_browser_acceptance_review_accepts_ready_revision_resolution \
  tests/unit/test_cli_runtime.py::test_review_browser_investigation_blocks_when_sufficiency_not_ready \
  tests/unit/test_cli_runtime.py::test_final_browser_acceptance_review_blocks_unready_revision_resolution \
  tests/unit/test_schemas.py::test_browser_dars_revision_resolution_schema_enforces_ready_gates \
  tests/unit/test_schemas.py::test_final_browser_acceptance_schema_preserves_human_review_boundary \
  -q
```

Expected:

```text
all selected tests pass
```

**Step 3: Run full suite**

```bash
python3 -m pytest
```

Expected:

```text
all tests pass
```

**Step 4: Commit**

No commit unless baseline docs are modified.

---

# Phase 1: Extract Browser Workflow Without Behavior Change

### Task 1.1: Create browser workflow package skeleton

**Objective:** Add dedicated modules for browser workflow code while leaving behavior unchanged.

**Files:**
- Create: `src/hisys/browser/__init__.py`
- Create: `src/hisys/browser/workflow.py`
- Create: `src/hisys/browser/review_chain.py`
- Create: `src/hisys/browser/reports.py`
- Modify later: `src/hisys/cli/main.py`

**Step 1: Create package files**

```python
# src/hisys/browser/__init__.py
"""Governed browser investigation and acceptance workflow."""
```

```python
# src/hisys/browser/workflow.py
"""Browser investigation orchestration extracted from the CLI.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations
```

```python
# src/hisys/browser/review_chain.py
"""Chief Editor / DARS browser review chain helpers.

Traceability: HISYS-FR-INV-001..006, HISYS-FR-AGT-001..005,
HISYS-DARS-CONTRACT-001.
"""

from __future__ import annotations
```

```python
# src/hisys/browser/reports.py
"""Browser workflow report rendering and persistence helpers."""

from __future__ import annotations
```

**Step 2: Run import smoke**

```bash
PYTHONPATH=src python3 - <<'PY'
import hisys.browser.workflow
import hisys.browser.review_chain
import hisys.browser.reports
print('ok')
PY
```

Expected:

```text
ok
```

**Step 3: Run tests**

```bash
python3 -m pytest tests/unit/test_cli_runtime.py::test_full_browser_review_chain_from_investigation_report_to_final_acceptance -q
```

Expected: pass.

**Step 4: Commit**

```bash
git add src/hisys/browser
git commit -m "refactor: add browser workflow package"
```

---

### Task 1.2: Move pure browser helper functions to `browser/reports.py`

**Objective:** Extract rendering/persistence helpers that do not need argparse into browser modules.

**Files:**
- Modify: `src/hisys/browser/reports.py`
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_cli_runtime.py`

**Move candidates from `src/hisys/cli/main.py`:**

```text
_write_browser_investigation_report
_browser_investigation_report
_render_browser_investigation_report_md
_render_browser_chief_editor_review_md
_render_browser_dars_revision_resolution_md
_render_final_browser_acceptance_review_md
```

If exact function names differ, search:

```bash
python3 - <<'PY'
from pathlib import Path
p=Path('src/hisys/cli/main.py')
for i,l in enumerate(p.read_text().splitlines(),1):
    if 'browser' in l.lower() and ('report' in l.lower() or 'render' in l.lower()):
        print(i, l[:120])
PY
```

**Step 1: Move one helper at a time**

After moving each helper, import it in `cli/main.py`:

```python
from hisys.browser.reports import (
    _browser_investigation_report,
    _write_browser_investigation_report,
)
```

Prefer public names if cleaning during extraction:

```python
from hisys.browser.reports import build_browser_investigation_report, write_browser_investigation_report
```

But avoid large rename churn unless tests require it.

**Step 2: Run focused test after each move group**

```bash
python3 -m pytest tests/unit/test_cli_runtime.py::test_full_browser_review_chain_from_investigation_report_to_final_acceptance -q
```

Expected: pass.

**Step 3: Commit**

```bash
git add src/hisys/browser/reports.py src/hisys/cli/main.py
git commit -m "refactor: move browser report helpers"
```

---

### Task 1.3: Move Browser-G and Browser-H builders to `browser/review_chain.py`

**Objective:** Extract DARS revision resolution and final acceptance builders into a review-chain module.

**Files:**
- Modify: `src/hisys/browser/review_chain.py`
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_cli_runtime.py`

**Move candidates:**

```text
_build_browser_dars_revision_resolution
_build_final_browser_acceptance_review
_normalize_browser_segment
_primary_browser_segment
any helper that computes segment/corroboration status
```

**Step 1: Move builders and tests still pass**

Keep command functions in `cli/main.py` for now. Only move pure computation.

**Step 2: Run focused tests**

```bash
python3 -m pytest \
  tests/unit/test_cli_runtime.py::test_resolve_browser_dars_revisions_marks_segment_and_corroboration_ready \
  tests/unit/test_cli_runtime.py::test_final_browser_acceptance_review_accepts_ready_revision_resolution \
  tests/unit/test_cli_runtime.py::test_final_browser_acceptance_review_blocks_unready_revision_resolution \
  -q
```

Expected: pass.

**Step 3: Run schema tests**

```bash
python3 -m pytest tests/unit/test_schemas.py -q
```

Expected: pass.

**Step 4: Commit**

```bash
git add src/hisys/browser/review_chain.py src/hisys/cli/main.py
git commit -m "refactor: move browser review chain builders"
```

---

### Task 1.4: Move Browser-I readiness review builder to `browser/review_chain.py`

**Objective:** Extract Chief Editor readiness computation while preserving CLI behavior.

**Files:**
- Modify: `src/hisys/browser/review_chain.py`
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_cli_runtime.py`

**Move candidates:**

```text
_cmd_review_browser_investigation should remain in CLI initially
pure review artifact builder should move
readiness reason/status helper should move
```

**Step 1: Extract pure builder only**

Target shape:

```python
def build_browser_chief_editor_readiness_review(...):
    ...
    return review_dict
```

**Step 2: Keep command-level file IO in CLI**

Do not move argparse or `InstanceRoot` wiring yet.

**Step 3: Run tests**

```bash
python3 -m pytest \
  tests/unit/test_cli_runtime.py::test_full_browser_review_chain_from_investigation_report_to_final_acceptance \
  tests/unit/test_cli_runtime.py::test_review_browser_investigation_blocks_when_sufficiency_not_ready \
  -q
```

Expected: pass.

**Step 4: Commit**

```bash
git add src/hisys/browser/review_chain.py src/hisys/cli/main.py
git commit -m "refactor: move browser readiness review builder"
```

---

### Task 1.5: Move browser investigation orchestration to `browser/workflow.py`

**Objective:** Reduce `_cmd_browser_investigate_topic` size by delegating to a workflow function.

**Files:**
- Modify: `src/hisys/browser/workflow.py`
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_source_connector_cli.py`

**Target API:**

```python
@dataclass(frozen=True)
class BrowserInvestigationRunConfig:
    instance_root: Path
    config_path: Path
    yyyymmdd: str
    request_id: str
    topic: str
    user_opinion: str
    approval_ref: str
    source_urls: list[str]
    orchestrator_decide_domains: bool
    browser_fixture_html: list[Path]
    follow_links: bool
    max_follow_links_per_source: int
    orchestrator_corroborating_urls: list[str]


def run_browser_investigation(config: BrowserInvestigationRunConfig) -> int:
    ...
```

CLI command should become a thin adapter:

```python
return run_browser_investigation(
    BrowserInvestigationRunConfig(...)
)
```

**Step 1: Move existing command body into workflow function**

Preserve behavior and return codes.

**Step 2: Keep CLI parser unchanged**

Do not rename flags in this task.

**Step 3: Run focused source connector/browser tests**

```bash
python3 -m pytest tests/unit/test_source_connector_cli.py tests/unit/test_cli_runtime.py::test_full_browser_review_chain_from_investigation_report_to_final_acceptance -q
```

Expected: pass.

**Step 4: Commit**

```bash
git add src/hisys/browser/workflow.py src/hisys/cli/main.py
git commit -m "refactor: extract browser investigation workflow"
```

---

# Phase 2: Public Profile Validation

### Task 2.1: Add public browser profile schema

**Objective:** Define a Pydantic schema for public browser launch profile validation.

**Files:**
- Create: `src/hisys/browser/public_profile.py`
- Test: `tests/unit/browser/test_public_profile.py`

**Step 1: Write failing tests**

Create `tests/unit/browser/test_public_profile.py`:

```python
import pytest
from pydantic import ValidationError

from hisys.browser.public_profile import PublicBrowserProfile


def _valid_profile():
    return {
        "profile_id": "public-browser-beta",
        "live_network_enabled": True,
        "connector_id": "playwright_read_only",
        "mode": "read_only",
        "external_call_allowed": True,
        "domain_decision_policy": "orchestrator_decided",
        "allow_credentials": False,
        "allow_mutation": False,
        "fixture_mode_publicly_exposed": False,
        "manual_smoke_env_var": "HISYS_ALLOW_BROWSER_SMOKE",
        "max_source_urls": 10,
        "max_follow_links_per_source": 3,
        "navigation_timeout_ms": 20000,
        "allowed_url_schemes": ["https", "http"],
        "forbidden_actions": [
            "login",
            "credential_use",
            "form_submit",
            "upload",
            "purchase",
            "post",
            "mutation",
            "access_control_bypass",
        ],
    }


def test_public_browser_profile_accepts_safe_live_read_only_profile():
    profile = PublicBrowserProfile.model_validate(_valid_profile())
    assert profile.connector_id == "playwright_read_only"
    assert profile.fixture_mode_publicly_exposed is False


def test_public_browser_profile_rejects_credentials():
    bad = _valid_profile()
    bad["allow_credentials"] = True
    with pytest.raises(ValidationError):
        PublicBrowserProfile.model_validate(bad)


def test_public_browser_profile_rejects_public_fixture_exposure():
    bad = _valid_profile()
    bad["fixture_mode_publicly_exposed"] = True
    with pytest.raises(ValidationError):
        PublicBrowserProfile.model_validate(bad)


def test_public_browser_profile_rejects_missing_forbidden_action():
    bad = _valid_profile()
    bad["forbidden_actions"] = ["login"]
    with pytest.raises(ValidationError):
        PublicBrowserProfile.model_validate(bad)
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/unit/browser/test_public_profile.py -q
```

Expected: fail because module does not exist.

**Step 3: Implement schema**

Create `src/hisys/browser/public_profile.py`:

```python
"""Public browser launch profile validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


_REQUIRED_FORBIDDEN_ACTIONS = {
    "login",
    "credential_use",
    "form_submit",
    "upload",
    "purchase",
    "post",
    "mutation",
    "access_control_bypass",
}


class PublicBrowserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str
    live_network_enabled: bool
    connector_id: Literal["playwright_read_only"]
    mode: Literal["read_only"]
    external_call_allowed: bool
    domain_decision_policy: Literal["orchestrator_decided", "static_allowlist"]
    allow_credentials: bool
    allow_mutation: bool
    fixture_mode_publicly_exposed: bool = False
    manual_smoke_env_var: str = "HISYS_ALLOW_BROWSER_SMOKE"
    max_source_urls: int = Field(default=10, ge=1, le=50)
    max_follow_links_per_source: int = Field(default=3, ge=0, le=10)
    navigation_timeout_ms: int = Field(default=20000, ge=1000, le=60000)
    allowed_url_schemes: list[Literal["https", "http"]] = Field(default_factory=lambda: ["https", "http"])
    forbidden_actions: list[str]

    @model_validator(mode="after")
    def enforce_public_safety(self) -> "PublicBrowserProfile":
        if not self.live_network_enabled:
            raise ValueError("public browser profile must enable live_network_enabled")
        if not self.external_call_allowed:
            raise ValueError("public browser profile must explicitly allow read-only external calls")
        if self.allow_credentials:
            raise ValueError("public browser profile must not allow credentials")
        if self.allow_mutation:
            raise ValueError("public browser profile must not allow mutation")
        if self.fixture_mode_publicly_exposed:
            raise ValueError("fixture mode must not be exposed in public profile")
        missing = _REQUIRED_FORBIDDEN_ACTIONS - set(self.forbidden_actions)
        if missing:
            raise ValueError(f"public browser profile missing forbidden actions: {sorted(missing)}")
        return self
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/unit/browser/test_public_profile.py -q
```

Expected: pass.

**Step 5: Commit**

```bash
git add src/hisys/browser/public_profile.py tests/unit/browser/test_public_profile.py
git commit -m "feat: add public browser profile schema"
```

---

### Task 2.2: Add CLI command to validate public profile file

**Objective:** Provide a deterministic operator command for validating public browser profile YAML.

**Files:**
- Modify: `src/hisys/cli/main.py`
- Modify: `src/hisys/browser/public_profile.py`
- Test: `tests/unit/browser/test_public_profile_cli.py`

**Step 1: Add loader function**

In `src/hisys/browser/public_profile.py`:

```python
from pathlib import Path
from typing import Any

import yaml


def load_public_browser_profile(path: str | Path) -> PublicBrowserProfile:
    raw: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return PublicBrowserProfile.model_validate(raw)
```

**Step 2: Write failing CLI tests**

Create `tests/unit/browser/test_public_profile_cli.py`:

```python
from pathlib import Path

from hisys.cli.main import main


def test_validate_public_browser_profile_accepts_safe_profile(tmp_path: Path, capsys):
    profile = tmp_path / "public-browser.yaml"
    profile.write_text(
        """
profile_id: public-browser-beta
live_network_enabled: true
connector_id: playwright_read_only
mode: read_only
external_call_allowed: true
domain_decision_policy: orchestrator_decided
allow_credentials: false
allow_mutation: false
fixture_mode_publicly_exposed: false
manual_smoke_env_var: HISYS_ALLOW_BROWSER_SMOKE
max_source_urls: 10
max_follow_links_per_source: 3
navigation_timeout_ms: 20000
allowed_url_schemes: [https, http]
forbidden_actions:
  - login
  - credential_use
  - form_submit
  - upload
  - purchase
  - post
  - mutation
  - access_control_bypass
""".strip()
        + "\n",
        encoding="utf-8",
    )
    assert main(["validate-public-browser-profile", "--profile", str(profile)]) == 0
    captured = capsys.readouterr()
    assert "public browser profile: valid" in captured.out


def test_validate_public_browser_profile_rejects_mutation(tmp_path: Path, capsys):
    profile = tmp_path / "bad-public-browser.yaml"
    profile.write_text(
        """
profile_id: bad
live_network_enabled: true
connector_id: playwright_read_only
mode: read_only
external_call_allowed: true
domain_decision_policy: orchestrator_decided
allow_credentials: false
allow_mutation: true
fixture_mode_publicly_exposed: false
forbidden_actions: [login, credential_use, form_submit, upload, purchase, post, mutation, access_control_bypass]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    assert main(["validate-public-browser-profile", "--profile", str(profile)]) == 2
    captured = capsys.readouterr()
    assert "public browser profile: invalid" in captured.err
```

**Step 3: Run test to verify failure**

```bash
python3 -m pytest tests/unit/browser/test_public_profile_cli.py -q
```

Expected: fail because CLI command does not exist.

**Step 4: Add parser and command handler**

In `_build_parser()` add:

```python
public_profile_parser = subparsers.add_parser(
    "validate-public-browser-profile",
    help="validate a governed public browser launch profile",
)
public_profile_parser.add_argument("--profile", type=Path, required=True)
```

In dispatch:

```python
if args.command == "validate-public-browser-profile":
    try:
        profile = load_public_browser_profile(args.profile)
    except Exception as exc:
        print(f"public browser profile: invalid reason={exc}", file=sys.stderr)
        return 2
    print(f"public browser profile: valid profile_id={profile.profile_id}")
    return 0
```

**Step 5: Run tests**

```bash
python3 -m pytest tests/unit/browser/test_public_profile_cli.py tests/unit/browser/test_public_profile.py -q
```

Expected: pass.

**Step 6: Commit**

```bash
git add src/hisys/cli/main.py src/hisys/browser/public_profile.py tests/unit/browser/test_public_profile_cli.py
git commit -m "feat: validate public browser profile"
```

---

### Task 2.3: Evaluate Camoufox as an optional browser transport spike

**Objective:** Consider Camoufox as a future optional read-only browser transport without making it the public default or weakening governance.

**Context:** Camoufox is an open-source Firefox/Playwright-oriented browser for AI agents. The Python package describes itself as a wrapper around Playwright that launches Camoufox and injects realistic device/browser characteristics. This may improve compatibility with some sites, but it also raises governance, compliance, reproducibility, and public-positioning concerns because it is associated with fingerprinting and anti-bot avoidance.

**Decision for public beta:**

```text
Keep Playwright Chromium as the default public transport.
Do not add Camoufox to the first public launch profile.
Evaluate Camoufox only behind an explicit experimental/internal transport flag.
Do not enable proxy rotation, credential use, CAPTCHA bypass, login, form submit, mutation, or access-control bypass.
```

**Files if implemented later:**
- Create: `src/hisys/connectors/camoufox_browser.py`
- Modify: `src/hisys/connectors/live_source_config.py`
- Modify: `examples/instance/config/source-connectors.yaml`
- Modify: `src/hisys/browser/public_profile.py`
- Test: `tests/unit/browser/test_camoufox_transport.py`
- Docs: `docs/use-cases/live-research-connectors.md`

**Step 1: Add a design note before code**

Create `docs/design/camoufox-browser-transport.md` with:

```text
- intended use: optional compatibility transport for read-only public pages
- non-goals: anti-bot bypass, proxy rotation, CAPTCHA bypass, login, scraping protected/private content
- governance: same SourceConnectorDispatchGate as Playwright
- artifact transport_kind: camoufox_live
- public profile default: disabled
- CI path: fixture or mocked transport only
```

**Step 2: Add connector config type only after design approval**

If approved, extend `SourceConnectorConfig.connector_type` with:

```python
"camoufox_read_only"
```

Then add disabled-by-default registry entry:

```yaml
camoufox_read_only:
  connector_id: camoufox_read_only
  connector_type: camoufox_read_only
  enabled: false
  mode: read_only
  external_call_allowed: false
  requires_human_approval: true
  approval_policy_ref: POLICY-LIVE-RESEARCH-001
  domain_decision_policy: orchestrator_decided
  forbidden_actions: *forbidden_live_actions
  output_schema: EvidencePackage
  manual_smoke_only: true
  manual_smoke_env_var: HISYS_ALLOW_CAMOUFOX_SMOKE
  smoke_test_in_ci: false
```

**Step 3: Implement transport behind existing BrowserTransport protocol**

Use the existing `BrowserTransport.fetch(url) -> tuple[...]` shape so workflow code remains transport-agnostic.

Sketch:

```python
class CamoufoxSyncTransport:
    transport_kind = "camoufox_live"

    def fetch(self, url: str) -> tuple[int, str, str, list[tuple[str, str]]]:
        try:
            from camoufox.sync_api import Camoufox
        except Exception as exc:
            raise PlaywrightUnavailableError(
                "camoufox is not installed; install optional camoufox extra and fetch browser runtime"
            ) from exc
        # read-only page.goto, title, body inner_text, links only
```

Verify the actual Camoufox API before implementing; do not rely on this sketch blindly.

**Step 4: Add explicit tests for forbidden positioning**

Tests must assert:

```text
Camoufox is disabled by default.
Public profile rejects Camoufox unless experimental flag is enabled.
Camoufox transport records transport_kind=camoufox_live.
Camoufox transport preserves mutation_performed=false.
Proxy/credential/CAPTCHA-bypass fields are rejected if introduced.
```

**Step 5: Run validation**

```bash
python3 -m pytest tests/unit/browser/test_camoufox_transport.py tests/unit/test_source_connector_cli.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected: pass.

**Step 6: Commit if implemented**

```bash
git add docs/design/camoufox-browser-transport.md src/hisys/connectors/camoufox_browser.py tests/unit/browser/test_camoufox_transport.py
git commit -m "spike: evaluate camoufox browser transport"
```

---

# Phase 3: Public Run UX and Summary

### Task 3.1: Add public browser run summary builder

**Objective:** Produce one Markdown/JSON summary for public beta evaluators.

**Files:**
- Create or modify: `src/hisys/browser/public_summary.py`
- Test: `tests/unit/browser/test_public_summary.py`

**Step 1: Write failing tests**

Create `tests/unit/browser/test_public_summary.py`:

```python
from pathlib import Path
import json

from hisys.browser.public_summary import write_public_browser_run_summary
from hisys.config.instance import InstanceRoot


def test_write_public_browser_run_summary_records_human_review_boundary(tmp_path: Path):
    instance = InstanceRoot(tmp_path)
    refs = {
        "browser_investigation_report_ref": "reports/run-summaries/20260511/browser-investigation-report.json",
        "chief_editor_review_ref": "data/chief-editor-reviews/20260511/CHIEF-REVIEW-X-BROWSER.json",
        "dars_review_ref": "data/dars-reviews/20260511/DARS-X-BROWSER.json",
        "revision_resolution_ref": "data/browser-dars-revision-resolutions/20260511/REVISION-X-BROWSER.json",
        "final_review_ref": "data/chief-editor-final-browser-reviews/20260511/FINAL-CHIEF-REVIEW-X-BROWSER.json",
    }
    summary_ref = write_public_browser_run_summary(
        instance=instance,
        yyyymmdd="20260511",
        request_id="HISYS-REQ-PUBLIC-001",
        topic="public smoke topic",
        source_urls=["https://example.com"],
        transport_kinds=["playwright_live"],
        final_decision="accept_for_human_reviewed_use",
        remaining_blockers=[],
        refs=refs,
        external_call_made=True,
        mutation_performed=False,
    )
    data = json.loads((tmp_path / summary_ref).read_text(encoding="utf-8"))
    assert data["publication_or_live_action_approved"] is False
    assert data["human_approval_required_for_consequential_use"] is True
    md = (tmp_path / summary_ref.replace(".json", ".md")).read_text(encoding="utf-8")
    assert "accept_for_human_reviewed_use" in md
    assert "Human approval is still required" in md
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/unit/browser/test_public_summary.py -q
```

Expected: fail because module does not exist.

**Step 3: Implement writer**

Create `src/hisys/browser/public_summary.py` with function:

```python
def write_public_browser_run_summary(...)-> str:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    ref = f"reports/run-summaries/{yyyymmdd}/public-browser-run-summary.json"
    payload = {
        "schema_id": "hisys.public_browser_run_summary",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "topic": topic,
        "source_urls": source_urls,
        "transport_kinds": transport_kinds,
        "external_call_made": external_call_made,
        "mutation_performed": mutation_performed,
        "final_decision": final_decision,
        "remaining_blockers": remaining_blockers,
        "publication_or_live_action_approved": False,
        "human_approval_required_for_consequential_use": True,
        "action_taken": "none",
        "artifact_refs": refs,
    }
    ...
    return ref
```

**Step 4: Run test**

```bash
python3 -m pytest tests/unit/browser/test_public_summary.py -q
```

Expected: pass.

**Step 5: Commit**

```bash
git add src/hisys/browser/public_summary.py tests/unit/browser/test_public_summary.py
git commit -m "feat: add public browser run summary"
```

---

### Task 3.2: Add public browser wrapper command

**Objective:** Add one public-friendly command that orchestrates the governed chain without bypassing artifacts or review gates.

**Files:**
- Modify: `src/hisys/cli/main.py`
- Create or modify: `src/hisys/browser/public_run.py`
- Test: `tests/unit/browser/test_public_browser_run_cli.py`

**Command shape:**

```bash
hisys browser-public-run \
  --instance examples/instance \
  --config examples/instance/config/source-connectors.yaml \
  --public-profile config/profiles/public-browser.yaml \
  --date 20260511 \
  --request-id HISYS-REQ-PUBLIC-001 \
  --topic "..." \
  --user-opinion "..." \
  --approval-ref APPROVAL-PUBLIC-BETA-001 \
  --source-url https://example.com \
  --orchestrator-decide-domains \
  --follow-links \
  --max-follow-links-per-source 2
```

**Step 1: Write test using fixture mode only internally**

The public wrapper test may use fixture to avoid network but must assert public docs/summary mark fixture as non-public if fixture flag is used only in test path.

Create `tests/unit/browser/test_public_browser_run_cli.py`:

```python
from pathlib import Path
import json

from hisys.cli.main import main


def test_browser_public_run_rejects_fixture_flag_without_internal_test_switch(tmp_path: Path, monkeypatch, capsys):
    # Public wrapper should not expose --browser-fixture-html.
    result = main(["browser-public-run", "--browser-fixture-html", "x.html"])
    assert result != 0
```

Then add an integration-style fixture-supported test only if you implement an explicit hidden/internal test flag, for example:

```text
--internal-test-browser-fixture-html
```

Do not document that flag in public quickstart.

**Step 2: Implement wrapper orchestration**

`src/hisys/browser/public_run.py` should call existing internal functions in order:

```text
1. validate public profile
2. run browser investigation
3. run Chief Editor readiness review
4. run DARS review
5. run DARS revision resolution
6. run final Chief Editor browser acceptance review
7. write public-browser-run-summary
```

Important: if any stage returns non-zero, stop and write a blocked summary where possible.

**Step 3: Run wrapper tests**

```bash
python3 -m pytest tests/unit/browser/test_public_browser_run_cli.py -q
```

Expected: pass.

**Step 4: Run full browser regression**

```bash
python3 -m pytest tests/unit/test_cli_runtime.py tests/unit/test_source_connector_cli.py tests/unit/browser -q
```

Expected: pass.

**Step 5: Commit**

```bash
git add src/hisys/cli/main.py src/hisys/browser/public_run.py tests/unit/browser/test_public_browser_run_cli.py
git commit -m "feat: add public browser run wrapper"
```

---

# Phase 4: Launch Profile and Public Docs

### Task 4.1: Add public browser profile file

**Objective:** Add a checked-in example public beta profile that validates but does not expose credentials or mutations.

**Files:**
- Create: `config/profiles/public-browser.yaml` or `examples/instance/config/profiles/public-browser.yaml`
- Test: `tests/unit/browser/test_public_profile_cli.py`

Prefer if repo currently has no root `config/`:

```text
examples/instance/config/profiles/public-browser.yaml
```

**Profile content:**

```yaml
profile_id: public-browser-beta
live_network_enabled: true
connector_id: playwright_read_only
mode: read_only
external_call_allowed: true
domain_decision_policy: orchestrator_decided
allow_credentials: false
allow_mutation: false
fixture_mode_publicly_exposed: false
manual_smoke_env_var: HISYS_ALLOW_BROWSER_SMOKE
max_source_urls: 10
max_follow_links_per_source: 3
navigation_timeout_ms: 20000
allowed_url_schemes:
  - https
  - http
forbidden_actions:
  - login
  - credential_use
  - form_submit
  - upload
  - purchase
  - post
  - mutation
  - access_control_bypass
```

**Step 1: Add test that repository profile validates**

```python
def test_checked_in_public_browser_profile_validates():
    assert main([
        "validate-public-browser-profile",
        "--profile",
        "examples/instance/config/profiles/public-browser.yaml",
    ]) == 0
```

**Step 2: Run test**

```bash
python3 -m pytest tests/unit/browser/test_public_profile_cli.py -q
```

Expected: pass.

**Step 3: Commit**

```bash
git add examples/instance/config/profiles/public-browser.yaml tests/unit/browser/test_public_profile_cli.py
git commit -m "feat: add public browser beta profile"
```

---

### Task 4.2: Add public quickstart

**Objective:** Create a user-facing public beta quickstart that uses installed CLI and live browser mode.

**Files:**
- Create: `docs/public/browser-quickstart.md`
- Modify: `README.md`

**Quickstart must include:**

```text
1. Install from clean checkout:
   pip install -e ".[browser]"
2. Install Playwright browser runtime:
   python -m playwright install chromium
3. Validate public profile:
   hisys validate-public-browser-profile --profile examples/instance/config/profiles/public-browser.yaml
4. Run public browser investigation/wrapper.
5. Read public-browser-run-summary.md.
6. State governance boundaries and known limits.
```

**Do not include public instruction using:**

```text
--browser-fixture-html
PYTHONPATH=src
```

Those belong only in developer docs.

**Step 1: Write doc**

Create `docs/public/browser-quickstart.md`.

**Step 2: Link from README**

Add a short public beta section:

```markdown
### Public browser beta

See `docs/public/browser-quickstart.md` for the governed public browser workflow.
```

**Step 3: Run doc search sanity**

```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/public/browser-quickstart.md').read_text()
assert '--browser-fixture-html' not in text
assert 'PYTHONPATH=src' not in text
assert 'accept_for_human_reviewed_use' in text
print('ok')
PY
```

Expected: `ok`.

**Step 4: Commit**

```bash
git add docs/public/browser-quickstart.md README.md
git commit -m "docs: add public browser quickstart"
```

---

# Phase 5: Public Readiness Gate

### Task 5.1: Add public browser readiness command

**Objective:** Add a single operator gate command that verifies the public launch path prerequisites.

**Files:**
- Create: `src/hisys/browser/readiness.py`
- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/browser/test_public_readiness_cli.py`

**Command shape:**

```bash
hisys public-browser-readiness \
  --profile examples/instance/config/profiles/public-browser.yaml \
  --config examples/instance/config/source-connectors.yaml
```

**Checks:**

```text
profile validates
source connector registry validates
playwright package import check returns clear pass/warn/fail
no credentials allowed
no mutations allowed
fixture mode not public
README/docs public quickstart exists
```

Do not require live network call in this readiness command.

**Step 1: Write failing CLI test**

```python
from hisys.cli.main import main


def test_public_browser_readiness_writes_operator_report(tmp_path, capsys):
    # Use minimal temp profile/config or checked-in profile after Task 4.1.
    result = main([
        "public-browser-readiness",
        "--profile",
        "examples/instance/config/profiles/public-browser.yaml",
        "--config",
        "examples/instance/config/source-connectors.yaml",
    ])
    assert result in {0, 1}  # 1 acceptable if Playwright optional runtime missing
    captured = capsys.readouterr()
    assert "public browser readiness" in captured.out
```

**Step 2: Implement readiness evaluator**

Return statuses:

```text
ready
ready_with_warnings
blocked
```

If Playwright is not installed, return `ready_with_warnings` or `blocked` depending chosen policy, but with install guidance:

```text
pip install -e ".[browser]"
python -m playwright install chromium
```

**Step 3: Run tests**

```bash
python3 -m pytest tests/unit/browser/test_public_readiness_cli.py -q
```

Expected: pass.

**Step 4: Commit**

```bash
git add src/hisys/browser/readiness.py src/hisys/cli/main.py tests/unit/browser/test_public_readiness_cli.py
git commit -m "feat: add public browser readiness gate"
```

---

# Phase 6: Validation, Traceability, and Release Report

### Task 6.1: Update traceability docs

**Objective:** Trace the public launch optimization features to requirements and tests.

**Files:**
- Modify: `docs/traceability/README.md`
- Possibly modify: `docs/use-cases/live-research-connectors.md`

**Add traceability rows for:**

```text
Public browser profile validation
Public browser run wrapper
Public browser run summary
Public browser readiness gate
```

Each row should cite:

```text
source files
test files
docs
safety requirements
```

**Step 1: Edit traceability doc**

Add rows near existing Browser-I/G/H rows.

**Step 2: Run traceability validation**

```bash
python3 scripts/validate_traceability.py
```

Expected:

```text
OK: schemas, trace test, and Hermes boundary convention pass traceability checks
```

**Step 3: Commit**

```bash
git add docs/traceability/README.md docs/use-cases/live-research-connectors.md
git commit -m "docs: trace public browser launch gates"
```

---

### Task 6.2: Run full validation gate

**Objective:** Prove optimization did not break governed behavior.

**Files:**
- Read only unless failures require fixes.

**Step 1: Run focused public/browser tests**

```bash
python3 -m pytest tests/unit/browser tests/unit/test_cli_runtime.py tests/unit/test_source_connector_cli.py tests/unit/test_schemas.py -q
```

Expected: pass.

**Step 2: Run full suite**

```bash
python3 -m pytest
```

Expected: pass.

**Step 3: Run traceability**

```bash
python3 scripts/validate_traceability.py
```

Expected:

```text
OK: schemas, trace test, and Hermes boundary convention pass traceability checks
```

**Step 4: Run secret scan**

```bash
python3 scripts/scan_secrets.py
```

Expected:

```text
hit_count=0
```

**Step 5: Run whitespace check**

```bash
git diff --check
```

Expected: no output and exit 0.

**Step 6: Commit final fixes if any**

```bash
git status --short
```

If dirty due final fixes:

```bash
git add <changed files>
git commit -m "chore: finalize public browser optimization"
```

---

## Final Acceptance Criteria

Optimization is complete when all are true:

```text
1. Browser workflow code is separated from monolithic CLI enough that browser behavior is reviewable.
2. Existing browser chain behavior and artifact schema semantics are unchanged.
3. Public browser profile validates with deterministic command.
4. Public docs do not expose fixture mode as normal UX.
5. Public wrapper or summary gives one readable operator artifact.
6. Public readiness command reports install/config/browser preconditions.
7. Full pytest passes.
8. Traceability validation passes.
9. Secret scan reports hit_count=0.
10. Working tree is clean after commits.
```

## Recommended Commit Sequence

```text
refactor: add browser workflow package
refactor: move browser report helpers
refactor: move browser review chain builders
refactor: move browser readiness review builder
refactor: extract browser investigation workflow
feat: add public browser profile schema
feat: validate public browser profile
feat: add public browser run summary
feat: add public browser run wrapper
feat: add public browser beta profile
docs: add public browser quickstart
feat: add public browser readiness gate
docs: trace public browser launch gates
chore: finalize public browser optimization
```

## Recommended Execution Strategy

Use small sequential implementation with verification after each commit. If using subagents, delegate one phase at a time and require two reviews:

```text
1. Spec compliance review: does it preserve governance and acceptance criteria?
2. Code quality review: does it reduce complexity without over-generalizing?
```

Do not start public launch profile creation until Phase 1 extraction and Phase 2 validation are complete.
