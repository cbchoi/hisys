import json

from hisys.cli.main import main


def test_get_run_summary_prints_json_summary(tmp_path, capsys):
    summary_dir = tmp_path / "reports" / "run-summaries" / "20260511"
    summary_dir.mkdir(parents=True)
    summary_dir.joinpath("public-browser-run-summary.json").write_text(
        json.dumps(
            {
                "schema_id": "hisys.public_browser_run_summary",
                "request_id": "HISYS-REQ-DEMO-001",
                "final_decision": "accept_for_human_reviewed_use",
                "mutation_performed": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = main(["get-run-summary", "--instance", str(tmp_path), "--date", "20260511"])

    assert result == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["request_id"] == "HISYS-REQ-DEMO-001"
    assert printed["final_decision"] == "accept_for_human_reviewed_use"
    assert printed["mutation_performed"] is False


def test_list_run_artifacts_returns_safe_relative_refs(tmp_path, capsys):
    paths = [
        "reports/run-summaries/20260511/public-browser-run-summary.json",
        "data/chief-editor-final-browser-reviews/20260511/FINAL-CHIEF-REVIEW-HISYS-REQ-DEMO-001-BROWSER.json",
        "data/evidence-packages/20260511/HISYS-REQ-DEMO-001-BROWSER.json",
    ]
    for ref in paths:
        path = tmp_path / ref
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"ok": true}\n', encoding="utf-8")

    result = main(
        [
            "list-run-artifacts",
            "--instance",
            str(tmp_path),
            "--date",
            "20260511",
            "--request-id",
            "HISYS-REQ-DEMO-001",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    refs = {item["ref"] for item in payload["artifacts"]}
    assert "reports/run-summaries/20260511/public-browser-run-summary.json" in refs
    assert "data/chief-editor-final-browser-reviews/20260511/FINAL-CHIEF-REVIEW-HISYS-REQ-DEMO-001-BROWSER.json" in refs
    assert all(not ref.startswith("/") and ".." not in ref for ref in refs)


def test_show_artifact_blocks_path_traversal(tmp_path, capsys):
    result = main(["show-artifact", "--instance", str(tmp_path), "--ref", "../secret.json"])

    assert result == 2
    captured = capsys.readouterr()
    assert "unsafe" in captured.err
