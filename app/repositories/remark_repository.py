from typing import Optional, Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.api.schemas.edugrade import RemarkCreate
from app.db.models import Remark

class RemarkRepository:
    async def get_by_id(self, db: AsyncSession, remark_id: int) -> Optional[Remark]:
        stmt = (
            select(Remark)
            .options(
                joinedload(Remark.elev),
                joinedload(Remark.profesor),
            )
            .where(Remark.id == remark_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_student(self, db: AsyncSession, student_id: int) -> Sequence[Remark]:
        stmt = (
            select(Remark)
            .options(
                joinedload(Remark.elev),
                joinedload(Remark.profesor),
            )
            .where(Remark.elev_id == student_id)
            .order_by(Remark.data.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count_by_student(self, db: AsyncSession, student_id: int) -> int:
        stmt = select(func.count()).select_from(Remark).where(Remark.elev_id == student_id)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def create(self, db: AsyncSession, teacher_id: int, data: RemarkCreate) -> Remark:
        remark = Remark(
            elev_id=data.elev_id,
            profesor_id=teacher_id,
            tip=data.tip,
            titlu=data.titlu,
            descriere=data.descriere,
            data=data.data or func.now(),
        )
        db.add(remark)
        await db.flush()
        return await self.get_by_id(db, remark.id)

    async def delete(self, db: AsyncSession, remark: Remark) -> None:
        await db.delete(remark)
        await db.flush()

remark_repository = RemarkRepository()
