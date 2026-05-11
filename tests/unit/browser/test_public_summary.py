from pathlib import Path
import json

from hisys.browser.public_summary import write_public_browser_run_summary
from hisys.config.instance import InstanceRoot


def test_write_public_browser_run_summary_records_human_review_boundary(tmp_path: Path):
    instance = InstanceRoot(tmp_path)
    refs = {
        "browser_investigation_report_ref": "reports/run-summaries/20260511/browser-investigation-report.json",
        "chief_editor_review_ref": "data/chief-editor-reviews/20260511/CHIEF-REVIEW-X-BROWSER.json",
        "dars_review_ref": "data/dars-browser-reviews/20260511/DARS-REVIEW-X-BROWSER.json",
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
    assert data["schema_id"] == "hisys.public_browser_run_summary"
    assert data["publication_or_live_action_approved"] is False
    assert data["human_approval_required_for_consequential_use"] is True
    assert data["action_taken"] == "none"
    assert data["artifact_refs"] == refs
    md = (tmp_path / summary_ref.replace(".json", ".md")).read_text(encoding="utf-8")
    assert "accept_for_human_reviewed_use" in md
    assert "Human approval is still required" in md


def test_write_public_browser_run_summary_rejects_mutation_boundary(tmp_path: Path):
    instance = InstanceRoot(tmp_path)

    try:
        write_public_browser_run_summary(
            instance=instance,
            yyyymmdd="20260511",
            request_id="HISYS-REQ-PUBLIC-001",
            topic="public smoke topic",
            source_urls=["https://example.com"],
            transport_kinds=["playwright_live"],
            final_decision="blocked",
            remaining_blockers=["test"],
            refs={},
            external_call_made=True,
            mutation_performed=True,
        )
    except ValueError as exc:
        assert "mutation" in str(exc)
    else:
        raise AssertionError("expected mutation boundary rejection")
