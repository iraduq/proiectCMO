from typing import Optional, Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Notification

class NotificationRepository:
    async def get_by_id(self, db: AsyncSession, notification_id: int) -> Optional[Notification]:
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
    ) -> Sequence[Notification]:
        stmt = select(Notification).where(Notification.utilizator_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.este_citita == False)
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count_unread(self, db: AsyncSession, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.utilizator_id == user_id, Notification.este_citita == False)
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        titlu: str,
        mesaj: str,
        tip: str = "SISTEM",
        referinta_id: Optional[int] = None,
    ) -> Notification:
        notif = Notification(
            utilizator_id=user_id,
            titlu=titlu,
            mesaj=mesaj,
            tip=tip,
            este_citita=False,
            referinta_id=referinta_id,
        )
        db.add(notif)
        await db.flush()
        return notif

    async def mark_as_read(self, db: AsyncSession, notification: Notification) -> Notification:
        notification.este_citita = True
        await db.flush()
        return notification

    async def mark_all_as_read(self, db: AsyncSession, user_id: int) -> int:
        notifications = await self.get_by_user(db, user_id, unread_only=True)
        count = 0
        for notif in notifications:
            notif.este_citita = True
            count += 1
        await db.flush()
        return count

notification_repository = NotificationRepository()
