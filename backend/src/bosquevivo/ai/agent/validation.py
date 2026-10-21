from dataclasses import dataclass, field

from bosquevivo.ai.agent.evidence import EvidenceStore
from bosquevivo.ai.guardrails import check_fidelity, find_accusatory_terms
from bosquevivo.core.config import Settings

MAX_COMMUNITY_CHARS = 300


@dataclass
class ValidationResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def validate_answer(
    text: str, evidence: EvidenceStore, role: str, question: str, settings: Settings
) -> ValidationResult:
    issues: list[str] = []
    fidelity = check_fidelity(text, evidence.payloads(), allowed_context=[question])
    if not fidelity.passed:
        issues.append(
            "estas cifras no aparecen en las evidencias: " + ", ".join(fidelity.unsupported)
        )
    accusatory = find_accusatory_terms(text)
    if accusatory:
        issues.append("usa lenguaje acusatorio: " + ", ".join(accusatory))
    if role == "comunidad" and len(text) > MAX_COMMUNITY_CHARS:
        issues.append(f"supera {MAX_COMMUNITY_CHARS} caracteres")
    secrets = [
        v
        for v in (
            settings.gemini_api_key,
            settings.whatsapp_token,
            settings.whatsapp_app_secret,
            settings.admin_token,
            settings.phone_hmac_key,
        )
        if v and len(v) >= 6
    ]
    if any(secret in text for secret in secrets):
        issues.append("contiene información confidencial")
    return ValidationResult(passed=not issues, issues=issues)
