from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

SECRET_KEY = os.environ.get("JWT_SECRET", "promanage-secret-key-2025-very-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: str, email: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kedaluwarsa")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token tidak ditemukan")
    payload = decode_token(credentials.credentials)
    return payload
