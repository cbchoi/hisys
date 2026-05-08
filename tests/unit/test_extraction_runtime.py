"""I5 extraction runtime tests.

Traceability: HISYS-FR-EXT-001..005, HISYS-DATA-002, HISYS-T-009,
HISYS-T-010, HISYS-D-015.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config import InstanceRoot
from hisys.extraction import ExtractionRuntime, FixtureSignalExtractor


def test_fixture_extractor_creates_signal_without_copying_raw_payload(hardware_adapter):
    result = hardware_adapter.collect()
    observation = hardware_adapter.to_observation(result, producer_id="extract-test")
    extractor = FixtureSignalExtractor(method="fixture-rule-v0")

    signals = extractor.extract(observation)

    assert len(signals) == 1
    signal = signals[0]
    assert signal.observation_refs == [observation.observation_id]
    assert signal.signal_type == "anomaly"
    assert signal.claim_or_event == "hardware_sensor reported over_threshold anomaly"
    assert signal.entities == ["SRC-HW-MOCK-001"]
    assert signal.confidence == observation.data_quality.source_confidence
    assert signal.uncertainty == "bounded_by_fixture_rules"
    assert signal.contradictions == []
    assert signal.extraction_method == "fixture-rule-v0"
    assert repr(result.payload) not in signal.claim_or_event


def test_extraction_runtime_persists_signals_under_instance_root(tmp_path: Path, hardware_adapter):
    result = hardware_adapter.collect()
    observation = hardware_adapter.to_observation(result, producer_id="extract-test")
    runtime = ExtractionRuntime(
        instance=InstanceRoot(tmp_path),
        extractor=FixtureSignalExtractor(method="fixture-rule-v0"),
        producer_id="extract-runtime-test",
    )

    report = runtime.extract_run([observation], yyyymmdd="20260508")

    assert report.requested_observation_refs == [observation.observation_id]
    assert len(report.extracted_signal_refs) == 1
    signal_id = report.extracted_signal_refs[0]
    signal_path = tmp_path / "data" / "extracted-signals" / "20260508" / f"{signal_id}.json"
    assert signal_path.exists()
    signal_data = json.loads(signal_path.read_text(encoding="utf-8"))
    assert signal_data["observation_refs"] == [observation.observation_id]
    assert signal_data["status"] == "proposed"
    assert "temperature_c" not in signal_data["claim_or_event"]
    assert report.policy_refs == ["HISYS-FR-EXT-001", "HISYS-DATA-002"]
