"""Configuration and runtime instance helpers."""

from .instance import InstanceRoot
from .loader import load_source_registry
from .obsidian_live import build_vault_plan, build_vault_template_plan, validate_vault_manifests, write_vault_plan_artifacts, write_vault_template_plan_artifacts, write_vault_validation_report
from .validation import ConfigEnvelope, ConfigValidationIssue, ConfigValidationReport, validate_config_document

__all__ = [
    "ConfigEnvelope",
    "ConfigValidationIssue",
    "ConfigValidationReport",
    "InstanceRoot",
    "build_vault_plan",
    "build_vault_template_plan",
    "load_source_registry",
    "validate_config_document",
    "validate_vault_manifests",
    "write_vault_plan_artifacts",
    "write_vault_template_plan_artifacts",
    "write_vault_validation_report",
]
