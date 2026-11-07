from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import DashboardSummary
from app.db.database import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user
from app.services.dashboard_services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Panou principal"])

@router.get("", response_model=DashboardSummary)
async def get_dashboard(
    student_id: Optional[int] = Query(default=None, description="Pentru parinti: ID-ul copilului afisat"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    return await dashboard_service.get_dashboard(db, current_user, student_id)
