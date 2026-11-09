import secrets
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from app.api.schemas.edugrade import RegisterRequest
from app.db.models import ParentStudent, Role, SchoolClass, TeacherClassSubject, User, UserRole

class AuthRepository:
    async def get_role_by_name(self, db: AsyncSession, role_name: str) -> Optional[Role]:
        result = await db.execute(
            select(Role).options(selectinload(Role.permissions)).where(Role.name == role_name)
        )
        return result.scalars().first()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .options(
                joinedload(User.role_rel).selectinload(Role.permissions),
                joinedload(User.clasa),
                joinedload(User.materie),
                selectinload(User.legaturi_copii).joinedload(ParentStudent.elev).joinedload(User.clasa),
                selectinload(User.legaturi_parinti).joinedload(ParentStudent.parinte),
            )
            .where(User.email.ilike(email))
        )
        return result.scalars().first()

    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(
            select(User)
            .options(
                joinedload(User.role_rel).selectinload(Role.permissions),
                joinedload(User.clasa),
                joinedload(User.materie),
                selectinload(User.legaturi_copii).joinedload(ParentStudent.elev).joinedload(User.clasa),
                selectinload(User.legaturi_parinti).joinedload(ParentStudent.parinte),
            )
            .where(User.id_utilizator == user_id)
        )
        return result.scalars().first()

    async def get_by_google_id(self, db: AsyncSession, google_id: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .options(
                joinedload(User.role_rel).selectinload(Role.permissions),
                joinedload(User.clasa),
            )
            .where(User.google_id == google_id)
        )
        return result.scalars().first()

    async def get_by_matricol(self, db: AsyncSession, matricol: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .options(
                joinedload(User.role_rel).selectinload(Role.permissions),
                joinedload(User.clasa),
            )
            .where(User.numar_matricol == matricol)
        )
        return result.scalars().first()

    async def create(self, db: AsyncSession, user_data: RegisterRequest, password_hash: str) -> User:
        role = await self.get_role_by_name(db, user_data.rol.value)
        if not role:
            role = Role(name=user_data.rol.value, description=f"Rol {user_data.rol.value}")
            db.add(role)
            await db.flush()

        user = User(
            nume=user_data.nume,
            email=user_data.email.lower().strip(),
            parola_hash=password_hash,
            role_id=role.id,
            numar_matricol=user_data.numar_matricol,
            telefon=user_data.telefon,
            clasa_id=user_data.clasa_id,
            materie_id=user_data.materie_id,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        if user_data.rol == UserRole.PROFESOR and user_data.materie_id:
            classes = (await db.execute(select(SchoolClass))).scalars().all()
            for sc in classes:
                assignment = TeacherClassSubject(
                    profesor_id=user.id_utilizator,
                    clasa_id=sc.id,
                    materie_id=user_data.materie_id,
                )
                db.add(assignment)
            await db.flush()
        return await self.get_by_id(db, user.id_utilizator)

    async def create_google_user(
        self,
        db: AsyncSession,
        email: str,
        nume: str,
        google_id: str,
        role_name: str,
        avatar_url: Optional[str] = None,
    ) -> User:
        role = await self.get_role_by_name(db, role_name)
        if not role:
            role = Role(name=role_name, description=f"Rol {role_name}")
            db.add(role)
            await db.flush()

        clasa_id = None
        numar_matricol = None
        if role_name == UserRole.ELEV.value:
            res = await db.execute(select(SchoolClass.id).limit(1))
            first_class = res.scalar_one_or_none()
            if first_class:
                clasa_id = first_class
            numar_matricol = f"USV-{abs(hash(email)) % 100000:05d}"

        user = User(
            nume=nume,
            email=email.lower().strip(),
            parola_hash=None,
            role_id=role.id,
            numar_matricol=numar_matricol,
            clasa_id=clasa_id,
            google_id=google_id,
            avatar_url=avatar_url,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        return await self.get_by_id(db, user.id_utilizator)

    async def link_parent_student(
        self,
        db: AsyncSession,
        parinte_id: int,
        elev_id: int,
        relatie: str = "Parinte",
    ) -> ParentStudent:
        existing = await db.execute(
            select(ParentStudent).where(
                ParentStudent.parinte_id == parinte_id,
                ParentStudent.elev_id == elev_id,
            )
        )
        link = existing.scalars().first()
        if not link:
            link = ParentStudent(parinte_id=parinte_id, elev_id=elev_id, relatie=relatie)
            db.add(link)
            await db.flush()
        return link

    async def get_children_for_parent(self, db: AsyncSession, parinte_id: int) -> Sequence[User]:
        stmt = (
            select(User)
            .join(ParentStudent, ParentStudent.elev_id == User.id_utilizator)
            .options(joinedload(User.clasa))
            .where(ParentStudent.parinte_id == parinte_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def is_parent_of_student(self, db: AsyncSession, parinte_id: int, elev_id: int) -> bool:
        stmt = select(ParentStudent).where(
            ParentStudent.parinte_id == parinte_id,
            ParentStudent.elev_id == elev_id,
        )
        result = await db.execute(stmt)
        return result.scalars().first() is not None

auth_repository = AuthRepository()
