"""Browser investigation orchestration helpers.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

from ..config import InstanceRoot
from ..connectors import (
    PlaywrightBrowserConnector,
    PlaywrightUnavailableError,
    SourceConnectorDispatchGate,
    load_source_connector_registry,
)
from ..investigator import ClaimRecord, EvidenceItem, EvidencePackage
from .reports import _browser_investigation_report, _write_browser_investigation_report
from .review_chain import _primary_browser_segment


@dataclass(frozen=True)
class BrowserInvestigationRunConfig:
    instance_root: Path
    config_path: Path
    yyyymmdd: str
    request_id: str
    topic: str
    user_opinion: str
    approval_ref: str
    source_urls: list[str]
    orchestrator_decide_domains: bool
    browser_fixture_html: list[Path]
    follow_links: bool
    max_follow_links_per_source: int
    orchestrator_corroborating_urls: list[str]


def run_browser_investigation(config: BrowserInvestigationRunConfig) -> int:
    """Collect approved pages through Playwright and write actual-data investigation artifacts."""

    instance_root = config.instance_root
    config_path = config.config_path
    yyyymmdd = config.yyyymmdd
    request_id = config.request_id
    topic = config.topic
    user_opinion = config.user_opinion
    approval_ref = config.approval_ref
    source_urls = config.source_urls
    orchestrator_decide_domains = config.orchestrator_decide_domains
    browser_fixture_html = config.browser_fixture_html
    follow_links = config.follow_links
    max_follow_links_per_source = config.max_follow_links_per_source
    orchestrator_corroborating_urls = config.orchestrator_corroborating_urls

    instance = InstanceRoot(instance_root)
    registry = load_source_connector_registry(config_path)
    connector_id = "playwright_read_only"
    connector = registry.connectors[connector_id]
    orchestrator_domain_decision_ref: str | None = None
    resolved_allowed_domains = list(connector.allowed_domains)
    if orchestrator_decide_domains:
        resolved_allowed_domains = _domains_from_source_urls(source_urls)
        orchestrator_domain_decision_ref = _write_orchestrator_domain_decision(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            connector_id=connector_id,
            approval_ref=approval_ref,
            source_urls=source_urls,
            decided_domains=resolved_allowed_domains,
            forbidden_actions=connector.forbidden_actions,
            domain_decision_policy=connector.domain_decision_policy,
        )
        connector = connector.model_copy(update={"allowed_domains": resolved_allowed_domains})
        connectors = dict(registry.connectors)
        connectors[connector_id] = connector
        registry = registry.model_copy(update={"connectors": connectors})
    env_name = connector.manual_smoke_env_var or "HISYS_ALLOW_BROWSER_SMOKE"
    if os.environ.get(env_name) != "1":
        report = _browser_investigation_report(
            request_id=request_id,
            topic=topic,
            user_opinion=user_opinion,
            status="blocked",
            reason_code="manual_browser_env_missing",
            source_urls=source_urls,
            source_access_refs=[],
            source_evidence_refs=[],
            transport_kinds=[],
            domain_decision_policy=connector.domain_decision_policy,
            resolved_allowed_domains=resolved_allowed_domains,
            orchestrator_domain_decision_ref=orchestrator_domain_decision_ref,
            evidence_package_ref=None,
            memo_ref=None,
            external_call_made=False,
        )
        _write_browser_investigation_report(instance, yyyymmdd, report)
        print("browser investigation: status=blocked reason=manual_browser_env_missing")
        return 2
    if browser_fixture_html and len(browser_fixture_html) != len(source_urls):
        raise ValueError("--browser-fixture-html count must match --source-url count when provided")

    gate = SourceConnectorDispatchGate(instance=instance)
    for source_url in source_urls:
        domain = urlparse(source_url).netloc or "unknown"
        decision = gate.evaluate(
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            registry=registry,
            connector_id=connector_id,
            approval_ref=approval_ref,
            requested_domain=domain,
            requested_actions=["read"],
        )
        if decision.decision != "allowed":
            report = _browser_investigation_report(
                request_id=request_id,
                topic=topic,
                user_opinion=user_opinion,
                status="blocked",
                reason_code=decision.reason_code,
                source_urls=source_urls,
                source_access_refs=[],
                source_evidence_refs=[],
                transport_kinds=[],
                domain_decision_policy=connector.domain_decision_policy,
                resolved_allowed_domains=resolved_allowed_domains,
                orchestrator_domain_decision_ref=orchestrator_domain_decision_ref,
                evidence_package_ref=None,
                memo_ref=None,
                external_call_made=False,
            )
            _write_browser_investigation_report(instance, yyyymmdd, report)
            return 2

    packages = []
    followed_source_urls: list[str] = []
    next_page_index = 1
    try:
        for index, source_url in enumerate(source_urls):
            connector_runtime = PlaywrightBrowserConnector()
            page_request_id = f"{request_id}-PAGE-{next_page_index:03d}"
            next_page_index += 1
            if browser_fixture_html:
                package = connector_runtime.collect_fixture(
                    request_id=page_request_id,
                    source_url=source_url,
                    fixture_html=browser_fixture_html[index],
                    output_root=instance.root,
                    yyyymmdd=yyyymmdd,
                )
            else:
                package = connector_runtime.collect_live(
                    request_id=page_request_id,
                    source_url=source_url,
                    output_root=instance.root,
                    yyyymmdd=yyyymmdd,
                )
            packages.append(package)
            if follow_links and not browser_fixture_html and max_follow_links_per_source > 0:
                links_to_follow = _select_browser_follow_links(
                    source_url=source_url,
                    discovered_links=package.discovered_links,
                    max_links=max_follow_links_per_source,
                )
                for follow_url in links_to_follow:
                    if follow_url in source_urls or follow_url in followed_source_urls:
                        continue
                    follow_domain = urlparse(follow_url).netloc or "unknown"
                    decision = gate.evaluate(
                        yyyymmdd=yyyymmdd,
                        request_id=request_id,
                        registry=registry,
                        connector_id=connector_id,
                        approval_ref=approval_ref,
                        requested_domain=follow_domain,
                        requested_actions=["read"],
                    )
                    if decision.decision != "allowed":
                        continue
                    followed_source_urls.append(follow_url)
                    follow_request_id = f"{request_id}-PAGE-{next_page_index:03d}"
                    next_page_index += 1
                    packages.append(
                        connector_runtime.collect_live(
                            request_id=follow_request_id,
                            source_url=follow_url,
                            output_root=instance.root,
                            yyyymmdd=yyyymmdd,
                        )
                    )
    except PlaywrightUnavailableError:
        report = _browser_investigation_report(
            request_id=request_id,
            topic=topic,
            user_opinion=user_opinion,
            status="blocked",
            reason_code="browser_fixture_or_playwright_required",
            source_urls=source_urls,
            source_access_refs=[],
            source_evidence_refs=[],
            transport_kinds=[],
            domain_decision_policy=connector.domain_decision_policy,
            resolved_allowed_domains=resolved_allowed_domains,
            orchestrator_domain_decision_ref=orchestrator_domain_decision_ref,
            evidence_package_ref=None,
            memo_ref=None,
            external_call_made=False,
        )
        _write_browser_investigation_report(instance, yyyymmdd, report)
        return 2

    evidence_items: list[EvidenceItem] = []
    claims: list[ClaimRecord] = []
    for index, page_package in enumerate(packages, start=1):
        source_evidence = page_package.evidence_items[0]
        title = page_package.access_record.title
        evidence_id = f"EV-{request_id}-BROWSER-{index:03d}"
        evidence_items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                task_id=f"TASK-{request_id}-BROWSER",
                agent_id="playwright-browser-investigator",
                source_id="SRC-BROWSER-PLAYWRIGHT-001",
                url=page_package.access_record.source_url,
                title=title,
                quoted_text=source_evidence.quoted_text,
                excerpt_ref=page_package.evidence_ref,
                retrieved_at=f"{yyyymmdd}T00:00:00Z",
                content_hash=f"sha256:{page_package.access_record.sha256}",
            )
        )
        snippet = (source_evidence.quoted_text or "")[:240]
        claims.append(
            ClaimRecord(
                claim_id=f"CLAIM-{request_id}-BROWSER-{index:03d}",
                text=f"Browser evidence from {title} says: {snippet}",
                confidence=0.65,
                evidence_refs=[evidence_id],
                limitations=["Single-page browser evidence; corroborate before final decision."],
            )
        )
    evidence_package = EvidencePackage(
        package_id=f"EPKG-{request_id}-BROWSER",
        task_id=f"TASK-{request_id}-BROWSER",
        agent_id="playwright-browser-investigator",
        agent_type="playwright_read_only",
        claims=claims,
        evidence=evidence_items,
        limitations=[
            "Browser acquisition is read-only and source-limited to approved URLs.",
            "Fixture-backed runs validate extraction shape; live runs require Playwright runtime and allowlisted domains.",
        ],
        open_questions=["Which additional primary sources, patents, papers, or filings should corroborate these page claims?"],
        external_side_effects=False,
        actions_taken=["read_page_visible_text" for _ in packages],
    )
    evidence_dir = instance.root / "data" / "evidence-packages" / yyyymmdd
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_ref = f"data/evidence-packages/{yyyymmdd}/{evidence_package.package_id}.json"
    (instance.root / evidence_ref).write_text(
        json.dumps(evidence_package.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    matrix = _build_browser_competitive_matrix(
        request_id=request_id,
        topic=topic,
        evidence_package=evidence_package,
    )
    matrix_ref = f"data/competitive-matrices/{yyyymmdd}/MATRIX-{request_id}-BROWSER.json"
    matrix_path = instance.root / matrix_ref
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    source_candidates = _build_browser_source_candidates(
        request_id=request_id,
        topic=topic,
        source_urls=source_urls,
        followed_source_urls=followed_source_urls,
        orchestrator_corroborating_urls=orchestrator_corroborating_urls,
        evidence_package=evidence_package,
        competitive_matrix=matrix,
    )
    source_candidates_ref = f"data/source-candidates/{yyyymmdd}/SRC-CANDIDATES-{request_id}-BROWSER.json"
    source_candidates_path = instance.root / source_candidates_ref
    source_candidates_path.parent.mkdir(parents=True, exist_ok=True)
    source_candidates_path.write_text(json.dumps(source_candidates, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sufficiency = _build_browser_evidence_sufficiency_assessment(
        request_id=request_id,
        topic=topic,
        source_urls=source_urls,
        followed_source_urls=followed_source_urls,
        orchestrator_corroborating_urls=orchestrator_corroborating_urls,
        evidence_package=evidence_package,
        competitive_matrix=matrix,
    )
    sufficiency_ref = f"data/evidence-sufficiency/{yyyymmdd}/SUFF-{request_id}-BROWSER.json"
    sufficiency_path = instance.root / sufficiency_ref
    sufficiency_path.parent.mkdir(parents=True, exist_ok=True)
    sufficiency_path.write_text(json.dumps(sufficiency, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    memo_ref = f"data/investigation-memos/{yyyymmdd}/MEM-{request_id}-BROWSER.md"
    memo_path = instance.root / memo_ref
    memo_path.parent.mkdir(parents=True, exist_ok=True)
    memo_path.write_text(
        _render_browser_investigation_memo(
            request_id=request_id,
            topic=topic,
            user_opinion=user_opinion,
            evidence_package=evidence_package,
            competitive_matrix=matrix,
            evidence_sufficiency=sufficiency,
        ),
        encoding="utf-8",
    )
    source_access_refs = [package.access_ref for package in packages]
    source_evidence_refs = [package.evidence_ref for package in packages]
    transport_kinds = [package.transport_kind for package in packages]
    report = _browser_investigation_report(
        request_id=request_id,
        topic=topic,
        user_opinion=user_opinion,
        status="completed",
        reason_code="browser_investigation_completed",
        source_urls=source_urls,
        source_access_refs=source_access_refs,
        source_evidence_refs=source_evidence_refs,
        transport_kinds=transport_kinds,
        domain_decision_policy=connector.domain_decision_policy,
        resolved_allowed_domains=resolved_allowed_domains,
        orchestrator_domain_decision_ref=orchestrator_domain_decision_ref,
        evidence_package_ref=evidence_ref,
        source_candidates_ref=source_candidates_ref,
        competitive_matrix_ref=matrix_ref,
        evidence_sufficiency_ref=sufficiency_ref,
        memo_ref=memo_ref,
        external_call_made=any(kind == "playwright_live" for kind in transport_kinds),
        followed_source_urls=followed_source_urls,
    )
    _write_browser_investigation_report(instance, yyyymmdd, report)
    print(f"browser investigation: status=completed report={instance.reports_dir / 'run-summaries' / yyyymmdd / 'browser-investigation-report.json'}")
    return 0

def _domains_from_source_urls(source_urls: list[str]) -> list[str]:
    domains: list[str] = []
    for source_url in source_urls:
        domain = urlparse(source_url).netloc
        if not domain:
            raise ValueError(f"source URL has no domain: {source_url}")
        if domain not in domains:
            domains.append(domain)
    return domains


def _write_orchestrator_domain_decision(
    *,
    instance: InstanceRoot,
    yyyymmdd: str,
    request_id: str,
    connector_id: str,
    approval_ref: str,
    source_urls: list[str],
    decided_domains: list[str],
    forbidden_actions: list[str],
    domain_decision_policy: str,
) -> str:
    decision_ref = (
        f"runtime-boundary/source-connectors/{yyyymmdd}/"
        f"orchestrator-domain-decision-{request_id}-{connector_id}.json"
    )
    payload = {
        "schema_id": "hisys.browser_investigation.orchestrator_domain_decision",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "connector_id": connector_id,
        "approval_ref": approval_ref,
        "domain_decision_policy": domain_decision_policy,
        "decision_basis": "orchestrator_selected_source_urls",
        "source_urls": source_urls,
        "decided_domains": decided_domains,
        "requested_actions": ["read"],
        "forbidden_actions_preserved": list(forbidden_actions),
        "external_call_made": False,
        "mutation_performed": False,
        "policy_refs": ["docs/use-cases/live-research-connectors.md"],
    }
    path = instance.root / decision_ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = path.with_suffix(".md")
    md_path.write_text(
        "\n".join(
            [
                f"# Orchestrator domain decision {request_id}",
                "",
                f"- connector_id: `{connector_id}`",
                f"- approval_ref: `{approval_ref}`",
                f"- domain_decision_policy: `{domain_decision_policy}`",
                f"- decided_domains: `{', '.join(decided_domains)}`",
                "- requested_actions: `read`",
                "- mutation_performed: `False`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return decision_ref


def _select_browser_follow_links(
    *,
    source_url: str,
    discovered_links: list[tuple[str, str]],
    max_links: int,
) -> list[str]:
    source_domain = urlparse(source_url).netloc
    selected: list[str] = []
    keywords = (
        "x-ray",
        "xray",
        "tube",
        "technology",
        "product",
        "ct",
        "lmb",
        "bearing",
        "microfocus",
        "nanofocus",
        "nano",
        "industrial",
        "medical",
        "analytical",
    )
    for label, href in discovered_links:
        absolute = urljoin(source_url, href)
        parsed = urlparse(absolute)
        source_parsed = urlparse(source_url)
        if parsed.scheme not in {"http", "https"} or parsed.netloc != source_domain:
            continue
        if parsed.path == source_parsed.path and parsed.fragment:
            continue
        haystack = f"{label} {parsed.path}".lower()
        if any(skip in haystack for skip in ["contact", "inquiry", "login", "register", "language", "privacy", "terms"]):
            continue
        if not any(keyword in haystack for keyword in keywords):
            continue
        if absolute not in selected:
            selected.append(absolute)
        if len(selected) >= max_links:
            break
    return selected


def _build_browser_source_candidates(
    *,
    request_id: str,
    topic: str,
    source_urls: list[str],
    followed_source_urls: list[str],
    orchestrator_corroborating_urls: list[str],
    evidence_package: EvidencePackage,
    competitive_matrix: dict[str, object],
) -> dict[str, object]:
    matrix_by_url = {
        str(row.get("url")): row
        for row in competitive_matrix.get("rows", [])
        if isinstance(row, dict) and row.get("url")
    }
    candidates: list[dict[str, object]] = []
    for item in evidence_package.evidence:
        url = item.url or ""
        signals = matrix_by_url.get(url, {})
        source_type = _classify_browser_source_type(url=url, title=item.title, text=item.quoted_text or "")
        usefulness_score = _score_browser_source_usefulness(source_type=source_type, signals=signals, text=item.quoted_text or "")
        candidates.append(
            {
                "url": url,
                "title": item.title,
                "domain": urlparse(url).netloc,
                "source_type": source_type,
                "usefulness_score": usefulness_score,
                "usefulness_reason": _browser_source_usefulness_reason(source_type=source_type, signals=signals),
                "evidence_role": _browser_source_evidence_role(source_type),
                "evidence_refs": [item.evidence_id],
                "selected_for_browser_read": url in source_urls,
                "discovered_by_follow_link": url in followed_source_urls,
                "orchestrator_provided": False,
                "read_status": "collected",
            }
        )
    for url in orchestrator_corroborating_urls:
        if url in {candidate["url"] for candidate in candidates}:
            continue
        source_type = _classify_browser_source_type(url=url, title="", text="")
        candidates.append(
            {
                "url": url,
                "title": "orchestrator-provided corroborating candidate",
                "domain": urlparse(url).netloc,
                "source_type": source_type,
                "usefulness_score": _score_browser_source_usefulness(source_type=source_type, signals={}, text=url),
                "usefulness_reason": _browser_source_usefulness_reason(source_type=source_type, signals={}),
                "evidence_role": _browser_source_evidence_role(source_type),
                "evidence_refs": [],
                "selected_for_browser_read": False,
                "discovered_by_follow_link": False,
                "orchestrator_provided": True,
                "read_status": "candidate_only_not_fetched",
            }
        )
    return {
        "schema_id": "hisys.browser_investigation.source_candidates",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "topic": topic,
        "risk_classification": "evidence_quality_source_discovery_not_cybersecurity",
        "candidate_count": len(candidates),
        "orchestrator_provided_corroborating_candidate_count": len([item for item in candidates if item.get("orchestrator_provided")]),
        "candidates": candidates,
        "next_source_classes_to_add": [
            "public datasheets/specification PDFs",
            "patent records",
            "filings or annual reports where applicable",
            "independent technical papers or standards references",
            "credible distributor/specification pages for corroboration",
        ],
        "notes": [
            "Populating useful public URLs is an evidence-quality/source-discovery task, not a cybersecurity risk by itself.",
            "Browser reads remain governed and read-only; final review should wait until source coverage is sufficient for the decision purpose.",
        ],
    }


def _classify_browser_source_type(*, url: str, title: str, text: str) -> str:
    location = f"{url} {title}".lower()
    haystack = f"{location} {text}".lower()
    if "patent" in location:
        return "patent"
    if any(term in location for term in ["annual report", "10-k", "investor relations", "sec filing"]):
        return "filing_or_annual_report"
    if any(term in location for term in ["doi", "journal", "conference", "abstract", "paper"]):
        return "technical_paper"
    if any(term in location for term in ["datasheet", "data sheet", "specification", ".pdf"]):
        return "datasheet_or_specification"
    if any(term in location for term in ["distributor", "shop", "store", "environmental-expert.com", "pxsinc.com", "gbmfrs.com"]):
        return "distributor_or_shop_page"
    if any(term in haystack for term in ["product", "technology", "solution", "tube", "ct", "x-ray", "xray"]):
        return "official_company_or_product_page"
    return "public_web_page"


def _score_browser_source_usefulness(*, source_type: str, signals: dict[str, object], text: str) -> str:
    if source_type in {"patent", "filing_or_annual_report", "technical_paper", "datasheet_or_specification"}:
        return "high"
    if signals.get("technology_signals") or any(term in text.lower() for term in ["technology", "tube", "ct", "x-ray", "xray"]):
        return "high"
    if source_type == "official_company_or_product_page":
        return "medium"
    return "low"


def _browser_source_usefulness_reason(*, source_type: str, signals: dict[str, object]) -> str:
    signal_text = str(signals.get("technology_signals", ""))
    if signal_text:
        return f"Contains technology detail signals: {signal_text}."
    if source_type in {"patent", "technical_paper", "datasheet_or_specification"}:
        return f"Provides corroborating {source_type.replace('_', ' ')} evidence for technical comparison."
    if source_type == "filing_or_annual_report":
        return "Provides commercial or market corroboration for company-level assessment."
    return "Useful as a public source candidate, but needs corroborating technical evidence."


def _browser_source_evidence_role(source_type: str) -> str:
    roles = {
        "official_company_or_product_page": "primary vendor technology claim",
        "datasheet_or_specification": "technical specification corroboration",
        "patent": "innovation/IP corroboration",
        "technical_paper": "independent technical corroboration",
        "filing_or_annual_report": "commercial/market corroboration",
        "distributor_or_shop_page": "third-party product/specification corroboration",
    }
    return roles.get(source_type, "supporting public web evidence")


def _build_browser_evidence_sufficiency_assessment(
    *,
    request_id: str,
    topic: str,
    source_urls: list[str],
    followed_source_urls: list[str],
    orchestrator_corroborating_urls: list[str],
    evidence_package: EvidencePackage,
    competitive_matrix: dict[str, object],
) -> dict[str, object]:
    all_domains = sorted({urlparse(item.url or "").netloc for item in evidence_package.evidence if item.url})
    source_types = [
        _classify_browser_source_type(url=item.url or "", title=item.title, text=item.quoted_text or "")
        for item in evidence_package.evidence
    ]
    matrix_rows = [row for row in competitive_matrix.get("rows", []) if isinstance(row, dict)]
    blockers: list[str] = []
    if len(all_domains) < 3:
        blockers.append("Need at least three distinct source/company domains before fair comparative review.")
    if len(matrix_rows) < 3:
        blockers.append("Need at least three comparable technology-signal rows before fair comparative review.")
    if not any(source_type in {"patent", "technical_paper", "datasheet_or_specification", "filing_or_annual_report", "distributor_or_shop_page"} for source_type in source_types):
        blockers.append("Need independent corroboration beyond company/product pages, such as datasheets, patents, filings, papers, or distributor/spec pages.")
    if len(followed_source_urls) < max(1, min(len(source_urls), 3)):
        blockers.append("Need more second-level detail URLs to reduce shallow-page bias.")
    ready = not blockers
    return {
        "schema_id": "hisys.browser_investigation.evidence_sufficiency",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "topic": topic,
        "review_readiness": "ready_for_fair_chief_editor_and_devil_review" if ready else "insufficient_for_fair_chief_editor_and_devil_review",
        "chief_editor_decision_allowed": ready,
        "devil_review_allowed": ready,
        "risk_classification": "evidence_quality_decision_fairness_not_cybersecurity",
        "observed_counts": {
            "source_url_count": len(source_urls),
            "followed_source_url_count": len(followed_source_urls),
            "orchestrator_provided_corroborating_candidate_count": len(orchestrator_corroborating_urls),
            "distinct_domain_count": len(all_domains),
            "matrix_row_count": len(matrix_rows),
        },
        "source_types_seen": sorted(set(source_types)),
        "blockers": blockers,
        "missing_evidence_plan": [
            "Promote orchestrator-provided corroborating URL candidates to governed browser/source reads after approval: " + ", ".join(orchestrator_corroborating_urls) if orchestrator_corroborating_urls else "Ask orchestrator to provide concrete corroborating URL candidates before Chief Editor / Devil review.",
            "Collect independent corroborating sources: public datasheets/specification PDFs, patents, filings, papers, or credible distributor/spec pages.",
            "Populate and score a broader URL candidate list before asking Chief Editor or Devil/DARS to decide.",
            "Follow product/detail links for each major vendor and record why each URL is useful.",
            "Only run final review after evidence covers technical specifications, IP/innovation, and commercial/market signals for the decision purpose.",
        ] if blockers else [],
    }


def _build_browser_competitive_matrix(
    *,
    request_id: str,
    topic: str,
    evidence_package: EvidencePackage,
) -> dict[str, object]:
    rows = []
    for item in evidence_package.evidence:
        signals = _browser_technology_signals(item.quoted_text or "")
        if not signals["technology_signals"]:
            continue
        source_type = _classify_browser_source_type(url=item.url or "", title=item.title, text=item.quoted_text or "")
        rows.append(
            {
                "company_or_source": item.title,
                "url": item.url,
                "source_type": source_type,
                "corroborating_evidence_class": source_type,
                "segment": _primary_browser_segment(signals["segment_signals"]),
                "segment_signals": signals["segment_signals"],
                "technology_signals": signals["technology_signals"],
                "competitive_signal_strength": signals["competitive_signal_strength"],
                "evidence_refs": [item.evidence_id],
                "evidence_excerpt": (item.quoted_text or "")[:500],
            }
        )
    return {
        "schema_id": "hisys.browser_investigation.competitive_matrix",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "topic": topic,
        "rows": rows,
        "limitations": [
            "Matrix is heuristic and based on captured browser-visible text only.",
            "Rows should be corroborated with product datasheets, patents, filings, or papers before final decisions.",
        ],
    }


def _browser_technology_signals(text: str) -> dict[str, str]:
    lower = text.lower()
    segment_terms = {
        "CT": ["ct", "computed tomography"],
        "industrial inspection/NDT": ["ndt", "inspection", "industrial", "security", "customs", "borders"],
        "medical/dental": ["medical", "dental", "veterinary"],
        "analytical XRF/XRD": ["analytical", "x-ray fluorescence", "xrf", "x-ray diffraction", "xrd"],
        "irradiation/security": ["irradiation", "security", "threat detection"],
    }
    technology_terms = {
        "liquid metal bearing": ["liquid metal bearing", "coolglide", "lmb"],
        "nano/micro focus": ["nano focus", "nanofocus", "microfocus", "micro focus", "ultra-high-resolution"],
        "rotating anode": ["rotating anode"],
        "stationary anode": ["stationary anode"],
        "high-power tube": ["high-power", "high power"],
        "stable dose/resolution": ["stable dose", "dependable resolution", "spectral purity"],
        "customized tube design": ["customized", "custom", "specific demands"],
        "compact/lightweight generator fit": ["small and light-weight", "small and lightweight", "light-weight"],
    }
    segments = [name for name, terms in segment_terms.items() if any(term in lower for term in terms)]
    technologies = [name for name, terms in technology_terms.items() if any(term in lower for term in terms)]
    strength = "low"
    if len(technologies) >= 2 or any(term in lower for term in ["gold standard", "100,000", "benchmark", "only manufacturer", "5 decades", "30 years"]):
        strength = "high"
    elif technologies:
        strength = "medium"
    return {
        "segment_signals": ", ".join(segments),
        "technology_signals": ", ".join(technologies),
        "competitive_signal_strength": strength,
    }


def _render_browser_investigation_memo(
    *,
    request_id: str,
    topic: str,
    user_opinion: str,
    evidence_package: EvidencePackage,
    competitive_matrix: dict[str, object] | None = None,
    evidence_sufficiency: dict[str, object] | None = None,
) -> str:
    rows = ["| Title | URL | Evidence excerpt |", "|---|---|---|"]
    for item in evidence_package.evidence:
        excerpt = (item.quoted_text or "").replace("|", "\\|")[:300]
        rows.append(f"| {item.title} | {item.url or ''} | {excerpt} |")
    claims = [f"- {claim.text}" for claim in evidence_package.claims]
    matrix_rows = ["| Company/source | Segment signals | Technology signals | Strength | Evidence refs |", "|---|---|---|---|---|"]
    for row in (competitive_matrix or {}).get("rows", []):
        if not isinstance(row, dict):
            continue
        matrix_rows.append(
            "| "
            + " | ".join(
                [
                    str(row.get("company_or_source", "")).replace("|", "\\|"),
                    str(row.get("segment_signals", "")).replace("|", "\\|"),
                    str(row.get("technology_signals", "")).replace("|", "\\|"),
                    str(row.get("competitive_signal_strength", "")).replace("|", "\\|"),
                    ", ".join(str(item) for item in row.get("evidence_refs", [])),
                ]
            )
            + " |"
        )
    sufficiency_lines: list[str] = []
    if evidence_sufficiency:
        sufficiency_lines = [
            "## Evidence Sufficiency for Review",
            "",
            f"- review_readiness: `{evidence_sufficiency.get('review_readiness')}`",
            f"- risk_classification: `{evidence_sufficiency.get('risk_classification')}`",
            f"- chief_editor_decision_allowed: `{evidence_sufficiency.get('chief_editor_decision_allowed')}`",
            f"- devil_review_allowed: `{evidence_sufficiency.get('devil_review_allowed')}`",
            "",
        ]
        blockers = evidence_sufficiency.get("blockers", [])
        if blockers:
            sufficiency_lines.extend(["Blockers:", "", *[f"- {item}" for item in blockers], ""])
    return "\n".join(
        [
            "# Browser Investigation Memo",
            "",
            f"- request_id: `{request_id}`",
            f"- topic: {topic}",
            f"- user_opinion: {user_opinion}",
            "- acquisition: governed Playwright read-only browser evidence",
            "- safety: no login, form submit, upload, purchase, post, mutation, or access-control bypass",
            "",
            "## Actual Browser Evidence Table",
            "",
            *rows,
            "",
            "## Evidence-Backed Claims",
            "",
            *claims,
            "",
            "## Competitive Technology Matrix",
            "",
            *matrix_rows,
            "",
            *sufficiency_lines,
            "## Limitations",
            "",
            *[f"- {item}" for item in evidence_package.limitations],
            "",
        ]
    ) + "\n"

