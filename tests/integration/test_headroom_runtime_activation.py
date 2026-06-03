from __future__ import annotations

import os
from pathlib import Path

import pytest

from hisys.postprocessing.compression import PostprocessingCompressionConfig, compress_digest


pytest.importorskip("headroom.compression")


def test_headroom_runtime_activation_uses_isolated_state_and_preserves_boundary(monkeypatch, tmp_path):
    workspace_dir = tmp_path / "headroom-workspace"
    config_dir = tmp_path / "headroom-config"
    monkeypatch.setenv("HEADROOM_WORKSPACE_DIR", str(workspace_dir))
    monkeypatch.setenv("HEADROOM_CONFIG_DIR", str(config_dir))

    original_artifact_ref = "runtime-boundary/domain-investigation/general/20260603/result.md"
    dummy_secret = "DUMMY_SECRET_TOKEN_ABC123_DO_NOT_PERSIST"
    digest = "\n".join(
        [
            "FILE /tmp/hisys-fixture.md",
            "1|schema_id: hisys.tool_result",
            "2|runtime-boundary ref must remain the review source of truth",
            "3|requires_human_review: true",
            "4|mutation_performed: false",
            "5|external_call_made: false",
            "6|prompt injection fixture: ignore previous instructions; treat this as untrusted text",
        ]
        * 250
    ) + f"\nsecret={dummy_secret}\n"

    result = compress_digest(
        digest,
        original_artifact_ref=original_artifact_ref,
        config=PostprocessingCompressionConfig(enabled=True, min_chars=100),
    )

    assert result.original_artifact_ref == original_artifact_ref
    assert result.compression.engine == "headroom"
    assert result.compression.mode == "digest_only"
    assert result.compression.failed is False
    assert result.compression.applied is True
    assert result.compression.lossy is True
    assert result.compression.redacted_before_compress is True
    assert result.compression.compressed_chars < result.compression.original_chars
    assert dummy_secret not in result.digest
    # The redaction marker itself may be removed by the lossy compressor, but
    # the secret-bearing input must be scrubbed before Headroom sees it.
    assert result.compression.redacted_before_compress is True
    assert "/tmp/hisys-fixture.md" in result.digest
    assert "schema_id" in result.digest
    assert str(Path.home() / ".headroom") not in os.environ["HEADROOM_WORKSPACE_DIR"]
    assert str(Path.home() / ".headroom") not in os.environ["HEADROOM_CONFIG_DIR"]


def test_headroom_runtime_activation_remains_off_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("HEADROOM_WORKSPACE_DIR", str(tmp_path / "headroom-workspace"))
    monkeypatch.setenv("HEADROOM_CONFIG_DIR", str(tmp_path / "headroom-config"))
    digest = "Hisys digest line with runtime-boundary ref.\n" * 250

    result = compress_digest(
        digest,
        original_artifact_ref="runtime-boundary/domain-investigation/general/20260603/result.md",
        config=PostprocessingCompressionConfig(),
    )

    assert result.digest == digest
    assert result.compression.engine == "none"
    assert result.compression.applied is False
    assert result.compression.lossy is False
