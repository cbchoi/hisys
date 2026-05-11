from pathlib import Path

from hisys.cli.main import main


PUBLIC_PROFILE = """
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
""".strip() + "\n"


def test_validate_public_browser_profile_accepts_safe_profile(tmp_path: Path, capsys):
    profile = tmp_path / "public-browser.yaml"
    profile.write_text(PUBLIC_PROFILE, encoding="utf-8")

    assert main(["validate-public-browser-profile", "--profile", str(profile)]) == 0

    captured = capsys.readouterr()
    assert "public browser profile: valid" in captured.out
    assert "public-browser-beta" in captured.out


def test_validate_public_browser_profile_rejects_mutation(tmp_path: Path, capsys):
    profile = tmp_path / "bad-public-browser.yaml"
    profile.write_text(PUBLIC_PROFILE.replace("allow_mutation: false", "allow_mutation: true"), encoding="utf-8")

    assert main(["validate-public-browser-profile", "--profile", str(profile)]) == 2

    captured = capsys.readouterr()
    assert "public browser profile: invalid" in captured.err
    assert "mutation" in captured.err


def test_checked_in_public_browser_profile_validates(capsys):
    assert main([
        "validate-public-browser-profile",
        "--profile",
        "examples/instance/config/profiles/public-browser.yaml",
    ]) == 0
    captured = capsys.readouterr()
    assert "public browser profile: valid" in captured.out
