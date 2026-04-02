from ezcut.repository.credentials import CredentialRepository
from ezcut.services.exceptions import AuthError


class AuthService:
    """Mattermost 사용자 인증 정보를 관리하는 서비스."""

    def __init__(self, repository: CredentialRepository | None = None) -> None:
        self.repository = repository or CredentialRepository()

    def get_password(self, email: str) -> str | None:
        """이메일에 해당하는 비밀번호를 가져온다."""
        try:
            return self.repository.get_password(email)
        except RuntimeError as exc:
            raise AuthError(str(exc)) from exc

    def has_password(self, email: str) -> bool:
        """이메일에 해당하는 비밀번호가 저장되어 있는지 확인한다."""
        try:
            return self.repository.has_password(email)
        except RuntimeError:
            return False

    def set_password(self, email: str, password: str) -> None:
        """이메일에 해당하는 비밀번호를 안전하게 저장한다."""
        try:
            self.repository.set_password(email, password)
        except RuntimeError as exc:
            raise AuthError(str(exc)) from exc
