from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.edugrade import DashboardSummary
from app.db.models import User, UserRole
from app.repositories.absence_repository import absence_repository
from app.repositories.auth_repository import auth_repository
from app.repositories.grade_repository import grade_repository
from app.repositories.notification_repository import notification_repository
from app.repositories.remark_repository import remark_repository
from app.services.absence_services import absence_service
from app.services.grade_services import grade_service
from app.services.remark_services import remark_service

class DashboardService:
    async def get_dashboard(
        self,
        db: AsyncSession,
        current_user: User,
        student_id: Optional[int] = None,
    ) -> DashboardSummary:
        role = current_user.role_rel.name if current_user.role_rel else "ELEV"
        target_student_id = current_user.id_utilizator

        if role == UserRole.PARINTE.value:
            if student_id:
                target_student_id = student_id
            else:
                children = await auth_repository.get_children_for_parent(db, current_user.id_utilizator)
                if children:
                    target_student_id = children[0].id_utilizator

        unread_notifs = await notification_repository.count_unread(db, current_user.id_utilizator)

        if role in (UserRole.ELEV.value, UserRole.PARINTE.value):
            grades = await grade_repository.get_by_student(db, target_student_id)
            absences = await absence_repository.get_by_student(db, target_student_id)
            remarks = await remark_repository.get_by_student(db, target_student_id)
            overall_avg = await grade_repository.calculate_student_overall_average(db, target_student_id)
            tot_abs, mot_abs, nemot_abs = await absence_repository.count_by_student(db, target_student_id)

            return DashboardSummary(
                rol=role,
                nume=current_user.nume,
                total_note=len(grades),
                medie_generala=overall_avg,
                total_absente=tot_abs,
                absente_nemotivate=nemot_abs,
                total_mentiuni=len(remarks),
                recent_grades=[grade_service._to_response(g) for g in grades[:5]],
                recent_absences=[absence_service._to_response(a) for a in absences[:5]],
                recent_remarks=[remark_service._to_response(r) for r in remarks[:5]],
                unread_notifications=unread_notifs,
            )

        if role == UserRole.PROFESOR.value:
            grades = await grade_repository.get_by_teacher(db, current_user.id_utilizator)
            return DashboardSummary(
                rol=role,
                nume=current_user.nume,
                total_note=len(grades),
                medie_generala=None,
                total_absente=0,
                absente_nemotivate=0,
                total_mentiuni=0,
                recent_grades=[grade_service._to_response(g) for g in grades[:5]],
                recent_absences=[],
                recent_remarks=[],
                unread_notifications=unread_notifs,
            )

        return DashboardSummary(
            rol=role,
            nume=current_user.nume,
            total_note=0,
            medie_generala=None,
            total_absente=0,
            absente_nemotivate=0,
            total_mentiuni=0,
            recent_grades=[],
            recent_absences=[],
            recent_remarks=[],
            unread_notifications=unread_notifs,
        )

dashboard_service = DashboardService()
