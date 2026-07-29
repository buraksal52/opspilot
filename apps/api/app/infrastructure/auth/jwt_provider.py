import uuid
from datetime import UTC, datetime, timedelta

import jwt


class TokenError(Exception):
    """Raised for any invalid, malformed, or expired access token."""


class JWTProvider:
    def __init__(self, secret_key: str, algorithm: str, access_token_expire_minutes: int) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes

    def create_access_token(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=self._access_token_expire_minutes),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_user_id(self, token: str) -> uuid.UUID:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise TokenError("Invalid or expired token.") from exc

        subject = payload.get("sub")
        if not subject:
            raise TokenError("Token is missing a subject claim.")

        try:
            return uuid.UUID(subject)
        except ValueError as exc:
            raise TokenError("Token subject is not a valid user id.") from exc
