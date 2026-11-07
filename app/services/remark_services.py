from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import RemarkCreate, RemarkResponse
from app.db.models import NotificationType, User, UserRole
from app.exceptions.exceptions import (
    ParentChildLinkError,
    RemarkNotFoundError,
    UnauthorizedAccessError,
    UserNotFoundError,
)
from app.repositories.auth_repository import auth_repository
from app.repositories.notification_repository import notification_repository
from app.repositories.remark_repository import remark_repository

class RemarkService:
    def _to_response(self, r) -> RemarkResponse:
        return RemarkResponse(
            id=r.id,
            elev_id=r.elev_id,
            elev_nume=r.elev.nume if r.elev else "Necunoscut",
            profesor_id=r.profesor_id,
            profesor_nume=r.profesor.nume if r.profesor else "Profesor",
            tip=r.tip,
            titlu=r.titlu,
            descriere=r.descriere,
            data=r.data,
            created_at=r.created_at,
        )

    async def _check_student_access(self, db: AsyncSession, current_user: User, student_id: int) -> None:
        role = current_user.role_rel.name if current_user.role_rel else ""
        if role in (UserRole.ADMINISTRATOR.value, UserRole.PROFESOR.value):
            return
        if role == UserRole.ELEV.value:
            if current_user.id_utilizator != student_id:
                raise UnauthorizedAccessError("Elevii pot consulta doar propriile mentiuni.")
            return
        if role == UserRole.PARINTE.value:
            is_parent = await auth_repository.is_parent_of_student(db, current_user.id_utilizator, student_id)
            if not is_parent:
                raise ParentChildLinkError("Acest elev nu este asociat contului dumneavoastra de parinte.")
            return
        raise UnauthorizedAccessError()

    async def add_remark(self, db: AsyncSession, current_user: User, data: RemarkCreate) -> RemarkResponse:
        role = current_user.role_rel.name if current_user.role_rel else ""
        if role not in (UserRole.PROFESOR.value, UserRole.ADMINISTRATOR.value):
            raise UnauthorizedAccessError("Doar cadrele didactice pot acorda mentiuni sau observatii.")

        student = await auth_repository.get_by_id(db, data.elev_id)
        if not student:
            raise UserNotFoundError(f"Elevul cu ID {data.elev_id} nu exista.")

        remark = await remark_repository.create(db, current_user.id_utilizator, data)

        await notification_repository.create(
            db=db,
            user_id=student.id_utilizator,
            titlu=f"Mentiune noua: {remark.titlu}",
            mesaj=f"Ai primit o mentiune de la {current_user.nume}: {remark.descriere}",
            tip=NotificationType.MENTIUNE.value,
            referinta_id=remark.id,
        )

        for legatura in student.legaturi_parinti:
            await notification_repository.create(
                db=db,
                user_id=legatura.parinte_id,
                titlu=f"Mentiune copil ({student.nume}): {remark.titlu}",
                mesaj=f"{student.nume} a primit o mentiune: {remark.descriere}",
                tip=NotificationType.MENTIUNE.value,
                referinta_id=remark.id,
            )

        return self._to_response(remark)

    async def delete_remark(self, db: AsyncSession, current_user: User, remark_id: int) -> None:
        role = current_user.role_rel.name if current_user.role_rel else ""
        remark = await remark_repository.get_by_id(db, remark_id)
        if not remark:
            raise RemarkNotFoundError(remark_id)

        if role != UserRole.ADMINISTRATOR.value and remark.profesor_id != current_user.id_utilizator:
            raise UnauthorizedAccessError("Puteti sterge doar mentiunile adaugate de dumneavoastra.")

        await remark_repository.delete(db, remark)

    async def get_student_remarks(
        self,
        db: AsyncSession,
        current_user: User,
        student_id: int,
    ) -> list[RemarkResponse]:
        await self._check_student_access(db, current_user, student_id)
        remarks = await remark_repository.get_by_student(db, student_id)
        return [self._to_response(r) for r in remarks]

remark_service = RemarkService()
