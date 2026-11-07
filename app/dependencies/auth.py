from typing import Any, Callable, Optional
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import User, UserRole
from app.exceptions.exceptions import InvalidTokenError, UnauthorizedAccessError, UserNotFoundError
from app.repositories.auth_repository import auth_repository
from app.utils.roles import PermissionCode
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

async def get_current_user(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = bearer_token or request.cookies.get("access_token")
    if not token:
        raise InvalidTokenError()

    payload = decode_access_token(token)
    if not payload:
        raise InvalidTokenError()

    user_id_val: Any = payload.get("sub")
    if not user_id_val:
        raise InvalidTokenError()

    try:
        user_id = int(user_id_val)
    except ValueError:
        raise InvalidTokenError()

    user = await auth_repository.get_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(user_id)

    return user

def require_roles(*allowed_roles: UserRole) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role_rel.name if current_user.role_rel else None
        allowed_names = [r.value for r in allowed_roles]
        if role_name not in allowed_names:
            raise UnauthorizedAccessError("Nu aveti rolul necesar pentru a efectua aceasta actiune.")
        return current_user

    return role_checker

def require_permission(required_permission: PermissionCode) -> Callable:
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_permissions = [p.code for p in current_user.role_rel.permissions] if current_user.role_rel else []
        if required_permission.value not in user_permissions:
            raise UnauthorizedAccessError("Nu aveti permisiunea necesara pentru a efectua aceasta actiune.")
        return current_user

    return permission_checker
