from enum import Enum
from app.db.models import UserRole

class PermissionCode(str, Enum):
    GRADES_READ = "grades:read"
    GRADES_CREATE = "grades:create"
    GRADES_UPDATE = "grades:update"
    GRADES_DELETE = "grades:delete"

    ABSENCES_READ = "absences:read"
    ABSENCES_CREATE = "absences:create"
    ABSENCES_MOTIVATE = "absences:motivate"
    ABSENCES_DELETE = "absences:delete"

    REMARKS_READ = "remarks:read"
    REMARKS_CREATE = "remarks:create"
    REMARKS_DELETE = "remarks:delete"

    STUDENTS_READ = "students:read"
    STUDENTS_MANAGE = "students:manage"
    CLASSES_READ = "classes:read"
    CLASSES_MANAGE = "classes:manage"

    SUBJECTS_READ = "subjects:read"
    SUBJECTS_MANAGE = "subjects:manage"

    NOTIFICATIONS_READ = "notifications:read"
    NOTIFICATIONS_SEND = "notifications:send"

    ANALYTICS_READ = "analytics:read"

PERMISSION_DESCRIPTIONS = {
    PermissionCode.GRADES_READ: "Vizualizare note si medii",
    PermissionCode.GRADES_CREATE: "Adaugare nota noua elevului",
    PermissionCode.GRADES_UPDATE: "Modificare nota acordata",
    PermissionCode.GRADES_DELETE: "Stergere nota",

    PermissionCode.ABSENCES_READ: "Vizualizare absente",
    PermissionCode.ABSENCES_CREATE: "Inregistrare absenta",
    PermissionCode.ABSENCES_MOTIVATE: "Motivare absenta elev",
    PermissionCode.ABSENCES_DELETE: "Stergere absenta",

    PermissionCode.REMARKS_READ: "Vizualizare mentiuni si observatii",
    PermissionCode.REMARKS_CREATE: "Adaugare mentiune sau observatie",
    PermissionCode.REMARKS_DELETE: "Stergere mentiune",

    PermissionCode.STUDENTS_READ: "Consultare lista elevi",
    PermissionCode.STUDENTS_MANAGE: "Administrare conturi elevi si asocieri parinti",

    PermissionCode.CLASSES_READ: "Vizualizare clase si orare/incadrari",
    PermissionCode.CLASSES_MANAGE: "Creare si editare clase de elevi",

    PermissionCode.SUBJECTS_READ: "Vizualizare catalog materii",
    PermissionCode.SUBJECTS_MANAGE: "Administrare materii scolare",

    PermissionCode.NOTIFICATIONS_READ: "Primire si citire notificari",
    PermissionCode.NOTIFICATIONS_SEND: "Transmitere notificari catre elevi/parinti",

    PermissionCode.ANALYTICS_READ: "Consultare rapoarte academice, statistici si grafice",
}

ROLE_PERMISSIONS_MAP: dict[UserRole, list[PermissionCode]] = {
    UserRole.ADMINISTRATOR: [
        PermissionCode.GRADES_READ,
        PermissionCode.GRADES_CREATE,
        PermissionCode.GRADES_UPDATE,
        PermissionCode.GRADES_DELETE,
        PermissionCode.ABSENCES_READ,
        PermissionCode.ABSENCES_CREATE,
        PermissionCode.ABSENCES_MOTIVATE,
        PermissionCode.ABSENCES_DELETE,
        PermissionCode.REMARKS_READ,
        PermissionCode.REMARKS_CREATE,
        PermissionCode.REMARKS_DELETE,
        PermissionCode.STUDENTS_READ,
        PermissionCode.STUDENTS_MANAGE,
        PermissionCode.CLASSES_READ,
        PermissionCode.CLASSES_MANAGE,
        PermissionCode.SUBJECTS_READ,
        PermissionCode.SUBJECTS_MANAGE,
        PermissionCode.NOTIFICATIONS_READ,
        PermissionCode.NOTIFICATIONS_SEND,
        PermissionCode.ANALYTICS_READ,
    ],
    UserRole.PROFESOR: [
        PermissionCode.GRADES_READ,
        PermissionCode.GRADES_CREATE,
        PermissionCode.GRADES_UPDATE,
        PermissionCode.GRADES_DELETE,
        PermissionCode.ABSENCES_READ,
        PermissionCode.ABSENCES_CREATE,
        PermissionCode.ABSENCES_MOTIVATE,
        PermissionCode.ABSENCES_DELETE,
        PermissionCode.REMARKS_READ,
        PermissionCode.REMARKS_CREATE,
        PermissionCode.REMARKS_DELETE,
        PermissionCode.STUDENTS_READ,
        PermissionCode.CLASSES_READ,
        PermissionCode.SUBJECTS_READ,
        PermissionCode.NOTIFICATIONS_READ,
        PermissionCode.NOTIFICATIONS_SEND,
        PermissionCode.ANALYTICS_READ,
    ],
    UserRole.ELEV: [
        PermissionCode.GRADES_READ,
        PermissionCode.ABSENCES_READ,
        PermissionCode.REMARKS_READ,
        PermissionCode.CLASSES_READ,
        PermissionCode.SUBJECTS_READ,
        PermissionCode.NOTIFICATIONS_READ,
        PermissionCode.ANALYTICS_READ,
    ],
    UserRole.PARINTE: [
        PermissionCode.GRADES_READ,
        PermissionCode.ABSENCES_READ,
        PermissionCode.REMARKS_READ,
        PermissionCode.CLASSES_READ,
        PermissionCode.SUBJECTS_READ,
        PermissionCode.NOTIFICATIONS_READ,
        PermissionCode.ANALYTICS_READ,
    ],
}
