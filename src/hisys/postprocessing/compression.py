"""Optional lossy compression for Hisys presentation digests.

This module deliberately sits after Hisys evidence generation. It can shorten a
user-facing or agent-facing digest, but it must never replace runtime-boundary,
evidence-store, DARS, or audit artifacts as the system of record.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_SECRET_PATTERNS = (
    re.compile(r"DUMMY_SECRET_TOKEN_[A-Za-z0-9_\-]+"),
    re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[^\s,'\"]{8,}"),
)


@dataclass(frozen=True)
class PostprocessingCompressionConfig:
    """Configuration for optional presentation-only compression."""

    enabled: bool = False
    engine: str = "headroom"
    mode: str = "digest_only"
    min_chars: int = 4000
    require_original_artifact_ref: bool = True
    fail_open: bool = True
    redact_before_compress: bool = True


@dataclass(frozen=True)
class CompressionMetadata:
    """Machine-readable compression boundary record."""

    engine: str
    mode: str
    applied: bool
    lossy: bool
    failed: bool
    original_chars: int
    compressed_chars: int
    redacted_before_compress: bool = False
    failure_reason: str = ""


@dataclass(frozen=True)
class CompressedDigestResult:
    """Digest plus explicit pointer to the uncompressed source artifact."""

    digest: str
    original_artifact_ref: str
    compression: CompressionMetadata

    def as_tool_result_fragment(self) -> dict[str, Any]:
        """Return JSON-serializable fields for a Hisys tool result."""

        return {
            "summary": self.digest,
            "original_artifact_ref": self.original_artifact_ref,
            "compression": {
                "engine": self.compression.engine,
                "mode": self.compression.mode,
                "applied": self.compression.applied,
                "lossy": self.compression.lossy,
                "failed": self.compression.failed,
                "original_chars": self.compression.original_chars,
                "compressed_chars": self.compression.compressed_chars,
                "redacted_before_compress": self.compression.redacted_before_compress,
                "failure_reason": self.compression.failure_reason,
            },
        }


def compress_digest(
    digest: str,
    *,
    original_artifact_ref: str,
    config: PostprocessingCompressionConfig | None = None,
) -> CompressedDigestResult:
    """Optionally compress a presentation digest without touching evidence.

    The returned object always carries ``original_artifact_ref``. Compression is
    skipped unless explicitly enabled, the digest is long enough, and the engine
    succeeds with a shorter result. Runtime failures fall back to the original
    digest when ``fail_open`` is true, preserving Hisys core behavior.
    """

    cfg = config or PostprocessingCompressionConfig()
    original_chars = len(digest)
    if not cfg.enabled:
        return _unchanged(digest, original_artifact_ref, cfg, engine="none")
    if cfg.mode != "digest_only":
        return _failed(digest, original_artifact_ref, cfg, f"unsupported compression mode: {cfg.mode}")
    if cfg.require_original_artifact_ref and not original_artifact_ref:
        return _failed(digest, original_artifact_ref, cfg, "original_artifact_ref is required")
    if original_chars < max(0, int(cfg.min_chars)):
        return _unchanged(digest, original_artifact_ref, cfg, engine=cfg.engine)
    if cfg.engine != "headroom":
        return _failed(digest, original_artifact_ref, cfg, f"unsupported compression engine: {cfg.engine}")

    candidate = digest
    redacted = False
    if cfg.redact_before_compress:
        candidate, redacted = _redact_secret_like_text(candidate)
    try:
        compressed = _compress_with_headroom(candidate)
    except Exception as exc:  # pragma: no cover - exercised via public fallback
        if not cfg.fail_open:
            raise
        return _failed(digest, original_artifact_ref, cfg, str(exc), redacted=redacted)

    compressed = compressed.strip()
    if not compressed or len(compressed) >= len(digest):
        return _unchanged(
            digest,
            original_artifact_ref,
            cfg,
            engine=cfg.engine,
            redacted=redacted,
        )
    return CompressedDigestResult(
        digest=compressed,
        original_artifact_ref=original_artifact_ref,
        compression=CompressionMetadata(
            engine=cfg.engine,
            mode=cfg.mode,
            applied=True,
            lossy=True,
            failed=False,
            original_chars=original_chars,
            compressed_chars=len(compressed),
            redacted_before_compress=redacted,
        ),
    )


def _compress_with_headroom(text: str) -> str:
    from headroom.compression import compress as headroom_compress  # type: ignore

    result = headroom_compress(text)
    compressed = getattr(result, "compressed", result)
    return "" if compressed is None else str(compressed)


def _redact_secret_like_text(text: str) -> tuple[str, bool]:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted, redacted != text


def _unchanged(
    digest: str,
    original_artifact_ref: str,
    cfg: PostprocessingCompressionConfig,
    *,
    engine: str,
    redacted: bool = False,
) -> CompressedDigestResult:
    return CompressedDigestResult(
        digest=digest,
        original_artifact_ref=original_artifact_ref,
        compression=CompressionMetadata(
            engine=engine,
            mode=cfg.mode,
            applied=False,
            lossy=False,
            failed=False,
            original_chars=len(digest),
            compressed_chars=len(digest),
            redacted_before_compress=redacted,
        ),
    )


def _failed(
    digest: str,
    original_artifact_ref: str,
    cfg: PostprocessingCompressionConfig,
    reason: str,
    *,
    redacted: bool = False,
) -> CompressedDigestResult:
    return CompressedDigestResult(
        digest=digest,
        original_artifact_ref=original_artifact_ref,
        compression=CompressionMetadata(
            engine=cfg.engine,
            mode=cfg.mode,
            applied=False,
            lossy=False,
            failed=True,
            original_chars=len(digest),
            compressed_chars=len(digest),
            redacted_before_compress=redacted,
            failure_reason=reason,
        ),
    )
