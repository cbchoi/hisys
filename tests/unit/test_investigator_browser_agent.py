"""Tests for disabled-by-default Selenium/browser research harness.

Traceability: HISYS-T-028, HISYS-T-027, HISYS-CON-022..023, HISYS-D-015,
HISYS-DATA-002.
"""

import pytest

from hisys.investigator import ResearchTask
from hisys.investigator.browser import BrowserAgentConfig, BrowserAgentSafetyError, SeleniumReadOnlyAgent


def test_selenium_read_only_agent_refuses_to_run_when_disabled():
    agent = SeleniumReadOnlyAgent(BrowserAgentConfig(enabled=False))
    task = ResearchTask(
        task_id="TASK-BROWSER-001",
        agent_type="selenium_read_only",
        question="Read approved browser fixture.",
        query="file:///tmp/static.html",
    )

    with pytest.raises(BrowserAgentSafetyError, match="disabled"):
        agent.run(task)


def test_selenium_read_only_agent_refuses_non_allowed_domain():
    agent = SeleniumReadOnlyAgent(BrowserAgentConfig(enabled=True, allowed_domains=["docs.example.org"]))
    task = ResearchTask(
        task_id="TASK-BROWSER-002",
        agent_type="selenium_read_only",
        question="Read non-allowed browser page.",
        query="https://unapproved.example.com/page",
    )

    with pytest.raises(BrowserAgentSafetyError, match="not allowed"):
        agent.run(task)


def test_selenium_read_only_agent_refuses_forbidden_actions():
    agent = SeleniumReadOnlyAgent(BrowserAgentConfig(enabled=True, allowed_domains=["docs.example.org"]))
    task = ResearchTask(
        task_id="TASK-BROWSER-003",
        agent_type="selenium_read_only",
        question="Login before reading.",
        query="https://docs.example.org/page",
        disallowed_actions=["login"],
    )

    with pytest.raises(BrowserAgentSafetyError, match="forbidden"):
        agent.run(task, requested_actions=["login"])


def test_selenium_read_only_agent_declares_evidence_package_schema_contract():
    agent = SeleniumReadOnlyAgent(BrowserAgentConfig(enabled=False))

    assert agent.agent_id == "selenium-read-only-agent"
    assert agent.agent_type == "selenium_read_only"
    assert agent.output_schema == "EvidencePackage"
