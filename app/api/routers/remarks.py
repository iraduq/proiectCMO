from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import RemarkCreate, RemarkResponse
from app.db.database import get_db
from app.db.models import User, UserRole
from app.dependencies.auth import get_current_user
from app.repositories.auth_repository import auth_repository
from app.services.remark_services import remark_service

router = APIRouter(prefix="/remarks", tags=["Mentiuni & Aprecieri"])

@router.post("", response_model=RemarkResponse, status_code=status.HTTP_201_CREATED)
async def add_remark(
    data: RemarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RemarkResponse:
    return await remark_service.add_remark(db, current_user, data)

@router.get("", response_model=list[RemarkResponse])
async def list_remarks(
    student_id: Optional[int] = Query(default=None, description="ID elev pentru parinti/profesori"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RemarkResponse]:
    target_id = student_id
    role = current_user.role_rel.name if current_user.role_rel else ""

    if role == UserRole.ELEV.value:
        target_id = current_user.id_utilizator
    elif role == UserRole.PARINTE.value and not target_id:
        children = await auth_repository.get_children_for_parent(db, current_user.id_utilizator)
        if children:
            target_id = children[0].id_utilizator
        else:
            return []

    if not target_id:
        target_id = current_user.id_utilizator

    return await remark_service.get_student_remarks(db, current_user, target_id)

@router.get("/student/{student_id}", response_model=list[RemarkResponse])
async def get_student_remarks(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RemarkResponse]:
    return await remark_service.get_student_remarks(db, current_user, student_id)

@router.delete("/{remark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_remark(
    remark_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await remark_service.delete_remark(db, current_user, remark_id)
