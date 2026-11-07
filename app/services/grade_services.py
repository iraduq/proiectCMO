from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import (
    GradeCreate,
    GradeResponse,
    GradeUpdate,
    StudentAcademicOverview,
    SubjectGradesGroup,
)
from app.db.models import NotificationType, User, UserRole
from app.exceptions.exceptions import (
    GradeNotFoundError,
    InvalidGradeValueError,
    ParentChildLinkError,
    SubjectNotFoundError,
    UnauthorizedAccessError,
    UserNotFoundError,
)
from app.repositories.absence_repository import absence_repository
from app.repositories.auth_repository import auth_repository
from app.repositories.class_repository import class_repository
from app.repositories.grade_repository import grade_repository
from app.repositories.notification_repository import notification_repository
from app.repositories.remark_repository import remark_repository

class GradeService:
    def _to_response(self, grade) -> GradeResponse:
        return GradeResponse(
            id=grade.id,
            elev_id=grade.elev_id,
            elev_nume=grade.elev.nume if grade.elev else "Necunoscut",
            profesor_id=grade.profesor_id,
            profesor_nume=grade.profesor.nume if grade.profesor else "Profesor",
            materie_id=grade.materie_id,
            materie_nume=grade.materie.nume if grade.materie else "Materie",
            valoare=grade.valoare,
            tip_evaluare=grade.tip_evaluare,
            data_notare=grade.data_notare,
            observatii=grade.observatii,
            created_at=grade.created_at,
        )

    async def _check_student_access(self, db: AsyncSession, current_user: User, student_id: int) -> None:
        role = current_user.role_rel.name if current_user.role_rel else ""
        if role == UserRole.ADMINISTRATOR.value or role == UserRole.PROFESOR.value:
            return
        if role == UserRole.ELEV.value:
            if current_user.id_utilizator != student_id:
                raise UnauthorizedAccessError("Elevii isi pot consulta doar propria situatie scolara.")
            return
        if role == UserRole.PARINTE.value:
            is_parent = await auth_repository.is_parent_of_student(db, current_user.id_utilizator, student_id)
            if not is_parent:
                raise ParentChildLinkError("Acest elev nu este asociat contului dumneavoastra de parinte.")
            return
        raise UnauthorizedAccessError()

    async def add_grade(self, db: AsyncSession, current_user: User, data: GradeCreate) -> GradeResponse:
        role = current_user.role_rel.name if current_user.role_rel else ""
        if role not in (UserRole.PROFESOR.value, UserRole.ADMINISTRATOR.value):
            raise UnauthorizedAccessError("Doar profesorii si administratorii pot introduce note.")

        if role == UserRole.PROFESOR.value and current_user.materie_id:
            if data.materie_id != current_user.materie_id:
                raise UnauthorizedAccessError("Puteți adăuga note doar la materia dumneavoastră.")

        if data.valoare < 1 or data.valoare > 10:
            raise InvalidGradeValueError(data.valoare)

        student = await auth_repository.get_by_id(db, data.elev_id)
        if not student:
            raise UserNotFoundError(f"Elevul cu ID {data.elev_id} nu exista.")

        subject = await class_repository.get_subject_by_id(db, data.materie_id)
        if not subject:
            raise SubjectNotFoundError(data.materie_id)

        grade = await grade_repository.create(db, current_user.id_utilizator, data)

        notif_msg = f"Ai primit nota {grade.valoare} la materia {subject.nume} ({grade.tip_evaluare})."
        await notification_repository.create(
            db=db,
            user_id=student.id_utilizator,
            titlu=f"Nota noua: {grade.valoare} la {subject.nume}",
            mesaj=notif_msg,
            tip=NotificationType.NOTA.value,
            referinta_id=grade.id,
        )

        for legatura in student.legaturi_parinti:
            await notification_repository.create(
                db=db,
                user_id=legatura.parinte_id,
                titlu=f"Nota copil: {student.nume} a primit {grade.valoare} la {subject.nume}",
                mesaj=f"Elevul {student.nume} a fost notat cu {grade.valoare} la disciplina {subject.nume}.",
                tip=NotificationType.NOTA.value,
                referinta_id=grade.id,
            )

        return self._to_response(grade)

    async def update_grade(
        self,
        db: AsyncSession,
        current_user: User,
        grade_id: int,
        data: GradeUpdate,
    ) -> GradeResponse:
        role = current_user.role_rel.name if current_user.role_rel else ""
        grade = await grade_repository.get_by_id(db, grade_id)
        if not grade:
            raise GradeNotFoundError(grade_id)

        if role != UserRole.ADMINISTRATOR.value and grade.profesor_id != current_user.id_utilizator:
            raise UnauthorizedAccessError("Puteti modifica doar notele acordate de dumneavoastra.")

        if data.valoare is not None and (data.valoare < 1 or data.valoare > 10):
            raise InvalidGradeValueError(data.valoare)

        updated = await grade_repository.update(db, grade, data)
        return self._to_response(updated)

    async def delete_grade(self, db: AsyncSession, current_user: User, grade_id: int) -> None:
        role = current_user.role_rel.name if current_user.role_rel else ""
        grade = await grade_repository.get_by_id(db, grade_id)
        if not grade:
            raise GradeNotFoundError(grade_id)

        if role != UserRole.ADMINISTRATOR.value and grade.profesor_id != current_user.id_utilizator:
            raise UnauthorizedAccessError("Puteti sterge doar notele acordate de dumneavoastra.")

        await grade_repository.delete(db, grade)

    async def get_student_grades(
        self,
        db: AsyncSession,
        current_user: User,
        student_id: int,
        subject_id: Optional[int] = None,
    ) -> list[GradeResponse]:
        await self._check_student_access(db, current_user, student_id)
        grades = await grade_repository.get_by_student(db, student_id, subject_id)
        return [self._to_response(g) for g in grades]

    async def get_student_academic_overview(
        self,
        db: AsyncSession,
        current_user: User,
        student_id: int,
    ) -> StudentAcademicOverview:
        await self._check_student_access(db, current_user, student_id)

        student = await auth_repository.get_by_id(db, student_id)
        if not student:
            raise UserNotFoundError(f"Elevul cu ID {student_id} nu a fost gasit.")

        subjects = await class_repository.list_subjects(db)
        all_grades = await grade_repository.get_by_student(db, student_id)

        grades_by_subject: dict[int, list[GradeResponse]] = {s.id: [] for s in subjects}
        for g in all_grades:
            if g.materie_id in grades_by_subject:
                grades_by_subject[g.materie_id].append(self._to_response(g))

        subject_groups: list[SubjectGradesGroup] = []
        for s in subjects:
            note_list = grades_by_subject[s.id]
            avg = None
            if note_list:
                avg = round(sum(n.valoare for n in note_list) / len(note_list), 2)
            subject_groups.append(
                SubjectGradesGroup(
                    materie_id=s.id,
                    materie_nume=s.nume,
                    materie_cod=s.cod,
                    note=note_list,
                    medie=avg,
                )
            )

        medie_gen = await grade_repository.calculate_student_overall_average(db, student_id)
        tot_abs, mot_abs, nemot_abs = await absence_repository.count_by_student(db, student_id)
        total_ment = await remark_repository.count_by_student(db, student_id)

        return StudentAcademicOverview(
            elev_id=student.id_utilizator,
            elev_nume=student.nume,
            numar_matricol=student.numar_matricol,
            clasa_nume=student.clasa.nume if student.clasa else None,
            materii=subject_groups,
            medie_generala=medie_gen,
            total_absente=tot_abs,
            total_absente_nemotivate=nemot_abs,
            total_mentiuni=total_ment,
        )

grade_service = GradeService()
