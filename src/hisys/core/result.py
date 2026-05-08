"""Generic ``Result`` type for adapter and pipeline returns.

Traceability: HISYS-IDD-001 Section 2 (error status and retry policy in
common interface rules); HISYS-SDD-001 Section 8 (isolated failure
handling rather than raised exceptions across pipeline boundaries).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    """Outcome of a pipeline or adapter operation.

    Either ``value`` is populated (success) or ``error`` is populated
    (failure). ``audit_refs`` carries audit event IDs to be linked.
    """

    value: T | None = None
    error: str | None = None
    audit_refs: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.error is None

    @classmethod
    def success(cls, value: T, audit_refs: tuple[str, ...] = ()) -> "Result[T]":
        return cls(value=value, audit_refs=audit_refs)

    @classmethod
    def failure(cls, error: str, audit_refs: tuple[str, ...] = ()) -> "Result[T]":
        return cls(error=error, audit_refs=audit_refs)
