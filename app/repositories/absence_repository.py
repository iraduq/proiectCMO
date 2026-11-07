from datetime import datetime, timezone
from typing import Optional, Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.api.schemas.edugrade import AbsenceCreate
from app.db.models import Absence

class AbsenceRepository:
    async def get_by_id(self, db: AsyncSession, absence_id: int) -> Optional[Absence]:
        stmt = (
            select(Absence)
            .options(
                joinedload(Absence.elev),
                joinedload(Absence.profesor),
                joinedload(Absence.materie),
            )
            .where(Absence.id == absence_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_student(
        self,
        db: AsyncSession,
        student_id: int,
        subject_id: Optional[int] = None,
    ) -> Sequence[Absence]:
        stmt = (
            select(Absence)
            .options(
                joinedload(Absence.elev),
                joinedload(Absence.profesor),
                joinedload(Absence.materie),
            )
            .where(Absence.elev_id == student_id)
        )
        if subject_id:
            stmt = stmt.where(Absence.materie_id == subject_id)
        stmt = stmt.order_by(Absence.data.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count_by_student(self, db: AsyncSession, student_id: int) -> tuple[int, int, int]:
        stmt_total = select(func.count()).select_from(Absence).where(Absence.elev_id == student_id)
        stmt_mot = (
            select(func.count())
            .select_from(Absence)
            .where(Absence.elev_id == student_id, Absence.este_motivata == True)
        )
        total = (await db.execute(stmt_total)).scalar_one()
        motivate = (await db.execute(stmt_mot)).scalar_one()
        nemotivate = total - motivate
        return total, motivate, nemotivate

    async def create(self, db: AsyncSession, teacher_id: int, data: AbsenceCreate) -> Absence:
        absence = Absence(
            elev_id=data.elev_id,
            profesor_id=teacher_id,
            materie_id=data.materie_id,
            data=data.data or func.now(),
            este_motivata=data.este_motivata,
            motiv=data.motiv,
        )
        db.add(absence)
        await db.flush()
        return await self.get_by_id(db, absence.id)

    async def motivate(
        self,
        db: AsyncSession,
        absence: Absence,
        este_motivata: bool,
        motiv: Optional[str] = None,
    ) -> Absence:
        absence.este_motivata = este_motivata
        absence.data_motivare = func.now() if este_motivata else None
        if motiv:
            absence.motiv = motiv
        await db.flush()
        return await self.get_by_id(db, absence.id)

    async def delete(self, db: AsyncSession, absence: Absence) -> None:
        await db.delete(absence)
        await db.flush()

absence_repository = AbsenceRepository()
