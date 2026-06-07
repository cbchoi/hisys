"""Pure data contracts for separated Hisys subsystem services.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
Task 6.1.

These contracts describe transport-neutral invocation payloads for future
Altas, DARS, and Judge separation. They intentionally do not start subprocesses,
open live providers, mutate state, publish, or infer authority from approval
text. Defaults remain fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from hisys.mcp.contracts import McpSafetyFlags


@dataclass(frozen=True)
class ServiceInvocationEnvelope:
    """Common subsystem invocation envelope.

    ``safety`` is explicit and defaults inside :class:`McpSafetyFlags` are
    fail-closed. ``approval_ref`` records review context only; it does not grant
    live, mutation, publication, or provider authority.
    """

    request_id: str
    trace_id: str | None
    objective: str
    evidence_refs: tuple[str, ...]
    safety: McpSafetyFlags
    approval_ref: str | None = None


__all__ = ["ServiceInvocationEnvelope"]
