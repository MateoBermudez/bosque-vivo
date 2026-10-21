class BosqueVivoError(Exception):
    pass


class NotFoundError(BosqueVivoError):
    pass


class ValidationFailedError(BosqueVivoError):
    pass


class ExternalServiceError(BosqueVivoError):
    pass
