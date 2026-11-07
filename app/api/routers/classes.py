from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import (
    SchoolClassCreate,
    SchoolClassResponse,
    SubjectCreate,
    SubjectResponse,
    TeacherAssignmentCreate,
    TeacherAssignmentResponse,
    UserResponse,
)
from app.db.database import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user
from app.services.class_services import class_service

router = APIRouter(tags=["Clase si materii"])

@router.get("/classes", response_model=list[SchoolClassResponse])
async def list_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SchoolClassResponse]:
    return await class_service.list_classes(db)

@router.get("/students", response_model=list[UserResponse])
async def list_students(
    class_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserResponse]:
    return await class_service.list_students(db, class_id=class_id, query=q)

@router.get("/classes/{class_id}", response_model=SchoolClassResponse)
async def get_class(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SchoolClassResponse:
    return await class_service.get_class(db, class_id)

@router.get("/classes/{class_id}/students", response_model=list[UserResponse])
async def get_class_students(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserResponse]:
    return await class_service.get_class_students(db, class_id)

@router.post("/classes", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    data: SchoolClassCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SchoolClassResponse:
    return await class_service.create_class(db, current_user, data)

@router.get("/subjects", response_model=list[SubjectResponse])
async def list_subjects(
    all_subjects: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SubjectResponse]:
    from app.db.models import UserRole
    from app.repositories.class_repository import class_repository
    if not all_subjects and current_user.role_rel and current_user.role_rel.name == UserRole.PROFESOR.value and current_user.materie_id:
        subj = await class_repository.get_subject_by_id(db, current_user.materie_id)
        if subj:
            return [
                SubjectResponse(
                    id=subj.id,
                    nume=subj.nume,
                    cod=subj.cod,
                    descriere=subj.descriere,
                    coeficient_credite=subj.coeficient_credite,
                    is_active=subj.is_active,
                )
            ]
    return await class_service.list_subjects(db)

@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubjectResponse:
    return await class_service.create_subject(db, current_user, data)

@router.post("/classes/assign-teacher", response_model=TeacherAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_teacher(
    data: TeacherAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeacherAssignmentResponse:
    return await class_service.assign_teacher(db, current_user, data)
