from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import NotificationResponse, UnreadCountResponse
from app.db.database import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user
from app.services.notification_services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notificari"])

@router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(default=False, description="Doar notificarile necitite"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    return await notification_service.get_my_notifications(db, current_user, unread_only)

@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountResponse:
    return await notification_service.get_unread_count(db, current_user)

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    return await notification_service.mark_as_read(db, current_user, notification_id)

@router.patch("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    count = await notification_service.mark_all_as_read(db, current_user)
    return {"marked_as_read": count}
