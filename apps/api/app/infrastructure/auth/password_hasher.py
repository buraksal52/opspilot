from pwdlib import PasswordHash

# PasswordHash.recommended() hashes with Argon2 (ADR-019) and can still verify
# older hashes if the recommended algorithm ever changes.
_password_hash = PasswordHash.recommended()


class PasswordHasher:
    def hash(self, plain_password: str) -> str:
        return _password_hash.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return _password_hash.verify(plain_password, hashed_password)
