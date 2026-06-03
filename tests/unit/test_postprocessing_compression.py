import sys
import types

from hisys.postprocessing.compression import (
    PostprocessingCompressionConfig,
    compress_digest,
)


def test_disabled_compression_does_not_import_headroom(monkeypatch):
    def fail_import(name, *args, **kwargs):
        if name == "headroom.compression":
            raise AssertionError("headroom should not be imported when disabled")
        return original_import(name, *args, **kwargs)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fail_import)

    result = compress_digest(
        "long Hisys digest" * 500,
        original_artifact_ref="runtime-boundary/domain/result.md",
        config=PostprocessingCompressionConfig(enabled=False),
    )

    assert result.digest.startswith("long Hisys digest")
    assert result.compression.engine == "none"
    assert result.compression.applied is False
    assert result.original_artifact_ref == "runtime-boundary/domain/result.md"
    assert result.compression.lossy is False


def test_enabled_headroom_compresses_digest_only_and_preserves_artifact_ref(monkeypatch):
    calls = []

    def fake_compress(text):
        calls.append(text)
        return types.SimpleNamespace(compressed="compressed advisory digest")

    headroom_module = types.ModuleType("headroom")
    compression_module = types.ModuleType("headroom.compression")
    setattr(compression_module, "compress", fake_compress)
    monkeypatch.setitem(sys.modules, "headroom", headroom_module)
    monkeypatch.setitem(sys.modules, "headroom.compression", compression_module)

    result = compress_digest(
        "Hisys advisory digest " * 500,
        original_artifact_ref="runtime-boundary/domain/result.md",
        config=PostprocessingCompressionConfig(enabled=True, min_chars=10),
    )

    assert calls == ["Hisys advisory digest " * 500]
    assert result.digest == "compressed advisory digest"
    assert result.original_artifact_ref == "runtime-boundary/domain/result.md"
    assert result.compression.engine == "headroom"
    assert result.compression.applied is True
    assert result.compression.lossy is True
    assert result.compression.failed is False
    assert result.compression.original_chars > result.compression.compressed_chars


def test_headroom_failure_falls_back_without_failing_hisys(monkeypatch):
    def fake_compress(text):
        raise RuntimeError("headroom unavailable")

    headroom_module = types.ModuleType("headroom")
    compression_module = types.ModuleType("headroom.compression")
    setattr(compression_module, "compress", fake_compress)
    monkeypatch.setitem(sys.modules, "headroom", headroom_module)
    monkeypatch.setitem(sys.modules, "headroom.compression", compression_module)

    source = "Hisys advisory digest " * 500
    result = compress_digest(
        source,
        original_artifact_ref="runtime-boundary/domain/result.md",
        config=PostprocessingCompressionConfig(enabled=True, min_chars=10, fail_open=True),
    )

    assert result.digest == source
    assert result.compression.engine == "headroom"
    assert result.compression.applied is False
    assert result.compression.failed is True
    assert "headroom unavailable" in result.compression.failure_reason


def test_redacts_before_compressing_and_reports_redaction(monkeypatch):
    calls = []

    def fake_compress(text):
        calls.append(text)
        return types.SimpleNamespace(compressed=text[:80])

    headroom_module = types.ModuleType("headroom")
    compression_module = types.ModuleType("headroom.compression")
    setattr(compression_module, "compress", fake_compress)
    monkeypatch.setitem(sys.modules, "headroom", headroom_module)
    monkeypatch.setitem(sys.modules, "headroom.compression", compression_module)

    secret = "DUMMY_SECRET_TOKEN_ABC123_DO_NOT_PERSIST"
    result = compress_digest(
        ("Hisys digest " * 100) + secret,
        original_artifact_ref="runtime-boundary/domain/result.md",
        config=PostprocessingCompressionConfig(enabled=True, min_chars=10),
    )

    assert secret not in calls[0]
    assert secret not in result.digest
    assert "[REDACTED_SECRET]" in calls[0]
    assert result.compression.redacted_before_compress is True


def test_requires_original_artifact_ref_when_configured():
    result = compress_digest(
        "Hisys advisory digest " * 500,
        original_artifact_ref="",
        config=PostprocessingCompressionConfig(
            enabled=True,
            min_chars=10,
            require_original_artifact_ref=True,
        ),
    )

    assert result.compression.applied is False
    assert result.compression.failed is True
    assert "original_artifact_ref" in result.compression.failure_reason
