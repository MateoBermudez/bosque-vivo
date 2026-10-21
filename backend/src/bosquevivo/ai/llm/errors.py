from bosquevivo.core.errors import ExternalServiceError


class QuotaExceededError(ExternalServiceError):
    pass


class LLMBlockedError(ExternalServiceError):
    pass
