import json

from hisys.connectors.general_web_search import GeneralWebSearchConnector


def test_general_web_search_fixture_collection_records_no_external_call(tmp_path):
    fixture = tmp_path / "search-results.json"
    fixture.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "title": "Fixture search result",
                        "url": "https://example.test/source",
                        "snippet": "Fixture-only search evidence.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    connector = GeneralWebSearchConnector()

    package = connector.collect_fixture(
        request_id="HISYS-REQ-SEARCH-FIXTURE-001",
        query="fixture-only query",
        fixture_path=fixture,
        output_root=tmp_path,
        yyyymmdd="20260512",
    )

    access = json.loads((tmp_path / package.access_ref).read_text(encoding="utf-8"))
    assert package.access_record.external_call_made is False
    assert access["external_call_made"] is False
