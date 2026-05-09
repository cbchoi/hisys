"""DARS configuration contract validation tests.

Traceability: HISYS-FR-AGT-001..005, HISYS-T-019, HISYS-T-020,
HISYS-CON-010, HISYS-CON-011, HISYS-CON-012.
"""

from __future__ import annotations

from pathlib import Path

from hisys.agents.dars_config import load_dars_config, validate_dars_config_document
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
        },
    }


def test_valid_dars_config_loads_concise_roles_and_disabled_backends(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    dars_path = config_dir / "dars.yaml"
    dars_path.write_text(
        """
schema_id: hisys.dars.config
schema_version: 0.1.0
config_id: dars-default
config_version: 0.1.0
owner: sysailab
status: draft
classification: runtime_config
traceability:
  requirements: [HISYS-FR-AGT-001, HISYS-T-019, HISYS-T-020]
  constraints: [HISYS-CON-010, HISYS-CON-011, HISYS-CON-012]
spec:
  default_backend: loopback_placeholder
  policy:
    enabled: false
    allowed_actions: advisory_only
    require_human_approval_for_external_call: true
    require_structured_output_schema: DarsCritiqueRecord
    allow_external_side_effects: false
    max_runtime_seconds: 300
    redact_markdown_outputs: true
  roles:
    default_devil_advocate:
      kind: devil_advocate
      profession: systems_safety_reviewer
      stance: skeptical_but_constructive
      strictness: high
      creativity: medium
      verbosity: concise_structured
      critique_dimensions: [unsupported_claims, counterarguments, risk_findings, missing_evidence]
      prompt:
        objective: "Challenge unsupported claims and hidden assumptions."
        focus: "Prefer evidence-linked objections over generic criticism."
      sampling:
        temperature: 0.2
        top_p: 0.9
        max_output_tokens: 2000
      output_contract: DarsCritiqueRecord
  backends:
    loopback_placeholder:
      kind: loopback
      enabled: true
      mode: local_only
      external_call_allowed: false
      output_contract: DarsCritiqueRecord
    claude_dars:
      kind: cli_agent
      enabled: false
      mode: read_only
      command: claude
      allowed_tools: [Read]
      disallowed_tools: [Edit, Write]
      external_call_allowed: false
      output_contract: DarsCritiqueRecord
""".lstrip(),
        encoding="utf-8",
    )

    config = load_dars_config(InstanceRoot(tmp_path))

    assert config.spec.default_backend == "loopback_placeholder"
    assert config.spec.roles["default_devil_advocate"].strictness == "high"
    assert config.spec.roles["default_devil_advocate"].prompt.objective.startswith("Challenge")
    assert config.spec.backends["claude_dars"].enabled is False


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
