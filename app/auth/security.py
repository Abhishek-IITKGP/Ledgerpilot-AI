from datetime import datetime, timedelta, timezone
import os

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.auth.user_repository import AuthenticatedUser, UserRepository
from app.database.connection import get_connection


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_auth_connection() -> Generator:
    connection = get_connection()

    try:
        yield connection
    finally:
        connection.close()


def create_access_token(
    user_id: int,
    email: str,
    role: str,
) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=30)

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        os.environ["JWT_SECRET_KEY"],
        algorithm=os.environ.get("JWT_ALGORITHM", "HS256"),
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    connection=Depends(get_auth_connection),
) -> AuthenticatedUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[os.environ.get("JWT_ALGORITHM", "HS256")],
        )
        subject = payload.get("sub")
        user_id = int(subject)
    except (jwt.PyJWTError, TypeError, ValueError, KeyError) as error:
        raise credentials_exception from error

    user = UserRepository(connection).get_by_id(user_id)

    if user is None or not user.is_active:
        raise credentials_exception

    return user

def require_roles(*allowed_roles: str):
    normalized_roles = {
        role.value if hasattr(role, "value") else role
        for role in allowed_roles
    }

    def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if current_user.role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker