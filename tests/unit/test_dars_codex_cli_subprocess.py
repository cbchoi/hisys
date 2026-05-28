"""Codex CLI subprocess prompt-mode preparation tests.

Traceability: DARS-CODEX-CLI-SUBPROCESS-PROMPT-MODE-PREP,
DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP,
docs/runbooks/dars-codex-subscription-executor-runbook.md,
docs/plans/dars-codex-cli-subprocess-failure-mode-fixture-prep-tasks.md.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from hisys.config.instance import InstanceRoot


def _codex_policy_data(**overrides):
    data = {
        "policy_id": "DARS-CODEX-POLICY-20260522-001",
        "approval_ref": "APPROVAL-DARS-CODEX-20260522-001",
        "operator_id": "operator:cbchoi",
        "provider_id": "codex",
        "access_mode": "subscription",
        "subscription_account_ref": "vault://existing-auth/codex-subscription",
        "adapter_class": "codex_subscription",
        "redaction_policy_ref": "policy://hisys/dars/codex-subscription-redaction-v1",
        "egress_scope": "subscription_only",
        "max_session_or_token_budget": 100000,
        "expires_at": "2026-06-22T00:00:00Z",
        "revocation_ref": "revocation://dars/codex/subscription-001",
        "audit_required": True,
    }
    data.update(overrides)
    return data


def _codex_activation_data(policy_ref: str, **overrides):
    data = {
        "activation_id": "DARS-CODEX-ACT-20260522-001",
        "backend_id": "codex_subscription_dars",
        "backend_kind": "remote_subscription",
        "endpoint_scope": "external_api",
        "allowed_actions": "advisory_only",
        "human_approved": True,
        "approval_ref": "APPROVAL-DARS-CODEX-20260522-001",
        "expires_at": "2026-06-22T00:00:00Z",
        "remote_policy_packet_ref": policy_ref,
    }
    data.update(overrides)
    return data


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _executor_payload(prompt: str = "Critique the bounded DARS evidence summary only.") -> dict[str, object]:
    return {
        "request_id": "REQ-DARS-CODEX-001",
        "source_execution_id": "EXEC-DARS-CODEX-001",
        "backend_id": "codex_subscription_dars",
        "backend_kind": "remote_subscription",
        "provider_id": "codex",
        "adapter_class": "codex_subscription",
        "approval_ref": "APPROVAL-DARS-CODEX-20260522-001",
        "policy_ref": "docs/examples/dars/codex-subscription-policy.recommended.json",
        "activation_ref": "docs/examples/dars/codex-subscription-activation.recommended.json",
        "allowed_actions": "advisory_only",
        "prompt": prompt,
        "external_call_made": True,
        "mutation_performed": False,
        "publication_performed": False,
        "transport_kind": "codex_cli_subprocess_prompt_mode",
    }


def test_prepare_codex_scratch_git_workdir_creates_ephemeral_repo_under_instance(tmp_path: Path):
    from hisys.agents.dars_codex_cli_subprocess import prepare_codex_scratch_git_workdir

    scratch = prepare_codex_scratch_git_workdir(tmp_path, request_id="REQ-DARS-CODEX-001")

    assert scratch == tmp_path / "codex-cli-scratch" / "REQ-DARS-CODEX-001"
    assert (scratch / ".git").is_dir()
    assert scratch.is_dir()


def test_codex_cli_prompt_mode_executor_uses_read_only_noninteractive_command(tmp_path: Path):
    from hisys.agents.dars_codex_cli_subprocess import (
        CodexCliSubprocessConfig,
        build_codex_cli_prompt_mode_executor,
        prepare_codex_scratch_git_workdir,
    )

    calls = []

    def fake_runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="  Codex advisory critique text.  ", stderr="")

    workdir = prepare_codex_scratch_git_workdir(tmp_path, request_id="REQ-DARS-CODEX-001")
    executor = build_codex_cli_prompt_mode_executor(
        CodexCliSubprocessConfig(
            codex_executable="/usr/bin/codex",
            workdir=workdir,
            timeout_seconds=15,
        ),
        runner=fake_runner,
    )

    critique = executor(_executor_payload())

    assert critique == "Codex advisory critique text."
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[:7] == [
        "/usr/bin/codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--sandbox",
        "read-only",
        "--cd",
    ]
    assert argv[7] == str(workdir)
    assert argv[8] == "--"
    prompt_arg = argv[9]
    assert "transport_kind=codex_cli_subprocess_prompt_mode" in prompt_arg
    assert "allowed_actions=advisory_only" in prompt_arg
    assert "Do not mutate files" in prompt_arg
    assert "Do not use web search" in prompt_arg
    forbidden_flags = {
        "--search",
        "--full-auto",
        "--yolo",
        "--dangerously-bypass-approvals-and-sandbox",
        "danger-full-access",
    }
    assert forbidden_flags.isdisjoint(set(argv))
    assert kwargs["cwd"] == workdir
    assert kwargs["timeout"] == 15
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["check"] is False
    assert kwargs["shell"] is False
    assert set(kwargs["env"]) == {"PATH"}


@pytest.mark.parametrize(
    ("payload_override", "error_code"),
    [
        ({"provider_id": "claude"}, "codex_cli_invalid_provider"),
        ({"adapter_class": "claude_subscription"}, "codex_cli_invalid_adapter_class"),
        ({"allowed_actions": "mutation_allowed"}, "codex_cli_invalid_allowed_actions"),
        ({"mutation_performed": True}, "codex_cli_mutation_flag_not_allowed"),
        ({"publication_performed": True}, "codex_cli_publication_flag_not_allowed"),
        ({"prompt": "contains " + "api" + "_" + "key" + "=" + "sk" + "-test-secret"}, "codex_cli_prompt_not_redacted"),
    ],
)
def test_codex_cli_prompt_mode_executor_fails_closed_before_runner(
    tmp_path: Path, payload_override: dict[str, object], error_code: str
):
    from hisys.agents.dars_codex_cli_subprocess import (
        CodexCliSubprocessConfig,
        build_codex_cli_prompt_mode_executor,
    )

    contacted = False

    def fail_if_called(_argv, **_kwargs):
        nonlocal contacted
        contacted = True
        raise AssertionError("runner must not be contacted")

    workdir = tmp_path / "codex-workdir"
    workdir.mkdir()
    payload = _executor_payload()
    payload.update(payload_override)
    executor = build_codex_cli_prompt_mode_executor(
        CodexCliSubprocessConfig(codex_executable="codex", workdir=workdir),
        runner=fail_if_called,
    )

    with pytest.raises(ValueError, match=error_code):
        executor(payload)

    assert contacted is False


def test_codex_cli_prompt_mode_executor_fails_closed_on_empty_or_failed_output(tmp_path: Path):
    from hisys.agents.dars_codex_cli_subprocess import (
        CodexCliSubprocessConfig,
        build_codex_cli_prompt_mode_executor,
    )

    workdir = tmp_path / "codex-workdir"
    workdir.mkdir()

    def empty_runner(_argv, **_kwargs):
        return SimpleNamespace(returncode=0, stdout="   ", stderr="")

    executor = build_codex_cli_prompt_mode_executor(
        CodexCliSubprocessConfig(codex_executable="codex", workdir=workdir),
        runner=empty_runner,
    )
    with pytest.raises(ValueError, match="codex_cli_subprocess_empty_output"):
        executor(_executor_payload())

    def failed_runner(_argv, **_kwargs):
        return SimpleNamespace(returncode=2, stdout="", stderr="sandbox failed")

    executor = build_codex_cli_prompt_mode_executor(
        CodexCliSubprocessConfig(codex_executable="codex", workdir=workdir),
        runner=failed_runner,
    )
    with pytest.raises(ValueError, match="codex_cli_subprocess_failed"):
        executor(_executor_payload())


def test_dispatch_boundary_can_record_codex_cli_subprocess_transport_kind(tmp_path: Path):
    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _codex_policy_data())
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _codex_activation_data(str(policy_ref)),
    )

    def fake_codex_cli_executor(payload):
        assert payload["provider_id"] == "codex"
        assert payload["adapter_class"] == "codex_subscription"
        assert payload["transport_kind"] == "codex_cli_subprocess_prompt_mode"
        return "Codex CLI subprocess advisory critique."

    result = run_dars_remote_subscription_dispatch(
        InstanceRoot(tmp_path),
        RemoteSubscriptionDispatchRequest(
            yyyymmdd="20260522",
            request_id="REQ-DARS-CODEX-001",
            backend_id="codex_subscription_dars",
            backend_kind="remote_subscription",
            source_execution_id="EXEC-DARS-CODEX-001",
            approval_ref="APPROVAL-DARS-CODEX-20260522-001",
            activation_packet_ref=str(activation_ref),
            policy_packet_ref=str(policy_ref),
            prompt="Critique bounded evidence only.",
            transport_kind="codex_cli_subprocess_prompt_mode",
        ),
        executor=fake_codex_cli_executor,
    )

    boundary = json.loads((tmp_path / result.boundary_ref).read_text(encoding="utf-8"))
    assert boundary["transport_kind"] == "codex_cli_subprocess_prompt_mode"
    assert boundary["provider_id"] == "codex"
    assert boundary["adapter_class"] == "codex_subscription"
    assert boundary["external_call_made"] is True
    assert boundary["mutation_performed"] is False
    assert boundary["publication_performed"] is False


# ---------------------------------------------------------------------------
# DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP focused cohort
# Anchored by docs/plans/dars-codex-cli-subprocess-failure-mode-fixture-prep-tasks.md.
# ---------------------------------------------------------------------------


def _build_executor_with_runner(tmp_path: Path, runner):
    from hisys.agents.dars_codex_cli_subprocess import (
        CodexCliSubprocessConfig,
        build_codex_cli_prompt_mode_executor,
    )

    workdir = tmp_path / "codex-workdir"
    workdir.mkdir(exist_ok=True)
    return build_codex_cli_prompt_mode_executor(
        CodexCliSubprocessConfig(
            codex_executable="/usr/bin/codex",
            workdir=workdir,
            timeout_seconds=17,
        ),
        runner=runner,
    )


def test_codex_cli_subprocess_timeout_fails_closed_with_deterministic_code(tmp_path: Path):
    def timeout_runner(argv, **kwargs):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs.get("timeout", 0))

    executor = _build_executor_with_runner(tmp_path, timeout_runner)

    with pytest.raises(ValueError) as excinfo:
        executor(_executor_payload())

    message = str(excinfo.value)
    assert message.startswith("codex_cli_subprocess_timeout")
    assert "timeout_seconds=17" in message


def test_codex_cli_subprocess_failed_redacts_secret_like_stderr(tmp_path: Path):
    secret_token = "sk" + "-" + "live" + "-leak-1234567890"
    stderr_payload = (
        "fatal error\n"
        "Auth" + "orization:" + " Bearer " + secret_token + "\n"
        "ap" + "i_" + "key=" + secret_token + "\n"
    )

    def failed_runner(argv, **kwargs):
        return SimpleNamespace(returncode=3, stdout="", stderr=stderr_payload)

    executor = _build_executor_with_runner(tmp_path, failed_runner)

    with pytest.raises(ValueError) as excinfo:
        executor(_executor_payload())

    message = str(excinfo.value)
    assert message.startswith("codex_cli_subprocess_failed: returncode=3")
    assert secret_token not in message
    assert "Bearer " + secret_token not in message
    assert "stderr-redacted-secret-detected" in message


def test_codex_cli_subprocess_failed_preserves_non_secret_stderr(tmp_path: Path):
    stderr_payload = "sandbox read-only: cannot open /etc/shadow"

    def failed_runner(argv, **kwargs):
        return SimpleNamespace(returncode=2, stdout="", stderr=stderr_payload)

    executor = _build_executor_with_runner(tmp_path, failed_runner)

    with pytest.raises(ValueError) as excinfo:
        executor(_executor_payload())

    message = str(excinfo.value)
    assert message.startswith("codex_cli_subprocess_failed: returncode=2")
    assert stderr_payload in message


@pytest.mark.parametrize(
    "stdout_value",
    ["", "   ", "\n\n\n", "\t \t", "\r\n  \r\n"],
)
def test_codex_cli_subprocess_blank_output_variants_fail_closed(tmp_path: Path, stdout_value: str):
    def blank_runner(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout=stdout_value, stderr="")

    executor = _build_executor_with_runner(tmp_path, blank_runner)

    with pytest.raises(ValueError, match="codex_cli_subprocess_empty_output"):
        executor(_executor_payload())


def test_codex_cli_subprocess_output_too_long_fails_closed(tmp_path: Path):
    long_output = "A" * 32_001

    def long_runner(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout=long_output, stderr="")

    executor = _build_executor_with_runner(tmp_path, long_runner)

    with pytest.raises(ValueError, match="codex_cli_subprocess_output_too_long"):
        executor(_executor_payload())


@pytest.mark.parametrize(
    "control_payload",
    [
        "Critique body\x00 with null",
        "Critique body\x07 with bell",
        "Critique body\x1b[31m with escape",
        "Critique body\x08 with backspace",
    ],
)
def test_codex_cli_subprocess_output_with_control_chars_fails_closed(
    tmp_path: Path, control_payload: str
):
    def control_runner(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout=control_payload, stderr="")

    executor = _build_executor_with_runner(tmp_path, control_runner)

    with pytest.raises(
        ValueError, match="codex_cli_subprocess_output_contains_control_chars"
    ):
        executor(_executor_payload())


def test_codex_cli_subprocess_output_preserves_tab_newline_cr(tmp_path: Path):
    payload = "Critique line one.\n- Risk:\trecorded.\r\n- Recommendation: rerun fixtures."

    def ok_runner(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout=payload, stderr="")

    executor = _build_executor_with_runner(tmp_path, ok_runner)

    critique = executor(_executor_payload())

    assert critique == payload.strip()


@pytest.mark.parametrize(
    "claim_payload",
    [
        "workspace_write: true",
        "Workspace-Write := True",
        "web_search: true",
        "Web Search: True",
        "sandbox bypass requested",
        "danger-full-access requested",
        "mutation_performed: true",
        "publication_performed: true",
        "requires_human_review: false",
        "<<executing shell>>",
        "<<tool call>>: please run rm -rf /",
    ],
)
def test_codex_cli_subprocess_output_claiming_unauthorized_authority_fails_closed(
    tmp_path: Path, claim_payload: str
):
    full_output = f"Advisory critique header\n- {claim_payload}\n- end."

    def claim_runner(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout=full_output, stderr="")

    executor = _build_executor_with_runner(tmp_path, claim_runner)

    with pytest.raises(
        ValueError, match="codex_cli_subprocess_output_claims_unauthorized_authority"
    ):
        executor(_executor_payload())


@pytest.mark.parametrize(
    "secret_fragment",
    [
        "sk" + "-" + "abc123XYZ",
        "sk" + "_" + "abc123XYZ",
        "ghp" + "_" + "abc123XYZ",
        "xo" + "xb-" + "abc123XYZ",
        "xo" + "xp-" + "abc123XYZ",
        "hf" + "_" + "abc123XYZ",
        "Auth" + "orization:" + " Bearer abc123XYZ",
        "ap" + "i_" + "key=" + "abc123XYZ",
        "refresh" + "_token=" + "abc123XYZ",
        "access" + "_token=" + "abc123XYZ",
    ],
)
def test_codex_cli_subprocess_secret_like_output_fails_closed(
    tmp_path: Path, secret_fragment: str
):
    full_output = f"Advisory critique header\nLeaked: {secret_fragment}\nEnd."

    def leak_runner(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout=full_output, stderr="")

    executor = _build_executor_with_runner(tmp_path, leak_runner)

    with pytest.raises(ValueError, match="codex_cli_output_not_redacted"):
        executor(_executor_payload())


def test_codex_cli_subprocess_allows_benign_governance_boundary_terms(tmp_path: Path):
    full_output = (
        "Advisory critique only. Credential lookup was not performed. "
        "The existing-auth reference remains abstract, requires_human_review stays true, "
        "and no secret value, token field, Authorization header, mutation, or publication is present."
    )

    def governance_runner(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout=full_output, stderr="")

    executor = _build_executor_with_runner(tmp_path, governance_runner)

    assert executor(_executor_payload()) == full_output
