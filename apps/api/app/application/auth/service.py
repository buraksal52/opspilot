from app.core.errors import UnauthorizedError
from app.infrastructure.auth.jwt_provider import JWTProvider
from app.infrastructure.auth.password_hasher import PasswordHasher
from app.infrastructure.database.repositories.user_repository import UserRepository

_INVALID_CREDENTIALS_MESSAGE = "Invalid email or password."


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        jwt_provider: JWTProvider,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._jwt_provider = jwt_provider

    async def login(self, email: str, password: str) -> str:
        user = await self._user_repository.get_by_email(email)
        if user is None or not self._password_hasher.verify(password, user.hashed_password):
            # Same error whether the email is unknown or the password is wrong,
            # so login failures do not reveal which emails are registered.
            raise UnauthorizedError(_INVALID_CREDENTIALS_MESSAGE)

        return self._jwt_provider.create_access_token(user.id)
