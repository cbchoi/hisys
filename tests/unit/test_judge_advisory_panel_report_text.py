"""Judge advisory panel report text-rendering tests.

These tests pin the Judge-only, read-only rendering of a bundled advisory panel
report (the mapping produced by ``build_judge_advisory_panel_report``) into a
single deterministic, human-readable advisory panel report text for a human
reviewer. ``render_judge_advisory_panel_report_text`` surfaces the panel summary
counts, the most-restrictive advisory outcome, and the most-restrictive-first
human-review work queue.

The renderer is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the text stays
advisory-only and always states that human review is required, matching the
Judge authority boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.
"""

from __future__ import annotations


def _payload(verdict: str = "pass") -> dict:
    return {
        "packet_id": f"JDP-{verdict}",
        "decision_subject_ref": f"claim://altas/retrieval-packet/{verdict}",
        "verdict": verdict,
        "rationale": f"Bounded advisory rationale for {verdict}.",
        "evidence_refs": ["evidence://store/handle/aaa"],
        "opposition_refs": ["dars://opposition/packet/ccc"],
    }


def _packet(verdict: str = "pass") -> dict:
    from hisys.judge import build_judge_gate_result_packet, render_judge_gate_result

    return build_judge_gate_result_packet(render_judge_gate_result(_payload(verdict)))


def _rejected_packet() -> dict:
    from hisys.judge import build_judge_gate_result_packet, render_judge_gate_result

    payload = _payload("pass")
    del payload["rationale"]
    return build_judge_gate_result_packet(render_judge_gate_result(payload))


def _report(*verdicts: str) -> dict:
    from hisys.judge import build_judge_advisory_panel_report

    return build_judge_advisory_panel_report([_packet(v) for v in verdicts])


def test_export_is_available_from_judge_package() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    assert callable(render_judge_advisory_panel_report_text)


def test_returns_a_string() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    text = render_judge_advisory_panel_report_text(_report("pass"))

    assert isinstance(text, str)


def test_renders_title_and_section_headers() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    text = render_judge_advisory_panel_report_text(_report("pass", "block"))

    assert "Judge Advisory Panel Report" in text
    assert "Gate status counts:" in text
    assert "Human-review work queue (most restrictive first):" in text


def test_surfaces_packet_count() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    text = render_judge_advisory_panel_report_text(_report("pass", "fail", "block"))

    assert "Packets reviewed: 3" in text


def test_surfaces_most_restrictive_gate_status() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    text = render_judge_advisory_panel_report_text(_report("pass", "block", "fail"))

    assert "Most restrictive gate status: advisory_block" in text


def test_surfaces_gate_status_counts() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    text = render_judge_advisory_panel_report_text(
        _report("pass", "pass", "block")
    )

    assert "  - advisory_block: 1" in text
    assert "  - advisory_pass: 2" in text


def test_surfaces_work_queue_most_restrictive_first() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    text = render_judge_advisory_panel_report_text(_report("pass", "block"))
    lines = text.splitlines()
    queue_header = lines.index("Human-review work queue (most restrictive first):")

    assert lines[queue_header + 1] == "  1. advisory_block - JDP-block"
    assert lines[queue_header + 2] == "  2. advisory_pass - JDP-pass"


def test_states_advisory_only_and_human_review() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    text = render_judge_advisory_panel_report_text(_report("pass"))

    assert "Advisory only: yes" in text
    assert "Requires human review: yes" in text


def test_includes_non_authorization_note() -> None:
    from hisys.judge import (
        JUDGE_GATE_NON_AUTHORIZATION_NOTE,
        render_judge_advisory_panel_report_text,
    )

    text = render_judge_advisory_panel_report_text(_report("pass"))

    assert JUDGE_GATE_NON_AUTHORIZATION_NOTE in text


def test_empty_report_renders_none_placeholders() -> None:
    from hisys.judge import (
        build_judge_advisory_panel_report,
        render_judge_advisory_panel_report_text,
    )

    text = render_judge_advisory_panel_report_text(build_judge_advisory_panel_report([]))

    assert "Packets reviewed: 0" in text
    assert "Most restrictive gate status: (none)" in text
    lines = text.splitlines()
    counts_header = lines.index("Gate status counts:")
    queue_header = lines.index("Human-review work queue (most restrictive first):")
    assert lines[counts_header + 1] == "  (none)"
    assert lines[queue_header + 1] == "  (none)"


def test_rejected_packet_surfaces_in_text() -> None:
    from hisys.judge import (
        build_judge_advisory_panel_report,
        render_judge_advisory_panel_report_text,
    )

    report = build_judge_advisory_panel_report([_packet("pass"), _rejected_packet()])
    text = render_judge_advisory_panel_report_text(report)

    assert "Most restrictive gate status: rejected" in text
    assert "  - rejected: 1" in text
    assert "rejected - (unidentified)" in text


def test_malformed_entry_surfaces_as_malformed() -> None:
    from hisys.judge import (
        build_judge_advisory_panel_report,
        render_judge_advisory_panel_report_text,
    )

    report = build_judge_advisory_panel_report(
        [_packet("pass"), {"no_gate_status": True}]
    )
    text = render_judge_advisory_panel_report_text(report)

    assert "Most restrictive gate status: malformed" in text
    assert "  - malformed: 1" in text


def test_is_deterministic() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    report = _report("pass", "block", "fail")

    assert render_judge_advisory_panel_report_text(
        report
    ) == render_judge_advisory_panel_report_text(report)


def test_does_not_mutate_input_report() -> None:
    import copy

    from hisys.judge import render_judge_advisory_panel_report_text

    report = _report("pass", "block")
    before = copy.deepcopy(report)

    render_judge_advisory_panel_report_text(report)

    assert report == before


def test_no_escalation_authority_tokens_leak_into_text() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    text = render_judge_advisory_panel_report_text(_report("pass", "block"))

    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in text
