import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256

@dataclass(frozen=True)
class Session:
    token: str
    user_id: str
    expires_at: datetime

class SecurityService:
    """
    Development-only session implementation.
    Production should use Argon2id/bcrypt and signed JWT or opaque
    server-side sessions with rotation, revocation and MFA.
    """

    def hash_password(self, password: str, salt: str | None = None):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        salt = salt or secrets.token_hex(16)
        digest = sha256((salt + password).encode()).hexdigest()
        return digest, salt

    def verify_password(self, password, digest, salt):
        actual, _ = self.hash_password(password, salt)
        return secrets.compare_digest(actual, digest)

    def issue_dev_session(self, user_id: str, minutes: int = 30):
        if minutes <= 0:
            raise ValueError("Invalid session lifetime")
        return Session(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=minutes),
        )
