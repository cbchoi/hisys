"""Schema-backed MCP request/result contracts.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

McpToolStatus = Literal["ok", "blocked", "needs_more_evidence", "error"]


class McpSafetyFlags(BaseModel):
    """Explicit request-side authority flags; all fail closed by default."""

    external_call_allowed: bool = False
    mutation_allowed: bool = False
    publication_allowed: bool = False
    live_provider_allowed: bool = False


class McpRequestEnvelope(BaseModel):
    """Transport-neutral MCP tool request envelope."""

    request_id: str | None = None
    trace_id: str | None = None
    tool_name: str
    approval_ref: str | None = None
    safety: McpSafetyFlags = Field(default_factory=McpSafetyFlags)
    payload: dict[str, Any] = Field(default_factory=dict)


class McpToolResultEnvelope(BaseModel):
    """Transport-neutral MCP tool response envelope.

    Defaults intentionally do not infer authority from approval text. A future
    explicit approval contract may fill additional fields, but this first MCP
    slice remains local/read-only and human-reviewed by default.
    """

    status: McpToolStatus
    tool_name: str
    request_id: str | None = None
    trace_id: str | None = None
    external_call_made: bool = False
    mutation_performed: bool = False
    publication_or_live_action_approved: bool = False
    human_approval_required: bool = True
    artifact_refs: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


__all__ = [
    "McpRequestEnvelope",
    "McpSafetyFlags",
    "McpToolResultEnvelope",
    "McpToolStatus",
]
