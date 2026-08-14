from dataclasses import dataclass


@dataclass(frozen=True)
class RiskCategory:
    key: str
    label: str
    search_query: str
    # Baseline severity when the evidence contains none of the escalating
    # or mitigating keywords below — some clause types (e.g. liability,
    # indemnification) default to a higher baseline concern than others
    # (e.g. confidentiality) purely because of what's typically at stake.
    baseline_severity: str
    escalating_keywords: tuple[str, ...]
    mitigating_keywords: tuple[str, ...]


# The 12 categories from the product spec with a natural, fixed retrieval
# query. "Unusual clauses" is deliberately not included here: flagging an
# *unusual* clause requires outlier detection across a corpus (e.g. this
# clause's embedding is far from typical clauses of its kind), not a fixed
# keyword search — a different technique than the rest of this list, not
# yet implemented. See docs/agent.md for the same honesty pattern applied
# to other heuristic pieces of this system.
RISK_CATEGORIES: list[RiskCategory] = [
    RiskCategory(
        key="termination",
        label="Termination",
        search_query="termination clause termination rights notice period",
        baseline_severity="medium",
        escalating_keywords=("immediately", "sole discretion", "without cause", "no notice"),
        mitigating_keywords=("mutual", "cure period", "written notice"),
    ),
    RiskCategory(
        key="payment_terms",
        label="Payment Terms",
        search_query="payment terms invoicing fees due date",
        baseline_severity="low",
        escalating_keywords=("penalty", "interest", "immediately due", "acceleration"),
        mitigating_keywords=("net 30", "net 60", "installment"),
    ),
    RiskCategory(
        key="renewal",
        label="Renewal",
        search_query="renewal automatic renewal term extension",
        baseline_severity="medium",
        escalating_keywords=("automatic renewal", "automatically renew", "evergreen"),
        mitigating_keywords=("mutual written consent", "opt-in", "notice to renew"),
    ),
    RiskCategory(
        key="liability",
        label="Liability",
        search_query="limitation of liability liability cap damages",
        baseline_severity="medium",
        escalating_keywords=("unlimited liability", "uncapped", "no limitation", "without limit"),
        mitigating_keywords=("cap", "capped", "shall not exceed", "limited to"),
    ),
    RiskCategory(
        key="indemnification",
        label="Indemnification",
        search_query="indemnification indemnify hold harmless",
        baseline_severity="medium",
        escalating_keywords=("broad indemnification", "any and all claims", "without limitation"),
        mitigating_keywords=("mutual indemnification", "limited to", "third-party claims"),
    ),
    RiskCategory(
        key="confidentiality",
        label="Confidentiality",
        search_query="confidentiality non-disclosure confidential information",
        baseline_severity="low",
        escalating_keywords=("perpetual", "no expiration"),
        mitigating_keywords=("mutual", "standard exceptions", "term of"),
    ),
    RiskCategory(
        key="governing_law",
        label="Governing Law",
        search_query="governing law jurisdiction applicable law",
        baseline_severity="low",
        escalating_keywords=(),
        mitigating_keywords=(),
    ),
    RiskCategory(
        key="dispute_resolution",
        label="Dispute Resolution",
        search_query="dispute resolution arbitration venue litigation",
        baseline_severity="low",
        escalating_keywords=("binding arbitration", "waive right to jury", "class action waiver"),
        mitigating_keywords=("mediation", "good faith negotiation"),
    ),
    RiskCategory(
        key="data_protection",
        label="Data Protection",
        search_query="data protection privacy data processing personal data",
        baseline_severity="medium",
        escalating_keywords=("no security obligations", "sole discretion"),
        mitigating_keywords=("gdpr", "encryption", "security measures", "breach notification"),
    ),
    RiskCategory(
        key="audit_rights",
        label="Audit Rights",
        search_query="audit rights inspection records",
        baseline_severity="low",
        escalating_keywords=("unrestricted access", "any time without notice"),
        mitigating_keywords=("reasonable notice", "annual", "business hours"),
    ),
    RiskCategory(
        key="penalties",
        label="Penalties",
        search_query="penalties liquidated damages late fees",
        baseline_severity="medium",
        escalating_keywords=("liquidated damages", "penalty", "compounding"),
        mitigating_keywords=("capped at", "sole remedy"),
    ),
    RiskCategory(
        key="sla",
        label="SLA Obligations",
        search_query="service level agreement uptime availability obligations",
        baseline_severity="low",
        escalating_keywords=("no service credits", "best efforts only"),
        mitigating_keywords=("service credits", "uptime guarantee", "remedy"),
    ),
]

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def classify_severity(category: RiskCategory, evidence_text: str) -> str:
    """Heuristic severity classification from evidence text. Works with
    any LLM's prose output (or none) rather than requiring structured
    JSON generation, which keeps this provider-agnostic — see
    docs/analysis.md for why this is a documented simplification rather
    than real risk-scoring intelligence."""
    text_lower = evidence_text.lower()
    severity = category.baseline_severity

    if any(kw in text_lower for kw in category.escalating_keywords):
        severity = "high"
    elif any(kw in text_lower for kw in category.mitigating_keywords):
        if _SEVERITY_RANK[category.baseline_severity] > 0:
            severity = "low"

    return severity
