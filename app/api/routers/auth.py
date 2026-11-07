from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import (
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    Token,
    UserProfileResponse,
    UserResponse,
)
from app.db.database import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user
from app.services.auth_services import auth_service

router = APIRouter(prefix="/auth", tags=["Autentificare si utilizatori"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    return await auth_service.register(db, data)

@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Token:
    token = await auth_service.login(db, credentials)
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        samesite="lax",
    )
    return token

@router.post("/token", response_model=Token)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    credentials = LoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.login(db, credentials)

@router.post("/google", response_model=Token)
async def login_google(
    data: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    return await auth_service.login_with_google(db, data)

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    return await auth_service.get_user_profile(db, current_user)

@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key="access_token")
    return {"message": "Deconectare reusita."}

@router.post("/admin/create-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    data: RegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    from app.db.models import UserRole
    from app.exceptions.exceptions import UnauthorizedAccessError
    if not current_user.role_rel or current_user.role_rel.name != UserRole.ADMINISTRATOR.value:
        raise UnauthorizedAccessError("Doar administratorul poate crea conturi de utilizator.")
    return await auth_service.create_user_by_admin(db, data)
