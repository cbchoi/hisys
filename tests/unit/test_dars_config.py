"""DARS configuration contract validation tests.

Traceability: HISYS-FR-AGT-001..005, HISYS-T-019, HISYS-T-020,
HISYS-CON-010, HISYS-CON-011, HISYS-CON-012.

Local DARS endpoint policy tests trace to the Local DARS / ByeSys
Provenance plan Milestone 1 (`docs/plans/2026-05-16-local-dars-byesys-provenance.md`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.agents.dars_config import (
    DarsBackendConfig,
    DarsConfig,
    build_dars_panel_config_from_hisys_config,
    derive_local_backend_metadata,
    load_dars_config,
    validate_dars_config_document,
)
from hisys.config.instance import InstanceRoot


def _minimal_dars_config() -> dict:
    return {
        "schema_id": "hisys.dars.config",
        "schema_version": "0.1.0",
        "config_id": "dars-default",
        "config_version": "0.1.0",
        "owner": "sysailab",
        "status": "draft",
        "classification": "runtime_config",
        "traceability": {
            "requirements": ["HISYS-FR-AGT-001", "HISYS-T-019", "HISYS-T-020"],
            "constraints": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
        },
        "spec": {
            "default_backend": "loopback_placeholder",
            "policy": {
                "enabled": False,
                "allowed_actions": "advisory_only",
                "require_human_approval_for_external_call": True,
                "require_structured_output_schema": "DarsCritiqueRecord",
                "allow_external_side_effects": False,
                "max_runtime_seconds": 300,
                "redact_markdown_outputs": True,
            },
            "roles": {
                "default_devil_advocate": {
                    "kind": "devil_advocate",
                    "profession": "systems_safety_reviewer",
                    "stance": "skeptical_but_constructive",
                    "strictness": "high",
                    "creativity": "medium",
                    "verbosity": "concise_structured",
                    "critique_dimensions": ["unsupported_claims", "counterarguments", "risk_findings", "missing_evidence"],
                    "prompt": {
                        "objective": "Challenge unsupported claims and hidden assumptions.",
                        "focus": "Prefer evidence-linked objections over generic criticism.",
                    },
                    "sampling": {"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 2000},
                    "output_contract": "DarsCritiqueRecord",
                }
            },
            "backends": {
                "loopback_placeholder": {
                    "kind": "loopback",
                    "enabled": True,
                    "mode": "local_only",
                    "external_call_allowed": False,
                    "output_contract": "DarsCritiqueRecord",
                },
                "claude_dars": {
                    "kind": "cli_agent",
                    "enabled": False,
                    "mode": "read_only",
                    "command": "claude",
                    "allowed_tools": ["Read"],
                    "disallowed_tools": ["Edit", "Write"],
                    "external_call_allowed": False,
                    "output_contract": "DarsCritiqueRecord",
                },
            },
            "panels": {},
        },
    }


def test_valid_dars_config_loads_concise_roles_and_disabled_backends(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    dars_path = config_dir / "dars.json"
    dars_path.write_text(json.dumps(_minimal_dars_config(), indent=2), encoding="utf-8")

    config = load_dars_config(InstanceRoot(tmp_path))

    assert config.spec.default_backend == "loopback_placeholder"
    assert config.spec.roles["default_devil_advocate"].strictness == "high"
    assert config.spec.roles["default_devil_advocate"].prompt.objective.startswith("Challenge")
    assert config.spec.backends["claude_dars"].enabled is False


def test_active_runtime_config_may_select_enabled_cli_agent_backend():
    data = _minimal_dars_config()
    data["status"] = "active"
    data["spec"]["default_backend"] = "claude_dars"
    data["spec"]["policy"]["enabled"] = True
    data["spec"]["backends"]["claude_dars"]["enabled"] = True
    data["spec"]["backends"]["claude_dars"]["model"] = "sonnet"

    report = validate_dars_config_document(data, config_ref="inline://active-runtime-dars")

    assert report.valid is True


def test_hisys_dars_config_can_define_named_panel_without_sidecar_file():
    """R4 mapped panel prep: panel composition belongs in Hisys DARS config, not hardcoded CLI JSON."""

    data = _minimal_dars_config()
    data["spec"]["backends"]["codex_subscription_dars"] = {
        "kind": "remote_subscription",
        "enabled": False,
        "mode": "external_api",
        "external_call_allowed": False,
        "credential_ref": "subscription-account-ref://codex/default",
        "output_contract": "DarsCritiqueRecord",
    }
    data["spec"]["panels"] = {
        "r4_mapped_subscription_panel": {
            "panel_id": "PANEL-DARS-R4-MAPPED-SUBSCRIPTION-CONFIGURED",
            "max_parallel_critics": 2,
            "failure_policy": "continue_collect_errors",
            "advisory_only": True,
            "critics": [
                {
                    "critic_id": "logical-devil",
                    "critic_role": "logical_devil",
                    "backend_id": "codex_subscription_dars",
                    "rubric_ref": "docs/rubrics/dars/logical-devil.md",
                    "critique_dimensions": ["claim_consistency", "logical_validity"],
                    "external_call_allowed": False,
                    "mutation_allowed": False,
                },
                {
                    "critic_id": "evidence-governance-devil",
                    "critic_role": "evidence_governance_devil",
                    "backend_id": "codex_subscription_dars",
                    "rubric_ref": "docs/rubrics/dars/evidence-governance-devil.md",
                    "critique_dimensions": ["evidence_sufficiency", "boundary_truthfulness"],
                    "external_call_allowed": False,
                    "mutation_allowed": False,
                },
            ],
        }
    }

    report = validate_dars_config_document(data, config_ref="inline://dars-panel-configured")
    assert report.valid is True

    panel = build_dars_panel_config_from_hisys_config(
        DarsConfig.model_validate(data),
        panel_key="r4_mapped_subscription_panel",
    )
    assert panel.panel_id == "PANEL-DARS-R4-MAPPED-SUBSCRIPTION-CONFIGURED"
    assert panel.max_parallel_critics == 2
    assert [critic.critic_id for critic in panel.critics] == [
        "logical-devil",
        "evidence-governance-devil",
    ]
    assert all(critic.backend_id == "codex_subscription_dars" for critic in panel.critics)


def test_hisys_dars_config_rejects_panel_unknown_backend():
    data = _minimal_dars_config()
    data["spec"]["panels"] = {
        "bad_panel": {
            "panel_id": "PANEL-BAD",
            "critics": [
                {
                    "critic_id": "logical-devil",
                    "critic_role": "logical_devil",
                    "backend_id": "missing_backend",
                    "rubric_ref": "docs/rubrics/dars/logical-devil.md",
                }
            ],
        }
    }

    report = validate_dars_config_document(data, config_ref="inline://bad-panel")

    assert report.valid is False
    assert {issue.code for issue in report.issues} >= {"unknown_panel_backend"}


def test_dars_config_validation_rejects_policy_and_schema_violations():
    data = _minimal_dars_config()
    data["spec"]["roles"]["default_devil_advocate"]["strictness"] = "extreme"
    data["spec"]["roles"]["default_devil_advocate"]["summary"] = "Long prose outside prompt is ambiguous."
    data["spec"]["roles"]["default_devil_advocate"]["sampling"]["temperature"] = 1.5
    data["spec"]["backends"]["claude_dars"]["enabled"] = True
    data["spec"]["backends"]["claude_dars"]["api_key"] = "sk-test-should-not-appear"
    data["spec"]["backends"]["claude_dars"]["output_contract"] = "PlainText"

    report = validate_dars_config_document(data, config_ref="inline://bad-dars")

    assert report.valid is False
    by_path = {issue.path: issue.code for issue in report.issues}
    assert by_path["spec.roles.default_devil_advocate.strictness"] == "invalid_enum_value"
    assert by_path["spec.roles.default_devil_advocate.summary"] == "interpretive_text_outside_prompt"
    assert by_path["spec.roles.default_devil_advocate.sampling.temperature"] == "invalid_sampling_bounds"
    assert by_path["spec.backends.claude_dars.enabled"] == "non_loopback_backend_enabled_by_default"
    assert by_path["spec.backends.claude_dars.api_key"] == "raw_secret_value_not_allowed"
    assert by_path["spec.backends.claude_dars.output_contract"] == "invalid_output_contract"


# ---------------------------------------------------------------------------
# Local DARS / ByeSys provenance plan — Milestone 1 (Ralph M8.1)
# Strict localhost endpoint policy for `openai_compatible` + `local_network_only`.
# ---------------------------------------------------------------------------


def _local_openai_compatible_backend(
    endpoint: str | None = "http://127.0.0.1:11434/v1/chat/completions",
) -> dict:
    return {
        "kind": "openai_compatible",
        "enabled": False,
        "mode": "local_network_only",
        "endpoint": endpoint,
        "model": "qwen2.5:14b-instruct",
        "external_call_allowed": False,
        "output_contract": "DarsCritiqueRecord",
    }


def _config_with_local_backend(endpoint: str | None) -> dict:
    data = _minimal_dars_config()
    data["spec"]["backends"]["local_llm_dars"] = _local_openai_compatible_backend(endpoint)
    return data


def _endpoint_codes(report) -> set[str]:
    return {
        issue.code
        for issue in report.issues
        if issue.path == "spec.backends.local_llm_dars.endpoint"
    }


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://localhost:11434/v1/chat/completions",
        "http://localhost/v1/chat/completions",
        "https://localhost:8443/v1/chat/completions",
    ],
)
def test_local_openai_compatible_backend_accepts_localhost_hostname(endpoint: str):
    data = _config_with_local_backend(endpoint)
    report = validate_dars_config_document(data, config_ref="inline://local-llm")
    # The endpoint itself must not raise localhost-policy issues.
    blocking = {"non_local_endpoint", "missing_endpoint", "missing_endpoint_host", "unsupported_endpoint_scheme"}
    assert not (_endpoint_codes(report) & blocking)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://127.0.0.1:11434/v1/chat/completions",
        "http://127.0.0.1/v1/chat/completions",
        "http://127.0.0.2:11434/v1/chat/completions",
    ],
)
def test_local_openai_compatible_backend_accepts_ipv4_loopback_endpoint(endpoint: str):
    data = _config_with_local_backend(endpoint)
    report = validate_dars_config_document(data, config_ref="inline://local-llm-v4")
    blocking = {"non_local_endpoint", "missing_endpoint", "missing_endpoint_host", "unsupported_endpoint_scheme"}
    assert not (_endpoint_codes(report) & blocking)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://[::1]:11434/v1/chat/completions",
        "http://[::1]/v1/chat/completions",
    ],
)
def test_local_openai_compatible_backend_accepts_ipv6_loopback_endpoint(endpoint: str):
    data = _config_with_local_backend(endpoint)
    report = validate_dars_config_document(data, config_ref="inline://local-llm-v6")
    blocking = {"non_local_endpoint", "missing_endpoint", "missing_endpoint_host", "unsupported_endpoint_scheme"}
    assert not (_endpoint_codes(report) & blocking)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://203.0.113.5:11434/v1/chat/completions",
        "http://example.com:11434/v1/chat/completions",
        "http://10.0.0.1:11434/v1/chat/completions",
        "http://192.168.1.1:11434/v1/chat/completions",
        "http://[2001:db8::1]:11434/v1/chat/completions",
    ],
)
def test_local_openai_compatible_backend_rejects_remote_endpoint(endpoint: str):
    data = _config_with_local_backend(endpoint)
    report = validate_dars_config_document(data, config_ref="inline://remote-llm")
    assert "non_local_endpoint" in _endpoint_codes(report)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://localhost.evil.com:11434/v1/chat/completions",
        "http://127.0.0.1.evil.com:11434/v1/chat/completions",
        "http://evil-localhost:11434/v1/chat/completions",
        "http://localhost-evil.com/v1/chat/completions",
    ],
)
def test_local_openai_compatible_backend_rejects_deceptive_localhost_suffix(endpoint: str):
    data = _config_with_local_backend(endpoint)
    report = validate_dars_config_document(data, config_ref="inline://deceptive-llm")
    assert "non_local_endpoint" in _endpoint_codes(report)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://localhost@evil.com:11434/v1/chat/completions",
        "http://user:pass@evil.com:11434/v1/chat/completions",
        "http://127.0.0.1@evil.com:11434/v1/chat/completions",
    ],
)
def test_local_openai_compatible_backend_rejects_userinfo_host_trick(endpoint: str):
    data = _config_with_local_backend(endpoint)
    report = validate_dars_config_document(data, config_ref="inline://userinfo-llm")
    assert "non_local_endpoint" in _endpoint_codes(report)


@pytest.mark.parametrize(
    "endpoint,expected_code",
    [
        ("ftp://127.0.0.1:11434/v1/chat/completions", "unsupported_endpoint_scheme"),
        ("file:///tmp/127.0.0.1/v1/chat/completions", "unsupported_endpoint_scheme"),
        ("ws://127.0.0.1:11434/v1/chat/completions", "unsupported_endpoint_scheme"),
        ("http://", "missing_endpoint_host"),
        (None, "missing_endpoint"),
        ("", "missing_endpoint"),
    ],
)
def test_local_openai_compatible_backend_rejects_missing_or_unsupported_scheme(
    endpoint: str | None, expected_code: str
):
    data = _config_with_local_backend(endpoint)
    report = validate_dars_config_document(data, config_ref="inline://scheme-llm")
    assert expected_code in _endpoint_codes(report)


def test_local_openai_compatible_backend_exposes_localhost_metadata():
    backend = DarsBackendConfig.model_validate(_local_openai_compatible_backend())
    metadata = derive_local_backend_metadata(backend)
    assert metadata == {
        "endpoint_scope": "localhost_only",
        "model_boundary_required": True,
        "external_call_expected": False,
    }


def test_derive_local_backend_metadata_is_empty_for_non_local_backends():
    cli_backend = DarsBackendConfig.model_validate(
        {
            "kind": "cli_agent",
            "enabled": False,
            "mode": "read_only",
            "command": "claude",
            "allowed_tools": ["Read"],
            "disallowed_tools": ["Edit"],
            "external_call_allowed": False,
            "output_contract": "DarsCritiqueRecord",
        }
    )
    assert derive_local_backend_metadata(cli_backend) == {}

    external_backend = DarsBackendConfig.model_validate(
        {
            "kind": "openai_compatible",
            "enabled": False,
            "mode": "external_api",
            "endpoint": "https://api.example.com/v1/chat/completions",
            "model": "remote",
            "external_call_allowed": True,
            "credential_ref": "ref://remote",
            "output_contract": "DarsCritiqueRecord",
        }
    )
    assert derive_local_backend_metadata(external_backend) == {}


def test_local_openai_compatible_backend_does_not_require_credential_ref():
    data = _config_with_local_backend("http://127.0.0.1:11434/v1/chat/completions")
    report = validate_dars_config_document(data, config_ref="inline://no-cred")
    cred_codes = {
        issue.code
        for issue in report.issues
        if issue.path == "spec.backends.local_llm_dars.credential_ref"
    }
    assert "missing_credential_ref" not in cred_codes
