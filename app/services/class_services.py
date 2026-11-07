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
from app.db.models import User, UserRole
from app.exceptions.exceptions import ClassNotFoundError, SubjectNotFoundError, UnauthorizedAccessError
from app.repositories.class_repository import class_repository

class ClassService:
    async def list_classes(self, db: AsyncSession) -> list[SchoolClassResponse]:
        classes = await class_repository.list_classes(db)
        return [
            SchoolClassResponse(
                id=c.id,
                nume=c.nume,
                specializare=c.specializare,
                an_scolar=c.an_scolar,
                diriginte_id=c.diriginte_id,
                diriginte_nume=c.diriginte.nume if c.diriginte else None,
                numar_elevi=len(c.elevi) if c.elevi else 0,
            )
            for c in classes
        ]

    async def get_class(self, db: AsyncSession, class_id: int) -> SchoolClassResponse:
        c = await class_repository.get_class_by_id(db, class_id)
        if not c:
            raise ClassNotFoundError(class_id)
        return SchoolClassResponse(
            id=c.id,
            nume=c.nume,
            specializare=c.specializare,
            an_scolar=c.an_scolar,
            diriginte_id=c.diriginte_id,
            diriginte_nume=c.diriginte.nume if c.diriginte else None,
            numar_elevi=len(c.elevi) if c.elevi else 0,
        )

    async def get_class_students(self, db: AsyncSession, class_id: int) -> list[UserResponse]:
        c = await class_repository.get_class_by_id(db, class_id)
        if not c:
            raise ClassNotFoundError(class_id)
        return [
            UserResponse(
                id_utilizator=e.id_utilizator,
                nume=e.nume,
                email=e.email,
                role=e.role_rel.name if e.role_rel else "ELEV",
                numar_matricol=e.numar_matricol,
                telefon=e.telefon,
                avatar_url=e.avatar_url,
                clasa_id=c.id,
                clasa_nume=c.nume,
                is_active=e.is_active,
                created_at=e.created_at,
            )
            for e in (c.elevi or [])
        ]

    async def create_class(self, db: AsyncSession, current_user: User, data: SchoolClassCreate) -> SchoolClassResponse:
        if current_user.role_rel.name != UserRole.ADMINISTRATOR.value:
            raise UnauthorizedAccessError("Doar administratorii pot crea clase noi.")
        created = await class_repository.create_class(db, data)
        return SchoolClassResponse(
            id=created.id,
            nume=created.nume,
            specializare=created.specializare,
            an_scolar=created.an_scolar,
            diriginte_id=created.diriginte_id,
            diriginte_nume=created.diriginte.nume if created.diriginte else None,
            numar_elevi=0,
        )

    async def list_subjects(self, db: AsyncSession) -> list[SubjectResponse]:
        subjects = await class_repository.list_subjects(db)
        return [
            SubjectResponse(
                id=s.id,
                nume=s.nume,
                cod=s.cod,
                descriere=s.descriere,
                coeficient_credite=s.coeficient_credite,
                is_active=s.is_active,
            )
            for s in subjects
        ]

    async def create_subject(self, db: AsyncSession, current_user: User, data: SubjectCreate) -> SubjectResponse:
        if current_user.role_rel.name != UserRole.ADMINISTRATOR.value:
            raise UnauthorizedAccessError("Doar administratorii pot adauga materii noi.")
        created = await class_repository.create_subject(db, data)
        return SubjectResponse(
            id=created.id,
            nume=created.nume,
            cod=created.cod,
            descriere=created.descriere,
            coeficient_credite=created.coeficient_credite,
            is_active=created.is_active,
        )

    async def assign_teacher(
        self,
        db: AsyncSession,
        current_user: User,
        data: TeacherAssignmentCreate,
    ) -> TeacherAssignmentResponse:
        if current_user.role_rel.name != UserRole.ADMINISTRATOR.value:
            raise UnauthorizedAccessError("Doar administratorii pot asigna profesori.")
        assignment = await class_repository.assign_teacher(db, data)
        return TeacherAssignmentResponse(
            id=assignment.id,
            profesor_id=assignment.profesor_id,
            profesor_nume=assignment.profesor.nume,
            clasa_id=assignment.clasa_id,
            clasa_nume=assignment.clasa.nume,
            materie_id=assignment.materie_id,
            materie_nume=assignment.materie.nume,
        )

class_service = ClassService()
