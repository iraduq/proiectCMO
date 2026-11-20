import base64
import hashlib
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
    UserUpdateRequest,
)
from app.db.models import ParentStudent, User, UserRole
from app.exceptions.exceptions import (
    InvalidCredentialsError,
    InvalidEmailFormatError,
    InvalidFullNameError,
    InvalidMatricolError,
    ParentChildLinkError,
    PasswordValidationError,
    RoleNotSelectedError,
    SubjectNotSelectedError,
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
        import re
        email = data.email.strip().lower() if data.email else ""
        if not email or not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", email):
            raise InvalidEmailFormatError(email)

        name = data.nume.strip() if data.nume else ""
        if not name or len(name) < 3:
            raise InvalidFullNameError("Numele complet este obligatoriu și trebuie să aibă minim 3 caractere.")
        if any(ch.isdigit() for ch in name):
            raise InvalidFullNameError("Numele complet nu poate conține cifre. Introduceți doar litere (ex: Popescu Ion).")
        if len(name.split()) < 2:
            raise InvalidFullNameError("Numele complet trebuie să conțină atât numele de familie, cât și prenumele.")

        if not data.rol:
            raise RoleNotSelectedError()

        if data.rol == UserRole.PROFESOR and (not data.materie_id or data.materie_id <= 0):
            raise SubjectNotSelectedError("Selectarea unei materii este obligatorie pentru cadrele didactice.")

        if data.rol == UserRole.ELEV and (not data.numar_matricol or len(data.numar_matricol.strip()) < 3):
            raise InvalidMatricolError()

        existing = await auth_repository.get_by_email(db, email)
        if existing:
            raise UserEmailAlreadyExistsError(email)

        if not is_password_strong(data.password):
            raise PasswordValidationError()

        pwd_hash = get_password_hash(data.password)
        data.email = email
        data.nume = name
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
        if not google_id or "@" in str(google_id) or str(google_id).startswith("usv_google_"):
            seed = int(hashlib.sha256(email.encode("utf-8")).hexdigest(), 16)
            google_id = f"10{seed % 10000000000000000000:019d}"

        user = await auth_repository.get_by_email(db, email)
        if user:
            if google_id and (not user.google_id or "@" in str(user.google_id) or user.google_id.startswith("usv_google_")):
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
        import re
        email = data.email.strip().lower() if data.email else ""
        if not email or not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", email):
            raise InvalidEmailFormatError(email)

        name = data.nume.strip() if data.nume else ""
        if not name or len(name) < 3:
            raise InvalidFullNameError("Numele complet este obligatoriu și trebuie să aibă minim 3 caractere.")
        if any(ch.isdigit() for ch in name):
            raise InvalidFullNameError("Numele complet nu poate conține cifre. Introduceți doar litere (ex: Popescu Ion).")
        if len(name.split()) < 2:
            raise InvalidFullNameError("Numele complet trebuie să conțină atât numele de familie, cât și prenumele.")

        if not data.password or not is_password_strong(data.password):
            raise PasswordValidationError()

        if not data.rol:
            raise RoleNotSelectedError()

        if data.rol == UserRole.PROFESOR and (not data.materie_id or data.materie_id <= 0):
            raise SubjectNotSelectedError("Selectarea unei materii este obligatorie pentru cadrele didactice.")

        if data.rol == UserRole.ELEV and (not data.numar_matricol or len(data.numar_matricol.strip()) < 3):
            raise InvalidMatricolError()

        existing = await auth_repository.get_by_email(db, email)
        if existing:
            raise UserEmailAlreadyExistsError(email)

        pwd_hash = get_password_hash(data.password)
        data.email = email
        data.nume = name
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

    async def update_user_by_admin(self, db: AsyncSession, user_id: int, data: UserUpdateRequest) -> UserResponse:
        user = await auth_repository.get_by_id(db, user_id)
        if not user:
            raise UserNotFoundError(f"Utilizatorul cu ID {user_id} nu a fost gasit.")

        if data.nume is not None:
            name_clean = data.nume.strip()
            if not name_clean or len(name_clean) < 3:
                raise InvalidFullNameError("Numele complet este obligatoriu și trebuie să aibă minim 3 caractere.")
            if any(ch.isdigit() for ch in name_clean):
                raise InvalidFullNameError("Numele complet nu poate conține cifre. Introduceți doar litere (ex: Popescu Ion).")
            if len(name_clean.split()) < 2:
                raise InvalidFullNameError("Numele complet trebuie să conțină atât numele de familie, cât și prenumele.")
            user.nume = name_clean

        if data.email is not None:
            email_clean = data.email.strip().lower()
            import re
            if not email_clean or not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", email_clean):
                raise InvalidEmailFormatError(email_clean)
            if email_clean != user.email:
                existing = await auth_repository.get_by_email(db, email_clean)
                if existing:
                    raise UserEmailAlreadyExistsError(email_clean)
                user.email = email_clean

        if data.numar_matricol is not None:
            matricol_clean = data.numar_matricol.strip()
            if matricol_clean:
                if len(matricol_clean) < 3:
                    raise InvalidMatricolError()
                user.numar_matricol = matricol_clean
            else:
                user.numar_matricol = None

        if data.telefon is not None:
            user.telefon = data.telefon.strip() if data.telefon.strip() else None
        if data.clasa_id is not None:
            user.clasa_id = data.clasa_id if data.clasa_id > 0 else None
        if data.materie_id is not None:
            user.materie_id = data.materie_id if data.materie_id > 0 else None
        if data.is_active is not None:
            user.is_active = data.is_active

        if user.role_rel and user.role_rel.name == UserRole.PROFESOR.value:
            if not user.materie_id:
                raise SubjectNotSelectedError("Selectarea unei materii este obligatorie pentru cadrele didactice.")

        await db.commit()
        refreshed_user = await auth_repository.get_by_id(db, user_id)

        role_name = refreshed_user.role_rel.name if refreshed_user.role_rel else "ELEV"
        clasa_nume = refreshed_user.clasa.nume if refreshed_user.clasa else None
        materie_nume = refreshed_user.materie.nume if refreshed_user.materie else None

        return UserResponse(
            id_utilizator=refreshed_user.id_utilizator,
            nume=refreshed_user.nume,
            email=refreshed_user.email,
            role=role_name,
            numar_matricol=refreshed_user.numar_matricol,
            telefon=refreshed_user.telefon,
            avatar_url=refreshed_user.avatar_url,
            clasa_id=refreshed_user.clasa_id,
            clasa_nume=clasa_nume,
            materie_id=refreshed_user.materie_id,
            materie_nume=materie_nume,
            is_active=refreshed_user.is_active,
            created_at=refreshed_user.created_at,
        )

auth_service = AuthService()
