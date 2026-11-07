from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import NotificationResponse, UnreadCountResponse
from app.db.models import User
from app.exceptions.exceptions import NotificationNotFoundError, UnauthorizedAccessError
from app.repositories.notification_repository import notification_repository

class NotificationService:
    def _to_response(self, notif) -> NotificationResponse:
        return NotificationResponse(
            id=notif.id,
            utilizator_id=notif.utilizator_id,
            titlu=notif.titlu,
            mesaj=notif.mesaj,
            tip=notif.tip,
            este_citita=notif.este_citita,
            referinta_id=notif.referinta_id,
            created_at=notif.created_at,
        )

    async def get_my_notifications(
        self,
        db: AsyncSession,
        current_user: User,
        unread_only: bool = False,
    ) -> list[NotificationResponse]:
        notifications = await notification_repository.get_by_user(
            db=db,
            user_id=current_user.id_utilizator,
            unread_only=unread_only,
        )
        return [self._to_response(n) for n in notifications]

    async def get_unread_count(self, db: AsyncSession, current_user: User) -> UnreadCountResponse:
        count = await notification_repository.count_unread(db, current_user.id_utilizator)
        return UnreadCountResponse(unread_count=count)

    async def mark_as_read(
        self,
        db: AsyncSession,
        current_user: User,
        notification_id: int,
    ) -> NotificationResponse:
        notif = await notification_repository.get_by_id(db, notification_id)
        if not notif:
            raise NotificationNotFoundError(notification_id)
        if notif.utilizator_id != current_user.id_utilizator:
            raise UnauthorizedAccessError("Puteti marca drept citite doar propriile notificari.")
        updated = await notification_repository.mark_as_read(db, notif)
        return self._to_response(updated)

    async def mark_all_as_read(self, db: AsyncSession, current_user: User) -> int:
        return await notification_repository.mark_all_as_read(db, current_user.id_utilizator)

notification_service = NotificationService()
