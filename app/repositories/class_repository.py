from typing import Optional, Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from app.api.schemas.edugrade import SchoolClassCreate, SubjectCreate, TeacherAssignmentCreate
from app.db.models import SchoolClass, Subject, TeacherClassSubject, User

class ClassRepository:
    async def get_class_by_id(self, db: AsyncSession, class_id: int) -> Optional[SchoolClass]:
        stmt = (
            select(SchoolClass)
            .options(
                joinedload(SchoolClass.diriginte),
                selectinload(SchoolClass.elevi),
            )
            .where(SchoolClass.id == class_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_classes(self, db: AsyncSession) -> Sequence[SchoolClass]:
        stmt = (
            select(SchoolClass)
            .options(
                joinedload(SchoolClass.diriginte),
                selectinload(SchoolClass.elevi),
            )
            .where(SchoolClass.is_active == True)
            .order_by(SchoolClass.nume.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def list_all_students(self, db: AsyncSession, class_id: Optional[int] = None) -> Sequence[User]:
        stmt = (
            select(User)
            .options(
                joinedload(User.clasa),
                joinedload(User.role_rel),
            )
            .where(User.clasa_id.is_not(None), User.is_active == True)
        )
        if class_id:
            stmt = stmt.where(User.clasa_id == class_id)
        stmt = stmt.order_by(User.nume.asc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_class(self, db: AsyncSession, data: SchoolClassCreate) -> SchoolClass:
        school_class = SchoolClass(
            nume=data.nume,
            specializare=data.specializare,
            an_scolar=data.an_scolar,
            diriginte_id=data.diriginte_id,
            is_active=True,
        )
        db.add(school_class)
        await db.flush()
        return await self.get_class_by_id(db, school_class.id)

    async def get_subject_by_id(self, db: AsyncSession, subject_id: int) -> Optional[Subject]:
        stmt = select(Subject).where(Subject.id == subject_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_subject_by_code(self, db: AsyncSession, code: str) -> Optional[Subject]:
        stmt = select(Subject).where(Subject.cod.ilike(code))
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_subjects(self, db: AsyncSession) -> Sequence[Subject]:
        stmt = select(Subject).where(Subject.is_active == True).order_by(Subject.nume.asc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_subject(self, db: AsyncSession, data: SubjectCreate) -> Subject:
        subject = Subject(
            nume=data.nume,
            cod=data.cod.upper(),
            descriere=data.descriere,
            coeficient_credite=data.coeficient_credite,
            is_active=True,
        )
        db.add(subject)
        await db.flush()
        return subject

    async def assign_teacher(self, db: AsyncSession, data: TeacherAssignmentCreate) -> TeacherClassSubject:
        assignment = TeacherClassSubject(
            profesor_id=data.profesor_id,
            clasa_id=data.clasa_id,
            materie_id=data.materie_id,
        )
        db.add(assignment)
        await db.flush()
        stmt = (
            select(TeacherClassSubject)
            .options(
                joinedload(TeacherClassSubject.profesor),
                joinedload(TeacherClassSubject.clasa),
                joinedload(TeacherClassSubject.materie),
            )
            .where(TeacherClassSubject.id == assignment.id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_teacher_assignments(self, db: AsyncSession, teacher_id: int) -> Sequence[TeacherClassSubject]:
        stmt = (
            select(TeacherClassSubject)
            .options(
                joinedload(TeacherClassSubject.profesor),
                joinedload(TeacherClassSubject.clasa),
                joinedload(TeacherClassSubject.materie),
            )
            .where(TeacherClassSubject.profesor_id == teacher_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

class_repository = ClassRepository()
