"""Regression tests for I9 secret/redaction hardening.

Traceability: HISYS-T-021, HISYS-NFR-SEC-001, HISYS-NFR-SEC-002,
HISYS-FR-ADM-001.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hisys.security.secret_scan import SecretScanReport, scan_paths


def test_secret_scan_reports_redacted_hits_and_skips_runtime_caches(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    root.mkdir()
    secret_assignment = "API" + "_KEY=" + "live-value-12345"
    (root / "leaky.txt").write_text(f"connector {secret_assignment}\n", encoding="utf-8")
    safe_assignment = "api" + "_key=" + "[REDACTED]" + "\n" + "password" + "=" + "[REDACTED]" + "\n"
    (root / "safe.txt").write_text(safe_assignment, encoding="utf-8")
    cache_dir = root / ".git"
    cache_dir.mkdir()
    ignored_assignment = "password" + "=" + "ignored-cache-value"
    (cache_dir / "ignored.txt").write_text(ignored_assignment + "\n", encoding="utf-8")

    report = scan_paths([root])

    assert isinstance(report, SecretScanReport)
    assert report.hit_count == 1
    assert report.hits[0].relative_path == "leaky.txt"
    assert report.hits[0].line_number == 1
    assert "live-value-12345" not in report.model_dump_json()
    assert "API_KEY=[REDACTED]" in report.hits[0].redacted_excerpt


def test_secret_scan_streams_text_like_files_with_late_decode_noise(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    root.mkdir()
    noisy = root / "noisy.log"
    unsafe_value = "unsafe" + "-value"
    noisy.write_bytes((("password" + "=") + unsafe_value + "\ntext before a late non-utf8 byte: ").encode("utf-8") + b"\xff\n")

    report = scan_paths([root])

    assert report.hit_count == 1
    assert report.scanned_files == 1
    assert report.skipped_files == 0
    assert report.hits[0].relative_path == "noisy.log"
    assert report.hits[0].redacted_excerpt == "password=[REDACTED]"
    assert unsafe_value not in report.model_dump_json()


def test_secret_scan_script_outputs_json_and_nonzero_on_hits(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    secret_assignment = "password" + "=" + "unsafe-value"
    (root / "config.env").write_text(secret_assignment + "\n", encoding="utf-8")
    script = Path(__file__).resolve().parents[2] / "scripts" / "scan_secrets.py"

    completed = subprocess.run(
        [sys.executable, str(script), "--json", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["hit_count"] == 1
    assert payload["hits"][0]["redacted_excerpt"] == "password=[REDACTED]"
    assert "unsafe-value" not in completed.stdout
