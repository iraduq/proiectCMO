from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import (
    AbsenceCreate,
    AbsenceResponse,
    AbsenceSummary,
    AbsenceMotivateRequest,
)
from app.db.database import get_db
from app.db.models import User, UserRole
from app.dependencies.auth import get_current_user
from app.repositories.auth_repository import auth_repository
from app.services.absence_services import absence_service
from app.services.class_services import class_service

router = APIRouter(prefix="/absences", tags=["Absente"])

@router.get("", response_model=AbsenceSummary)
async def list_absences(
    student_id: Optional[int] = Query(default=None, description="ID elev pentru parinti/profesori"),
    subject_id: Optional[int] = Query(default=None, description="Filtrare dupa materie"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AbsenceSummary:
    target_id = student_id
    role = current_user.role_rel.name if current_user.role_rel else ""

    if role == UserRole.ELEV.value:
        target_id = current_user.id_utilizator
    elif role == UserRole.PARINTE.value and not target_id:
        children = await auth_repository.get_children_for_parent(db, current_user.id_utilizator)
        if children:
            target_id = children[0].id_utilizator
        else:
            return AbsenceSummary(total_absente=0, total_motivate=0, total_nemotivate=0, absente=[])
    elif role == UserRole.PROFESOR.value and not target_id:
        classes = await class_service.list_classes(db)
        if classes:
            st = await class_service.get_class_students(db, classes[0].id)
            if st:
                target_id = st[0].id_utilizator

    if not target_id:
        target_id = current_user.id_utilizator

    return await absence_service.get_student_absences(db, current_user, target_id, subject_id)

@router.get("/student/{student_id}", response_model=AbsenceSummary)
async def get_student_absences(
    student_id: int,
    subject_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AbsenceSummary:
    return await absence_service.get_student_absences(db, current_user, student_id, subject_id)

@router.post("", response_model=AbsenceResponse, status_code=status.HTTP_201_CREATED)
async def add_absence(
    data: AbsenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AbsenceResponse:
    return await absence_service.add_absence(db, current_user, data)

@router.post("/{absence_id}/motivate", response_model=AbsenceResponse)
async def motivate_absence(
    absence_id: int,
    data: AbsenceMotivateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AbsenceResponse:
    return await absence_service.motivate_absence(db, current_user, absence_id, data)

@router.delete("/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_absence(
    absence_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await absence_service.delete_absence(db, current_user, absence_id)
