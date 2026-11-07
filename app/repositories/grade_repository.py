from typing import Optional, Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.api.schemas.edugrade import GradeCreate, GradeUpdate
from app.db.models import Grade, Subject, User

class GradeRepository:
    async def get_by_id(self, db: AsyncSession, grade_id: int) -> Optional[Grade]:
        stmt = (
            select(Grade)
            .options(
                joinedload(Grade.elev),
                joinedload(Grade.profesor),
                joinedload(Grade.materie),
            )
            .where(Grade.id == grade_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_student(
        self,
        db: AsyncSession,
        student_id: int,
        subject_id: Optional[int] = None,
    ) -> Sequence[Grade]:
        stmt = (
            select(Grade)
            .options(
                joinedload(Grade.elev),
                joinedload(Grade.profesor),
                joinedload(Grade.materie),
            )
            .where(Grade.elev_id == student_id)
        )
        if subject_id:
            stmt = stmt.where(Grade.materie_id == subject_id)
        stmt = stmt.order_by(Grade.data_notare.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_teacher(self, db: AsyncSession, teacher_id: int) -> Sequence[Grade]:
        stmt = (
            select(Grade)
            .options(
                joinedload(Grade.elev),
                joinedload(Grade.profesor),
                joinedload(Grade.materie),
            )
            .where(Grade.profesor_id == teacher_id)
            .order_by(Grade.data_notare.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, teacher_id: int, data: GradeCreate) -> Grade:
        grade = Grade(
            elev_id=data.elev_id,
            profesor_id=teacher_id,
            materie_id=data.materie_id,
            valoare=data.valoare,
            tip_evaluare=data.tip_evaluare,
            data_notare=data.data_notare or func.now(),
            observatii=data.observatii,
        )
        db.add(grade)
        await db.flush()
        return await self.get_by_id(db, grade.id)

    async def update(self, db: AsyncSession, grade: Grade, data: GradeUpdate) -> Grade:
        if data.valoare is not None:
            grade.valoare = data.valoare
        if data.tip_evaluare is not None:
            grade.tip_evaluare = data.tip_evaluare
        if data.observatii is not None:
            grade.observatii = data.observatii
        await db.flush()
        return await self.get_by_id(db, grade.id)

    async def delete(self, db: AsyncSession, grade: Grade) -> None:
        await db.delete(grade)
        await db.flush()

    async def calculate_student_subject_average(
        self,
        db: AsyncSession,
        student_id: int,
        subject_id: int,
    ) -> Optional[float]:
        stmt = (
            select(func.avg(Grade.valoare))
            .where(Grade.elev_id == student_id, Grade.materie_id == subject_id)
        )
        result = await db.execute(stmt)
        val = result.scalar()
        return round(float(val), 2) if val is not None else None

    async def calculate_student_overall_average(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> Optional[float]:
        stmt = (
            select(Grade.materie_id, func.avg(Grade.valoare).label("medie_materie"))
            .where(Grade.elev_id == student_id)
            .group_by(Grade.materie_id)
        )
        result = await db.execute(stmt)
        rows = result.all()
        if not rows:
            return None
        subject_averages = [float(row.medie_materie) for row in rows]
        overall = sum(subject_averages) / len(subject_averages)
        return round(overall, 2)

grade_repository = GradeRepository()
