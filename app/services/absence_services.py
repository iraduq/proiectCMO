from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import AbsenceCreate, AbsenceMotivateRequest, AbsenceResponse, AbsenceSummary
from app.db.models import NotificationType, User, UserRole
from app.exceptions.exceptions import (
    AbsenceNotFoundError,
    ParentChildLinkError,
    SubjectNotFoundError,
    UnauthorizedAccessError,
    UserNotFoundError,
)
from app.repositories.absence_repository import absence_repository
from app.repositories.auth_repository import auth_repository
from app.repositories.class_repository import class_repository
from app.repositories.notification_repository import notification_repository

class AbsenceService:
    def _to_response(self, abs_obj) -> AbsenceResponse:
        return AbsenceResponse(
            id=abs_obj.id,
            elev_id=abs_obj.elev_id,
            elev_nume=abs_obj.elev.nume if abs_obj.elev else "Necunoscut",
            profesor_id=abs_obj.profesor_id,
            profesor_nume=abs_obj.profesor.nume if abs_obj.profesor else "Profesor",
            materie_id=abs_obj.materie_id,
            materie_nume=abs_obj.materie.nume if abs_obj.materie else "Materie",
            data=abs_obj.data,
            este_motivata=abs_obj.este_motivata,
            data_motivare=abs_obj.data_motivare,
            motiv=abs_obj.motiv,
            created_at=abs_obj.created_at,
        )

    async def _check_student_access(self, db: AsyncSession, current_user: User, student_id: int) -> None:
        role = current_user.role_rel.name if current_user.role_rel else ""
        if role in (UserRole.ADMINISTRATOR.value, UserRole.PROFESOR.value):
            return
        if role == UserRole.ELEV.value:
            if current_user.id_utilizator != student_id:
                raise UnauthorizedAccessError("Elevii isi pot consulta doar propriile absente.")
            return
        if role == UserRole.PARINTE.value:
            is_parent = await auth_repository.is_parent_of_student(db, current_user.id_utilizator, student_id)
            if not is_parent:
                raise ParentChildLinkError("Acest elev nu este asociat contului dumneavoastra de parinte.")
            return
        raise UnauthorizedAccessError()

    async def add_absence(self, db: AsyncSession, current_user: User, data: AbsenceCreate) -> AbsenceResponse:
        role = current_user.role_rel.name if current_user.role_rel else ""
        if role not in (UserRole.PROFESOR.value, UserRole.ADMINISTRATOR.value):
            raise UnauthorizedAccessError("Doar profesorii pot trece absente.")

        if role == UserRole.PROFESOR.value and current_user.materie_id:
            if data.materie_id != current_user.materie_id:
                raise UnauthorizedAccessError("Puteți adăuga absențe doar la materia dumneavoastră.")

        student = await auth_repository.get_by_id(db, data.elev_id)
        if not student:
            raise UserNotFoundError(f"Elevul cu ID {data.elev_id} nu exista.")

        subject = await class_repository.get_subject_by_id(db, data.materie_id)
        if not subject:
            raise SubjectNotFoundError(data.materie_id)

        absence = await absence_repository.create(db, current_user.id_utilizator, data)

        await notification_repository.create(
            db=db,
            user_id=student.id_utilizator,
            titlu=f"Absenta noua la {subject.nume}",
            mesaj=f"A fost inregistrata o absenta la ora de {subject.nume}.",
            tip=NotificationType.ABSENTA.value,
            referinta_id=absence.id,
        )

        for legatura in student.legaturi_parinti:
            await notification_repository.create(
                db=db,
                user_id=legatura.parinte_id,
                titlu=f"Absenta copil: {student.nume} la {subject.nume}",
                mesaj=f"Copilul dumneavoastra {student.nume} are o absenta nemotivata la {subject.nume}.",
                tip=NotificationType.ABSENTA.value,
                referinta_id=absence.id,
            )

        return self._to_response(absence)

    async def motivate_absence(
        self,
        db: AsyncSession,
        current_user: User,
        absence_id: int,
        data: AbsenceMotivateRequest,
    ) -> AbsenceResponse:
        role = current_user.role_rel.name if current_user.role_rel else ""
        if role not in (UserRole.PROFESOR.value, UserRole.ADMINISTRATOR.value):
            raise UnauthorizedAccessError("Doar profesorii sau dirigintii pot motiva absente.")

        absence = await absence_repository.get_by_id(db, absence_id)
        if not absence:
            raise AbsenceNotFoundError(absence_id)

        updated = await absence_repository.motivate(db, absence, data.este_motivata, data.motiv)

        if data.este_motivata:
            student = await auth_repository.get_by_id(db, updated.elev_id)
            if student:
                await notification_repository.create(
                    db=db,
                    user_id=student.id_utilizator,
                    titlu=f"Absenta motivata la {updated.materie.nume}",
                    mesaj=f"Absenta din {updated.data.strftime('%d.%m.%Y')} a fost motivata cu succes.",
                    tip=NotificationType.ABSENTA.value,
                    referinta_id=updated.id,
                )

        return self._to_response(updated)

    async def delete_absence(self, db: AsyncSession, current_user: User, absence_id: int) -> None:
        role = current_user.role_rel.name if current_user.role_rel else ""
        absence = await absence_repository.get_by_id(db, absence_id)
        if not absence:
            raise AbsenceNotFoundError(absence_id)

        if role != UserRole.ADMINISTRATOR.value and absence.profesor_id != current_user.id_utilizator:
            raise UnauthorizedAccessError("Puteti sterge doar absentele inregistrate de dumneavoastra.")

        await absence_repository.delete(db, absence)

    async def get_student_absences(
        self,
        db: AsyncSession,
        current_user: User,
        student_id: int,
        subject_id: Optional[int] = None,
    ) -> AbsenceSummary:
        await self._check_student_access(db, current_user, student_id)
        absences = await absence_repository.get_by_student(db, student_id, subject_id)
        total, motivate, nemotivate = await absence_repository.count_by_student(db, student_id)

        return AbsenceSummary(
            total_absente=total,
            total_motivate=motivate,
            total_nemotivate=nemotivate,
            absente=[self._to_response(a) for a in absences],
        )

absence_service = AbsenceService()
