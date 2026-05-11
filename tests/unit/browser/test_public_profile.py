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
    assert profile.transport_kind == "playwright_live"


def test_public_browser_profile_rejects_credentials():
    bad = _valid_profile()
    bad["allow_credentials"] = True
    with pytest.raises(ValidationError):
        PublicBrowserProfile.model_validate(bad)


def test_public_browser_profile_rejects_mutation():
    bad = _valid_profile()
    bad["allow_mutation"] = True
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


def test_public_browser_profile_rejects_camoufox_without_experimental_flag():
    bad = _valid_profile()
    bad["connector_id"] = "camoufox_read_only"
    bad["transport_kind"] = "camoufox_live"
    with pytest.raises(ValidationError):
        PublicBrowserProfile.model_validate(bad)
