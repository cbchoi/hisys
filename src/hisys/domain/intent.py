"""Natural-language domain intent resolution for Hisys request construction.

This module is intentionally deterministic and local. It does not mutate a
``DomainInvestigationRequest`` after validation; callers use it before building
request JSON so the selected domain remains explicit and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Literal, Sequence

from hisys.schemas.domain_investigation import DomainName, DomainSourceRef

DomainConfidence = Literal["explicit", "high", "medium", "low"]

_RESEARCH_TEXT_SIGNALS = (
    "research paper",
    "paper review",
    "manuscript",
    "journal fit",
    "venue fit",
    "reviewer",
    "literature",
    "formalism",
    "research gap",
    "claim/evidence",
    "source/pdf",
    "pdf checks",
    "publication readiness",
    "논문",
    "원고",
    "저널",
    "학술지",
    "문헌",
    "리뷰어",
    "게재",
)

_RESEARCH_PATH_SUFFIXES = (
    ".tex",
    ".bib",
    ".pdf",
)

_CODEBASE_TEXT_SIGNALS = (
    "codebase",
    "source code",
    "repo",
    "repository",
    "implementation",
    "adapter",
    "architecture",
    "tests",
    "traceability",
    "coverage",
    "freshness",
    "change-impact",
    "requirements-analysis",
    "코드",
    "구현",
    "테스트",
    "아키텍처",
)

_CODEBASE_PATH_PARTS = (
    "/src/",
    "/tests/",
    "/docs/",
    "/requirements/",
    "/repos/",
)

_CODEBASE_FILE_SUFFIXES = (
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
)

_INVESTMENT_TEXT_SIGNALS = (
    "investment",
    "valuation",
    "portfolio",
    "financial",
    "market price",
    "투자",
    "가치평가",
    "포트폴리오",
)

_BUSINESS_TEXT_SIGNALS = (
    "business model",
    "product concept",
    "market fit",
    "customer",
    "gtm",
    "go-to-market",
    "사업",
    "비즈니스",
    "고객",
)

_ISO_TEXT_SIGNALS = (
    "iso",
    "qms",
    "quality management",
    "audit process",
    "controlled procedure",
    "iso procedure",
    "프로세스",
    "감사",
    "품질경영",
)


@dataclass(frozen=True)
class DomainIntentInput:
    """Caller-supplied text and source refs used before request construction."""

    objective: str
    sources: Sequence[DomainSourceRef] = ()
    user_focus: str | None = None
    explicit_domain: DomainName | None = None


@dataclass(frozen=True)
class DomainIntentResolution:
    """Auditable domain-selection result for request construction."""

    domain: DomainName
    confidence: DomainConfidence
    reason_codes: tuple[str, ...]

    @property
    def audit_ref(self) -> str:
        return f"domain-inference:{self.domain}:{self.confidence}"


def infer_domain_intent(intent: DomainIntentInput) -> DomainIntentResolution:
    """Map natural-language request intent to the best implemented domain.

    The resolver is artifact-first and conservative: explicit domains are
    preserved; manuscript/paper review signals route to ``research``; code/repo
    architecture signals route to ``codebase``; ``general`` is only the fallback
    when no implemented adapter signal matches.
    """

    if intent.explicit_domain is not None:
        return DomainIntentResolution(
            domain=intent.explicit_domain,
            confidence="explicit",
            reason_codes=("explicit_domain_override",),
        )

    text = _combined_text(intent)
    sources = tuple(intent.sources)
    source_refs = tuple(source.ref for source in sources)

    research_reasons = _research_reasons(text=text, sources=sources)
    codebase_reasons = _codebase_reasons(text=text, source_refs=source_refs)

    if research_reasons and _research_precedes_codebase(
        research_reasons=research_reasons, codebase_reasons=codebase_reasons
    ):
        return DomainIntentResolution(
            domain="research",
            confidence="high",
            reason_codes=research_reasons,
        )

    if codebase_reasons:
        return DomainIntentResolution(
            domain="codebase",
            confidence="high",
            reason_codes=codebase_reasons,
        )

    for domain, signals in (
        ("investment", _INVESTMENT_TEXT_SIGNALS),
        ("business", _BUSINESS_TEXT_SIGNALS),
        ("iso_process", _ISO_TEXT_SIGNALS),
    ):
        if _contains_any(text, signals):
            return DomainIntentResolution(
                domain=domain,  # type: ignore[arg-type]
                confidence="medium",
                reason_codes=(f"{domain}_text_signal",),
            )

    return DomainIntentResolution(
        domain="general",
        confidence="low",
        reason_codes=("no_specific_implemented_adapter_signal",),
    )


def _combined_text(intent: DomainIntentInput) -> str:
    return " ".join(
        part for part in (intent.objective, intent.user_focus or "") if part
    ).casefold()


def _research_reasons(*, text: str, sources: Sequence[DomainSourceRef]) -> tuple[str, ...]:
    reasons: list[str] = []
    source_refs = tuple(source.ref for source in sources)
    if _contains_any(text, _RESEARCH_TEXT_SIGNALS):
        reasons.append("manuscript_or_paper_review_signal")
    if any(_path_suffix_matches(ref, _RESEARCH_PATH_SUFFIXES) for ref in source_refs):
        reasons.append("research_artifact_signal")
    if any(source.source_type == "publisher_source" for source in sources):
        reasons.append("publisher_source_signal")
    return tuple(reasons)


def _codebase_reasons(*, text: str, source_refs: Sequence[str]) -> tuple[str, ...]:
    reasons: list[str] = []
    if _contains_any(text, _CODEBASE_TEXT_SIGNALS):
        reasons.append("codebase_text_signal")
    if any(_is_codebase_ref(ref) for ref in source_refs):
        reasons.append("codebase_artifact_signal")
    return tuple(reasons)


def _research_precedes_codebase(
    *, research_reasons: tuple[str, ...], codebase_reasons: tuple[str, ...]
) -> bool:
    if "manuscript_or_paper_review_signal" in research_reasons:
        return True
    if "research_artifact_signal" in research_reasons and not codebase_reasons:
        return True
    return False


def _contains_any(text: str, signals: Sequence[str]) -> bool:
    for signal in signals:
        folded = signal.casefold()
        if folded.isascii() and folded.replace("-", "").replace("_", "").isalnum():
            if re.search(rf"(?<![a-z0-9]){re.escape(folded)}(?![a-z0-9])", text):
                return True
        elif folded in text:
            return True
    return False


def _path_suffix_matches(ref: str, suffixes: Sequence[str]) -> bool:
    path = PurePosixPath(ref.casefold())
    return any(str(path).endswith(suffix) for suffix in suffixes)


def _is_codebase_ref(ref: str) -> bool:
    ref_lower = ref.casefold()
    if any(part in ref_lower for part in _CODEBASE_PATH_PARTS):
        return True
    return _path_suffix_matches(ref_lower, _CODEBASE_FILE_SUFFIXES)
