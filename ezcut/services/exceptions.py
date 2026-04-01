"""서비스 계층 공용 예외 정의."""


class ServiceError(Exception):
    """모든 서비스 에러의 기본 클래스."""

    pass


class HistoryNotFoundError(ServiceError):
    """히스토리 데이터를 찾을 수 없을 때 발생."""

    pass


class ConfigError(ServiceError):
    """설정 데이터 관련 에러."""

    pass


class AuthError(ServiceError):
    """인증 데이터 관련 에러."""

    pass
