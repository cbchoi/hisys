"""M-CP-LIVE-4 local smoke runbook documentation tests."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "runbooks" / "dars-live-panel-localhost-smoke.md"


def test_live_panel_local_smoke_runbook_requires_operator_supplied_localhost_endpoint() -> None:
    """The live panel smoke runbook must keep real local-model calls human-gated."""

    text = RUNBOOK.read_text(encoding="utf-8")

    assert "operator-supplied localhost endpoint" in text
    assert "already-running localhost-only model endpoint" in text
    assert "HISYS_DARS_LOCAL_ENDPOINT" in text
    assert "http://127.0.0.1:<port>/v1/chat/completions" in text
    assert "--local-model-endpoint \"$HISYS_DARS_LOCAL_ENDPOINT\"" in text
    assert "--activation-packet" in text
    assert "--instance \"$HISYS_INSTANCE\"" in text
    assert "--config" not in text


def test_live_panel_local_smoke_runbook_preserves_stop_conditions_and_boundaries() -> None:
    """The smoke runbook must document explicit stop conditions and no-action boundaries."""

    text = RUNBOOK.read_text(encoding="utf-8")

    required_phrases = [
        "Do not run this procedure unless the operator has already started the model runner",
        "non-loopback endpoint",
        "missing activation packet",
        "credential requirement",
        "tool/search/browser permission",
        "mutation request",
        "failed secret scan",
        "human uncertainty",
        "external_call_made=false",
        "mutation_performed=false",
        "publication_performed=false",
        "allowed_actions=advisory_only",
        "No credential lookup",
        "No remote API",
        "No Authorization header",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_live_panel_local_smoke_runbook_is_traceable_to_live_increments() -> None:
    """The runbook should identify prerequisite fake-server and CLI rehearsal gates."""

    text = RUNBOOK.read_text(encoding="utf-8")

    for increment in ("M-CP-LIVE-1", "M-CP-LIVE-2", "M-CP-LIVE-3", "M-CP-LIVE-4"):
        assert increment in text
    assert "tests/unit/test_dars_critic_panel_live_config.py" in text
    assert "tests/unit/test_dars_critic_panel_live_adapter.py" in text
    assert "tests/unit/test_dars_critic_panel_cli.py" in text
