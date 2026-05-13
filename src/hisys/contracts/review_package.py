"""Advisory pass-contract review package helpers.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations


def build_review_package(*, candidate_ref: str, reviewers: list[str]) -> dict[str, object]:
    return {
        "schema_id": "hisys.pass_contract.review_package",
        "schema_version": "0.1.0",
        "candidate_ref": candidate_ref,
        "reviewers": reviewers,
        "approval_authority_transferred": False,
        "promotion_allowed": False,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
