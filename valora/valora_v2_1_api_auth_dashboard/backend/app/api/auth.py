from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from ..core.security import SecurityService

router = APIRouter(prefix="/auth", tags=["auth"])
security = SecurityService()

# Development-only in-memory user store.
# Production uses PostgreSQL.
USERS = {}

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(req: RegisterRequest):
    email = str(req.email).lower()
    if email in USERS:
        raise HTTPException(409, "User already exists")

    digest, salt = security.hash_password(req.password)
    user_id = "usr_" + email.replace("@", "_").replace(".", "_")
    USERS[email] = {
        "user_id": user_id,
        "password_hash": digest,
        "salt": salt,
    }
    return {"user_id": user_id, "status": "created"}

@router.post("/login")
def login(req: LoginRequest):
    email = str(req.email).lower()
    user = USERS.get(email)
    if not user or not security.verify_password(
        req.password, user["password_hash"], user["salt"]
    ):
        raise HTTPException(401, "Invalid credentials")

    session = security.issue_dev_session(user["user_id"])
    return {
        "access_token": session.token,
        "token_type": "bearer",
        "expires_at": session.expires_at.isoformat(),
        "user_id": user["user_id"],
    }
