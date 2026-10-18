import json
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedIdentity:
    subject: str
    email: str
    display_name: str
    roles: frozenset[str]


class JwksCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._keys: dict[str, dict[str, Any]] = {}
        self._expires_at = 0.0
        self._lock = Lock()

    def get_key(self, key_id: str) -> dict[str, Any]:
        if time.monotonic() >= self._expires_at or key_id not in self._keys:
            self._refresh()

        key = self._keys.get(key_id)
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token signing key is unknown",
            )
        return key

    def _refresh(self) -> None:
        with self._lock:
            if time.monotonic() < self._expires_at and self._keys:
                return
            try:
                with urlopen(settings.keycloak_jwks_url, timeout=5) as response:
                    payload = json.load(response)
            except (URLError, TimeoutError, ValueError) as error:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service is unavailable",
                ) from error

            self._keys = {key["kid"]: key for key in payload.get("keys", []) if "kid" in key}
            self._expires_at = time.monotonic() + self.ttl_seconds


jwks_cache = JwksCache()


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
        key_id = header.get("kid")
        if not key_id or header.get("alg") != "RS256":
            raise JWTError("Unsupported token header")

        return jwt.decode(
            token,
            jwks_cache.get_key(key_id),
            algorithms=["RS256"],
            audience=settings.keycloak_backend_client_id,
            issuer=settings.keycloak_public_issuer_url,
            options={"require_sub": True, "require_exp": True},
        )
    except JWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def get_authenticated_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = decode_access_token(credentials.credentials)
    email = claims.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token does not contain an email address",
        )

    realm_access = claims.get("realm_access") or {}
    roles = frozenset(realm_access.get("roles") or [])
    if not roles.intersection({role.value for role in UserRole}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No WorkHub role is assigned",
        )

    return AuthenticatedIdentity(
        subject=claims["sub"],
        email=email,
        display_name=claims.get("name") or claims.get("preferred_username") or email,
        roles=roles,
    )


def get_current_user(
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    database: Session = Depends(get_db),
) -> User:
    role = UserRole.ADMIN if UserRole.ADMIN.value in identity.roles else UserRole.EMPLOYEE
    user = database.scalar(select(User).where(User.keycloak_subject == identity.subject))

    if user is None:
        email_owner = database.scalar(select(User).where(User.email == identity.email))
        if email_owner is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email is already linked to another identity",
            )
        user = User(
            keycloak_subject=identity.subject,
            email=identity.email,
            display_name=identity.display_name,
            role=role,
        )
        database.add(user)
    else:
        user.email = identity.email
        user.display_name = identity.display_name
        user.role = role

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The authenticated profile conflicts with an existing user",
        ) from error

    database.refresh(user)
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="WorkHub account is inactive",
        )
    return user


def require_role(required_role: UserRole):
    def role_dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role.value.capitalize()} role is required",
            )
        return user

    return role_dependency


require_employee = require_role(UserRole.EMPLOYEE)
require_admin = require_role(UserRole.ADMIN)
