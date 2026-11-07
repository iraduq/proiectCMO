from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import (
    GradeCreate,
    GradeResponse,
    GradeUpdate,
    StudentAcademicOverview,
)
from app.db.database import get_db
from app.db.models import User, UserRole
from app.dependencies.auth import get_current_user
from app.repositories.auth_repository import auth_repository
from app.services.grade_services import grade_service
from app.services.class_services import class_service

router = APIRouter(prefix="/grades", tags=["Note si situatie scolara"])

@router.post("", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def add_grade(
    data: GradeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GradeResponse:
    return await grade_service.add_grade(db, current_user, data)

@router.get("", response_model=list[GradeResponse])
async def list_grades(
    student_id: Optional[int] = Query(default=None, description="ID-ul elevului (optional pentru parinte/profesor)"),
    subject_id: Optional[int] = Query(default=None, description="Filtrare dupa materie"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GradeResponse]:
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

    if target_id:
        return await grade_service.get_student_grades(db, current_user, target_id, subject_id)

    from app.repositories.grade_repository import grade_repository
    grades = await grade_repository.get_by_teacher(db, current_user.id_utilizator)
    return [grade_service._to_response(g) for g in grades]

@router.get("/my-overview", response_model=StudentAcademicOverview)
async def get_my_academic_overview(
    student_id: Optional[int] = Query(default=None, description="ID copil pentru conturile de parinte"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudentAcademicOverview:
    target_id = student_id
    role = current_user.role_rel.name if current_user.role_rel else ""

    if role == UserRole.ELEV.value:
        target_id = current_user.id_utilizator
    elif role == UserRole.PARINTE.value and not target_id:
        children = await auth_repository.get_children_for_parent(db, current_user.id_utilizator)
        if children:
            target_id = children[0].id_utilizator
        else:
            from app.exceptions.exceptions import ParentChildLinkError
            raise ParentChildLinkError("Nu aveti niciun elev asociat contului.")
    elif role == UserRole.PROFESOR.value and not target_id:
        classes = await class_service.list_classes(db)
        if classes:
            st = await class_service.get_class_students(db, classes[0].id)
            if st:
                target_id = st[0].id_utilizator

    return await grade_service.get_student_academic_overview(db, current_user, target_id)

@router.get("/student/{student_id}", response_model=list[GradeResponse])
async def get_grades_for_student(
    student_id: int,
    subject_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GradeResponse]:
    return await grade_service.get_student_grades(db, current_user, student_id, subject_id)

@router.get("/student/{student_id}/overview", response_model=StudentAcademicOverview)
async def get_student_overview(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudentAcademicOverview:
    return await grade_service.get_student_academic_overview(db, current_user, student_id)

@router.put("/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: int,
    data: GradeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GradeResponse:
    return await grade_service.update_grade(db, current_user, grade_id, data)

@router.delete("/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade(
    grade_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await grade_service.delete_grade(db, current_user, grade_id)
