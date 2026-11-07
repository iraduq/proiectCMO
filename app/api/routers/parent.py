from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import ChildSummary, LinkChildRequest
from app.db.database import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user
from app.services.auth_services import auth_service

router = APIRouter(prefix="/parent", tags=["Parinte si copii"])

@router.get("/children", response_model=list[ChildSummary])
async def list_children(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChildSummary]:
    profile = await auth_service.get_user_profile(db, current_user)
    return profile.copii

@router.post("/link-child", response_model=ChildSummary, status_code=status.HTTP_201_CREATED)
async def link_child(
    data: LinkChildRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChildSummary:
    return await auth_service.link_child_to_parent(db, current_user, data)
