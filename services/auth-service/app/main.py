import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from .auth import create_access_token

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Auth Service")

# NOTE: this is an in-memory placeholder. Replace with a real user store
# (e.g. the account-service DB) and password hashing (bcrypt/argon2)
# before this touches anything resembling production.
FAKE_USER_DB = {
    "demo@fintrack.dev": "demo-password",
}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    stored_password = FAKE_USER_DB.get(payload.email)
    if stored_password is None or stored_password != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=payload.email)
    return TokenResponse(access_token=token)
