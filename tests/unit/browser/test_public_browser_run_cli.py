import json
from pathlib import Path

from hisys.cli.main import main


def _public_browser_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(
        Path("examples/instance/config/source-connectors.yaml")
        .read_text(encoding="utf-8")
        .replace("live_network_enabled: false", "live_network_enabled: true", 1)
        .replace(
            "playwright_read_only:\n    connector_id: playwright_read_only\n    connector_type: playwright_read_only\n    enabled: false\n    mode: read_only\n    external_call_allowed: false",
            "playwright_read_only:\n    connector_id: playwright_read_only\n    connector_type: playwright_read_only\n    enabled: true\n    mode: read_only\n    external_call_allowed: true",
        ),
        encoding="utf-8",
    )
    return config_path


def test_public_browser_run_executes_governed_chain_and_writes_summary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_BROWSER_SMOKE", "1")

    from hisys.connectors import playwright_browser

    class FakePlaywrightSyncTransport:
        def fetch(self, url: str):
            if "patent" in url:
                return (
                    200,
                    "Dunlee liquid metal bearing patent",
                    "Dunlee patent evidence describes liquid metal bearing and rotating anode CT x-ray tube cooling technology.",
                    [("x-ray tube patent detail", "https://patents.example/detail/patent-dunlee")],
                )
            if "datasheet" in url or url.endswith(".pdf"):
                return (
                    200,
                    "Varex industrial tube datasheet",
                    "Varex datasheet specification covers industrial NDT x-ray tube stable dose and customized tube design technology.",
                    [("industrial x-ray tube datasheet detail", "https://datasheets.example/detail/varex-datasheet.pdf")],
                )
            return (
                200,
                "Comet x-ray tube technical paper",
                "Technical paper evidence covers industrial x-ray tube microfocus resolution and inspection technology.",
                [("industrial x-ray tube paper detail", "https://papers.example/detail/comet-paper")],
            )

    monkeypatch.setattr(playwright_browser, "PlaywrightSyncTransport", FakePlaywrightSyncTransport)

    result = main(
        [
            "public-browser-run",
            "--instance",
            str(tmp_path),
            "--config",
            str(_public_browser_config(tmp_path)),
            "--profile",
            "examples/instance/config/profiles/public-browser.yaml",
            "--date",
            "20260511",
            "--request-id",
            "HISYS-REQ-PUBLIC-RUN-001",
            "--topic",
            "compare x-ray tube technology public evidence",
            "--user-opinion",
            "Use governed public browser beta chain.",
            "--approval-ref",
            "APPROVAL-PUBLIC-BROWSER-RUN-001",
            "--source-url",
            "https://patents.example/patent-dunlee",
            "--source-url",
            "https://datasheets.example/varex-datasheet.pdf",
            "--source-url",
            "https://papers.example/comet-paper",
            "--follow-links",
            "--max-follow-links-per-source",
            "1",
        ]
    )

    assert result == 0
    summary_path = tmp_path / "reports" / "run-summaries" / "20260511" / "public-browser-run-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["final_decision"] == "accept_for_human_reviewed_use"
    assert summary["transport_kinds"] == ["playwright_live"] * 6
    assert summary["external_call_made"] is True
    assert summary["mutation_performed"] is False
    assert summary["publication_or_live_action_approved"] is False
    assert summary["human_approval_required_for_consequential_use"] is True
    assert summary["artifact_refs"]["browser_investigation_report_ref"] == "reports/run-summaries/20260511/browser-investigation-report.json"
    assert summary["artifact_refs"]["final_review_ref"] == "data/chief-editor-final-browser-reviews/20260511/FINAL-CHIEF-REVIEW-HISYS-REQ-PUBLIC-RUN-001-BROWSER.json"
