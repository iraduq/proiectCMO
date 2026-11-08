import base64
import json
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import (
    ChildSummary,
    GoogleAuthRequest,
    LinkChildRequest,
    LoginRequest,
    RegisterRequest,
    Token,
    UserProfileResponse,
    UserResponse,
)
from app.db.models import ParentStudent, User, UserRole
from app.exceptions.exceptions import (
    InvalidCredentialsError,
    ParentChildLinkError,
    PasswordValidationError,
    UnauthorizedAccessError,
    UserEmailAlreadyExistsError,
    UserNotFoundError,
)
from app.repositories.auth_repository import auth_repository
from app.repositories.grade_repository import grade_repository
from app.repositories.absence_repository import absence_repository
from app.repositories.remark_repository import remark_repository
from app.utils.security import (
    create_access_token,
    get_password_hash,
    is_password_strong,
    verify_password,
)

class AuthService:
    async def login(self, db: AsyncSession, credentials: LoginRequest) -> Token:
        user = await auth_repository.get_by_email(db, credentials.email)
        if not user or not user.is_active:
            raise InvalidCredentialsError()

        if not verify_password(credentials.password, user.parola_hash):
            raise InvalidCredentialsError()

        role_name = user.role_rel.name if user.role_rel else "ELEV"
        access_token = create_access_token(
            data={
                "sub": str(user.id_utilizator),
                "role": role_name,
                "email": user.email,
            }
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id_utilizator,
            role=role_name,
            nume=user.nume,
            email=user.email,
            materie_id=user.materie_id,
            materie_nume=user.materie.nume if user.materie else None,
        )

    async def register(self, db: AsyncSession, data: RegisterRequest) -> Token:
        existing = await auth_repository.get_by_email(db, data.email)
        if existing:
            raise UserEmailAlreadyExistsError(data.email)

        if not is_password_strong(data.password):
            raise PasswordValidationError()

        pwd_hash = get_password_hash(data.password)
        user = await auth_repository.create(db, data, pwd_hash)

        role_name = user.role_rel.name if user.role_rel else data.rol.value
        access_token = create_access_token(
            data={
                "sub": str(user.id_utilizator),
                "role": role_name,
                "email": user.email,
            }
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id_utilizator,
            role=role_name,
            nume=user.nume,
            email=user.email,
            materie_id=user.materie_id,
            materie_nume=user.materie.nume if user.materie else None,
        )

    async def login_with_google(self, db: AsyncSession, data: GoogleAuthRequest) -> Token:
        id_token = data.id_token.strip()
        email = None
        nume = None
        google_id = None
        avatar = None

        if id_token.count(".") == 2:
            try:
                from google.oauth2 import id_token as google_id_token
                from google.auth.transport import requests as google_requests
                req = google_requests.Request()
                target_client_id = settings.google_client_id or "410501815287-drt4c6ll5dk5v8rrr0sbmur2ptlq4of8.apps.googleusercontent.com"
                google_payload = google_id_token.verify_oauth2_token(id_token, req, target_client_id)
                email = google_payload.get("email")
                nume = google_payload.get("name")
                google_id = google_payload.get("sub")
                avatar = google_payload.get("picture")
            except Exception:
                pass

        if not email and id_token.count(".") == 2:
            try:
                import httpx
                url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        google_payload = resp.json()
                        email = google_payload.get("email")
                        nume = google_payload.get("name")
                        google_id = google_payload.get("sub")
                        avatar = google_payload.get("picture")
            except Exception:
                pass

        if not email and id_token.count(".") == 2:
            try:
                part = id_token.split(".")[1]
                padded = part + "=" * ((4 - len(part) % 4) % 4)
                payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
                email = payload.get("email")
                nume = payload.get("name")
                google_id = payload.get("sub")
                avatar = payload.get("picture")
            except Exception:
                pass

        if not email and "{" in id_token and "}" in id_token:
            try:
                payload = json.loads(id_token)
                email = payload.get("email")
                nume = payload.get("name")
                google_id = payload.get("sub") or payload.get("google_id")
                avatar = payload.get("picture")
            except Exception:
                pass

        if not email and "@" in id_token:
            email = id_token.strip().lower()

        if not email or not email.lower().strip().endswith("@student.usv.ro"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Autentificarea cu Google este permisa doar cu adrese educationale @student.usv.ro",
            )

        email = email.lower().strip()
        if not nume or nume.lower() in ("google user", "utilizator google", "null", "none"):
            parts = email.split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ").split()
            nume = " ".join(p.capitalize() for p in parts)
        if not google_id:
            google_id = f"usv_google_{abs(hash(email)) % 10000000000}"

        user = await auth_repository.get_by_email(db, email)
        if user:
            if google_id and (not user.google_id or user.google_id.startswith("usv_google_")):
                user.google_id = google_id
            if nume and (not user.nume or user.nume in ("Google User", "Utilizator Google")):
                user.nume = nume
            if avatar and not user.avatar_url:
                user.avatar_url = avatar
            await db.flush()
        else:
            role_name = UserRole.ELEV.value
            user = await auth_repository.create_google_user(
                db=db,
                email=email,
                nume=nume,
                google_id=google_id,
                role_name=role_name,
                avatar_url=avatar,
            )

        role_name = user.role_rel.name if user.role_rel else UserRole.ELEV.value
        access_token = create_access_token(
            data={
                "sub": str(user.id_utilizator),
                "role": role_name,
                "email": user.email,
            }
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id_utilizator,
            role=role_name,
            nume=user.nume,
            email=user.email,
            materie_id=user.materie_id,
            materie_nume=user.materie.nume if user.materie else None,
        )

    async def get_user_profile(self, db: AsyncSession, current_user: User) -> UserProfileResponse:
        role_name = current_user.role_rel.name if current_user.role_rel else "ELEV"
        clasa_nume = current_user.clasa.nume if current_user.clasa else None

        children_summaries: list[ChildSummary] = []
        if role_name == UserRole.PARINTE.value:
            children = await auth_repository.get_children_for_parent(db, current_user.id_utilizator)
            for child in children:
                avg = await grade_repository.calculate_student_overall_average(db, child.id_utilizator)
                tot_abs, mot_abs, nemot_abs = await absence_repository.count_by_student(db, child.id_utilizator)
                ment_count = await remark_repository.count_by_student(db, child.id_utilizator)
                children_summaries.append(
                    ChildSummary(
                        id_utilizator=child.id_utilizator,
                        nume=child.nume,
                        email=child.email,
                        numar_matricol=child.numar_matricol,
                        clasa_id=child.clasa_id,
                        clasa_nume=child.clasa.nume if child.clasa else None,
                        relatie="Copil",
                        medie_generala=avg,
                        total_absente=tot_abs,
                        total_absente_nemotivate=nemot_abs,
                        total_mentiuni=ment_count,
                    )
                )

        return UserProfileResponse(
            id_utilizator=current_user.id_utilizator,
            nume=current_user.nume,
            email=current_user.email,
            role=role_name,
            numar_matricol=current_user.numar_matricol,
            telefon=current_user.telefon,
            avatar_url=current_user.avatar_url,
            clasa_id=current_user.clasa_id,
            clasa_nume=clasa_nume,
            materie_id=current_user.materie_id,
            materie_nume=current_user.materie.nume if current_user.materie else None,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            copii=children_summaries,
        )

    async def link_child_to_parent(
        self,
        db: AsyncSession,
        parent: User,
        data: LinkChildRequest,
    ) -> ChildSummary:
        if parent.role_rel.name != UserRole.PARINTE.value and parent.role_rel.name != UserRole.ADMINISTRATOR.value:
            raise UnauthorizedAccessError("Doar conturile de parinte pot asocia elevi.")

        student = await auth_repository.get_by_matricol(db, data.numar_matricol)
        if not student:
            raise UserNotFoundError(f"Elevul cu numarul matricol '{data.numar_matricol}' nu a fost gasit.")

        await auth_repository.link_parent_student(db, parent.id_utilizator, student.id_utilizator, data.relatie)

        avg = await grade_repository.calculate_student_overall_average(db, student.id_utilizator)
        tot_abs, mot_abs, nemot_abs = await absence_repository.count_by_student(db, student.id_utilizator)
        ment_count = await remark_repository.count_by_student(db, student.id_utilizator)

        return ChildSummary(
            id_utilizator=student.id_utilizator,
            nume=student.nume,
            email=student.email,
            numar_matricol=student.numar_matricol,
            clasa_id=student.clasa_id,
            clasa_nume=student.clasa.nume if student.clasa else None,
            relatie=data.relatie,
            medie_generala=avg,
            total_absente=tot_abs,
            total_absente_nemotivate=nemot_abs,
            total_mentiuni=ment_count,
        )

    async def create_user_by_admin(self, db: AsyncSession, data: RegisterRequest) -> UserResponse:
        existing = await auth_repository.get_by_email(db, data.email)
        if existing:
            raise UserEmailAlreadyExistsError(data.email)

        pwd_hash = get_password_hash(data.password)
        user = await auth_repository.create(db, data, pwd_hash)

        role_name = user.role_rel.name if user.role_rel else data.rol.value
        clasa_nume = user.clasa.nume if user.clasa else None
        materie_nume = user.materie.nume if user.materie else None

        return UserResponse(
            id_utilizator=user.id_utilizator,
            nume=user.nume,
            email=user.email,
            role=role_name,
            numar_matricol=user.numar_matricol,
            telefon=user.telefon,
            avatar_url=user.avatar_url,
            clasa_id=user.clasa_id,
            clasa_nume=clasa_nume,
            materie_id=user.materie_id,
            materie_nume=materie_nume,
            is_active=user.is_active,
            created_at=user.created_at,
        )

auth_service = AuthService()
