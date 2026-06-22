import os
import datetime
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "changeme-too")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 30


def create_access_token(subject: str) -> str:
    payload = {
        "sub": subject,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXPIRY_MINUTES),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
