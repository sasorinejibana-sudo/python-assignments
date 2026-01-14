from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status

# Hardcoded users exactly as requested
USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "privuser": {"password": "priv123", "role": "PrivilegedUser"},
}

JWT_SECRET = "THIS_IS_A_DEMO_SECRET_CHANGE_ME"
JWT_ALG = "HS256"
JWT_EXPIRE_MIN = 60


def authenticate(username: str, password: str):
    u = USERS.get(username)
    if not u:
        return None
    if u["password"] != password:
        return None
    return {"username": username, "role": u["role"]}


def create_token(username: str, role: str):
    expires = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MIN)
    payload = {
        "sub": username,
        "role": role,
        "exp": expires
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token, expires


def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            return None
        return {"username": username, "role": role}
    except JWTError:
        return None


def require_auth_header(auth_header: str | None):
    """
    Accepts: Authorization: Bearer <token>
    Returns user dict or raises 401.
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth_header.split(" ", 1)[1].strip()
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
