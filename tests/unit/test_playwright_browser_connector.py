import json

from hisys.connectors.playwright_browser import PlaywrightBrowserConnector


def test_playwright_fixture_collection_records_no_external_call(tmp_path):
    html = tmp_path / "source.html"
    html.write_text("<html><head><title>Fixture Source</title></head><body>Fixture body text.</body></html>", encoding="utf-8")
    connector = PlaywrightBrowserConnector()

    package = connector.collect_fixture(
        request_id="HISYS-REQ-BROWSER-FIXTURE-001",
        source_url="https://example.test/fixture-source",
        fixture_html=html,
        output_root=tmp_path,
        yyyymmdd="20260512",
    )

    access = json.loads((tmp_path / package.access_ref).read_text(encoding="utf-8"))
    assert package.transport_kind == "playwright_fixture"
    assert access["external_call_made"] is False


class EmptySecurityRiskTransport:
    def fetch(self, url: str):
        return (200, "Cybersecurity risk", "")


def test_playwright_connector_persists_blocked_or_empty_page_without_crashing(tmp_path):
    connector = PlaywrightBrowserConnector(transport=EmptySecurityRiskTransport())

    package = connector.collect_live(
        request_id="HISYS-REQ-SECURITY-BLOCK-001",
        source_url="https://blocked.example/security-risk",
        output_root=tmp_path,
        yyyymmdd="20260511",
    )

    evidence = json.loads((tmp_path / package.evidence_ref).read_text(encoding="utf-8"))
    assert evidence["quoted_text"] == "[no visible text captured; page may be empty, blocked, or unavailable]"
    assert evidence["confidence"] == "low"
    assert "source_access_blocked" in evidence["uncertainty"]
    access = json.loads((tmp_path / package.access_ref).read_text(encoding="utf-8"))
    assert access["external_call_made"] is True
    assert access["title"] == "Cybersecurity risk"


class AccessDeniedTransport:
    def fetch(self, url: str):
        return (403, "Access Denied", 'Access Denied You do not have permission to access this server.')


def test_playwright_connector_classifies_access_denied_as_source_access_limitation(tmp_path):
    connector = PlaywrightBrowserConnector(transport=AccessDeniedTransport())

    package = connector.collect_live(
        request_id="HISYS-REQ-ACCESS-DENIED-001",
        source_url="https://blocked.example/optical-networks",
        output_root=tmp_path,
        yyyymmdd="20260511",
    )

    evidence = json.loads((tmp_path / package.evidence_ref).read_text(encoding="utf-8"))
    assert evidence["confidence"] == "low"
    assert "page_capture_status=source_access_blocked" in evidence["uncertainty"]
    assert "cybersecurity" not in evidence["uncertainty"].lower()
