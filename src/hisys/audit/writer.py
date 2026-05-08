"""Audit JSONL writer.

Traceability: HISYS-D-015, HISYS-FR-ADM-002, HISYS-T-008,
HISYS-R-008.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ..config import InstanceRoot
from ..schemas import AuditEvent

_SECRET_PATTERNS = [
    re.compile(r"(?i)(token|api[_-]?key|password|secret)=([^\s,;]+)"),
]


def redact_text(text: str) -> str:
    """Redact simple inline credential patterns before persistence."""

    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]", redacted)
    return redacted


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_value(item) for key, item in value.items()}
    return value


class AuditJsonlWriter:
    """Append AuditEvent records under ``data/audit/<YYYYMMDD>/``."""

    def __init__(self, instance: InstanceRoot) -> None:
        self.instance = instance

    def append(self, event: AuditEvent, *, yyyymmdd: str) -> Path:
        path = self.instance.audit_log_path(yyyymmdd)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = event.model_dump(mode="json") if isinstance(event, BaseModel) else dict(event)
        payload = _redact_value(payload)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return path


__all__ = ["AuditJsonlWriter", "redact_text"]
